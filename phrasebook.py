"""オフライン用フレーズ集: static/phrasebook/ にデータがある言語の一覧"""
import os

from languages import LANGUAGES

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "phrasebook")


def available_languages():
    """データ(JSON)がある対応言語の英語名リスト（LANGUAGES の並び順）"""
    try:
        files = set(os.listdir(DIR))
    except OSError:
        return []
    return [l["name"] for l in LANGUAGES if l["code"].lower() + ".json" in files]
