// main.js
// Handles PDF and CSV/XLSX uploads, OCR, sorting, and PDF download (all in-browser)

// Utility: Load PDF file as ArrayBuffer
function readFileAsArrayBuffer(file) {
    return new Promise((resolve, reject) => {
        let reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsArrayBuffer(file);
    });
}

// Utility: Parse CSV or XLSX to array of codes
function parseOrderFile(file) {
    return new Promise((resolve) => {
        if (file.name.endsWith(".csv")) {
            Papa.parse(file, {
                complete: (results) => {
                    // Get all codes from first column
                    const codes = results.data.map(row => String(row[0]).trim()).filter(x => x && x !== "undefined");
                    resolve(codes);
                }
            });
        } else if (file.name.endsWith(".xlsx")) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: "array" });
                const sheet = workbook.Sheets[workbook.SheetNames[0]];
                const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });
                const codes = rows.map(row => String(row[0]).trim()).filter(x => x && x !== "undefined");
                resolve(codes);
            };
            reader.readAsArrayBuffer(file);
        }
    });
}

// Render PDF page to image (needed for OCR)
async function renderPdfPageToImage(pdf, pageIndex) {
    const page = await pdf.getPage(pageIndex + 1);
    const viewport = page.getViewport({ scale: 2 });
    const canvas = document.createElement('canvas');
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    const ctx = canvas.getContext('2d');
    await page.render({ canvasContext: ctx, viewport }).promise;
    return canvas;
}

// OCR image with Tesseract.js
async function ocrImage(canvas) {
    const { data: { text } } = await Tesseract.recognize(canvas, 'eng');
    return text;
}

// MAIN FUNCTION
document.getElementById('processBtn').onclick = async () => {
    const pdfFile = document.getElementById('pdfInput').files[0];
    const orderFile = document.getElementById('orderInput').files[0];
    if (!pdfFile || !orderFile) {
        alert("Please upload both PDF and CSV/XLSX files!");
        return;
    }
    document.getElementById('progress').textContent = "Parsing order file...";
    const orderCodes = await parseOrderFile(orderFile);

    document.getElementById('progress').textContent = "Loading PDF...";
    // Load PDF for extraction
    const pdfBytes = await readFileAsArrayBuffer(pdfFile);
    const pdfjsLib = window['pdfjs-dist/build/pdf'];
    pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.2.67/pdf.worker.min.js";
    const pdfDoc = await pdfjsLib.getDocument({ data: pdfBytes }).promise;

    // For creating new PDF
    const PDFLib = window.PDFLib;
    const outputPdf = await PDFLib.PDFDocument.create();

    let codeToPageIdx = {};
    let pageImgs = [];

    // OCR each page
    for (let i = 0; i < pdfDoc.numPages; i++) {
        document.getElementById('progress').textContent = `Processing page ${i + 1}/${pdfDoc.numPages}...`;
        const canvas = await renderPdfPageToImage(pdfDoc, i);
        const ocrText = await ocrImage(canvas);

        // Try to match with orderCodes
        for (let code of orderCodes) {
            if (ocrText.includes(code)) {
                codeToPageIdx[code] = i;
                break;
            }
        }
        // Save canvas as PNG for PDF creation
        pageImgs.push(canvas.toDataURL("image/png"));
    }

    // Add matched pages to output PDF in order
    for (let code of orderCodes) {
        if (codeToPageIdx[code] !== undefined) {
            const pngUrl = pageImgs[codeToPageIdx[code]];
            const page = await outputPdf.addPage();
            const pngImage = await outputPdf.embedPng(pngUrl);
            const { width, height } = pngImage.scale(1);
            page.setSize(width, height);
            page.drawImage(pngImage, { x: 0, y: 0, width, height });
        }
    }

    // Download the new PDF
    const outBytes = await outputPdf.save();
    const blob = new Blob([outBytes], { type: "application/pdf" });
    const link = document.getElementById("downloadLink");
    link.href = URL.createObjectURL(blob);
    link.download = "sorted_labels.pdf";
    link.style.display = "";
    link.textContent = "Download Reordered PDF";

    document.getElementById('progress').textContent = "Done!";
};
