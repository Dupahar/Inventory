Inventory Comparison Tool

A web-based tool for comparing two Excel files containing inventory data. The tool checks for discrepancies between:

    OpeningQty (Opening Stock)
    QtyIn (Stock In)
    QtyOut (Stock Out)
    ClosingQty (Closing Stock)

Features

    Simple web interface for uploading two Excel files
    Automatic detection of matching columns between files
    Visual highlighting of discrepancies
    Calculation of differences between values
    Compatible with .xls and .xlsx file formats

Installation Instructions

    Ensure you have Python 3.7+ installed
    Clone or download this repository
    Create and activate a virtual environment (recommended):

    python -m venv venv

    # On Windows
    venv\Scripts\activate

    # On macOS/Linux
    source venv/bin/activate

    Install the required packages:

    pip install -r requirements.txt

    Run the application:

    python app.py

    Open your web browser and navigate to:

    http://127.0.0.1:5000

File Structure

inventory_comparison_tool/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
└── templates/
    ├── upload.html        # File upload page
    └── results.html       # Comparison results page

How to Use

    Launch the application using the instructions above
    On the main page, upload your two inventory Excel files:
        Previous/Old inventory file (File 1)
        Current/New inventory file (File 2)
    Click "Compare Files"
    Review the results:
        Green cells indicate matching values
        Red cells indicate discrepancies
        The "_diff" columns show the numerical difference between values

Excel File Format Requirements

Your Excel files should contain the following columns:

    An item identifier column (e.g., "Item", "ItemCode", "SKU")
    "OpeningQty" - Beginning inventory
    "QtyIn" - Items received
    "QtyOut" - Items sold/used
    "ClosingQty" - Ending inventory

Troubleshooting

    If you encounter a "No common item identifier column" error, ensure both Excel files have a matching column name for item identification (like "Item", "ItemCode", etc.)
    For large Excel files, the application may take a few moments to process the comparison

