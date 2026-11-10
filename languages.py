# 対応言語リスト（name はフォーム値・Geminiへの指示に使う英語名、code は音声認識用 BCP-47）
# 言語を増やすときは LANGUAGES に1行足すだけでOK
AUTO = "Auto"  # 翻訳元の自動判定（翻訳元にだけ指定できる）

# name: フォーム値・Geminiへの指示に使う英語名 / code: 音声認識・読み上げ用 BCP-47 / rtl: 右から左へ書く言語
_RAW = [
    ("Japanese", "ja-JP", "日本語", False),
    ("English", "en-US", "English", False),
    ("Chinese (Simplified)", "zh-CN", "简体中文", False),
    ("Chinese (Traditional)", "zh-TW", "繁體中文", False),
    ("Korean", "ko-KR", "한국어", False),
    ("Spanish", "es-ES", "Español", False),
    ("French", "fr-FR", "Français", False),
    ("German", "de-DE", "Deutsch", False),
    ("Italian", "it-IT", "Italiano", False),
    ("Portuguese", "pt-BR", "Português", False),
    ("Russian", "ru-RU", "Русский", False),
    ("Arabic", "ar-SA", "العربية", True),
    ("Hindi", "hi-IN", "हिन्दी", False),
    ("Bengali", "bn-BD", "বাংলা", False),
    ("Tamil", "ta-IN", "தமிழ்", False),
    ("Urdu", "ur-PK", "اردو", True),
    ("Persian", "fa-IR", "فارسی", True),
    ("Hebrew", "he-IL", "עברית", True),
    ("Turkish", "tr-TR", "Türkçe", False),
    ("Indonesian", "id-ID", "Bahasa Indonesia", False),
    ("Malay", "ms-MY", "Bahasa Melayu", False),
    ("Filipino", "fil-PH", "Filipino", False),
    ("Thai", "th-TH", "ไทย", False),
    ("Vietnamese", "vi-VN", "Tiếng Việt", False),
    ("Dutch", "nl-NL", "Nederlands", False),
    ("Polish", "pl-PL", "Polski", False),
    ("Ukrainian", "uk-UA", "Українська", False),
    ("Czech", "cs-CZ", "Čeština", False),
    ("Slovak", "sk-SK", "Slovenčina", False),
    ("Hungarian", "hu-HU", "Magyar", False),
    ("Romanian", "ro-RO", "Română", False),
    ("Bulgarian", "bg-BG", "Български", False),
    ("Greek", "el-GR", "Ελληνικά", False),
    ("Croatian", "hr-HR", "Hrvatski", False),
    ("Serbian", "sr-RS", "Српски", False),
    ("Swedish", "sv-SE", "Svenska", False),
    ("Norwegian", "nb-NO", "Norsk", False),
    ("Danish", "da-DK", "Dansk", False),
    ("Finnish", "fi-FI", "Suomi", False),
    ("Catalan", "ca-ES", "Català", False),
    ("Swahili", "sw-KE", "Kiswahili", False),
]
LANGUAGES = [{"name": n, "code": c, "native": nat, "rtl": rtl} for n, c, nat, rtl in _RAW]

SUPPORTED_LANGUAGES = [l["name"] for l in LANGUAGES]
_BY_NAME = {l["name"]: l for l in LANGUAGES}
_BY_LOWER = {l["name"].lower(): l["name"] for l in LANGUAGES}


def is_supported(name, allow_auto=False):
    return name in _BY_NAME or (allow_auto and name == AUTO)


def normalize_language_name(name):
    """Geminiが返した言語名などを、対応言語の正式名に寄せる。見つからなければ None"""
    if not name:
        return None
    key = str(name).strip().lower()
    if key in _BY_LOWER:
        return _BY_LOWER[key]
    if key == "chinese":
        return "Chinese (Simplified)"
    for lower, canonical in _BY_LOWER.items():  # "Chinese (Mandarin)" のような揺れ
        if key.split(" (")[0] == lower.split(" (")[0]:
            return canonical
    return None


def get_lang_code(name):
    if name == AUTO:
        return ""
    return _BY_NAME.get(name, _BY_NAME["English"])["code"]


def get_native_name(name):
    return _BY_NAME.get(name, {}).get("native", name)


