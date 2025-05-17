from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
import pandas as pd
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'inventory_comparison_tool')

# Allowed extensions for upload
ALLOWED_EXT = {'xls', 'xlsx', 'csv'}
# Required headers
REQUIRED_HEADERS = ['Item Details', 'Op. Qty.', 'Qty. In', 'Qty. Out', 'Cl. Qty.']


def allowed_file(fname):
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def load_and_normalize(file_stream, ext):
    """
    Reads raw Excel/CSV, detects header row by matching REQUIRED_HEADERS,
    and returns a DataFrame with proper columns.
    """
    # Read raw with no header
    if ext == 'csv':
        raw = pd.read_csv(file_stream, header=None, dtype=str)
    else:
        raw = pd.read_excel(file_stream, header=None, dtype=str, engine='openpyxl')
    # Find header row index
    header_idx = None
    for i in range(min(20, len(raw))):
        row = raw.iloc[i].astype(str).tolist()
        matches = sum(1 for h in REQUIRED_HEADERS if h in row)
        if matches >= 3:
            header_idx = i
            break
    if header_idx is None:
        # fallback to first row
        header_idx = 0
    # Use header row and data below
    df = raw.iloc[header_idx+1:].copy()
    df.columns = [str(c) for c in raw.iloc[header_idx]]
    # Drop any fully empty columns
    df = df.dropna(axis=1, how='all')
    return df


def compare_single(df):
    # Rename columns
    df = df.rename(columns={
        'Item Details': 'Item',
        'Op. Qty.': 'OpeningQty',
        'Qty. In': 'QtyIn',
        'Qty. Out': 'QtyOut',
        'Cl. Qty.': 'ClosingQty'
    })
    # Ensure numeric
    for col in ['OpeningQty','QtyIn','QtyOut','ClosingQty']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    # Compute
    df['ExpectedClosingQty'] = df['OpeningQty'] + df['QtyIn'] - df['QtyOut']
    df['BalanceMatch'] = df['ClosingQty'] == df['ExpectedClosingQty']
    df['Discrepancy'] = df['ClosingQty'] - df['ExpectedClosingQty']
    df = df[df['Item'].notna()]
    return df


@app.route('/', methods=['GET'])
def upload_page():
    return render_template('upload.html')


@app.route('/compare', methods=['POST'])
def compare():
    single = 'single_file_mode' in request.form
    files = ['file1'] if single else ['file1','file2']
    # Validate
    for key in files:
        f = request.files.get(key)
        if not f or not allowed_file(f.filename):
            flash('Please upload valid file(s)', 'error')
            return render_template('upload.html'), 400
    # Load & normalize
    dfs = {}
    for key in files:
        f = request.files[key]
        ext = f.filename.rsplit('.',1)[1].lower()
        fstream = BytesIO(f.read())
        dfs[key] = load_and_normalize(fstream, ext)
    # Single-file mode
    if single:
        df = dfs['file1']
        missing = [h for h in REQUIRED_HEADERS if h not in df.columns]
        if missing:
            flash(f"Missing required columns: {', '.join(missing)}", 'error')
            return render_template('upload.html'), 400
        df = compare_single(df)
        display_cols = ['Item','OpeningQty','QtyIn','QtyOut','ExpectedClosingQty','ClosingQty','BalanceMatch','Discrepancy']
        res = df[display_cols]
        # Style
        styled = res.style.applymap(lambda v: 'background:#ffcccc' if v is False else '', subset=['BalanceMatch'])
        return render_template('results.html', table=styled.to_html(classes='table table-bordered'), single=True, count=(~df['BalanceMatch']).sum())
    # Two-file mode
    df1, df2 = dfs['file1'], dfs['file2']
    # Compare single to ensure columns
    for df in (df1, df2):
        missing = [h for h in REQUIRED_HEADERS if h not in df.columns]
        if missing:
            flash(f"Missing required columns in one file: {', '.join(missing)}", 'error')
            return render_template('upload.html'), 400
    # Process both
    df1 = compare_single(df1)
    df2 = compare_single(df2)
    # Merge on Item
    merged = df1.merge(df2, on='Item', suffixes=('_old','_new'), how='outer')
    result = merged[['Item']].copy()
    discrepancies=False
    for col in ['OpeningQty','QtyIn','QtyOut','ClosingQty']:
        o = merged[f"{col}_old"].fillna(0)
        n = merged[f"{col}_new"].fillna(0)
        result[f"{col}_old"] = o
        result[f"{col}_new"] = n
        match = o==n
        result[f"{col}_match"] = match
        result[f"{col}_diff"] = n-o
        discrepancies = discrepancies or not match.all()
    styled = result.style.applymap(lambda v: 'background:#ffcccc' if v is False else '', subset=[c for c in result.columns if c.endswith('_match')])
    return render_template('results.html', table=styled.to_html(classes='table table-bordered'), single=False, discrepancies=discrepancies)

if __name__=='__main__':
    app.run(debug=True, use_reloader=False)
