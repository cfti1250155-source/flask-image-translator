// 音声読み上げ (TTS)
const hasTTS = 'speechSynthesis' in window;

function unlockTTS() {
    if (!hasTTS) return;
    try { const u = new SpeechSynthesisUtterance(' '); u.volume = 0; speechSynthesis.speak(u); } catch (e) {}
}

function speak(text, lang) {
    if (!hasTTS) { alert(UI.err_tts); return; }
    if (!text) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang || 'en-US';
    const want = u.lang.toLowerCase().replace('_', '-');
    const voices = speechSynthesis.getVoices();
    const v = voices.find(v => (v.lang || '').toLowerCase().replace('_', '-') === want)
           || voices.find(v => (v.lang || '').toLowerCase().split('-')[0] === want.split('-')[0]);
    if (v) u.voice = v;
    speechSynthesis.speak(u);
}

function speakResult(elementId) {
    const el = $(elementId);
    if (el) speak(el.innerText, RESULT && RESULT.tcode);
}

// 音声入力
let recognition = null;
let isRecording = false;

function toggleVoiceRecording() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const status = $('voice-status');
    if (!SR) { status.textContent = UI.err_no_speech_api; return; }
    if (isRecording && recognition) { recognition.stop(); return; }

    recognition = new SR();
    recognition.lang = SOURCE_CODE || navigator.language || 'en-US';
    recognition.continuous = false;
    recognition.interimResults = true;
    let transcript = '';

    recognition.onstart = () => {
        isRecording = true;
        $('mic-icon').className = 'fa-solid fa-square text-red-400 animate-pulse';
        status.textContent = UI.voice_listening;
    };
    recognition.onresult = (event) => {
        transcript = '';
        for (let i = 0; i < event.results.length; i++) transcript += event.results[i][0].transcript;
        $('voice_text').value = transcript;
        $('voice-form').classList.remove('hidden');
    };
    recognition.onerror = (event) => {
        status.textContent = (event.error === 'no-speech') ? UI.err_no_speech : (UI.err_no_speech + ' (' + event.error + ')');
    };
    recognition.onend = () => {
        isRecording = false;
        $('mic-icon').className = 'fa-solid fa-microphone';
        if (transcript.trim()) {
            $('voice-form').requestSubmit();
        } else if (status.textContent === UI.voice_listening) {
            status.textContent = UI.err_no_speech;
        }
    };
    recognition.start();
}

// カメラ
let videoStream = null;

async function startCamera() {
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
        const video = $('camera-video');
        video.srcObject = videoStream;
        video.classList.remove('hidden');
        $('camera-placeholder').classList.add('hidden');
    } catch (err) {
        alert(UI.err_camera + ': ' + err.message);
    }
}

function captureCamera() {
    const video = $('camera-video');
    if (!videoStream || !video.videoWidth) { alert(UI.err_camera_first); return; }
    const scale = Math.min(1, 1600 / Math.max(video.videoWidth, video.videoHeight));
    const canvas = $('camera-canvas');
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    $('camera_data').value = canvas.toDataURL('image/jpeg', 0.85);
    videoStream.getTracks().forEach(t => t.stop());
    $('camera-form').requestSubmit();
}