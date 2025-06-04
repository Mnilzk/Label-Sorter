import io
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter

def sort_labels_csv_only(pdf_data, order_data, setProgress, setMessage):
    # PDF in memory
    setMessage("Reading PDF...")
    pdf = PdfReader(io.BytesIO(pdf_data))
    total = len(pdf.pages)
    setProgress(0)

    # CSV codes
    setMessage("Reading CSV order codes...")
    csv_io = io.BytesIO(order_data)
    df = pd.read_csv(csv_io, header=None)
    codes = df.iloc[:,0].astype(str).tolist()

    # Dummy logic: Assume each PDF page contains order code somewhere in text
    setMessage("Scanning pages for order codes...")
    page_map = {}
    for i, page in enumerate(pdf.pages):
        setProgress(int((i/total)*100))
        text = page.extract_text() or ""
        for code in codes:
            if code in text:
                page_map[code] = i
                break
    setProgress(100)

    # Reorder pages to match CSV
    setMessage("Building output PDF...")
    writer = PdfWriter()
    found = 0
    for code in codes:
        if code in page_map:
            writer.add_page(pdf.pages[page_map[code]])
            found += 1
    setMessage(f"Done. Matched {found}/{len(codes)} codes.")

    # Output as bytes
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()
