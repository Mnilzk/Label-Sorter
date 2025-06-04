import js
import pandas as pd
import io

def handle_sort_labels(event=None):
    # Get PDF bytes and order file bytes from JS global variables
    pdf_bytes = js.window.pdfBytes.to_py()
    order_bytes = js.window.orderBytes.to_py()
    order_name = js.window.orderFileName

    # Load order codes
    if order_name.endswith('.csv'):
        order_df = pd.read_csv(io.BytesIO(order_bytes))
    elif order_name.endswith('.xlsx'):
        order_df = pd.read_excel(io.BytesIO(order_bytes))
    else:
        js.window.showStatus("Unsupported order file type!", "error")
        return

    # Get first column as codes (make sure they're strings)
    order_codes = [str(code).strip() for code in order_df.iloc[:, 0] if str(code).strip() and str(code).lower() != "nan"]
    js.window.showStatus(f"Loaded {len(order_codes)} codes from order list.", "progress")

    # Use JS PDF.js and Tesseract to OCR/extract codes from each PDF page
    page_codes = js.window.extractPdfCodes().to_py()  # Returns array of OCRd strings per page

    # Map: code in page -> page idx
    code_to_page_idx = {}
    for idx, text in enumerate(page_codes):
        for code in order_codes:
            if code in text:
                code_to_page_idx[code] = idx
                break

    js.window.showStatus("Matched codes to PDF pages, reordering...", "progress")

    # Compose new PDF: call JS helper to reorder PDF using the page indexes
    sorted_pages = [code_to_page_idx[code] for code in order_codes if code in code_to_page_idx]
    if not sorted_pages:
        js.window.showStatus("No codes matched! Check if codes are visible in the labels.", "error")
        return

    # Call JS helper to generate new PDF, get bytes back
    new_pdf_bytes = js.window.makeSortedPdf(sorted_pages)
    js.window.triggerDownload(new_pdf_bytes, "sorted_labels.pdf")

    js.window.showStatus(f"Done! {len(sorted_pages)} labels sorted and ready to download.", "success")
