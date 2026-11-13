// 履歴・お気に入り（localStorage）
const HKEY = 'tl_history_v1';
const HMAX = 200;
const GKEY = 'tl_glossary_v1';
const GMAX_EXAMPLES = 30;
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

function loadHistory() {
    try {
        const a = JSON.parse(localStorage.getItem(HKEY) || '[]');
        return Array.isArray(a) ? a : [];
    } catch (e) { return []; }
}

function saveHistory(list) {
    try { localStorage.setItem(HKEY, JSON.stringify(list)); } catch (e) {}
}

function addHistory(entry) {
    const list = loadHistory();
    const last = list[0];
    if (last && last.mode === entry.mode && last.src === entry.src && last.out === entry.out && last.tgt === entry.tgt && Date.now() - last.ts < 10 * 60 * 1000) {
        return last.id;
    }
    const e = Object.assign({}, entry, {
        id: uid(),
        ts: Date.now(),
        fav: false,
    });
    list.unshift(e);
    let n = 0;
    saveHistory(list.filter(x => x.fav || ++n <= HMAX));
    return e.id;
}

function updateHistory(id, fn) {
    const list = loadHistory();
    const e = list.find(x => x.id === id);
    if (!e) return null;
    fn(e);
    saveHistory(list);
    return e;
}

// 用語集・修正例
function loadGlossary() {
    try {
        const a = JSON.parse(localStorage.getItem(GKEY) || '[]');
        return Array.isArray(a) ? a : [];
    } catch (e) { return []; }
}

function saveGlossary(list) {
    try { localStorage.setItem(GKEY, JSON.stringify(list)); } catch (e) {}
}

function relevantGlossary(text, toLang) {
    const t = (text || '').toLowerCase();
    const g = loadGlossary().filter(e => e.to === toLang);
    const terms = g.filter(e => e.kind === 'term' && t.includes(e.term.toLowerCase())).slice(0, 15);
    const examples = g.filter(e => e.kind === 'example').slice(0, 3);
    return terms.concat(examples).map(e => ({ term: e.term, meaning: e.meaning, kind: e.kind }));
}

function upsertGlossary(kind, term, meaning, to) {
    term = (term || '').trim(); meaning = (meaning || '').trim();
    if (!term || !meaning) return;
    let list = loadGlossary().filter(e => !(e.kind === kind && e.to === to && e.term === term));
    list.unshift({ id: uid(), kind, term, meaning, to, ts: Date.now() });
    let n = 0;
    list = list.filter(e => e.kind !== 'example' || ++n <= GMAX_EXAMPLES);
    saveGlossary(list);
}

function learnCorrection(src, out, toLang) {
    if (src && src.length <= 300) upsertGlossary('example', src, out, toLang);
}

// チャット（キーはバックアップ機能でも使う）
const CKEY = 'tl_conv_langs_v1';
const CHATKEY = 'tl_chat_v1';
const PREFKEY = 'tl_chat_prefs_v1';

function loadChat() {
    try {
        const a = JSON.parse(localStorage.getItem(CHATKEY) || '[]');
        return Array.isArray(a) ? a : [];
    } catch (e) { return []; }
}
function saveChat(list) {
    try { localStorage.setItem(CHATKEY, JSON.stringify(list.slice(-100))); } catch (e) {}
}

// 単語帳（学習用）。box は覚えた度合い(0〜5)、due は次に復習する時刻
const VKEY = 'tl_vocab_v1';
const VMAX = 1000;
const SRS_DAYS = [0, 1, 3, 7, 14, 30];

function loadVocab() {
    try {
        const a = JSON.parse(localStorage.getItem(VKEY) || '[]');
        return Array.isArray(a) ? a : [];
    } catch (e) { return []; }
}

function saveVocab(list) {
    try { localStorage.setItem(VKEY, JSON.stringify(list)); } catch (e) {}
}

// 追加。同じ原文・同じ翻訳先がすでにあれば訳だけ更新して false を返す
function addVocab(entry) {
    const src = String(entry.src || '').trim().slice(0, 500);
    const out = String(entry.out || '').trim().slice(0, 500);
    if (!src || !out) return false;
    const list = loadVocab();
    const dup = list.find(x => x.src === src && x.tgt === entry.tgt);
    if (dup) {
        dup.out = out;
        dup.pron = String(entry.pron || '').slice(0, 500);
        saveVocab(list);
        return false;
    }
    list.unshift({
        id: uid(), ts: Date.now(), src, out,
        srcLang: entry.srcLang || '', tgt: entry.tgt || '', tcode: entry.tcode || '',
        pron: String(entry.pron || '').slice(0, 500), box: 0, due: 0,
    });
    saveVocab(list.slice(0, VMAX));
    return true;
}
