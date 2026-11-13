// フレーズ集（オフラインでも使える定型文）。データは /static/phrasebook/*.json（Service Worker が端末に保存）
const PBKEY = 'tl_phrase_lang_v1';
let pbIndex = null;
const pbFiles = {};

async function pbGet(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
}

function pbSetStatus(text) {
    const el = $('phrase-status');
    el.textContent = text || '';
    el.classList.toggle('hidden', !text);
}

function pbInitControls() {
    const sel = $('phrase-lang');
    if (sel.options.length) return;
    PHRASE_LANGS.forEach(name => {
        const l = langByName(name);
        const o = document.createElement('option');
        o.value = name; o.textContent = l ? l.native : name;
        sel.appendChild(o);
    });
    let saved = null;
    try { saved = localStorage.getItem(PBKEY); } catch (e) {}
    // 初期値: 前回の選択 → 翻訳先（自分の言語でなければ）→ 自分の言語以外の代表（英語/日本語）
    const guess = [TARGET_LANG, UI_LANG === 'English' ? 'Japanese' : 'English'].find(n => n !== UI_LANG && PHRASE_LANGS.includes(n));
    sel.value = PHRASE_LANGS.includes(saved) ? saved : (guess || PHRASE_LANGS[0]);
    sel.addEventListener('change', () => {
        try { localStorage.setItem(PBKEY, sel.value); } catch (e) {}
        renderPhrasebook();
    });
    $('phrase-search').addEventListener('input', renderPhrasebook);
}

function phraseCard(text, meaning, code) {
    const card = document.createElement('div');
    card.className = 'p-3 rounded-2xl bg-slate-950/60 border border-slate-800 flex gap-2 items-start';
    const body = document.createElement('div');
    body.className = 'min-w-0 flex-1 space-y-0.5';
    const t = document.createElement('div');
    t.dir = 'auto';
    t.className = 'text-base text-indigo-100 font-medium whitespace-pre-wrap break-words';
    t.textContent = text;
    body.appendChild(t);
    if (meaning && meaning !== text) {
        const m = document.createElement('div');
        m.className = 'text-xs text-slate-400 break-words';
        m.textContent = meaning;
        body.appendChild(m);
    }
    const btns = document.createElement('div');
    btns.className = 'flex gap-1 flex-shrink-0';
    btns.append(
        iconBtn('fa-solid fa-volume-high', UI.speak, () => speak(text, code)),
        iconBtn('fa-solid fa-copy', 'copy', async () => { try { await navigator.clipboard.writeText(text); } catch (e) {} }),
    );
    card.append(body, btns);
    return card;
}

async function renderPhrasebook() {
    if (!PHRASE_LANGS.length) { pbSetStatus(UI.phrase_empty); return; }
    pbInitControls();
    const lang = $('phrase-lang').value;
    const file = codeOf(lang).toLowerCase();
    const q = $('phrase-search').value.trim().toLowerCase();
    const box = $('phrase-list');
    try {
        if (!pbIndex) pbIndex = await pbGet('/static/phrasebook/index.json');
        if (!pbFiles[file]) pbFiles[file] = await pbGet('/static/phrasebook/' + file + '.json');
        pbSetStatus('');
    } catch (e) {
        box.replaceChildren();
        pbSetStatus(UI.phrase_load_failed);
        return;
    }
    const data = pbFiles[file];
    const mk = UI_LANG === 'Japanese' ? 'ja' : 'en';
    box.replaceChildren();
    let shown = 0;
    pbIndex.forEach(cat => {
        const cards = cat.phrases
            .map(p => ({ text: data[p.id], meaning: p[mk] }))
            .filter(x => x.text && (!q || x.text.toLowerCase().includes(q) || x.meaning.toLowerCase().includes(q)));
        if (!cards.length) return;
        const h = document.createElement('div');
        h.className = 'text-[11px] font-semibold text-slate-400 pt-1';
        h.textContent = cat[mk];
        const group = document.createElement('div');
        group.className = 'space-y-2';
        cards.forEach(x => group.appendChild(phraseCard(x.text, x.meaning, codeOf(lang))));
        box.append(h, group);
        shown += cards.length;
    });
    $('phrase-empty').classList.toggle('hidden', shown > 0);
}
