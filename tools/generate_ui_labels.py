import os
import sys
import time  # ★ 追加

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui_i18n
from languages import LANGUAGES, UI_LABELS


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

        time.sleep(1.5)  # ★ ここに待機時間を追加（1.5秒）

    print(f"done: {ok} generated, {skipped} skipped, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()