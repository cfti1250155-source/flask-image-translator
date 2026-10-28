import io
import json
import os
import time
import base64
from flask import Flask, render_template, request, redirect, url_for, session
from google import genai
import pytesseract
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "app-secret-key-12345")

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

SUPPORTED_LANGUAGES = [
    "Japanese", "English", "Spanish", "French", "German", 
    "Chinese (Simplified)", "Chinese (Traditional)", "Korean", "Italian", "Russian", 
    "Portuguese", "Thai", "Vietnamese", "Indonesian", "Turkish", 
    "Arabic", "Hindi", "Dutch", "Polish", "Swedish", 
    "Greek", "Czech", "Hungarian", "Romanian", "Ukrainian", 
    "Hebrew", "Malay", "Persian", "Tagalog", "Swahili", 
    "Danish", "Finnish", "Norwegian"
]

# 各言語のUI表示テキスト（下部ナビゲーション含む）
UI_CACHE = {
    "Japanese": {
        "title": "AI万能翻訳アプリ",
        "text_placeholder": "テキストを入力...",
        "btn_text_translate": "翻訳する",
        "image_input_label": "クリックして画像を選択",
        "btn_image_translate": "画像を翻訳する",
        "result_label": "翻訳結果",
        "nav_text": "テキスト",
        "nav_image": "画像",
        "nav_voice": "音声",
        "nav_camera": "カメラ"
    },
    "English": {
        "title": "AI Multi-Translator",
        "text_placeholder": "Enter text...",
        "btn_text_translate": "Translate",
        "image_input_label": "Click to select image",
        "btn_image_translate": "Translate Image",
        "result_label": "Translation Result",
        "nav_text": "Text",
        "nav_image": "Image",
        "nav_voice": "Voice",
        "nav_camera": "Camera"
    },
    "Spanish": {
        "title": "Traductor Multilingüe IA",
        "text_placeholder": "Ingrese texto...",
        "btn_text_translate": "Traducir",
        "image_input_label": "Haga clic para seleccionar imagen",
        "btn_image_translate": "Traducir Imagen",
        "result_label": "Resultado de Traducción",
        "nav_text": "Texto",
        "nav_image": "Imagen",
        "nav_voice": "Voz",
        "nav_camera": "Cámara"
    },
    "French": {
        "title": "Traducteur Multi-IA",
        "text_placeholder": "Saisir du texte...",
        "btn_text_translate": "Traduire",
        "image_input_label": "Cliquez pour choisir une image",
        "btn_image_translate": "Traduire l'Image",
        "result_label": "Résultat de Traduction",
        "nav_text": "Texte",
        "nav_image": "Image",
        "nav_voice": "Voix",
        "nav_camera": "Caméra"
    },
    "German": {
        "title": "KI-Multisprach-Übersetzer",
        "text_placeholder": "Text eingeben...",
        "btn_text_translate": "Übersetzen",
        "image_input_label": "Klicken Sie, um ein Bild auszuwählen",
        "btn_image_translate": "Bild übersetzen",
        "result_label": "Übersetzungsergebnis",
        "nav_text": "Text",
        "nav_image": "Bild",
        "nav_voice": "Sprache",
        "nav_camera": "Kamera"
    },
    "Chinese (Simplified)": {
        "title": "AI 多功能翻译器",
        "text_placeholder": "输入文本...",
        "btn_text_translate": "翻译",
        "image_input_label": "点击选择图片",
        "btn_image_translate": "翻译图片",
        "result_label": "翻译结果",
        "nav_text": "文本",
        "nav_image": "图片",
        "nav_voice": "语音",
        "nav_camera": "相机"
    },
    "Korean": {
        "title": "AI 만능 번역기",
        "text_placeholder": "텍스트 입력...",
        "btn_text_translate": "번역하기",
        "image_input_label": "클릭하여 이미지 선택",
        "btn_image_translate": "이미지 번역하기",
        "result_label": "번역 결과",
        "nav_text": "텍스트",
        "nav_image": "이미지",
        "nav_voice": "음성",
        "nav_camera": "카메라"
    }
}

def generate_content_with_retry(prompt, retries=3, initial_delay=2):
    if not client:
        return None
    delay = initial_delay
    for attempt in range(retries):
        try:
            return client.models.generate_content(model='gemini-3.8-flash', contents=prompt)
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise e

def get_ui_labels(lang):
    """言語設定に応じたUIラベルを取得（辞書にない言語はEnglishフォールバック）"""
    return UI_CACHE.get(lang, UI_CACHE["English"])

@app.route('/select-language')
def select_language():
    lang_type = request.args.get('type', 'target')
    return render_template('select_language.html', languages=SUPPORTED_LANGUAGES, lang_type=lang_type)

@app.route('/set-language', methods=['POST'])
def set_language():
    selected_lang = request.form.get('target_lang', 'English')
    lang_type = request.form.get('lang_type', 'target')
    
    if lang_type == 'source':
        session['source_lang'] = selected_lang
    else:
        session['target_lang'] = selected_lang
        
    return redirect(url_for('index'))

@app.route('/swap-language', methods=['POST'])
def swap_language():
    source_lang = session.get('source_lang', 'Japanese')
    target_lang = session.get('target_lang', 'English')

    session['source_lang'] = target_lang
    session['target_lang'] = source_lang
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'source_lang' not in session:
        session['source_lang'] = 'Japanese'
    if 'target_lang' not in session:
        session['target_lang'] = 'English'

    source_lang = session.get('source_lang', 'Japanese')
    target_lang = session.get('target_lang', 'English')
    
    # 自分側の言語 (source_lang) に連動してUI表記を変更
    ui = get_ui_labels(source_lang)

    ocr_text = ''
    translated_text = ''
    detected_lang = ''
    active_mode = 'text'

    if request.method == 'POST':
        mode = request.form.get('mode', 'text')
        active_mode = mode
        raw_input_text = ""

        if mode == 'text':
            raw_input_text = request.form.get('direct_text', '').strip()
        elif mode == 'voice':
            raw_input_text = request.form.get('voice_text', '').strip()
        elif mode == 'image':
            file = request.files.get('image')
            if file and file.filename != '':
                try:
                    image = Image.open(file.stream)
                    raw_input_text = pytesseract.image_to_string(image, lang='eng+jpn').strip()
                except Exception as e:
                    raw_input_text = f"文字認識エラー: {e}"
        elif mode == 'camera':
            camera_data = request.form.get('camera_data')
            if camera_data and ',' in camera_data:
                try:
                    img_bytes = base64.b64decode(camera_data.split(',')[1])
                    image = Image.open(io.BytesIO(img_bytes))
                    raw_input_text = pytesseract.image_to_string(image, lang='eng+jpn').strip()
                except Exception as e:
                    raw_input_text = f"カメラ画像解析エラー: {e}"

        ocr_text = raw_input_text

        if ocr_text and not ocr_text.startswith("文字認識エラー") and not ocr_text.startswith("カメラ画像解析エラー"):
            if client:
                try:
                    if mode == 'text':
                        prompt = f"Translate the following text from {source_lang} to {target_lang} naturally without extra explanations:\n\n{ocr_text}"
                        detected_lang = source_lang
                    else:
                        prompt = f"Identify original language, then