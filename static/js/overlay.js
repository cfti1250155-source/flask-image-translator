// 画像の重ね翻訳（画像選択の下に、訳文を画像の文字の位置へ重ねて表示）と PDF 翻訳
const IMG_KEY = 'tl_last_img';          // 直前に翻訳した画像（縮小済み）。タブを閉じると消える sessionStorage に置く
const IMG_MAX_SIDE = 1600;
let overlayOn = true;

const isPdf = (f) => f && (f.type === 'application/pdf' || /\.pdf$/i.test(f.name || ''));

// ---- 画像を縮小（アップロードを軽くし、表示用に端末へ保持する） ----
function loadBitmap(file) {
    if (window.createImageBitmap) return createImageBitmap(file);
    return new Promise((resolve, reject) => {
        const url = URL.createObjectURL(file), img = new Image();
        img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
        img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('decode')); };
        img.src = url;
    });
}

async function downscaleImage(file) {
    try {
        const bmp = await loadBitmap(file);
        const w0 = bmp.width, h0 = bmp.height;
        if (!w0 || !h0) return null;
        const k = Math.min(1, IMG_MAX_SIDE / Math.max(w0, h0));
        const c = document.createElement('canvas');
        c.width = Math.round(w0 * k);
        c.height = Math.round(h0 * k);
        c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
        return await new Promise(res => c.toBlob(b => res(b), 'image/jpeg', 0.85));
    } catch (e) { return null; }
}

function blobToDataURL(blob) {
    return new Promise((resolve, reject) => {
        const r = new FileReader();
        r.onload = () => resolve(String(r.result));
        r.onerror = () => reject(r.error);
        r.readAsDataURL(blob);
    });
}

function storeLastImage(url) {
    try { if (url) sessionStorage.setItem(IMG_KEY, url); else sessionStorage.removeItem(IMG_KEY); } catch (e) {
        try { sessionStorage.removeItem(IMG_KEY); } catch (e2) {}
    }
}
function lastImage() { try { return sessionStorage.getItem(IMG_KEY) || ''; } catch (e) { return ''; } }

// ---- 重ね表示 ----
function fitBlock(el) {
    const h = el.clientHeight, w = el.clientWidth;
    if (!h || !w) return;
    let fs = Math.min(h * 0.85, 40);
    el.style.fontSize = fs + 'px';
    while (fs > 7 && (el.scrollHeight > h + 1 || el.scrollWidth > w + 1)) { fs -= 1; el.style.fontSize = fs + 'px'; }
}
function fitAllBlocks() { document.querySelectorAll('#overlay-layer .ov-block').forEach(fitBlock); }

function setOverlayVisible(on) {
    overlayOn = on;
    $('overlay-layer').classList.toggle('hidden', !on);
    $('overlay-toggle').textContent = on ? UI.ov_hide : UI.ov_show;
    if (on) fitAllBlocks();
}
function toggleOverlay() { setOverlayVisible(!overlayOn); }

function renderOverlay(blocks, imgUrl) {
    const box = $('overlay-box');
    box.classList.remove('hidden');
    const layer = $('overlay-layer'), list = $('overlay-list'), stage = $('overlay-stage');
    layer.replaceChildren();
    list.replaceChildren();

    if (!imgUrl) {   // 画像を保持できなかったとき（HEIC など）は訳文の一覧にする
        stage.classList.add('hidden');
        $('overlay-toggle').classList.add('hidden');
        list.classList.remove('hidden');
        const note = document.createElement('p');
        note.className = 'text-[11px] text-slate-500';
        note.textContent = UI.ov_fallback;
        list.appendChild(note);
        blocks.forEach(b => {
            const d = document.createElement('div');
            d.dir = 'auto';
            d.className = 'p-2 rounded-xl bg-slate-950/60 border border-slate-800 text-sm text-indigo-100 whitespace-pre-wrap';
            d.textContent = b.translation;
            list.appendChild(d);
        });
        return;
    }

    $('overlay-img').src = imgUrl;
    blocks.forEach(b => {
        const [y0, x0, y1, x1] = b.box;
        const el = document.createElement('div');
        el.className = 'ov-block';
        el.dir = 'auto';
        el.style.cssText = `left:${x0 / 10}%;top:${y0 / 10}%;width:${(x1 - x0) / 10}%;height:${(y1 - y0) / 10}%;`;
        el.textContent = b.translation;
        el.title = b.text || '';
        let showing = 'tr';
        el.addEventListener('click', () => {   // タップで原文 ⇄ 訳文
            if (!b.text) return;
            showing = showing === 'tr' ? 'src' : 'tr';
            el.textContent = showing === 'tr' ? b.translation : b.text;
            el.classList.toggle('ov-src', showing === 'src');
            fitBlock(el);
        });
        layer.appendChild(el);
    });
    setOverlayVisible(true);
    if (window.ResizeObserver) new ResizeObserver(fitAllBlocks).observe(stage);   // タブが開いたとき・回転したときに合わせ直す
    else window.addEventListener('resize', fitAllBlocks);
    $('overlay-img').addEventListener('load', fitAllBlocks);
}

