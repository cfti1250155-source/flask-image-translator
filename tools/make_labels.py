import json
import os
import sys
import time

# プロジェクトルート（translation-main）を取得してパスに追加
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from deep_translator import GoogleTranslator
from languages import LANGUAGES, UI_LABELS, get_lang_code

LABEL_DIR = os.path.join(BASE_DIR, 'ui_labels')
os.makedirs(LABEL_DIR, exist_ok=True)

# 基準データ（languages.py 内の英語ラベル）
base_labels = UI_LABELS.get("English", {})

if not base_labels:
    print("エラー: languages.UI_LABELS['English'] が見つかりません。")
    sys.exit(1)

print(f"ベースデータ（Englishラベル {len(base_labels)} 件）を取得しました。処理を開始します...")

for lang_info in LANGUAGES:
    lang_name = lang_info["name"]

    # 英語と日本語は languages.py 内に直書きされているため JSON 生成をスキップ
    if lang_name in ["English", "Japanese"]:
        continue

    code = get_lang_code(lang_name).lower()
    out_path = os.path.join(LABEL_DIR, f"{code}.json")

    if os.path.exists(out_path):
        print(f"スキップ: {code}.json は既に存在します")
        continue

    print(f"生成中: {lang_name} ({code})...")
    target_code = code.split('-')[0]
    translator = GoogleTranslator(source='en', target=target_code)

    keys = list(base_labels.keys())
    values = [base_labels[k] for k in keys]

    try:
        # 一括翻訳（1回のリクエストにまとめてレート制限を回避）
        translated_values = translator.translate_batch(values)
        translated = dict(zip(keys, translated_values))
    except Exception as e:
        print(f"  - 一括翻訳失敗、個別フォールバックを実行: {e}")
        translated = {}
        for k, v in base_labels.items():
            if isinstance(v, str) and v.strip():
                try:
                    translated[k] = translator.translate(v)
                    time.sleep(0.3)  # レート制限回避用の安全ウェイト
                except Exception as err:
                    print(f"  - 翻訳スキップ [{k}]: {err}")
                    translated[k] = v
            else:
                translated[k] = v

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(translated, f, ensure_ascii=False, indent=2)

    print(f"完了: {out_path}")
    time.sleep(1.0)  # 次の言語に移る前の安全待機

print("\n全言語の UI Label 生成処理が完了しました！")