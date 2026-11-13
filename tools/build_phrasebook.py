"""tools/phrasebook_data.py → static/phrasebook/ に書き出す。
  python tools/build_phrasebook.py
index.json = カテゴリと日本語/英語の文、<言語コード小文字>.json = その言語の訳。
Gemini で作った他言語のファイル（generate_phrasebook.py）は消さずに残す。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from phrasebook_data import CATEGORIES, T  # noqa: E402

OUT = os.path.join(ROOT, "static", "phrasebook")


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    dump(os.path.join(OUT, "index.json"), [
        {"id": cid, "ja": ja, "en": en, "phrases": [{"id": p[0], "ja": p[1], "en": p[2]} for p in ph]}
        for cid, ja, en, ph in CATEGORIES])
    for code, d in T.items():
        dump(os.path.join(OUT, code.lower() + ".json"), d)
    print(f"wrote index.json + {len(T)} languages -> {OUT}")


if __name__ == "__main__":
    main()
