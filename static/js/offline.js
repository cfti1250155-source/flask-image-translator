// オフライン画面の初期化（履歴・お気に入り・用語集・フレーズ集・データを開く）
document.addEventListener('DOMContentLoaded', () => {
    $('tab-history').classList.remove('hidden');
    populateLangSelect($('gl-to'), TARGET_LANG);
    setHistFilter(PHRASE_LANGS.length ? 'phrases' : 'all');
});
