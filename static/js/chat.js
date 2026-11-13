let convLangs = Object.assign({}, DEFAULT_CONV);
try {
    const saved = JSON.parse(localStorage.getItem(CKEY) || 'null');
    if (saved && langByName(saved.A) && langByName(saved.B)) convLangs = saved;
} catch (e) {}
if (!langByName(convLangs.A)) convLangs.A = UI_LANG;
if (!langByName(convLangs.B)) convLangs.B = 'English';

let chatPrefs = { speak: true, autoSwitch: true };
try { Object.assign(chatPrefs, JSON.parse(localStorage.getItem(PREFKEY) || '{}')); } catch (e) {}

let speaker = 'A';
function setSpeaker(side) {
    speaker = side;
    const styles = { A: ['border-indigo-500', 'bg-indigo-950/40'], B: ['border-emerald-500', 'bg-emerald-950/30'] };
    ['A', 'B'].forEach(sd => {
        const card = $('chat-card-' + sd);
        card.classList.remove('border-indigo-500', 'bg-indigo-950/40', 'border-emerald-500', 'bg-emerald-950/30');
        card.classList.remove('border-slate-800', 'bg-slate-950/50');
        if (sd === side) card.classList.add(...styles[sd]); else card.classList.add('border-slate-800', 'bg-slate-950/50');
    });
    $('conv-input').lang = codeOf(convLangs[side]);
    $('conv-send').className = 'w-11 h-11 flex-shrink-0 text-white rounded-full flex items-center justify-center transition ' +
        (side === 'A' ? 'bg-indigo-600 hover:bg-indigo-500' : 'bg-emerald-600 hover:bg-emerald-500');
}

const setConvStatus = (t) => { $('conv-status').textContent = t || ''; };

function buildBubble(msg) {
    $('conv-empty').classList.add('hidden');
    const isA = msg.side === 'A';
    const wrap = document.createElement('div');
    wrap.className = 'flex ' + (isA ? 'justify-start' : 'justify-end');
    const b = document.createElement('div');
    b.className = 'max-w-[88%] rounded-2xl px-3 py-2 space-y-1 border ' +
        (isA ? 'bg-indigo-950/50 border-indigo-800/60' : 'bg-emerald-950/40 border-emerald-800/60');

    const head = document.createElement('div');
    head.className = 'text-[10px] text-slate-500';
    head.textContent = (isA ? UI.conv_person_a : UI.conv_person_b) + ' · ' + ((langByName(msg.srcLang) || {}).native || msg.srcLang);

    const orig = document.createElement('div');
    orig.dir = 'auto';
    orig.className = 'text-sm text-slate-100 whitespace-pre-wrap break-words';
    orig.textContent = msg.src;

    const trans = document.createElement('div');
    trans.dir = 'auto';
    trans.className = 'text-sm font-medium whitespace-pre-wrap break-words border-t border-slate-700/60 pt-1 ' +
        (isA ? 'text-indigo-200' : 'text-emerald-200');
    trans.textContent = msg.out || '…';

    const pron = document.createElement('div');
    pron.dir = 'auto';
    pron.className = 'text-xs text-slate-400 whitespace-pre-wrap break-words' + (msg.pron ? '' : ' hidden');
    pron.textContent = msg.pron || '';

    const actions = document.createElement('div');
    actions.className = 'flex justify-end gap-1';
    const note = document.createElement('div');
    note.dir = 'auto';
    note.className = 'hidden text-xs text-amber-200 bg-amber-950/30 border border-amber-900/50 rounded-xl p-2 whitespace-pre-wrap leading-relaxed';

    function addActions() {
        actions.replaceChildren(
            iconBtn('fa-solid fa-volume-high', UI.speak, () => speak(msg.out, msg.tcode)),
            iconBtn('fa-regular fa-bookmark', UI.vocab_save, (ev) => saveVocabEntry(
                { src: msg.src, out: msg.out, srcLang: msg.srcLang, tgt: msg.tgt, tcode: msg.tcode, pron: msg.pron }, ev.currentTarget)),
            iconBtn('fa-solid fa-expand', UI.big_show, () => showBig(msg.out, msg.pron, 'auto')),
            iconBtn('fa-solid fa-pen', UI.edit_translation, () => {
                const v = prompt(UI.edit_prompt, msg.out);
                if (v === null) return;
                const nv = v.trim();
                if (!nv || nv === msg.out) return;
                msg.out = nv;
                trans.textContent = nv;
                const list = loadChat();
                const m = list.find(x => x.id === msg.id);
                if (m) { m.out = nv; saveChat(list); }
                learnCorrection(msg.src, nv, msg.tgt);
            }),
            iconBtn('fa-solid fa-lightbulb', UI.explain, () => explainText(msg.src, msg.srcLang, note)),
        );
    }
    if (msg.out) addActions();

    b.append(head, orig, trans, pron, actions, note);
    wrap.appendChild(b);
    const log = $('conv-log');
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
    return {
        done() { trans.textContent = msg.out; pron.textContent = msg.pron || ''; pron.classList.toggle('hidden', !msg.pron); addActions(); log.scrollTop = log.scrollHeight; },
        fail(text) { trans.textContent = text; trans.classList.add('text-red-300'); },
        remove() { wrap.remove(); if (!log.children.length) $('conv-empty').classList.remove('hidden'); },
    };
}

