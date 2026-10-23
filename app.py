import io
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

# サポートする言語リスト（日本語＋英語表記）
SUPPORTED_LANGUAGES = [
    "日本語 (Japanese)", "英語 (English)", "スペイン語 (Spanish)", "フランス語 (French)", 
    "ドイツ語 (German)", "中国語・簡体字 (Chinese Simplified)", "中国語・繁体字 (Chinese Traditional)", 
    "韓国語 (Korean)", "イタリア語 (Italian)", "ロシア語 (Russian)", "ポルトガル語 (Portuguese)", 
    "タイ語 (Thai)", "ベトナム語 (Vietnamese)", "インドネシア語 (Indonesian)", "トルコ語 (Turkish)", 
    "アラビア語 (Arabic)", "ヒンディー語 (Hindi)", "オランダ語 (Dutch)", "ポーランド語 (Polish)", 
    "スウェーデン語 (Swedish)", "ギリシャ語 (Greek)", "チェコ語 (Czech)", "ハンガリー語 (Hungarian)", 
    "ルーマニア語 (Romanian)", "ウクライナ語 (Ukrainian)", "ヘブライ語 (Hebrew)", "マレー語 (Malay)", 
    "ペルシア語 (Persian)", "タガログ語 (Tagalog)", "スワヒリ語 (Swahili)", "デンマーク語 (Danish)", 
    "フィンランド語 (Finnish)", "ノルウェー語 (Norwegian)"
]

# 各言語のUI表示テキスト
UI_LABELS = {
    "日本語": {
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
        "change_lang": "言語変更"
    },
    "英語": {
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
        "change_lang": "Change Language"
    }
}

DEFAULT_UI = UI_LABELS["日本語"]

@app.route('/select-language')
def select_language():
    return render_template('select_language.html', languages=SUPPORTED_LANGUAGES)

@app.route('/set-language', methods=['POST'])
def set_language():
    selected = request.form.get('target_lang', '日本語 (Japanese)')
    # 表示用の言語名（「 (Japanese)」などを除去した部分）を取り出す
    clean_lang = selected.split(' (')[0]
    session['target_lang'] = clean_lang
    session['full_target_lang'] = selected
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'target_lang' not in session:
        return redirect(url_for('select_language'))

    target_lang = session.get('target_lang', '日本語')
    ui = UI_LABELS.get(target_lang, DEFAULT_UI)

    ocr_text = ''
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
以下の文章の「元の言語」を判定し、自然で読みやすい【{target_lang}】に翻訳・校正してください。
余計な解説は含めず、必ず以下の形式のみで出力してください：

【判定言語】
（ここに判定した元の言語名を出力）

【翻訳・校正結果】
（ここに【{target_lang}】への翻訳後の文章のみを出力）

対象文章：
{ocr_text}
"""
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt,
                    )
                    translated_text = response.text
                except Exception as e:
                    translated_text = f"AI翻訳エラー: {e}"
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