def is_rtl(name):
    return bool(_BY_NAME.get(name, {}).get("rtl"))


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
        'auto_detect': '自動判定',
        'search_lang': '言語を検索',
        'recent_langs': '最近使った言語',
        'no_results': '見つかりません',
        'nav_history': '履歴',
        'history_empty': 'まだ履歴がありません',
        'filter_all': 'すべて',
        'filter_fav': 'お気に入り',
        'clear_history': '履歴を消去',
        'confirm_clear': 'お気に入り以外の履歴をすべて消しますか？',
        'err_tts': 'この端末では読み上げできません。',
        'nav_conversation': 'チャット',
        'conv_hint': 'スマホを渡し合って、それぞれの言語で入力してください',
        'conv_person_a': '話者A',
        'conv_person_b': '話者B',
        'conv_type_placeholder': '文字で入力...',
        'conv_auto_speak': '翻訳を自動で読み上げる',
        'conv_clear': '会話をクリア',
        'conv_empty': '話しかけると、ここに会話が表示されます',
        'history_note': '履歴はこの端末内にのみ保存されます',
        'speak': '読み上げ',
        'favorite': 'お気に入り',
        'reuse': '再利用',
        'delete': '削除',
        'err_network': '通信エラーが発生しました。',
        'change_language': '言語・設定',
        'chat_input_placeholder': 'メッセージを入力...',
        'chat_auto_switch': '送信後に話者を自動で交代',
        'chat_next': '次は',
        'edit_translation': '訳を修正',
        'edit_prompt': '訳を修正してください（今後の翻訳に反映されます）',
        'explain': 'スラング・意味を解説',
        'explaining': '解説中...',
        'filter_glossary': '用語集',
        'glossary_hint': 'スラングや略語を登録すると、次回から指定どおりに訳されます。訳の修正も自動で保存されます。',
        'glossary_term': '語句（原文）',
        'glossary_meaning': '訳したい表現',
        'glossary_target': '翻訳先',
        'glossary_add': '追加',
        'glossary_empty': '登録された用語はありません',
        'glossary_kind_term': '用語',
        'glossary_kind_example': '修正例',
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
        'auto_detect': 'Auto-detect',
        'search_lang': 'Search languages',
        'recent_langs': 'Recent',
        'no_results': 'No results',
        'nav_history': 'History',
        'history_empty': 'No history yet',
        'filter_all': 'All',
        'filter_fav': 'Favorites',
        'clear_history': 'Clear history',
        'confirm_clear': 'Delete all history except favorites?',
        'err_tts': 'Speech playback is not available on this device.',
        'nav_conversation': 'Chat',
        'conv_hint': 'Pass the phone back and forth and type in your own language.',
        'conv_person_a': 'Person A',
        'conv_person_b': 'Person B',
        'conv_type_placeholder': 'Type instead...',
        'conv_auto_speak': 'Read translations aloud',
        'conv_clear': 'Clear conversation',
        'conv_empty': 'The conversation will appear here',
        'history_note': 'History is saved on this device only',
        'speak': 'Listen',
        'favorite': 'Favorite',
        'reuse': 'Reuse',
        'delete': 'Delete',
        'err_network': 'Network error. Please try again.',
        'change_language': 'Language & settings',
        'chat_input_placeholder': 'Type a message...',
        'chat_auto_switch': 'Switch speaker after sending',
        'chat_next': 'Next',
        'edit_translation': 'Edit translation',
        'edit_prompt': 'Edit the translation (it will be used to improve future translations)',
        'explain': 'Explain slang & meaning',
        'explaining': 'Explaining...',
        'filter_glossary': 'Glossary',
        'glossary_hint': 'Add slang or abbreviations and they will be translated the way you specify. Your corrections are saved automatically.',
        'glossary_term': 'Word or phrase (original)',
        'glossary_meaning': 'How it should be translated',
        'glossary_target': 'Translate into',
        'glossary_add': 'Add',
        'glossary_empty': 'No glossary entries yet',
        'glossary_kind_term': 'Term',
        'glossary_kind_example': 'Correction',
    },
}


# どの表示言語でも固定する文言
FIXED_LABELS = {
    'source_label': 'From',
    'target_label': 'To',
    'target_label_short': 'To',
}


def get_ui_labels(lang):
    """指定言語のUIラベル。足りないキーは English で補完する"""
    labels = dict(UI_LABELS['English'])
    labels.update(UI_LABELS.get(lang, {}))
    labels.update(FIXED_LABELS)
    return labels
