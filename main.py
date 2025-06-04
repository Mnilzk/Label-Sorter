# main.py - for Pyodide (no pandas needed!)
import io
import csv
from PyPDF2 import PdfReader, PdfWriter

def sort_labels_browser(pdf_bytes, csv_bytes, setProgress=None, setMessage=None):
    if setMessage: setMessage("Reading order from CSV...")
    # Parse CSV order codes
    codes = []
    with io.StringIO(csv_bytes.tobytes().decode('utf-8')) as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():
                codes.append(row[0].strip())

    if setMessage: setMessage("Reading PDF...")
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    if setMessage: setMessage("Sorting pages (no OCR, barcode, or matching, just as demo)...")
    # This DEMO just adds all pages in original order (change to match logic)
    for idx, code in enumerate(codes):
        if idx < len(pdf.pages):
            writer.add_page(pdf.pages[idx])
        if setProgress:
            setProgress(int(100 * (idx + 1) / len(codes)))

    out_bytes = io.BytesIO()
    writer.write(out_bytes)
    return out_bytes.getvalue()
