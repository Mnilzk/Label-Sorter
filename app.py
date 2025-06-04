const form = document.querySelector('form');
form.onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const response = await fetch('https://YOUR-BACKEND-URL/process', {
        method: 'POST',
        body: formData,
    });
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "sorted_labels.pdf";
        a.click();
        window.URL.revokeObjectURL(url);
    } else {
        alert('Processing failed!');
    }
};
