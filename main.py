import js
import io
import pandas as pd
from pyodide.ffi import create_proxy

def log(msg):
    js.console.log(msg)
    js.document.getElementById('progress').innerText = msg

def main(pdf_bytes, csv_bytes):
    log("Parsing order file...")
    # Parse CSV with pandas
    order_df = pd.read_csv(io.BytesIO(csv_bytes))
    codes = order_df.iloc[:, 0].astype(str).tolist()
    log(f"Read {len(codes)} order codes")

    log("Loading PDF (this may take a while)...")
    from PyPDF2 import PdfReader, PdfWriter
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    pdf_writer = PdfWriter()

    # Simple debug: show how many pages in original PDF
    log(f"Input PDF has {len(pdf_reader.pages)} pages.")

    # Naive barcode/OCR approach - you can wire up more later
    # For now, just output in the original order for testing
    for i, page in enumerate(pdf_reader.pages):
        pdf_writer.add_page(page)
        log(f"Added page {i+1}/{len(pdf_reader.pages)}")

    log("Writing output PDF...")
    out_buf = io.BytesIO()
    pdf_writer.write(out_buf)
    out_buf.seek(0)
    log("Done!")
    return out_buf.read()

# Expose the function to JS
def run_sort(pdf_bytes, csv_bytes):
    try:
        result = main(pdf_bytes, csv_bytes)
        js.handlePythonResult(result)
    except Exception as e:
        log(f"Error: {e}")

js.run_sort = create_proxy(run_sort)
