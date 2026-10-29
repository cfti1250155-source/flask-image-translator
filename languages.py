# 対応言語リスト
SUPPORTED_LANGUAGES = [
    "Japanese", "English", "Chinese", "Korean", "Spanish", 
    "French", "German", "Italian", "Russian", "Portuguese"
]

# 各言語のUIラベル辞書
UI_LABELS = {
    'Japanese': {
        'title': 'AI万能翻訳アプリ',
        'text_placeholder': 'テキストを入力...',
        'btn_text_translate': '翻訳する',
        'image_input_label': 'クリックして画像を選択',
        'btn_image_translate': '画像を翻訳する',
        'voice_instruction': 'マイクボタンを押して話してください',
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
    },
    'English': {
        'title': 'AI Universal Translator',
        'text_placeholder': 'Enter text here...',
        'btn_text_translate': 'Translate',
        'image_input_label': 'Click to select image',
        'btn_image_translate': 'Translate Image',
        'voice_instruction': 'Press mic button and speak',
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
    }
}

def get_ui_labels(lang):
    """指定された言語のUIラベルを取得（未登録ならEnglish）"""
    return UI_LABELS.get(lang, UI_LABELS['English'])