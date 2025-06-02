import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io

# --- Helper: Extract QR/barcode using OpenCV
def extract_qr_code(image):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img_cv)
    if data:
        return data.strip()
    return None

# --- Helper: OCR fallback
def extract_text_ocr(image):
    return pytesseract.image_to_string(image, config='--psm 6').strip()

# --- Helper: Process PDF, extract barcode/QR/label from each page as needed
def extract_labels_from_pdf(pdf_file):
    images = convert_from_bytes(pdf_file.read())
    labels = []
    for i, img in enumerate(images):
        label = extract_qr_code(img)
        if not label:
            label = extract_text_ocr(img)
        labels.append((i, label))
    return labels, images

# --- Streamlit UI ---
st.title("Label Sorter - No zbar Dependency")
csv_file = st.file_uploader("Upload CSV", type=["csv"])
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

if csv_file and pdf_file:
    st.info("Processing...")
    # Load CSV as DataFrame (adjust if needed)
    df = pd.read_csv(csv_file)
    # This assumes the column with labels is called 'Label' (change as needed)
    label_column = "Label"
    if label_column not in df.columns:
        label_column = st.selectbox("Select CSV label column:", df.columns)
    
    csv_labels = df[label_column].astype(str).tolist()
    pdf_labels, pdf_images = extract_labels_from_pdf(pdf_file)
    
    # Map label to page index
    label_to_page = {label: idx for idx, label in pdf_labels if label}
    
    # Reorder pages as per CSV
    output_images = []
    for label in csv_labels:
        idx = label_to_page.get(str(label))
        if idx is not None:
            output_images.append(pdf_images[idx])
        else:
            st.warning(f"Label not found in PDF: {label}")
    
    # Merge pages back to PDF
    if output_images:
        output_bytes = io.BytesIO()
        output_images[0].save(
            output_bytes,
            format="PDF",
            save_all=True,
            append_images=output_images[1:]
        )
        st.success("Done! Download your reordered PDF below.")
        st.download_button("Download Reordered PDF", data=output_bytes.getvalue(), file_name="reordered.pdf")
