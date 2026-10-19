import io
from flask import Flask, render_template, request
from google.cloud import vision
from google.cloud import translate_v2 as translate

app = Flask(__name__)

# クライアントの初期化
vision_client = vision.ImageAnnotatorClient()
translate_client = translate.Client()

@app.route('/', methods=['GET', 'POST'])
def index():
    ocr_text = ""
    translated_text = ""
    detected_lang_display = ""  # 表示用の言語名

    if request.method == 'POST':
        file = request.files.get('image')
        if file:
            # 1. 画像の読み込み
            content = file.read()
            image = vision.Image(content=content)

            # 2. Vision API で文字検出
            response = vision_client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                ocr_text = texts[0].description

                # 3. Translate API で翻訳
                result = translate_client.translate(ocr_text, target_language='ja')
                translated_text = result['translatedText']
                lang_code = result.get('detectedSourceLanguage', '')

                if lang_code:
                    # 言語コード（en等）から日本語での言語名（英語等）を取得
                    languages = translate_client.get_languages(target_language='ja')
                    lang_name = next((l['name'] for l in languages if l['language'] == lang_code), lang_code)
                    
                    # 「英語 (en)」の形式で作成
                    detected_lang_display = f"{lang_name} ({lang_code})"

    return render_template(
        'index.html', 
        ocr_text=ocr_text, 
        translated_text=translated_text,
        detected_lang=detected_lang_display
    )

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)