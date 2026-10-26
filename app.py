import io
import json
import os
from flask import Flask, render_template, request, redirect, url_for, session
from google import genai
import pytesseract
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "app-secret-key-12345")

# APIキーの取得とクライアント初期化
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# サポートする言語リスト（全33言語）
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
        "swap_btn": "言語切り替え"
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
        "swap_btn": "Swap Language"
    },
    "Spanish": {
        "title": "📷 Traductor Universal IA",
        "subtitle": "Traduzca mediante entrada de texto directa o carga de imágenes.",
        "text_input_label": "Ingrese texto directamente para traducir",
        "text_placeholder": "Ingrese el texto a traducir...",
        "btn_text_translate": "Traducir texto",
        "or": "o",
        "image_input_label": "Haga clic para seleccionar imagen",
        "btn_image_translate": "Traducir imagen",
        "target_text_label": "Texto de origen",
        "result_label": "Resultado de traducción e IA",
        "change_lang": "Cambiar idioma",
        "swap_btn": "Cambiar idioma"
    },
    "French": {
        "title": "📷 Traducteur Universel IA",
        "subtitle": "Traduisez par saisie directe de texte ou téléchargement d'image.",
        "text_input_label": "Saisir du texte directement pour traduire",
        "text_placeholder": "Entrez le texte à traduire...",
        "btn_text_translate": "Traduire le texte",
        "or": "ou",
        "image_input_label": "Cliquez pour sélectionner une image",
        "btn_image_translate": "Traduire l'image",
        "target_text_label": "Texte source",
        "result_label": "Résultat de la traduction IA",
        "change_lang": "Changer de langue",
        "swap_btn": "Changer de langue"
    },
    "German": {
        "title": "📷 KI-Multisprach-Übersetzer",
        "subtitle": "Übersetzen Sie per Texteingabe oder Bild-Upload.",
        "text_input_label": "Text direkt eingeben und übersetzen",
        "text_placeholder": "Geben Sie den Text ein...",
        "btn_text_translate": "Text übersetzen",
        "or": "oder",
        "image_input_label": "Klicken Sie, um ein Bild auszuwählen",
        "btn_image_translate": "Bild übersetzen",
        "target_text_label": "Quelltext",
        "result_label": "Übersetzungsergebnis",
        "change_lang": "Sprache wechseln",
        "swap_btn": "Sprache wechseln"
    }
}

def get_ui_labels(target_lang):
    """選択言語のUI文言を取得"""
    return UI_CACHE.get(target_lang, UI_CACHE["English"])

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
    """テキスト入力のみの言語入れ替え（検出言語 ⇄ Target）"""
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
    is_text_translation = False

    if request.method == 'POST':
        direct_text = request.form.get('direct_text')
        file = request.files.get('image')

        # 1. テキスト直接入力の場合
        if direct_text and direct_text.strip() != '':
            ocr_text = direct_text.strip()
            is_text_translation = True
        # 2. 画像ファイルの場合（画像翻訳は入れ替えデータの保存を行わない）
        elif file and file.filename != '':
            session.pop('last_detected_lang', None)
            session.pop('last_translation_result', None)
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
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt,
                    )
                    translated_text = response.text

                    # テキスト入力翻訳の時のみ切り替え用にセッション保存
                    if is_text_translation and "【Detected Language】" in translated_text and "【Translation Result】" in translated_text:
                        parts = translated_text.split("【Translation Result】")
                        detected = parts[0].replace("【Detected Language】", "").strip()
                        result_only = parts[1].strip()
                        session['last_detected_lang'] = detected
                        session['last_translation_result'] = result_only

                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        translated_text = "⚠️ Gemini APIの本日分の無料上限に達しました。時間を置いて試すか、APIキーを更新してください。"
                    else:
                        translated_text = f"AI翻訳エラー: {e}"
            else:
                translated_text = "GEMINI_API_KEY が設定されていません。"

    return render_template('index.html', 
                           ocr_text=ocr_text, 
                           translated_text=translated_text,
                           target_lang=target_lang,
                           ui=ui,
                           is_text_translation=is_text_translation)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)