// ---- 送信前の処理（画像は縮小して保持／PDF は別処理） ----
document.addEventListener('submit', async (ev) => {
    const form = ev.target;
    if (!form.closest || !form.closest('#tab-image')) return;
    const input = form.querySelector('input[type=file]');
    const file = input && input.files && input.files[0];
    if (!file) return;
    if (isPdf(file)) {
        ev.preventDefault();
        ev.stopImmediatePropagation();
        runPdf(file);
        return;
    }
    ev.preventDefault();   // 縮小が終わってから送る
    const blob = await downscaleImage(file);
    if (blob && blob.size < file.size * 1.5 + 1024) {
        try {
            const dt = new DataTransfer();
            dt.items.add(new File([blob], 'image.jpg', { type: 'image/jpeg' }));
            input.files = dt.files;
            storeLastImage(await blobToDataURL(blob));
        } catch (e) { storeLastImage(''); }
    } else {
        storeLastImage('');
    }
    form.submit();
}, true);

// ---- PDF 翻訳（数ページずつ） ----
let pdfAbort = null;

function pageCard(p) {
    const card = document.createElement('div');
    card.className = 'p-3 rounded-2xl bg-indigo-950/40 border border-indigo-800/60 space-y-1.5';
    const head = document.createElement('div');
    head.className = 'flex items-center justify-between gap-2';
    const t = document.createElement('span');
    t.className = 'text-xs font-bold text-indigo-400 uppercase tracking-wider';
    t.textContent = UI.pdf_page + ' ' + p.page;
    const row = document.createElement('div');
    row.className = 'flex gap-1';
    const body = document.createElement('div');
    body.dir = 'auto';
    body.className = 'text-sm text-indigo-100 whitespace-pre-wrap break-words leading-relaxed';
    body.textContent = p.translation || '—';
    row.append(
        iconBtn('fa-solid fa-expand', UI.big_show, () => showBig(p.translation, '', 'auto')),
        iconBtn('fa-solid fa-copy', 'copy', async () => { try { await navigator.clipboard.writeText(p.translation); } catch (e) {} }),
    );
    head.append(t, row);
    card.append(head, body);
    return card;
}

async function runPdf(file) {
    if (pdfAbort) pdfAbort.abort();
    const ctl = pdfAbort = new AbortController();
    const box = $('pdf-result');
    box.classList.remove('hidden');
    box.replaceChildren();

    const bar = document.createElement('div');
    bar.className = 'flex items-center justify-between gap-2 text-xs text-slate-300';
    const status = document.createElement('span');
    status.setAttribute('role', 'status');
    const stop = document.createElement('button');
    stop.type = 'button';
    stop.className = 'px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700';
    stop.textContent = UI.pdf_cancel;
    stop.onclick = () => ctl.abort();
    bar.append(status, stop);
    const cards = document.createElement('div');
    cards.className = 'space-y-2';
    box.append(bar, cards);

    const texts = [];
    let start = 1, limit = null, total = null;
    status.textContent = UI.translating;
    try {
        while (limit === null || start <= limit) {
            const fd = new FormData();
            fd.append('file', file);
            fd.append('target', TARGET_LANG);
            fd.append('start', String(start));
            fd.append('end', String(start + 2));
            fd.append('formality', loadSettings().formality);
            const r = await fetch('/api/translate-pdf', { method: 'POST', body: fd, signal: ctl.signal });
            let data = {};
            try { data = await r.json(); } catch (e) {}
            if (!r.ok || !data.pages) throw new Error(data.error || UI.err_failed);
            total = data.total; limit = data.limit;
            data.pages.forEach(p => { cards.appendChild(pageCard(p)); texts.push(p.translation); });
            start += 3;
            if (start <= limit) status.textContent = fmt(UI.pdf_progress, { p: start, n: limit });
        }
        status.textContent = fmt(UI.pdf_done, { n: texts.length });
        stop.remove();
        const all = iconBtn('fa-solid fa-copy', UI.pdf_copy_all, async () => { try { await navigator.clipboard.writeText(texts.join('\n\n')); } catch (e) {} });
        all.className = 'px-3 h-8 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs transition';
        all.append(' ' + UI.pdf_copy_all);
        bar.appendChild(all);
        if (total > limit) {
            const n = document.createElement('p');
            n.className = 'text-xs text-amber-200';
            n.textContent = fmt(UI.pdf_truncated, { m: limit });
            box.appendChild(n);
        }
    } catch (e) {
        stop.remove();
        if (e && e.name === 'AbortError') { status.textContent = UI.pdf_cancel; }
        else {
            status.textContent = e instanceof TypeError ? UI.err_network : (e.message || UI.err_failed);
            status.classList.add('text-red-300');
        }
    } finally {
        if (pdfAbort === ctl) pdfAbort = null;
    }
}

// ---- 起動時: 直前の画像翻訳の結果を重ねて表示 ----
document.addEventListener('DOMContentLoaded', () => {
    if (typeof OVERLAY_BLOCKS !== 'undefined' && Array.isArray(OVERLAY_BLOCKS) && OVERLAY_BLOCKS.length) {
        renderOverlay(OVERLAY_BLOCKS, lastImage());
    }
});
