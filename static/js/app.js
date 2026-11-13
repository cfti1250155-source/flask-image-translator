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

function toggleFavCurrent() {
    if (!currentEntryId) return;
    const e = updateHistory(currentEntryId, x => { x.fav = !x.fav; });
    if (e) setFavIcons(e.fav);
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
            const st = loadSettings();
            const f = form.querySelector('input[name=formality]'), pr = form.querySelector('input[name=pron]');
            if (f) f.value = st.formality;
            if (pr) pr.value = st.pron ? '1' : '0';
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
            checkChatSame();
            if (side === speaker) setSpeaker(speaker);
        });
    });

    loadChat().forEach(m => buildBubble(m));
    setSpeaker('A');
    checkChatSame();

    requestPersistence();
    switchTab(__pendingTab || INITIAL_TAB);
});

// ---- 結果カードの「…」メニュー ----
function closeResultMenus() {
    document.querySelectorAll('.rc-menu').forEach(m => m.classList.add('hidden'));
    document.querySelectorAll('.rc-more[aria-expanded=true]').forEach(b => b.setAttribute('aria-expanded', 'false'));
}

function toggleResultMenu(btn) {
    const menu = btn.parentElement.querySelector('.rc-menu');
    if (!menu) return;
    const willOpen = menu.classList.contains('hidden');
    closeResultMenus();
    if (!willOpen) return;
    menu.classList.remove('hidden', 'rc-down');
    btn.setAttribute('aria-expanded', 'true');
    // 上に出すと画面の外に出るときは下に出す
    if (menu.getBoundingClientRect().top < 8) menu.classList.add('rc-down');
    const first = menu.querySelector('.rc-item');
    if (first) first.focus({ preventScroll: true });
}

document.addEventListener('click', e => {
    if (!e.target.closest || !e.target.closest('.rc-wrap')) closeResultMenus();
});
document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    const open = document.querySelector('.rc-more[aria-expanded=true]');
    closeResultMenus();
    if (open) open.focus();
});
