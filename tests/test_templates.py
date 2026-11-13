"""テンプレートが途中で切れていない・タグが閉じているかの確認。
（ファイルの一部が欠けると <div> が閉じず、画面全体が崩れるため）"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = glob.glob(os.path.join(ROOT, "templates", "**", "*.html"), recursive=True)


def test_div_tags_are_balanced():
    for f in TEMPLATES:
        s = open(f, encoding="utf-8").read()
        assert len(re.findall(r"<div\b", s)) == len(re.findall(r"</div>", s)), os.path.relpath(f, ROOT)


def test_files_are_not_cut_off():
    for f in TEMPLATES:
        s = open(f, encoding="utf-8").read().rstrip()
        assert s.endswith((">", "}}", "%}")), f"{os.path.relpath(f, ROOT)} ends with: {s[-40:]!r}"
        assert s.count("<") == s.count(">") or "<script" in s or "{{" in s, os.path.relpath(f, ROOT)


def test_header_has_both_language_buttons():
    s = open(os.path.join(ROOT, "templates", "components", "header.html"), encoding="utf-8").read()
    assert "target_display" in s and s.rstrip().endswith("</div>")
