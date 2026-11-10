// タブ切り替え制御
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    const tab = $('tab-' + tabName);
    if (tab) tab.classList.remove('hidden');

    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('text-indigo-400', 'bg-indigo-950/40');
        btn.classList.add('text-slate-400');
    });
    const active = $('nav-' + tabName);
    if (active) {
        active.classList.remove('text-slate-400');
        active.classList.add('text-indigo-400', 'bg-indigo-950/40');
    }

    const ownLang = (tabName === 'conversation' || tabName === 'history');
    $('language-bar-wrapper').classList.toggle('hidden', ownLang);

    const needsSource = (tabName === 'text' || tabName === 'voice');
    $('source-lang-container').classList.toggle('hidden', !needsSource);
    $('swap-lang-container').classList.toggle('hidden', !needsSource);
    $('target-lang-container').classList.toggle('max-w-xs', !needsSource);
    $('target-lang-container').classList.toggle('mx-auto', !needsSource);
    $('target-lang-label').textContent = needsSource ? UI.target_label : UI.target_label_short;

    if (tabName === 'history') renderHistory();
}

function setFavIcons(isFav) {
    document.querySelectorAll('.fav-btn i').forEach(i => {
        i.className = isFav ? 'fa-solid fa-star text-yellow-400' : 'fa-regular fa-star';
    });
}

let currentEntryId = null;
function toggleFavCurrent() {
    if (!currentEntryId) return;
    const e = updateHistory(currentEntryId, x => { x.fav = !x.fav; });
    if (e) setFavIcons(e.fav);
}

let histFilter = 'all';
function setHistFilter(f) { histFilter = f; renderHistory(); }

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
        if (e.id === currentEntryId) setFavIcons(!e.fav);
        renderHistory();
    });
    row.append(
        star,
        iconBtn('fa-solid fa-volume-high', UI.speak, () => speak(e.out, e.tcode || codeOf(e.tgt))),
        iconBtn('fa-solid fa-copy', 'copy', async () => {
            try { await navigator.clipboard.writeText(e.out); } catch (err) {}
        }),
        iconBtn('fa-solid fa-rotate-left', UI.reuse, () => {
            const ta = document.querySelector('textarea[name=direct_text]');
            if (ta) ta.value = e.src || '';
            switchTab('text');
        }),
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
    ['all', 'fav', 'gl'].forEach(k => {
        $('hf-' + k).className = 'px-3 py-1.5 rounded-full text-xs font-semibold border border-slate-700 transition ' + (histFilter === k ? on : off);
    });
    const isGl = histFilter === 'gl';
    $('history-section').classList.toggle('hidden', isGl);
    $('glossary-section').classList.toggle('hidden', !isGl);
    $('history-clear-btn').classList.toggle('hidden', isGl);
    if (isGl) { renderGlossary(); return; }

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

function explainResult(mode) {
    if (!RESULT) return;
    explainText(RESULT.src || RESULT.out, RESULT.srcLang, $('explain-' + mode));
}

function editResult(elementId) {
    const el = $(elementId);
    if (!el || !RESULT) return;
    const v = prompt(UI.edit_prompt, el.innerText);
    if (v === null) return;
    const nv = v.trim();
    if (!nv || nv === RESULT.out) return;
    el.textContent = nv;
    RESULT.out = nv;
    if (currentEntryId) updateHistory(currentEntryId, x => { x.out = nv; });
    learnCorrection(RESULT.src, nv, RESULT.tgt);
}

async function copyResult(elementId, btn) {
    const el = $(elementId);
    if (!el) return;
    try {
        await navigator.clipboard.writeText(el.innerText);
        const icon = btn.querySelector('i');
        icon.className = 'fa-solid fa-check text-emerald-400';
        setTimeout(() => icon.className = 'fa-solid fa-copy', 1500);
    } catch (e) {}
}

// 初期化処理
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form.tx-form').forEach(form => {
        form.addEventListener('submit', () => {
            const g = form.querySelector('input[name=glossary]');
            if (g) {
                const ta = form.querySelector('textarea');
                g.value = JSON.stringify(relevantGlossary(ta ? ta.value : '', TARGET_LANG));
            }
            form.querySelectorAll('button[type=submit]').forEach(b => { b.disabled = true; b.classList.add('opacity-60'); });
            const label = form.querySelector('button[type=submit] .btn-label');
            if (label) label.textContent = UI.translating;
        });
    });

    if (RESULT && RESULT.out) {
        currentEntryId = addHistory(RESULT);
        const saved = loadHistory().find(x => x.id === currentEntryId);
        setFavIcons(!!(saved && saved.fav));
    }

    populateLangSelect($('gl-to'), TARGET_LANG);

    $('conv-auto-speak').checked = !!chatPrefs.speak;
    $('conv-auto-switch').checked = !!chatPrefs.autoSwitch;
    ['conv-auto-speak', 'conv-auto-switch'].forEach(id => $(id).addEventListener('change', () => {
        chatPrefs = { speak: $('conv-auto-speak').checked, autoSwitch: $('conv-auto-switch').checked };
        try { localStorage.setItem(PREFKEY, JSON.stringify(chatPrefs)); } catch (e) {}
    }));

    ['A', 'B'].forEach(side => {
        const sel = $('conv-lang-' + side);
        populateLangSelect(sel, convLangs[side]);
        sel.addEventListener('change', () => {
            convLangs[side] = sel.value;
            try { localStorage.setItem(CKEY, JSON.stringify(convLangs)); } catch (e) {}
            if (side === speaker) setSpeaker(speaker);
        });
    });

    loadChat().forEach(m => buildBubble(m));
    setSpeaker('A');

    switchTab(INITIAL_TAB);
});