import streamlit as st
# ... any other imports
st.info(
    "Having trouble reading a barcode or label? "
    "If you’re using Google Chrome, right-click the label image and select "
    "'Search image with Google Lens' for more options."
)
import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import easyocr
import tempfile
from pdf2image import convert_from_path
from PIL import Image

st.title("Label Sorter without zbar/pyzbar")

uploaded_pdf = st.file_uploader("Upload your PDF with labels", type=["pdf"])
uploaded_csv = st.file_uploader("Upload your CSV order file", type=["csv", "xlsx"])

if uploaded_pdf and uploaded_csv:
    st.write("Extracting text from labels, please wait...")
    reader = easyocr.Reader(['en'], gpu=False)

    # 1. Read CSV order list
    if uploaded_csv.name.endswith('.xlsx'):
        df_orders = pd.read_excel(uploaded_csv)
    else:
        df_orders = pd.read_csv(uploaded_csv)
    order_codes = df_orders.iloc[:, 0].astype(str).tolist()  # Adjust if needed

    # 2. Convert PDF to images
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
        tf.write(uploaded_pdf.read())
        tf.flush()
        images = convert_from_path(tf.name, dpi=300)

    # 3. Extract codes from images with EasyOCR
    pdf_labels = []
    for idx, img in enumerate(images):
        img_rgb = img.convert("RGB")
        img_np = np.array(img_rgb)
        result = reader.readtext(img_np, detail=0)
        code_found = None
        # Try to match OCR output to your order codes
        for r in result:
            for code in order_codes:
                if code in r:
                    code_found = code
                    break
            if code_found:
                break
        pdf_labels.append({
            "page_idx": idx,
            "ocr": result,
            "order_code": code_found
        })

    # 4. Sort PDF pages according to CSV order
    code_to_page = {label["order_code"]: label["page_idx"] for label in pdf_labels if label["order_code"]}
    pages_sorted = [code_to_page.get(code) for code in order_codes if code in code_to_page]

    # 5. Make new PDF
    out_pdf = fitz.open()
    original_pdf = fitz.open(tf.name)
    for page_idx in pages_sorted:
        if page_idx is not None:
            out_pdf.insert_pdf(original_pdf, from_page=page_idx, to_page=page_idx)
    output_path = tempfile.mktemp(suffix=".pdf")
    out_pdf.save(output_path)

    with open(output_path, "rb") as out_file:
        st.download_button("Download reordered PDF", data=out_file, file_name="sorted_labels.pdf")

    # Debug info
    st.write("Extracted label codes (per page):")
    for idx, label in enumerate(pdf_labels):
        st.write(f"Page {idx+1}: {label['ocr']}, Matched code: {label['order_code']}")

else:
    st.info("Upload both a PDF and CSV/XLSX order file to begin.")
