import os
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image
from pyzbar.pyzbar import decode
import io
from pathlib import Path  # ✅ Add this line
import os
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image
from pyzbar.pyzbar import decode
import io

# === CONFIGURATION ===
pdf_file = "Toronto 02.05.2025 - 51.pdf"
csv_file = "Untitled spreadsheet - Sheet1.csv"
output_pdf = "Reordered_Label_PDF.pdf"
match_log_file = "match_log.txt"
missing_log_file = "missing_entries.txt"
dpi = 300

# === Load spreadsheet ===
df = pd.read_csv(csv_file)
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
tracking_col = next((col for col in df.columns if "tracking" in col), None)
name_col = next((col for col in df.columns if "name" in col), None)

df[tracking_col] = df[tracking_col].astype(str).str.upper().str.replace(" ", "")
df[name_col] = df[name_col].astype(str).str.upper().str.strip()
orders = df[[tracking_col, name_col]].itertuples(index=False, name=None)
order_dict = {tracking: {'name': name, 'page': None} for tracking, name in orders}

# === Convert PDF pages to images and decode barcodes ===
doc = fitz.open(pdf_file)
decoded_pages = {}
logs = []

for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    decoded = decode(img)

    found = False
    for d in decoded:
        data = d.data.decode("utf-8").strip().upper().replace(" ", "")
        if data in order_dict and order_dict[data]['page'] is None:
            order_dict[data]['page'] = i
            decoded_pages[data] = i
            logs.append(f"✅ Page {i+1}: Barcode matched → {data}")
            found = True
            break

    if not found:
        logs.append(f"❌ Page {i+1}: No matching barcode found.")

# === Reorder pages to match spreadsheet ===
ordered_pages = []
missing_entries = []

for tracking, info in order_dict.items():
    page_idx = info.get('page')
    if page_idx is not None:
        ordered_pages.append(doc.load_page(page_idx))
    else:
        missing_entries.append(f"{tracking} | {info['name']}")

# === Export reordered PDF ===
if ordered_pages:
    output_path = Path(output_pdf)
    output_doc = fitz.open()
    for page in ordered_pages:
        output_doc.insert_pdf(doc, from_page=page.number, to_page=page.number)
    output_doc.save(output_pdf)
    output_doc.close()

# === Save logs ===
with open(match_log_file, "w") as f:
    f.write("\n".join(logs))

with open(missing_log_file, "w") as f:
    f.write("\n".join(missing_entries))

print(f"✅ Done. Reordered PDF: {output_pdf}")
print(f"📝 Match log saved: {match_log_file}")
print(f"❌ Missing entries saved: {missing_log_file}")
