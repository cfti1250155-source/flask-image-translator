// 単語帳と復習（忘れかけたころに出す簡易の間隔反復）。データはこの端末の localStorage のみ
let studyQueue = [];
let studyCurrent = null;
let studyTotal = 0;

// 訳文の「しおり」ボタンから保存
function saveVocabEntry(entry, btn) {
    addVocab(entry);
    const icon = btn && btn.querySelector('i');
    if (icon) {
        icon.className = 'fa-solid fa-bookmark text-indigo-400';
        btn.title = UI.vocab_saved;
    }
}

function saveVocabCurrent(mode, btn) {
    const el = $('resultText-' + mode);
    if (!el || !RESULT) return;
    const pr = $('pron-' + mode);
    saveVocabEntry({
        src: RESULT.src || RESULT.out, out: el.innerText, srcLang: RESULT.srcLang, tgt: RESULT.tgt,
        tcode: RESULT.tcode, pron: pr && !pr.classList.contains('hidden') ? pr.innerText : '',
    }, btn);
}

const dueCards = () => loadVocab().filter(v => (v.due || 0) <= Date.now()).sort((a, b) => (a.due || 0) - (b.due || 0));

function renderStudy() {
    const all = loadVocab(), due = dueCards();
    $('study-stats').textContent = fmt(UI.study_total, { n: all.length }) + ' / ' + fmt(UI.study_due, { n: due.length });
    $('study-start').classList.toggle('hidden', !due.length || !!studyCurrent);
    const msg = $('study-msg');
    if (!studyCurrent) {
        msg.classList.toggle('hidden', !all.length || !!due.length);
        msg.textContent = UI.study_nodue;
    }
    $('study-empty').classList.toggle('hidden', all.length > 0);

    const box = $('study-list');
    box.replaceChildren();
    all.forEach(v => {
        const card = document.createElement('div');
        card.className = 'p-3 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1';
        const src = document.createElement('div');
        src.dir = 'auto';
        src.className = 'text-sm text-slate-100 whitespace-pre-wrap break-words';
        src.textContent = v.src;
        const out = document.createElement('div');
        out.dir = 'auto';
        out.className = 'text-sm text-indigo-200 font-medium whitespace-pre-wrap break-words';
        out.textContent = v.out;
        const row = document.createElement('div');
        row.className = 'flex gap-1 justify-end';
        row.append(
            iconBtn('fa-solid fa-volume-high', UI.speak, () => speak(v.out, v.tcode || codeOf(v.tgt))),
            iconBtn('fa-solid fa-trash', UI.delete, () => {
                saveVocab(loadVocab().filter(x => x.id !== v.id));
                if (studyCurrent && studyCurrent.id === v.id) endStudy();
                renderStudy();
            }),
        );
        card.append(src, out, row);
        box.appendChild(card);
    });
}

function startStudy() {
    studyQueue = dueCards().slice(0, 20);
    studyTotal = studyQueue.length;
    if (!studyQueue.length) { renderStudy(); return; }
    $('study-msg').classList.add('hidden');
    nextStudy();
}

function nextStudy() {
    studyCurrent = studyQueue.shift() || null;
    if (!studyCurrent) { endStudy(true); return; }
    $('study-card').classList.remove('hidden');
    $('study-start').classList.add('hidden');
    $('study-front').textContent = studyCurrent.src;
    $('study-answer').textContent = studyCurrent.out;
    $('study-pron').textContent = studyCurrent.pron || '';
    $('study-speak').onclick = () => speak(studyCurrent.out, studyCurrent.tcode || codeOf(studyCurrent.tgt));
    $('study-left').textContent = fmt(UI.study_left, { n: studyQueue.length + 1 });
    $('study-back').classList.add('hidden');
    $('study-grade').classList.add('hidden');
    $('study-reveal').classList.remove('hidden');
}

function revealStudy() {
    if (!studyCurrent) return;
    $('study-back').classList.remove('hidden');
    $('study-grade').classList.remove('hidden');
    $('study-reveal').classList.add('hidden');
    speak(studyCurrent.out, studyCurrent.tcode || codeOf(studyCurrent.tgt));
}

function endStudy(finished) {
    studyCurrent = null;
    studyQueue = [];
    $('study-card').classList.add('hidden');
    renderStudy();
    if (finished) {
        const msg = $('study-msg');
        msg.textContent = UI.study_done;
        msg.classList.remove('hidden');
    }
}

// 覚えた: 次の復習までの間隔を延ばす / もう一度: 最初からやり直し（今回のうちにもう一度出す）
function gradeStudy(good) {
    if (!studyCurrent) return;
    const list = loadVocab();
    const v = list.find(x => x.id === studyCurrent.id);
    if (v) {
        if (good) {
            v.box = Math.min(SRS_DAYS.length - 1, (v.box || 0) + 1);
            v.due = Date.now() + SRS_DAYS[v.box] * 86400000;
        } else {
            v.box = 0;
            v.due = 0;
            studyQueue.push(v);
        }
        saveVocab(list);
    }
    nextStudy();
}
