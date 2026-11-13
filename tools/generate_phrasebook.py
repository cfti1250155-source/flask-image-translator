"""手書きデータが無い言語のフレーズ集を Gemini で作る（任意）。
使い方（プロジェクトのルートで）:
    export GEMINI_API_KEY=...
    python tools/generate_phrasebook.py             # 未作成の言語だけ
    python tools/generate_phrasebook.py Swahili     # 指定した言語だけ（作り直し）
作った JSON は static/phrasebook/ に保存されます。コミットして使ってください。
機械翻訳なので、ネイティブの方に確認してもらうと安心です（JSONを直接直して構いません）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import translator  # noqa: E402
from languages import LANGUAGES  # noqa: E402
from phrasebook_data import CATEGORIES  # noqa: E402

OUT = os.path.join(ROOT, "static", "phrasebook")
SYSTEM = ("You are a professional translator for a travel phrasebook. Respond ONLY with a JSON object that has "
          "exactly the same keys as the input, with every value translated naturally and politely, the way a "
          "native speaker would say it to a stranger.")


def make(lang):
    src = {p[0]: p[2] for c in CATEGORIES for p in c[3]}
    prompt = (f"Translate every value of this JSON object from English into {lang['name']}. Keep the keys. "
              "Keep each phrase short and natural.\n" + json.dumps(src, ensure_ascii=False))
    data = translator._loads_object(translator._call([prompt], system=SYSTEM)) or {}
    out = {k: str(data[k]).strip() for k in src if isinstance(data.get(k), str) and str(data[k]).strip()}
    if len(out) != len(src):
        raise RuntimeError(f"incomplete: {len(out)}/{len(src)}")
    path = os.path.join(OUT, lang["code"].lower() + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main():
    only = set(sys.argv[1:])
    os.makedirs(OUT, exist_ok=True)
    failed = 0
    for lang in LANGUAGES:
        exists = os.path.exists(os.path.join(OUT, lang["code"].lower() + ".json"))
        if (only and lang["name"] not in only) or (not only and exists):
            continue
        print(f"make {lang['name']} ...", end=" ", flush=True)
        try:
            make(lang)
            print("ok")
        except Exception as e:
            failed += 1
            print("FAILED", e)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
