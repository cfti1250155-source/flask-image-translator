import io
import os
from flask import Flask, render_template, request
from google.cloud import vision
from deep_translator import GoogleTranslator
from google import genai

app = Flask(__name__)

# クライアントの初期化（Vision API のみ Google Cloud を使用）
vision_client = vision.ImageAnnotatorClient()
translator = GoogleTranslator(source='auto', target='ja')

# Gemini API クライアント（環境変数 GEMINI_API_KEY を使用）
ai_client = genai.Client() if os.environ.get("GEMINI_API_KEY") else None

@app.route('/', methods=['GET', 'POST'])
def index():
    ocr_text = ''
    translated_text = ''
    detected_lang_display = ''

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename != '':
            content = file.read()
            
            # 1. Vision API で文字認識
            image = vision.Image(content=content)
            response = vision_client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                ocr_text = texts[0].description
                
                # 2. 完全無料ライブラリ（deep-translator）で翻訳
                raw_translation = translator.translate(ocr_text)

                # 3. Gemini API で自然な日本語に整える（APIキー設定時のみ）
                if ai_client:
                    try:
                        prompt = f"以下の文章の意味を維持しつつ、自然で読みやすい日本語に校正してください。余計な解説は含めず文章のみを出力してください:\n\n{raw_translation}"
                        res = ai_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt
                        )
                        translated_text = res.text
                    except Exception as e:
                        print(f"Gemini error: {e}")
                        translated_text = raw_translation
                else:
                    translated_text = raw_translation

    return render_template('index.html', 
                           ocr_text=ocr_text, 
                           translated_text=translated_text, 
                           detected_lang=detected_lang_display)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)