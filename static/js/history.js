// 履歴・お気に入り・用語集・フレーズ集・データの表示（メイン画面とオフライン画面の両方で使う）
let currentEntryId = null;
const OFFLINE_PAGE = !!window.IS_OFFLINE_PAGE;

let histFilter = 'all';
function setHistFilter(f) { histFilter = (f === 'data') ? 'settings' : f; renderHistory(); }

function iconBtn(icon, title, onClick) {
    const b = document.createElement('button');
    b.type = 'button';
    b.title = title;
    b.setAttribute('aria-label', title);
    b.className = 'w-8 h-8 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition';
    const i = document.createElement('i');
    i.className = icon;
    b.appendChild(i);
    b.addEventListener('click', onClick);
    return b;
}

function historyItem(e) {
    const card = document.createElement('div');
    card.className = 'p-3 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1.5';

    const meta = document.createElement('div');
    meta.className = 'text-[10px] text-slate-500 flex justify-between gap-2';
    const when = new Date(e.ts).toLocaleString([], { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    const l = document.createElement('span');
    const sn = (langByName(e.srcLang) || {}).native || e.srcLang || '?';
    const tn = (langByName(e.tgt) || {}).native || e.tgt;
    l.textContent = sn + ' → ' + tn;
    const r = document.createElement('span');
    r.textContent = when;
    meta.append(l, r);

    const src = document.createElement('div');
    src.dir = 'auto';
    src.className = 'text-xs text-slate-400 whitespace-pre-wrap break-words';
    src.textContent = e.src || '';

    const out = document.createElement('div');
    out.dir = 'auto';
    out.className = 'text-sm text-indigo-100 font-medium whitespace-pre-wrap break-words';
    out.textContent = e.out;

    const row = document.createElement('div');
    row.className = 'flex gap-1 justify-end pt-1';
    const star = iconBtn(e.fav ? 'fa-solid fa-star text-yellow-400' : 'fa-regular fa-star', UI.favorite, () => {
        updateHistory(e.id, x => { x.fav = !x.fav; });
        if (e.id === currentEntryId && typeof setFavIcons === 'function') setFavIcons(!e.fav);
        renderHistory();
    });
    row.append(
        star,
        iconBtn('fa-solid fa-volume-high', UI.speak, () => speak(e.out, e.tcode || codeOf(e.tgt))),
        iconBtn('fa-regular fa-bookmark', UI.vocab_save, (ev) => saveVocabEntry(
            { src: e.src, out: e.out, srcLang: e.srcLang, tgt: e.tgt, tcode: e.tcode || codeOf(e.tgt), pron: e.pron }, ev.currentTarget)),
        iconBtn('fa-solid fa-copy', 'copy', async () => {
            try { await navigator.clipboard.writeText(e.out); } catch (err) {}
        }),
        ...(OFFLINE_PAGE ? [] : [iconBtn('fa-solid fa-rotate-left', UI.reuse, () => {
            const ta = document.querySelector('textarea[name=direct_text]');
            if (ta) ta.value = e.src || '';
            switchTab('text');
        })]),
        iconBtn('fa-solid fa-trash', UI.delete, () => {
            saveHistory(loadHistory().filter(x => x.id !== e.id));
            renderHistory();
        }),
    );
    card.append(meta, src, out, row);
    return card;
}

function renderHistory() {
    const on = 'bg-indigo-600 text-white', off = 'bg-slate-800 text-slate-300';
    ['all', 'fav', 'gl', 'phrases', 'study', 'settings'].forEach(k => {
        const pill = $('hf-' + k);
        if (pill) pill.className = 'px-3 py-1.5 rounded-full text-xs font-semibold border border-slate-700 transition ' + (histFilter === k ? on : off);
    });
    const isGl = histFilter === 'gl', isPh = histFilter === 'phrases', isSet = histFilter === 'settings', isStudy = histFilter === 'study';
    $('history-section').classList.toggle('hidden', isGl || isPh || isSet || isStudy);
    $('glossary-section').classList.toggle('hidden', !isGl);
    $('phrase-section').classList.toggle('hidden', !isPh);
    $('settings-section').classList.toggle('hidden', !isSet);
    $('study-section').classList.toggle('hidden', !isStudy);
    $('history-clear-btn').classList.toggle('hidden', isGl || isPh || isSet || isStudy);
    if (isStudy) { renderStudy(); return; }
    if (isSet) { renderSettings(); renderDataInfo(); return; }
    if (isGl) { renderGlossary(); return; }
    if (isPh) { renderPhrasebook(); return; }

    const box = $('history-list');
    box.replaceChildren();
    const items = loadHistory().filter(e => histFilter === 'all' || e.fav);
    items.forEach(e => box.appendChild(historyItem(e)));
    $('history-empty').classList.toggle('hidden', items.length > 0);
}

function clearHistory() {
    if (!confirm(UI.confirm_clear)) return;
    saveHistory(loadHistory().filter(e => e.fav));
    renderHistory();
}

function populateLangSelect(sel, selected) {
    LANGS.forEach(l => {
        const o = document.createElement('option');
        o.value = l.name;
        o.textContent = l.native;
        sel.appendChild(o);
    });
    sel.value = selected;
}

function addGlossaryTerm(ev) {
    ev.preventDefault();
    upsertGlossary('term', $('gl-term').value, $('gl-meaning').value, $('gl-to').value);
    $('gl-term').value = '';
    $('gl-meaning').value = '';
    renderGlossary();
    return false;
}

function renderGlossary() {
    const box = $('glossary-list');
    box.replaceChildren();
    const list = loadGlossary();
    list.forEach(e => {
        const card = document.createElement('div');
        card.className = 'p-3 rounded-2xl bg-slate-950/60 border border-slate-800 flex gap-2 items-start';
        const body = document.createElement('div');
        body.className = 'min-w-0 flex-1 space-y-0.5';
        const tag = document.createElement('span');
        tag.className = 'text-[10px] text-slate-500';
        tag.textContent = (e.kind === 'example' ? UI.glossary_kind_example : UI.glossary_kind_term) +
            ' · → ' + ((langByName(e.to) || {}).native || e.to);
        const t = document.createElement('div');
        t.dir = 'auto';
        t.className = 'text-xs text-slate-300 whitespace-pre-wrap break-words';
        t.textContent = e.term;
        const m = document.createElement('div');
        m.dir = 'auto';
        m.className = 'text-sm text-indigo-100 font-medium whitespace-pre-wrap break-words';
        m.textContent = e.meaning;
        body.append(tag, t, m);
        card.append(body, iconBtn('fa-solid fa-trash', UI.delete, () => {
            saveGlossary(loadGlossary().filter(x => x.id !== e.id));
            renderGlossary();
        }));
        box.appendChild(card);
    });
    $('glossary-empty').classList.toggle('hidden', list.length > 0);
}

async function explainText(text, lang, el) {
    if (!text) return;
    el.classList.remove('hidden');
    el.textContent = UI.explaining;
    try {
        const r = await fetch('/api/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, lang, explain_in: UI_LANG }),
        });
        let d = {};
        try { d = await r.json(); } catch (e) {}
        if (!r.ok || !d.explanation) throw new Error(d.error || UI.err_failed);
        el.textContent = d.explanation;
    } catch (e) {
        el.textContent = e instanceof TypeError ? UI.err_network : (e.message || UI.err_failed);
    }
}

