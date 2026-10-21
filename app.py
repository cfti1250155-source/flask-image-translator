import io
import os
from flask import Flask, render_template, request
from google import genai
import pytesseract
from PIL import Image

app = Flask(__name__)

# APIキーの取得とクライアント初期化
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.route('/', methods=['GET', 'POST'])
def index():
    ocr_text = ''
    translated_text = ''

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename != '':
            try:
                # 1. OCR処理
                image = Image.open(file.stream)
                ocr_text = pytesseract.image_to_string(image, lang='eng+jpn')
            except Exception as e:
                ocr_text = f"文字認識エラー: {e}"

            # 2. 翻訳処理
            if ocr_text and not ocr_text.startswith("文字認識エラー"):
                if client:
                    try:
                        prompt = f"""
                        以下の文章の「元の言語」を判定し、自然で読みやすい日本語に翻訳・校正してください。
                        余計な解説は含めず、必ず以下の形式のみで出力してください：

                        【判定言語】
                        （ここに判定した言語名を出力。例：英語、フランス語、中国語など）

                        【翻訳・校正結果】
                        （ここに翻訳後の日本語のみを出力）

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
                           translated_text=translated_text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)