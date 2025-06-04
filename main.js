const pdfjsLib = window['pdfjs-dist/build/pdf'];
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.2.67/pdf.worker.min.js';

const tesseractWorker = Tesseract.createWorker();

async function extractImagesFromPDF(pdfData) {
  const loadingTask = pdfjsLib.getDocument({ data: pdfData });
  const pdf = await loadingTask.promise;
  let images = [];
  for (let i = 0; i < pdf.numPages; i++) {
    const page = await pdf.getPage(i + 1);
    const viewport = page.getViewport({ scale: 2 });
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    await page.render({ canvasContext: context, viewport }).promise;
    images.push(canvas.toDataURL());
  }
  return images;
}

function parseCSVorXLSX(file, callback) {
  const reader = new FileReader();
  reader.onload = function(e) {
    let data = new Uint8Array(e.target.result);
    let workbook = XLSX.read(data, {type: 'array'});
    let sheet = workbook.Sheets[workbook.SheetNames[0]];
    let json = XLSX.utils.sheet_to_json(sheet, {header:1});
    let codes = json.map(row => String(row[0])).filter(Boolean);
    callback(codes);
  };
  reader.readAsArrayBuffer(file);
}

async function ocrImage(imageDataURL) {
  await tesseractWorker.load();
  await tesseractWorker.loadLanguage('eng');
  await tesseractWorker.initialize('eng');
  const { data: { text } } = await tesseractWorker.recognize(imageDataURL);
  return text;
}

function downloadPDF(pagesDataURLs) {
  const pdf = new jspdf.jsPDF();
  pagesDataURLs.forEach((dataUrl, idx) => {
    if(idx !== 0) pdf.addPage();
    pdf.addImage(dataUrl, 'JPEG', 0, 0, 210, 297); // A4 size
  });
  pdf.save('reordered_labels.pdf');
}

document.getElementById('processBtn').onclick = async () => {
  const pdfFile = document.getElementById('pdfInput').files[0];
  const orderFile = document.getElementById('orderInput').files[0];
  const progress = document.getElementById('progress');
  if (!pdfFile || !orderFile) {
    progress.textContent = "Please upload both files.";
    return;
  }
  progress.textContent = "Parsing order file...";
  parseCSVorXLSX(orderFile, async orderCodes => {
    progress.textContent = "Extracting images from PDF...";
    const pdfData = await pdfFile.arrayBuffer();
    const images = await extractImagesFromPDF(pdfData);

    progress.textContent = "Running OCR on labels...";
    let codeToImage = {};
    for (let i = 0; i < images.length; i++) {
      progress.textContent = `OCR on page ${i + 1} of ${images.length}...`;
      let ocrText = await ocrImage(images[i]);
      for (let code of orderCodes) {
        if (ocrText.includes(code)) {
          codeToImage[code] = images[i];
          break;
        }
      }
    }
    progress.textContent = "Reordering pages and generating PDF...";

    let pagesInOrder = [];
    for (let code of orderCodes) {
      if (codeToImage[code]) pagesInOrder.push(codeToImage[code]);
    }

    if (!pagesInOrder.length) {
      progress.textContent = "No matching codes found!";
      return;
    }

    // Use jsPDF to save PDF
    const jsPDFScript = document.createElement('script');
    jsPDFScript.src = "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js";
    jsPDFScript.onload = () => {
      downloadPDF(pagesInOrder);
      progress.textContent = "Done! Download should start.";
    };
    document.body.appendChild(jsPDFScript);
  });
};
