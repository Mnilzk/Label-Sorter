import pandas as pd
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter

def sort_labels_browser(pdf_bytes, csv_text, setProgress, setMessage):
    setMessage("Parsing CSV...")
    # Read CSV
    order_codes = pd.read_csv(BytesIO(csv_text.encode('utf-8')), header=None)[0].astype(str).tolist()

    setMessage("Reading PDF...")
    pdf = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    setMessage("Extracting and sorting pages...")
    setProgress(10)
    page_matches = []
    for idx, page in enumerate(pdf.pages):
        # Extract text from page (PyPDF2)
        text = page.extract_text() or ""
        # Try to match one of the codes
        for code in order_codes:
            if code in text:
                page_matches.append((order_codes.index(code), idx))
                break

    # Sort by order in CSV
    page_matches.sort()
    for _, page_idx in page_matches:
        writer.add_page(pdf.pages[page_idx])

    setProgress(100)
    setMessage("Done!")
    outbuf = BytesIO()
    writer.write(outbuf)
    return outbuf.getvalue()
