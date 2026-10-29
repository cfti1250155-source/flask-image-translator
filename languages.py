# 対応言語リスト（name はフォーム値・Geminiへの指示に使う英語名、code は音声認識用 BCP-47）
# 言語を増やすときは LANGUAGES に1行足すだけでOK
LANGUAGES = [
    {"name": "Japanese",   "code": "ja-JP", "native": "日本語"},
    {"name": "English",    "code": "en-US", "native": "English"},
    {"name": "Chinese",    "code": "zh-CN", "native": "中文"},
    {"name": "Korean",     "code": "ko-KR", "native": "한국어"},
    {"name": "Spanish",    "code": "es-ES", "native": "Español"},
    {"name": "French",     "code": "fr-FR", "native": "Français"},
    {"name": "German",     "code": "de-DE", "native": "Deutsch"},
    {"name": "Italian",    "code": "it-IT", "native": "Italiano"},
    {"name": "Russian",    "code": "ru-RU", "native": "Русский"},
    {"name": "Portuguese", "code": "pt-BR", "native": "Português"},
]

SUPPORTED_LANGUAGES = [l["name"] for l in LANGUAGES]
_BY_NAME = {l["name"]: l for l in LANGUAGES}


def is_supported(name):
    return name in _BY_NAME


def get_lang_code(name):
    return _BY_NAME.get(name, _BY_NAME["English"])["code"]


def get_native_name(name):
    return _BY_NAME.get(name, {}).get("native", name)


# 各言語のUIラベル辞書（未登録の言語・キーは English で補完）
UI_LABELS = {
    'Japanese': {
        'title': 'AI万能翻訳アプリ',
        'source_label': '翻訳元',
        'target_label': '翻訳先',
        'target_label_short': '翻訳先言語',
        'select_language': '言語を選択',
        'confirm': '確定する',
        'text_placeholder': 'テキストを入力...',
        'btn_text_translate': '翻訳する',
        'image_input_label': 'クリックして画像を選択',
        'btn_image_translate': '画像を翻訳する',
        'voice_instruction': 'マイクボタンを押して話してください',
        'voice_listening': '音声入力中...',
        'voice_placeholder': '認識された音声...',
        'btn_voice_translate': '音声を翻訳する',
        'camera_instruction': '「カメラ起動」を押して撮影してください',
        'btn_camera_start': 'カメラ起動',
        'btn_camera_capture': '撮影して翻訳',
        'nav_text': 'テキスト',
        'nav_image': '画像',
        'nav_voice': '音声',
        'nav_camera': 'カメラ',
        'result_label': '翻訳結果',
        'original_label': '認識した原文',
        'translating': '翻訳中...',
        'copied': 'コピーしました',
        'err_empty': 'テキストを入力してください。',
        'err_too_long': 'テキストが長すぎます（最大5000文字）。',
        'err_rate': 'リクエストが多すぎます。少し待ってからもう一度お試しください。',
        'err_no_key': 'サーバーにAPIキー（GEMINI_API_KEY）が設定されていません。',
        'err_failed': '翻訳に失敗しました。時間をおいて再度お試しください。',
        'err_image': '画像を読み込めませんでした（PNG/JPG/WEBP/HEIC に対応）。',
        'err_too_big': '画像のサイズが大きすぎます（最大10MB）。',
        'err_no_text': '画像の中に文字が見つかりませんでした。',
        'err_no_speech': '音声が認識できませんでした。もう一度お試しください。',
        'err_no_speech_api': 'このブラウザは音声認識に対応していません。',
        'err_camera': 'カメラを起動できませんでした',
        'err_camera_first': '先にカメラを起動してください。',
    },
    'English': {
        'title': 'AI Universal Translator',
        'source_label': 'From',
        'target_label': 'To',
        'target_label_short': 'Target language',
        'select_language': 'Select language',
        'confirm': 'Confirm',
        'text_placeholder': 'Enter text here...',
        'btn_text_translate': 'Translate',
        'image_input_label': 'Click to select image',
        'btn_image_translate': 'Translate Image',
        'voice_instruction': 'Press mic button and speak',
        'voice_listening': 'Listening...',
        'voice_placeholder': 'Recognized speech...',
        'btn_voice_translate': 'Translate Voice',
        'camera_instruction': 'Press "Start Camera" to capture',
        'btn_camera_start': 'Start Camera',
        'btn_camera_capture': 'Capture & Translate',
        'nav_text': 'Text',
        'nav_image': 'Image',
        'nav_voice': 'Voice',
        'nav_camera': 'Camera',
        'result_label': 'Result',
        'original_label': 'Recognized text',
        'translating': 'Translating...',
        'copied': 'Copied',
        'err_empty': 'Please enter some text.',
        'err_too_long': 'Text is too long (max 5000 characters).',
        'err_rate': 'Too many requests. Please wait a moment and try again.',
        'err_no_key': 'The server has no API key (GEMINI_API_KEY) configured.',
        'err_failed': 'Translation failed. Please try again later.',
        'err_image': 'Could not read the image (PNG/JPG/WEBP/HEIC supported).',
        'err_too_big': 'The image is too large (max 10 MB).',
        'err_no_text': 'No text was found in the image.',
        'err_no_speech': 'Speech was not recognized. Please try again.',
        'err_no_speech_api': 'This browser does not support speech recognition.',
        'err_camera': 'Could not start the camera',
        'err_camera_first': 'Please start the camera first.',
    },
}


def get_ui_labels(lang):
    """指定言語のUIラベル。足りないキーは English で補完する"""
    labels = dict(UI_LABELS['English'])
    labels.update(UI_LABELS.get(lang, {}))
    return labels