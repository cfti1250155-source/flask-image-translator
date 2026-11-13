// 表示・翻訳の設定（丁寧さ・読み方・文字サイズ・配色）。この端末の localStorage に保存する
const SKEY = 'tl_settings_v1';
const SETTING_DEFAULTS = { formality: 'auto', pron: true, fs: 'm', theme: 'dark' };
const SETTING_CHOICES = { formality: ['auto', 'formal', 'casual'], fs: ['m', 'l', 'xl'], theme: ['dark', 'light'] };

function loadSettings() {
    const st = Object.assign({}, SETTING_DEFAULTS);
    try {
        const saved = JSON.parse(localStorage.getItem(SKEY) || '{}') || {};
        Object.keys(SETTING_CHOICES).forEach(k => { if (SETTING_CHOICES[k].indexOf(saved[k]) >= 0) st[k] = saved[k]; });
        if (typeof saved.pron === 'boolean') st.pron = saved.pron;
    } catch (e) {}
    return st;
}

function saveSettings(st) {
    try { localStorage.setItem(SKEY, JSON.stringify(st)); } catch (e) {}
}

function applySettings(st) {
    const d = document.documentElement;
    if (st.theme === 'light') d.setAttribute('data-theme', 'light'); else d.removeAttribute('data-theme');
    if (st.fs === 'l' || st.fs === 'xl') {
        d.setAttribute('data-fs', st.fs);
        d.style.fontSize = st.fs === 'xl' ? '128%' : '114%';
    } else {
        d.removeAttribute('data-fs');
        d.style.fontSize = '';
    }
    const meta = document.querySelector('meta[name=theme-color]');
    if (meta) meta.setAttribute('content', st.theme === 'light' ? '#f1f5f9' : '#0f172a');
}

function renderSettings() {
    const st = loadSettings();
    document.querySelectorAll('#settings-section [data-setting]').forEach(group => {
        const key = group.getAttribute('data-setting');
        group.querySelectorAll('button[data-v]').forEach(b => {
            const on = b.getAttribute('data-v') === st[key];
            b.setAttribute('aria-pressed', on ? 'true' : 'false');
            b.className = 'set-opt px-2 py-2 rounded-xl text-xs font-semibold border border-slate-700 transition ' +
                (on ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-300');
        });
    });
    const pron = document.getElementById('set-pron');
    if (pron) pron.checked = !!st.pron;
}

function bindSettings() {
    document.querySelectorAll('#settings-section [data-setting]').forEach(group => {
        const key = group.getAttribute('data-setting');
        group.addEventListener('click', ev => {
            const b = ev.target.closest('button[data-v]');
            if (!b) return;
            const st = loadSettings();
            st[key] = b.getAttribute('data-v');
            saveSettings(st);
            applySettings(st);
            renderSettings();
        });
    });
    const pron = document.getElementById('set-pron');
    if (pron) pron.addEventListener('change', () => {
        const st = loadSettings();
        st.pron = pron.checked;
        saveSettings(st);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    applySettings(loadSettings());
    bindSettings();
    renderSettings();
});

// ヘッダーの歯車ボタン: 履歴タブの「設定」を開く
function openSettings() {
    switchTab('history');
    setHistFilter('settings');
    window.scrollTo(0, 0);
}