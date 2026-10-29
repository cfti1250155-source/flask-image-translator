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

# 各言語のUI表示テキスト（全モードのテキストを追加）
UI_CACHE = {
    "Japanese": {
        "title": "AI万能翻訳アプリ",
        "text_placeholder": "テキストを入力...",
        "btn_text_translate": "翻訳する",
        "image_input_label": "クリックして画像を選択",
        "btn_image_translate": "画像を翻訳する",
        "voice_instruction": "マイクボタンを押して喋ってください",
        "voice_placeholder": "聞き取った音声...",
        "btn_voice_translate": "音声を翻訳する",
        "camera_instruction": "「カメラ起動」を押して写真を撮影してください",
        "btn_camera_start": "カメラ起動",
        "btn_camera_capture": "撮影して翻訳",
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
        "voice_instruction": "Press the mic button and speak",
        "voice_placeholder": "Recognized speech...",
        "btn_voice_translate": "Translate Voice",
        "camera_instruction": "Press 'Start Camera' to take a photo",
        "btn_camera_start": "Start Camera",
        "btn_camera_capture": "Capture & Translate",
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
        "voice_instruction": "Presione el micrófono y hable",
        "voice_placeholder": "Voz reconocida...",
        "btn_voice_translate": "Traducir Voz",
        "camera_instruction": "Presione 'Iniciar Cámara' para tomar foto",
        "btn_camera_start": "Iniciar Cámara",
        "btn_camera_capture": "Capturar y Traducir",
        "result_label": "Resultado",
        "nav_text": "Texto",
        "nav_image": "Imagen",
        "nav_voice": "Voz",
        "nav_camera": "Cámara"
    },
    "Chinese (Simplified)": {
        "title": "AI 多功能翻译器",
        "text_placeholder": "输入文本...",
        "btn_text_translate": "翻译",
        "image_input_label": "点击选择图片",
        "btn_image_translate": "翻译图片",
        "voice_instruction": "点击麦克风按钮开始说话",
        "voice_placeholder": "识别的语音...",
        "btn_voice_translate": "翻译语音",
        "camera_instruction": "点击“启动相机”拍照",
        "btn_camera_start": "启动相机",
        "btn_camera_capture": "拍照并翻译",
        "result_label": "翻译结果",
        "nav_text": "文本",
        "nav_image": "图片",
        "nav_voice": "语音",
        "nav_camera": "相机"
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

@app.route('/swap-language', methods=['GET', 'POST'])
def swap_language():
    # 翻訳元と翻訳先を安全に入れ替え
    source = session.get('source_lang', 'Japanese')
    target = session.get('target_lang', 'English')
    session['source_lang'] = target
    session['target_lang'] = source
    # 直前のページ（テキストタブ）へ戻る
    return redirect(request.referrer or url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'source_lang' not in session:
        session['source_lang'] = 'Japanese'
    if 'target_lang' not in session:
        session['target_lang'] = 'English'

    source_lang = session.get('source_lang', 'Japanese')
    target_lang = session.get('target_lang', 'English')
    
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
                        prompt = f"Identify original language, then translate strictly into 【{target_lang}】:\nFormat:\n【Detected Language】\n(Language)\n【Translation Result】\n(Result)\nText:\n{ocr_text}"

                    response = generate_content_with_retry(prompt)
                    if response:
                        raw_resp = response.text
                        if "【Detected Language】" in raw_resp and "【Translation Result】" in raw_resp:
                            parts = raw_resp.split("【Translation Result】")
                            detected_lang = parts[0].replace("【Detected Language】", "").strip()
                            translated_text = parts[1].strip()
                        else:
                            translated_text = raw_resp

                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        translated_text = "⚠️ Gemini APIの上限に達しました。時間をおいてお試しください。"
                    else:
                        translated_text = f"AI翻訳エラー: {e}"

    return render_template('index.html', 
                           ocr_text=ocr_text, 
                           translated_text=translated_text,
                           detected_lang=detected_lang,
                           source_lang=source_lang,
                           target_lang=target_lang,
                           ui=ui,
                           active_mode=active_mode)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)