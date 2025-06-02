import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import tempfile
import cv2
import numpy as np
import easyocr

st.title("Label Sorter (Cloud Compatible, No Zbar)")

uploaded_csv = st.file_uploader("Upload your CSV", type=["csv"])
uploaded_pdf = st.file_uploader("Upload your PDF", type=["pdf"])

@st.cache_data
def read_csv(file):
    df = pd.read_csv(file)
    return df

def pdf_page_to_image(page):
    pix = page.get_pixmap(dpi=300)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img

def detect_barcode_opencv(image):
    detector = cv2.wechat_qrcode_WeChatQRCode(
        "detect.prototxt", "detect.caffemodel",
        "sr.prototxt", "sr.caffemodel"
    )
    try:
        barcodes, _ = detector.detectAndDecode(image)
        return barcodes[0] if barcodes else None
    except:
        return None

def detect_text_easyocr(image):
    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(image)
    if results:
        return results[0][1]
    return None

def extract_barcodes_from_pdf(pdf_path, use_ocr_fallback=True):
    doc = fitz.open(pdf_path)
    barcode_results = []
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        image = pdf_page_to_image(page)
        barcode = detect_barcode_opencv(image)
        if barcode:
            barcode_results.append(barcode)
        elif use_ocr_fallback:
            text = detect_text_easyocr(image)
            barcode_results.append(text if text else "NOT FOUND")
        else:
            barcode_results.append("NOT FOUND")
    return barcode_results

if uploaded_csv and uploaded_pdf:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_pdf.read())
        pdf_path = temp_pdf.name

    df = read_csv(uploaded_csv)
    st.write("CSV Data Preview:", df.head())

    with st.spinner("Extracting barcodes..."):
        barcodes = extract_barcodes_from_pdf(pdf_path)
        st.write("Extracted Barcodes:", barcodes)

    # Implement your label matching logic below

    # st.download_button("Download Reordered PDF", result_bytes, file_name="reordered_labels.pdf")
