import io
import os
from flask import Flask, render_template, request
from deep_translator import GoogleTranslator
from google import genai
import easyocr

app = Flask(__name__)

# EasyOCR の初期化（英語・日本語に対応）
reader = easyocr.Reader(['en', 'ja'])

@app.route('/', methods=['GET', 'POST'])
def index():
    ocr_text = ''
    translated_text = ''
    detected_lang_display = ''

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename != '':
            content = file.read()
            
            # 1. EasyOCR で文字認識（クレジットカード完全不要）
            try:
                results = reader.readtext(content, detail=0)
                ocr_text = "\n".join(results)
            except Exception as e:
                ocr_text = f"文字認識エラー: {e}"

            # 2. deep-translator で日本語翻訳
            if ocr_text and not ocr_text.startswith("文字認識エラー"):
                try:
                    translator = GoogleTranslator(source='auto', target='ja')
                    raw_translation = translator.translate(ocr_text)
                except Exception as e:
                    raw_translation = f"翻訳エラー: {e}"

                # 3. Gemini API で文章校正
                api_key = os.environ.get("GEMINI_API_KEY")
                if api_key and not raw_translation.startswith("翻訳エラー"):
                    try:
                        ai_client = genai.Client(api_key=api_key)
                        prompt = f"以下の文章の意味を維持しつつ、自然で読みやすい日本語に校正してください。余計な解説は含めず文章のみを出力してください:\n\n{raw_translation}"
                        res = ai_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt
                        )
                        translated_text = res.text
                    except Exception as e:
                        translated_text = f"{raw_translation} (※AI整文スキップ: {e})"
                else:
                    translated_text = raw_translation

    return render_template('index.html', 
                           ocr_text=ocr_text, 
                           translated_text=translated_text, 
                           detected_lang=detected_lang_display)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)