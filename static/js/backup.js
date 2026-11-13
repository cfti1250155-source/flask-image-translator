// バックアップ（書き出し／読み込み）とデータ削除。保存先はこの端末の localStorage
const BKEY = 'tl_last_backup_v1';
const BACKUP_VERSION = 1;
const BACKUP_MAX_BYTES = 5 * 1024 * 1024;
const CHAT_MAX = 100;

const fmt = (s, vars) => String(s).replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m));
const str = (v, max) => (typeof v === 'string' ? v.slice(0, max) : '');
const num = (v, d) => (typeof v === 'number' && isFinite(v) ? v : d);

function readJSON(key, fallback) {
    try {
        const v = JSON.parse(localStorage.getItem(key) || 'null');
        return v === null ? fallback : v;
    } catch (e) { return fallback; }
}

function collectBackup() {
    return {
        app: 'tookie',
        version: BACKUP_VERSION,
        exportedAt: new Date().toISOString(),
        data: {
            history: loadHistory(),
            glossary: loadGlossary(),
            chat: loadChat(),
            vocab: loadVocab(),
            convLangs: readJSON(CKEY, null),
            chatPrefs: readJSON(PREFKEY, null),
        },
    };
}

// ---- 読み込み時の検査（壊れた／悪意のあるファイルから守る） ----
function cleanHistoryItem(e) {
    if (!e || typeof e !== 'object') return null;
    const out = str(e.out, 5000);
    if (!out) return null;
    return {
        id: str(e.id, 40) || uid(), ts: num(e.ts, Date.now()), fav: e.fav === true,
        mode: str(e.mode, 20) || 'text', src: str(e.src, 5000), out,
        srcLang: str(e.srcLang, 60), tgt: str(e.tgt, 60), tcode: str(e.tcode, 20),
    };
}
function cleanGlossaryItem(e) {
    if (!e || typeof e !== 'object') return null;
    const term = str(e.term, 300).trim(), meaning = str(e.meaning, 5000).trim(), to = str(e.to, 60);
    if (!term || !meaning || !langByName(to)) return null;
    return { id: str(e.id, 40) || uid(), kind: e.kind === 'example' ? 'example' : 'term', term, meaning, to, ts: num(e.ts, Date.now()) };
}
function cleanChatItem(e) {
    if (!e || typeof e !== 'object') return null;
    const src = str(e.src, 1000), out = str(e.out, 5000);
    if (!src || !out) return null;
    return {
        id: str(e.id, 40) || uid(), side: e.side === 'B' ? 'B' : 'A', src, out,
        srcLang: str(e.srcLang, 60), tgt: str(e.tgt, 60), tcode: str(e.tcode, 20), ts: num(e.ts, Date.now()),
    };
}
function cleanVocabItem(e) {
    if (!e || typeof e !== 'object') return null;
    const src = str(e.src, 500).trim(), out = str(e.out, 500).trim();
    if (!src || !out) return null;
    return {
        id: str(e.id, 40) || uid(), ts: num(e.ts, Date.now()), src, out,
        srcLang: str(e.srcLang, 60), tgt: str(e.tgt, 60), tcode: str(e.tcode, 20), pron: str(e.pron, 500),
        box: Math.max(0, Math.min(SRS_DAYS.length - 1, Math.round(num(e.box, 0)))), due: num(e.due, 0),
    };
}
const cleanList = (raw, fn, cap) => (Array.isArray(raw) ? raw.slice(0, cap).map(fn).filter(Boolean) : []);

function parseBackup(text) {
    let obj;
    try { obj = JSON.parse(text); } catch (e) { return null; }
    if (!obj || obj.app !== 'tookie' || typeof obj.data !== 'object' || !obj.data) return null;
    if (num(obj.version, 0) > BACKUP_VERSION) return null;
    const d = obj.data;
    return {
        history: cleanList(d.history, cleanHistoryItem, 2000),
        glossary: cleanList(d.glossary, cleanGlossaryItem, 2000),
        chat: cleanList(d.chat, cleanChatItem, 500),
        vocab: cleanList(d.vocab, cleanVocabItem, VMAX),
    };
}

// ---- 統合（同じ項目は新しい方を残す。今ある履歴は消さない） ----
function mergeById(cur, inc, keyFn) {
    const map = new Map();
    cur.concat(inc).forEach(e => {
        const k = keyFn(e), old = map.get(k);
        if (!old || (e.ts || 0) >= (old.ts || 0)) map.set(k, Object.assign({}, old || {}, e, old && old.fav ? { fav: true } : {}));
    });
    return Array.from(map.values());
}