async function converse(side, text) {
    const other = side === 'A' ? 'B' : 'A';
    const src = convLangs[side], tgt = convLangs[other];
    const msg = { id: uid(), side, src: text, srcLang: src, tgt, tcode: codeOf(tgt), out: '', ts: Date.now() };
    const context = loadChat().filter(m => m.out).slice(-6).map(m => ({ speaker: m.side, text: m.src }));
    const bubble = buildBubble(msg);
    try {
        const r = await fetch('/api/translate-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, source: src, target: tgt, context, glossary: relevantGlossary(text, tgt), formality: loadSettings().formality, pron: loadSettings().pron }),
        });
        let data = {};
        try { data = await r.json(); } catch (e) {}
        if (!r.ok || !data.translation) throw new Error(data.error || UI.err_failed);
        msg.out = data.translation;
        msg.pron = data.pronunciation || '';
        bubble.done();
        const list = loadChat();
        list.push(msg);
        saveChat(list);
        addHistory({ mode: 'conversation', src: text, out: msg.out, srcLang: src, tgt, tcode: msg.tcode });
        if ($('conv-auto-speak').checked) speak(msg.out, msg.tcode);
    } catch (e) {
        bubble.fail(e instanceof TypeError ? UI.err_network : (e.message || UI.err_failed));
        if (!$('conv-input').value) $('conv-input').value = text;
    }
}

function afterSend(side) {
    if (!$('conv-auto-switch').checked) return;
    const other = side === 'A' ? 'B' : 'A';
    setSpeaker(other);
    setConvStatus(UI.chat_next + ': ' + (other === 'A' ? UI.conv_person_a : UI.conv_person_b));
}

function convSend(ev) {
    ev.preventDefault();
    unlockTTS();
    const input = $('conv-input');
    const text = input.value.trim();
    if (!text) return false;
    const side = speaker;
    input.value = '';
    converse(side, text);
    afterSend(side);
    return false;
}

let convRec = null;
function convListen() {
    unlockTTS();
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setConvStatus(UI.err_no_speech_api); return; }
    if (convRec) { convRec.stop(); return; }

    const side = speaker;
    const icon = $('conv-mic').querySelector('i');
    const rec = new SR();
    rec.lang = codeOf(convLangs[side]);
    rec.continuous = false;
    rec.interimResults = true;
    let transcript = '';

    rec.onstart = () => { icon.className = 'fa-solid fa-square text-red-400 animate-pulse'; setConvStatus(UI.voice_listening); };
    rec.onresult = (ev) => {
        transcript = '';
        for (let i = 0; i < ev.results.length; i++) transcript += ev.results[i][0].transcript;
        setConvStatus(transcript);
    };
    rec.onerror = (ev) => { setConvStatus(UI.err_no_speech + (ev.error && ev.error !== 'no-speech' ? ' (' + ev.error + ')' : '')); };
    rec.onend = () => {
        convRec = null;
        icon.className = 'fa-solid fa-microphone';
        if (transcript.trim()) {
            setConvStatus('');
            converse(side, transcript.trim());
            afterSend(side);
        }
    };
    convRec = rec;
    try { rec.start(); } catch (e) { convRec = null; icon.className = 'fa-solid fa-microphone'; }
}

function clearConversation() {
    saveChat([]);
    $('conv-log').replaceChildren();
    $('conv-empty').classList.remove('hidden');
    setConvStatus('');
}

// 2人の言語が同じなら警告を出す
function checkChatSame() {
    $('conv-warn').classList.toggle('hidden', convLangs.A !== convLangs.B);
}
