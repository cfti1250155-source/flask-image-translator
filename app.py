import os
from flask import Flask, render_template, request, session, redirect, url_for
# 作成した languages.py から読み込み
from languages import SUPPORTED_LANGUAGES, get_ui_labels

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key")

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'source_lang' not in session:
        session['source_lang'] = 'Japanese'
    if 'target_lang' not in session:
        session['target_lang'] = 'English'

    source_lang = session.get('source_lang', 'Japanese')
    target_lang = session.get('target_lang', 'English')
    
    # UIの表記は「翻訳先言語（target_lang）」を基準に取得
    ui = get_ui_labels(target_lang)

    active_mode = 'text'
    translated_text = None
    detected_lang = None

    if request.method == 'POST':
        active_mode = request.form.get('mode', 'text')
        # ※ここに既存の翻訳ロジック（テキスト・画像・音声・カメラ処理）が入ります

    return render_template('index.html', 
                           source_lang=source_lang, 
                           target_lang=target_lang, 
                           ui=ui, 
                           active_mode=active_mode,
                           translated_text=translated_text,
                           detected_lang=detected_lang)

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
    source = session.get('source_lang', 'Japanese')
    target = session.get('target_lang', 'English')
    session['source_lang'] = target
    session['target_lang'] = source
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)