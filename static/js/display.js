// 大きく表示（相手に見せる）と「別の言い方」
let bigEl = null;

function fitBigText(box, text) {
    let lo = 16, hi = 240;
    const room = box.clientHeight || window.innerHeight * 0.6;
    while (lo < hi) {
        const mid = Math.ceil((lo + hi) / 2);
        text.style.fontSize = mid + 'px';
        if (text.scrollHeight <= room && text.scrollWidth <= box.clientWidth + 1) lo = mid; else hi = mid - 1;
    }
    text.style.fontSize = lo + 'px';
}

function closeBig() {
    if (bigEl) { bigEl.remove(); bigEl = null; }
    document.removeEventListener('keydown', bigKey);
}
function bigKey(ev) { if (ev.key === 'Escape') closeBig(); }

function showBig(text, pron, dir) {
    if (!text) return;
    closeBig();
    const ov = document.createElement('div');
    ov.className = 'big-overlay';
    ov.setAttribute('role', 'dialog');
    ov.addEventListener('click', closeBig);

    const x = document.createElement('button');
    x.type = 'button';
    x.className = 'big-close';
    x.setAttribute('aria-label', UI.big_close);
    x.textContent = '✕';
    x.addEventListener('click', ev => { ev.stopPropagation(); closeBig(); });

    const box = document.createElement('div');
    box.className = 'big-box';
    const t = document.createElement('div');
    t.className = 'big-text';
    t.dir = dir || 'auto';
    t.textContent = text;
    box.appendChild(t);
    ov.append(x, box);
    if (pron) {
        const p = document.createElement('div');
        p.className = 'big-pron';
        p.dir = 'auto';
        p.textContent = pron;
        ov.appendChild(p);
    }
    document.body.appendChild(ov);
    bigEl = ov;
    document.addEventListener('keydown', bigKey);
    fitBigText(box, t);
}

function showBigResult(mode) {
    const el = $('resultText-' + mode);
    if (!el) return;
    const pr = $('pron-' + mode);
    showBig(el.innerText, pr && !pr.classList.contains('hidden') ? pr.innerText : '', 'auto');
}

// ---- 別の言い方 ----
async function showAlternatives(mode, btn) {
    const box = $('alts-' + mode), el = $('resultText-' + mode);
    if (!box || !el || !RESULT) return;
    const icon = btn && btn.querySelector('i');
    box.classList.remove('hidden');
    box.replaceChildren();
    const note = document.createElement('p');
    note.className = 'text-xs text-slate-400';
    note.textContent = UI.alts_loading;
    box.appendChild(note);
    if (btn) btn.disabled = true;
    try {
        const r = await fetch('/api/alternatives', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: RESULT.src || RESULT.out,
                translation: el.innerText,
                source: langByName(RESULT.srcLang) ? RESULT.srcLang : 'Auto',
                target: RESULT.tgt,
                formality: loadSettings().formality,
            }),
        });
        let data = {};
        try { data = await r.json(); } catch (e) {}
        if (!r.ok || !data.alternatives) throw new Error(data.error || UI.err_failed);
        const label = document.createElement('p');
        label.className = 'text-[11px] font-semibold text-slate-400';
        label.textContent = UI.alts_label;
        box.replaceChildren(label);
        data.alternatives.forEach(alt => {
            const b = document.createElement('button');
            b.type = 'button';
            b.dir = 'auto';
            b.className = 'alt-chip w-full text-left text-sm px-3 py-2 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-100 whitespace-pre-wrap transition';
            b.textContent = alt;
            b.addEventListener('click', () => useAlternative(mode, alt));
            box.appendChild(b);
        });
    } catch (e) {
        note.textContent = e instanceof TypeError ? UI.err_network : (e.message || UI.err_failed);
        note.className = 'text-xs text-red-300';
        box.replaceChildren(note);
    } finally {
        if (btn) btn.disabled = false;
    }
}

function useAlternative(mode, alt) {
    const el = $('resultText-' + mode);
    if (!el || !RESULT) return;
    el.textContent = alt;
    RESULT.out = alt;
    RESULT.pron = '';
    const pr = $('pron-' + mode);
    if (pr) { pr.textContent = ''; pr.classList.add('hidden'); }
    if (currentEntryId) updateHistory(currentEntryId, x => { x.out = alt; x.pron = ''; });
    $('alts-' + mode).classList.add('hidden');
}
