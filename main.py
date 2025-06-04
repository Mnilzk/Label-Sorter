import io
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter

def sort_labels_browser(pdf_data, csv_data, setProgress=None, setMessage=None):
    if setMessage:
        setMessage("Reading CSV...")
    # Read order codes from CSV
    csv_buf = io.BytesIO(csv_data)
    df = pd.read_csv(csv_buf)
    order_codes = df.iloc[:, 0].astype(str).tolist()
    if setMessage:
        setMessage("Reading PDF...")
    pdf = PdfReader(io.BytesIO(pdf_data))
    pages = pdf.pages
    found_pages = []
    # For demo, we simply put all pages in order (add your own code matching logic here)
    if setProgress:
        setProgress(10)
    for i, code in enumerate(order_codes):
        # This just grabs page by order (replace with your matching logic if you want)
        if i < len(pages):
            found_pages.append(pages[i])
        if setProgress:
            setProgress(int(10 + (i / len(order_codes)) * 90))
    writer = PdfWriter()
    for p in found_pages:
        writer.add_page(p)
    out_bytes = io.BytesIO()
    writer.write(out_bytes)
    if setProgress:
        setProgress(100)
    return out_bytes.getvalue()