function applyBackup(b) {
    let hist = mergeById(loadHistory(), b.history, e => e.id).sort((a, c) => c.ts - a.ts);
    let n = 0;
    hist = hist.filter(x => x.fav || ++n <= HMAX);
    saveHistory(hist);

    let gl = mergeById(loadGlossary(), b.glossary, e => e.kind + '|' + e.to + '|' + e.term).sort((a, c) => c.ts - a.ts);
    n = 0;
    gl = gl.filter(e => e.kind !== 'example' || ++n <= GMAX_EXAMPLES);
    saveGlossary(gl);

    const chat = mergeById(loadChat(), b.chat, e => e.id).sort((a, c) => a.ts - c.ts).slice(-CHAT_MAX);
    saveChat(chat);

    saveVocab(mergeById(loadVocab(), b.vocab, e => e.src + '|' + e.tgt).sort((a, c) => c.ts - a.ts).slice(0, VMAX));
    return { history: b.history.length, glossary: b.glossary.length, chat: b.chat.length };
}

function refreshDataViews() {
    const log = $('conv-log');
    if (log) {  // オフライン画面にはチャット欄が無い
        log.replaceChildren();
        $('conv-empty').classList.remove('hidden');
        loadChat().forEach(m => buildBubble(m));
    }
    renderHistory();
    renderDataInfo();
}

function setDataStatus(text, bad) {
    const el = $('data-status');
    el.textContent = text || '';
    el.classList.toggle('text-red-300', !!bad);
    el.classList.toggle('text-emerald-300', !bad);
}

// ---- 書き出し ----
async function exportBackup() {
    const stamp = new Date().toISOString().slice(0, 10);
    const name = 'tookie-backup-' + stamp + '.json';
    const blob = new Blob([JSON.stringify(collectBackup(), null, 1)], { type: 'application/json' });
    try {
        const file = new File([blob], name, { type: 'application/json' });
        // iPhone では共有シート（ファイルに保存）が最も確実
        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({ files: [file], title: name });
            markBackupDone();
            return;
        }
    } catch (e) {
        if (e && e.name === 'AbortError') return;   // 共有をキャンセルした
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    markBackupDone();
}

function markBackupDone() {
    try { localStorage.setItem(BKEY, String(Date.now())); } catch (e) {}
    setDataStatus(UI.backup_done, false);
    renderDataInfo();
}

// ---- 読み込み ----
function importBackup(input) {
    const f = input.files && input.files[0];
    input.value = '';
    if (!f) return;
    if (f.size > BACKUP_MAX_BYTES) { setDataStatus(UI.import_big, true); return; }
    const reader = new FileReader();
    reader.onerror = () => setDataStatus(UI.import_bad, true);
    reader.onload = () => {
        const b = parseBackup(String(reader.result || ''));
        if (!b || (!b.history.length && !b.glossary.length && !b.chat.length && !b.vocab.length)) { setDataStatus(UI.import_bad, true); return; }
        if (!confirm(fmt(UI.import_confirm_v, { h: b.history.length, g: b.glossary.length, v: b.vocab.length, c: b.chat.length }))) return;
        applyBackup(b);
        refreshDataViews();
        setDataStatus(fmt(UI.import_done_v, { h: b.history.length, g: b.glossary.length, v: b.vocab.length, c: b.chat.length }), false);
    };
    reader.readAsText(f);
}

// ---- 全削除（この端末のデータ＋サーバー側の設定Cookie） ----
async function deleteAllData() {
    if (!confirm(UI.data_delete_confirm)) return;
    try {
        Object.keys(localStorage).filter(k => k.indexOf('tl_') === 0).forEach(k => localStorage.removeItem(k));
    } catch (e) {}
    try { await caches.delete('tookie-mode'); } catch (e) {}
    try { await fetch('/api/clear-session', { method: 'POST' }); } catch (e) {}
    location.href = '/start';
}

// ---- 表示 ----
async function renderDataInfo() {
    $('data-counts').textContent = fmt(UI.data_counts_v, {
        h: loadHistory().length, g: loadGlossary().length, v: loadVocab().length, c: loadChat().length,
    });
    let last = 0;
    try { last = parseInt(localStorage.getItem(BKEY) || '0', 10) || 0; } catch (e) {}
    $('data-last').textContent = last ? UI.backup_last + ': ' + new Date(last).toLocaleDateString() : UI.backup_never;
    const stale = loadHistory().length + loadGlossary().length >= 10 && (!last || Date.now() - last > 30 * 86400000);
    $('data-remind').classList.toggle('hidden', !stale);
    let persisted = null;
    try { if (navigator.storage && navigator.storage.persisted) persisted = await navigator.storage.persisted(); } catch (e) {}
    $('data-persist').textContent = persisted === null ? '' : (persisted ? UI.storage_protected : UI.storage_unprotected);
}

// Safari が長く使われていないサイトのデータを消さないよう、永続化を依頼する（許可されない場合もある）
async function requestPersistence() {
    try { if (navigator.storage && navigator.storage.persist) await navigator.storage.persist(); } catch (e) {}
}
