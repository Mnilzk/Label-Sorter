import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import io

def sort_labels_browser(pdf_data, order_data, setProgress, setMessage):
    setMessage("Reading order CSV...")
    # Read CSV file to get order codes (assume first col)
    order_csv = io.BytesIO(order_data)
    orders = pd.read_csv(order_csv)
    order_codes = orders.iloc[:, 0].astype(str).tolist()

    setMessage("Reading PDF...")
    pdf_reader = PdfReader(io.BytesIO(pdf_data))
    n_pages = len(pdf_reader.pages)
    setMessage(f"PDF has {n_pages} pages.")

    # Use page number as "code" (in real use, add OCR/barcode here)
    # For demo, we assume codes appear as text in PDF page text.
    code_to_page = {}

    for i, page in enumerate(pdf_reader.pages):
        setProgress(int(100 * i / n_pages))
        text = page.extract_text() or ""
        for code in order_codes:
            if code in text:
                code_to_page[code] = i
                break

    setMessage("Reordering pages...")
    writer = PdfWriter()
    for code in order_codes:
        idx = code_to_page.get(code)
        if idx is not None:
            writer.add_page(pdf_reader.pages[idx])

    output = io.BytesIO()
    writer.write(output)
    setMessage("Done!")
    return output.getvalue()
