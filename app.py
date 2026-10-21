import io
import os
from flask import Flask, render_template, request
from google import genai
import pytesseract
from PIL import Image

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    ocr_text = ''
    translated_text = ''

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename != '':
            try:
                # 1. Tesseract OCR で文字認識
                image = Image.open(file.stream)
                ocr_text = pytesseract.image_to_string(image, lang='eng+jpn')
            except Exception as e:
                ocr_text = f"文字認識エラー: {e}"

            # 2. Gemini API で直接日本語翻訳＆校正
            if ocr_text and not ocr_text.startswith("文字認識エラー"):
                api_key = os.environ.get("GEMINI_API_KEY")
                if api_key:
                    try:
                        ai_client = genai.Client(api_key=api_key)
                        prompt = f"以下の文章を自然で読みやすい日本語に翻訳・校正してください。余計な解説は含めず、翻訳後の文章のみを出力してください:\n\n{ocr_text}"
                        res = ai_client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=prompt
                    )
                        translated_text = res.text
                    except Exception as e:
                        translated_text = f"AI翻訳エラー: {e}"
                else:
                    translated_text = "GEMINI_API_KEY が設定されていません。"

    return render_template('index.html', 
                           ocr_text=ocr_text, 
                           translated_text=translated_text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)