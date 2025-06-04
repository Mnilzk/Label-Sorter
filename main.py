import io
import csv
from js import setProgress, setMessage

def sort_labels_browser(pdf_data, order_data, setProgress, setMessage):
    import PyPDF2

    setMessage("Reading CSV...")
    # Read the CSV as a list of codes (first column)
    codes = []
    reader = csv.reader(io.BytesIO(order_data))
    for row in reader:
        if row and row[0].strip():
            codes.append(row[0].strip())

    setMessage("Reading PDF...")
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
    num_pages = len(pdf_reader.pages)

    # For demo: assume code matches page text (you can customize logic)
    page_map = {}
    setMessage("Scanning PDF pages...")
    for i, page in enumerate(pdf_reader.pages):
        setProgress(int(100 * i / max(num_pages, 1)))
        txt = page.extract_text() or ""
        for code in codes:
            if code in txt:
                page_map[code] = i
    setProgress(100)

    setMessage("Building output PDF...")
    writer = PyPDF2.PdfWriter()
    for code in codes:
        if code in page_map:
            writer.add_page(pdf_reader.pages[page_map[code]])
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
