document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('image-input');
    const submitBtn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    const resultContainer = document.getElementById('result-container');
    const ocrResult = document.getElementById('ocr-result');
    const translateResult = document.getElementById('translate-result');

    if (!fileInput.files[0]) return;

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);

    submitBtn.disabled = true;
    loading.classList.remove('hidden');
    resultContainer.classList.add('hidden');

    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            ocrResult.textContent = data.ocr_text;
            translateResult.textContent = data.translated_text;
            resultContainer.classList.remove('hidden');
        } else {
            alert('エラー: ' + (data.error || '処理に失敗しました'));
        }
    } catch (error) {
        alert('通信エラーが発生しました');
        console.error(error);
    } finally {
        submitBtn.disabled = false;
        loading.classList.add('hidden');
    }
});