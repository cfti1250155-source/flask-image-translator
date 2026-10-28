// 言語選択バーの表示切り替え関数（テキストは両方、それ以外は翻訳先のみ中央表示）
function updateLanguageBar(mode) {
    const sourceLang = document.getElementById('source-lang-container');
    const swapBtn = document.getElementById('swap-lang-btn');
    const targetLang = document.getElementById('target-lang-container');
    
    if (mode === 'text') {
        if (sourceLang) sourceLang.style.display = 'block';
        if (swapBtn) swapBtn.style.display = 'flex';
        if (targetLang) {
            targetLang.style.width = '';
            targetLang.style.margin = '';
        }
    } else {
        if (sourceLang) sourceLang.style.display = 'none';
        if (swapBtn) swapBtn.style.display = 'none';
        if (targetLang) {
            targetLang.style.width = '100%';
            targetLang.style.maxWidth = '250px';
            targetLang.style.margin = '0 auto';
        }
    }
}

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', () => {
    // 初期の言語バー状態を設定（デフォルトは text）
    updateLanguageBar('text');

    // タブ切り替えボタンのクリックイベントを設定
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.id.replace('nav-', '');
            updateLanguageBar(mode);
        });
    });
});

// 画像フォーム送信処理
document.getElementById('upload-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('image-input');
    const submitBtn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    const resultContainer = document.getElementById('result-container');
    const ocrResult = document.getElementById('ocr-result');
    const translateResult = document.getElementById('translate-result');

    if (!fileInput || !fileInput.files[0]) return;

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);

    if (submitBtn) submitBtn.disabled = true;
    if (loading) loading.classList.remove('hidden');
    if (resultContainer) resultContainer.classList.add('hidden');

    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            if (ocrResult) ocrResult.textContent = data.ocr_text;
            if (translateResult) translateResult.textContent = data.translated_text;
            if (resultContainer) resultContainer.classList.remove('hidden');
        } else {
            alert('エラー: ' + (data.error || '処理に失敗しました'));
        }
    } catch (error) {
        alert('通信エラーが発生しました');
        console.error(error);
    } finally {
        if (submitBtn) submitBtn.disabled = false;
        if (loading) loading.classList.add('hidden');
    }
});