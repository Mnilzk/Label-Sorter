import js
from pyodide.ffi import to_js
import pandas as pd
import fitz  # PyMuPDF

def process_files(pdf_bytes, order_bytes, order_filename):
    # Read order list
    if order_filename.endswith('.csv'):
        from io import StringIO
        df_orders = pd.read_csv(StringIO(order_bytes.decode("utf-8")))
    elif order_filename.endswith('.xlsx'):
        from io import BytesIO
        df_orders = pd.read_excel(BytesIO(order_bytes))
    else:
        js.console.log("Unknown order file type")
        return None

    order_codes = df_orders.iloc[:, 0].astype(str).tolist()
    
    # Open PDF
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    code_to_page = {}

    # Very basic: look for code as raw text on each page (not barcode/OCR yet)
    for i, page in enumerate(pdf):
        text = page.get_text()
        for code in order_codes:
            if code in text:
                code_to_page[code] = i

    # Reorder pages
    out_pdf = fitz.open()
    for code in order_codes:
        page_num = code_to_page.get(code)
        if page_num is not None:
            out_pdf.insert_pdf(pdf, from_page=page_num, to_page=page_num)
    out_bytes = out_pdf.write()
    return out_bytes

def handle_files(pdf_bytes, order_bytes, order_filename):
    # This function is called by JS after files are uploaded
    out_bytes = process_files(pdf_bytes, order_bytes, order_filename)
    if out_bytes:
        js.send_result(to_js(out_bytes))
    else:
        js.send_result(None)
