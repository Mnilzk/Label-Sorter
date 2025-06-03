import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import easyocr
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import numpy as np
import os

st.set_page_config(page_title="Label Sorter", layout="centered")
st.title("Label Sorter (No zbar/pyzbar required)")

st.info(
    "Having trouble reading a barcode or label? "
    "If you’re using Google Chrome, right-click the label image and select "
    "'Search image with Google Lens' for more options."
)

uploaded_pdf = st.file_uploader("Upload your PDF with labels", type=["pdf"])
uploaded_csv = st.file_uploader("Upload your CSV order file", type=["csv", "xlsx"])

if uploaded_pdf and uploaded_csv:
    st.write("Extracting text from labels, please wait...")
    reader = easyocr.Reader(['en'], gpu=False)

    # --- 1. Read the CSV or XLSX order file ---
    try:
        if uploaded_csv.name.endswith('.xlsx'):
            df_orders = pd.read_excel(uploaded_csv)
        else:
            df_orders = pd.read_csv(uploaded_csv)
        order_codes = df_orders.iloc[:, 0].astype(str).tolist()
    except Exception as e:
        st.error(f"Could not read the order file: {e}")
        st.stop()

    # --- 2. Convert PDF pages to images ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
        tf.write(uploaded_pdf.read())
        tf.flush()
        try:
            images = convert_from_path(tf.name, dpi=300)
        except Exception as e:
            st.error(f"Could not read PDF file: {e}")
            st.stop()

    # --- 3. Extract codes from each page using OCR ---
    pdf_labels = []
    for idx, img in enumerate(images):
        img_rgb = img.convert("RGB")
        img_np = np.array(img_rgb)
        result = reader.readtext(img_np, detail=0)
        code_found = None
        for r in result:
            for code in order_codes:
                if code.strip() in r:
                    code_found = code
                    break
            if code_found:
                break
        pdf_labels.append({
            "page_idx": idx,
            "ocr": result,
            "order_code": code_found
        })

    # --- 4. Sort PDF pages according to CSV order ---
    code_to_page = {label["order_code"]: label["page_idx"] for label in pdf_labels if label["order_code"]}
    pages_sorted = [code_to_page.get(code) for code in order_codes if code in code_to_page]

    # --- 5. Create a new PDF in correct order ---
    out_pdf = fitz.open()
    original_pdf = fitz.open(tf.name)
    for page_idx in pages_sorted:
        if page_idx is not None:
            out_pdf.insert_pdf(original_pdf, from_page=page_idx, to_page=page_idx)
    output_path = tempfile.mktemp(suffix=".pdf")
    out_pdf.save(output_path)

    # --- 6. Download button for result ---
    with open(output_path, "rb") as out_file:
        st.download_button("Download reordered PDF", data=out_file, file_name="sorted_labels.pdf")

    # --- 7. Show extracted codes per page for debugging ---
    st.subheader("Extracted label codes per page:")
    for idx, label in enumerate(pdf_labels):
        st.write(f"Page {idx+1}: {label['ocr']}, Matched code: {label['order_code']}")

    # Clean up temp file(s)
    try:
        os.remove(tf.name)
        os.remove(output_path)
    except Exception:
        pass

else:
    st.info("Upload both a PDF and CSV/XLSX order file to begin.")
