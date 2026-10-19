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
    ocr_text = ''
    translated_text = ''
    detected_lang_display = ''

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename != '':
            content = file.read()
            
            # Vision API で文字認識
            image = vision.Image(content=content)
            response = vision_client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                ocr_text = texts[0].description
                
                # Translation API で翻訳
                result = translate_client.translate(ocr_text, target_language='ja')
                translated_text = result.get('translatedText', '')
                detected_lang = result.get('detectedSourceLanguage', '')
                detected_lang_display = detected_lang.upper()

    return render_template('index.html', 
                           ocr_text=ocr_text, 
                           translated_text=translated_text, 
                           detected_lang=detected_lang_display)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)