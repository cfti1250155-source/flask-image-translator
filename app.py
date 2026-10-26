import io
import json
import os
import time
from flask import Flask, render_template, request, redirect, url_for, session
from google import genai
import pytesseract
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "app-secret-key-12345")

# APIキーの取得とクライアント初期化
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# サポートする言語リスト（全33言語・英語表記）
SUPPORTED_LANGUAGES = [
    "Japanese", "English", "Spanish", "French", "German", 
    "Chinese (Simplified)", "Chinese (Traditional)", "Korean", "Italian", "Russian", 
    "Portuguese", "Thai", "Vietnamese", "Indonesian", "Turkish", 
    "Arabic", "Hindi", "Dutch", "Polish", "Swedish", 
    "Greek", "Czech", "Hungarian", "Romanian", "Ukrainian", 
    "Hebrew", "Malay", "Persian", "Tagalog", "Swahili", 
    "Danish", "Finnish", "Norwegian"
]

# 各言語のUI表示テキスト（標準辞書）
UI_CACHE = {
    "Japanese": {
        "title": "📷 AI万能翻訳アプリ",
        "subtitle": "テキスト入力または画像アップロードで自動翻訳します。",
        "text_input_label": "テキストを直接入力して翻訳",
        "text_placeholder": "翻訳したい文章を入力...",
        "btn_text_translate": "テキストを翻訳する",
        "or": "または",
        "image_input_label": "クリックして画像を選択",
        "btn_image_translate": "画像を翻訳する",
        "target_text_label": "対象テキスト",
        "result_label": "翻訳・AI校正結果",
        "change_lang": "言語変更",
        "swap_btn": "⇄ 逆翻訳"
    },
    "English": {
        "title": "📷 AI Multi-Translator",
        "subtitle": "Translate via direct text input or image upload.",
        "text_input_label": "Direct Text Translation",
        "text_placeholder": "Enter text to translate...",
        "btn_text_translate": "Translate Text",
        "or": "OR",
        "image_input_label": "Click to select image",
        "btn_image_translate": "Translate Image",
        "target_text_label": "Source Text",
        "result_label": "Translation & AI Result",
        "change_lang": "Change Language",
        "swap_btn": "⇄ Reverse"
    }
}

def generate_content_with_retry(prompt, retries=3, initial_delay=2):
    """Gemini APIの一時的混雑（503エラー）に対応する自動リトライ（指数バックオフ）"""
    if not client:
        return None
    delay = initial_delay
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt
            )
            return response
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise e

def get_ui_labels(target_lang):
    """選択言語のUI文言を取得"""
    if target_lang in UI_CACHE:
        return UI_CACHE[target_lang]

    if client:
        try:
            prompt = f"""
Translate the following UI menu labels into {target_lang}.
Return ONLY valid JSON matching this exact structure:
{{
  "title": "📷 AI Multi-Translator",
  "subtitle": "Translate via direct text input or image upload.",
  "text_input_label": "Direct Text Translation",
  "text_placeholder": "Enter text to translate...",
  "btn_text_translate": "Translate Text",
  "or": "OR",
  "image_input_label": "Click to select image",
  "btn_image_translate": "Translate Image",
  "target_text_label": "Source Text",
  "result_label": "Translation & AI Result",
  "change_lang": "Change Language",
  "swap_btn": "⇄ Reverse"
}}
"""
            response = generate_content_with_retry(prompt)
            if response:
                text_resp = response.text.strip()
                if "```" in text_resp:
                    text_resp = text_resp.split("```")[1]
                    if text_resp.startswith("json"):
                        text_resp = text_resp[4:].strip()
                labels = json.loads(text_resp)
                UI_CACHE[target_lang] = labels
                return labels
        except Exception:
            pass

    return UI_CACHE["English"]

@app.route('/select-language')
def select_language():
    return render_template('select_language.html', languages=SUPPORTED_LANGUAGES)

@app.route('/set-language', methods=['POST'])
def set_language():
    target_lang = request.form.get('target_lang', 'English')
    session['target_lang'] = target_lang
    return redirect(url_for('index'))

@app.route('/swap-language', methods=['POST'])
def swap_language():
    """言語の双方向入れ替え（検出言語 ⇄ Target）"""
    last_detected = session.get('last_detected_lang')
    last_result = session.get('last_translation_result')
    current_target = session.get('target_lang', 'English')

    if last_detected and last_detected in SUPPORTED_LANGUAGES:
        session['target_lang'] = last_detected
    else:
        session['target_lang'] = "Japanese" if current_target != "Japanese" else "English"

    if last_result:
        session['input_preset'] = last_result

    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'target_lang' not in session:
        return redirect(url_for('select_language'))

    target_lang = session.get('target_lang', 'English')
    ui = get_ui_labels(target_lang)

    ocr_text = session.pop('input_preset', '')
    translated_text = ''

    if request.method == 'POST':
        direct_text = request.form.get('direct_text')
        file = request.files.get('image')

        if direct_text and direct_text.strip() != '':
            ocr_text = direct_text.strip()
        elif file and file.filename != '':
            try:
                image = Image.open(file.stream)
                ocr_text = pytesseract.image_to_string(image, lang='eng+jpn')
            except Exception as e:
                ocr_text = f"文字認識エラー: {e}"

        if ocr_text and not ocr_text.startswith("文字認識エラー"):
            if client:
                try:
                    prompt = f"""
Identify the original language of the text below, and translate it naturally into 【{target_lang}】.
Do not include extra explanations. Output strictly in this format:

【Detected Language】
(Name of the original language from this list if possible: {', '.join(SUPPORTED_LANGUAGES)})

【Translation Result】
(Translated text in {target_lang})

Text:
{ocr_text}
"""
                    response = generate_content_with_retry(prompt)
                    if response:
                        translated_text = response.text

                        if "【Detected Language】" in translated_text and "【Translation Result】" in translated_text:
                            parts = translated_text.split("【Translation Result】")
                            detected = parts[0].replace("【Detected Language】", "").strip()
                            result_only = parts[1].strip()
                            session['last_detected_lang'] = detected
                            session['last_translation_result'] = result_only
                except Exception as e:
                    translated_text = f"AI翻訳エラー: Google APIが混雑しています。数秒後に再度「翻訳する」を押してください ({e})"
            else:
                translated_text = "GEMINI_API_KEY が設定されていません。"

    return render_template('index.html', 
                           ocr_text=ocr_text, 
                           translated_text=translated_text,
                           target_lang=target_lang,
                           ui=ui)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)