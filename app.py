import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
from pyzbar.pyzbar import decode
import pytesseract
from PIL import Image
import io

st.set_page_config(page_title="Label Sorter (Barcode/OCR/Text)", layout="centered")
st.title("PDF Label Sorter with Barcode, OCR, and Text Matching")

uploaded_csv = st.file_uploader("Upload your CSV/XLSX file", type=["csv", "xlsx"])
uploaded_pdf = st.file_uploader("Upload your PDF label file", type="pdf")

def extract_codes_and_text(image):
    # Barcode/QR detection
    barcodes = decode(image)
    codes = [b.data.decode("utf-8") for b in barcodes]
    # OCR fallback
    text = pytesseract.image_to_string(image)
    return codes, text

def process_labels(csv_file, pdf_file):
    # Load order list
    if csv_file.name.endswith(".csv"):
        df = pd.read_csv(csv_file)
    else:
        df = pd.read_excel(csv_file)
    target_orders = df[df.columns[0]].astype(str).tolist()

    pdf_bytes = pdf_file.read()
    # Convert PDF pages to images
    images = convert_from_bytes(pdf_bytes, dpi=300)
    found_codes = []
    found_texts = []
    for img in images:
        codes, text = extract_codes_and_text(img)
        found_codes.append(codes)
        found_texts.append(text)
    
    # Open original PDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    output_pdf = fitz.open()
    log = []
    matched_pages = set()
    unmatched_orders = []

    for order in target_orders:
        matched = False
        # Try barcode/QR
        for idx, codes in enumerate(found_codes):
            if order in codes and idx not in matched_pages:
                output_pdf.insert_pdf(doc, from_page=idx, to_page=idx)
                log.append(f"Order {order}: matched barcode on page {idx+1}")
                matched_pages.add(idx)
                matched = True
                break
        if matched:
            continue
        # Try OCR/text
        for idx, text in enumerate(found_texts):
            if order in text and idx not in matched_pages:
                output_pdf.insert_pdf(doc, from_page=idx, to_page=idx)
                log.append(f"Order {order}: matched by OCR/text on page {idx+1}")
                matched_pages.add(idx)
                matched = True
                break
        if not matched:
            unmatched_orders.append(order)
            log.append(f"Order {order}: NOT FOUND in PDF")

    output_buffer = io.BytesIO()
    output_pdf.save(output_buffer)
    output_buffer.seek(0)

    log_txt = "\n".join(log)
    unmatched_txt = "\n".join(unmatched_orders)
    return output_buffer, log_txt, unmatched_txt

if uploaded_csv and uploaded_pdf:
    st.write("Press the button to process your PDF and match barcodes/text to your CSV.")
    if st.button("Process & Download Reordered PDF"):
        with st.spinner("Processing (this may take 1-2 minutes)..."):
            out_pdf, match_log, unmatched_log = process_labels(uploaded_csv, uploaded_pdf)
        st.success("Done!")
        st.download_button("Download Reordered PDF", out_pdf, file_name="Reordered_Labels.pdf", mime="application/pdf")
        st.write("### Match Report")
        st.text(match_log)
        st.download_button("Download Unmatched Orders (.txt)", unmatched_log, file_name="unmatched_orders.txt", mime="text/plain")
