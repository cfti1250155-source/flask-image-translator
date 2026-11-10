"""全言語の画面文言を事前生成して ui_labels/ に保存するスクリプト。

使い方（プロジェクトのルートで）:
    export GEMINI_API_KEY=...        # Windowsは set GEMINI_API_KEY=...
    pip install -r requirements.txt
    python tools/generate_ui_labels.py            # 未生成の言語だけ作る
    python tools/generate_ui_labels.py --force    # 全言語を作り直す

生成した ui_labels/*.json をコミットしておけば、デプロイ後に初回の待ち時間が出ません。
母語話者に確認してもらうと品質が上がります（JSONを直接編集して構いません）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui_i18n  # noqa: E402
from languages import LANGUAGES, UI_LABELS  # noqa: E402


def main():
    force = "--force" in sys.argv
    ok = failed = skipped = 0
    for lang in LANGUAGES:
        name = lang["name"]
        if name in UI_LABELS:
            continue
        if force:
            ui_i18n._mem.pop(name, None)
            try:
                os.remove(ui_i18n._path(name))
            except OSError:
                pass
        elif ui_i18n.has_labels(name):
            skipped += 1
            print(f"skip   {name}")
            continue
        print(f"make   {name} ...", end=" ", flush=True)
        if ui_i18n.ensure_ui_labels(name):
            ok += 1
            print("ok")
        else:
            failed += 1
            print("FAILED")
    print(f"done: {ok} generated, {skipped} skipped, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
