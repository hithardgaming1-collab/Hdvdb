#!/usr/bin/env python3
"""
Word-level accuracy test for Hiragana Stories.

What it checks
  1. READING   every story line is also written in normal kanji+kana (tests/reference.py). Three independent
               Japanese analyzers (Sudachi, Janome/IPADIC, pykakasi) read that line; the app's hiragana must
               equal the reading of at least two of them. Three words where analyzers use an unusual default
               (七時 しちじ, 四人 よにん, 蛙 かえる, 宝物 たからもの, お腹が空く おなかがすく) are settled by the JMdict dictionary.
  2. SPACING   spaces fall only between words, never inside one, never before a particle/ending, and never
               missing after a particle.
  3. DICTIONARY every word is looked up in JMdict: kanji, reading and English meaning must agree; common-word flag.
  4. MEANING   every word in the Japanese line has its English counterpart in the English line, and every concrete
               noun in the English line exists in the Japanese line; past/present tense, quotes and ! agree.
  5. COVERAGE  no word in any line escapes checks 3 and 4.
  6. LABELS    the app's Japanese button labels are checked the same way; English text spelling is checked.

Needs:  pip install sudachipy sudachidict_core janome pykakasi simplemma jamdict jamdict-data pyspellchecker
Run from the project folder:   python3 tests/check_words.py [--jlpt n5.csv n4.csv]
"""
import csv
import difflib
import re
import sys
import unicodedata as ud
import warnings

warnings.filterwarnings("ignore")

from common import load_stories, read
from reference import PAGES, TITLES
from sudachipy import dictionary, tokenizer
from janome.tokenizer import Tokenizer as Janome
import pykakasi
import simplemma
from jamdict import Jamdict

try:
    from spellchecker import SpellChecker
except ImportError:  # optional
    SpellChecker = None

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(("PASS  " if ok else "FAIL  ") + name)
    if detail and not ok:
        print("        " + str(detail).replace("\n", "\n        "))


def info(text):
    print("      . " + text)


# ----------------------------------------------------------------------------- text helpers
def hira(s):
    return "".join(chr(ord(c) - 0x60) if "\u30A1" <= c <= "\u30F6" else c for c in s)


def norm(s):
    """Reading comparison form: hiragana only, no spaces or punctuation."""
    return re.sub(r"[ 、。！？「」!?,.]", "", hira(ud.normalize("NFC", s)))


OVERRIDES = {"七時": "しちじ", "四人": "よにん", "蛙": "かえる", "宝物": "たからもの",
             "お腹が空い": "おなかがすい"}  # analyzer defaults differ; each is verified against JMdict below


def apply_overrides(text):
    for k, v in OVERRIDES.items():
        text = text.replace(k, v)
    return text


# ----------------------------------------------------------------------------- engines
_sud = dictionary.Dictionary(dict="core")
SUD = _sud.tokenizer() if hasattr(_sud, "tokenizer") else _sud.create()
MODE = tokenizer.Tokenizer.SplitMode.C
JAN = Janome()
KKS = pykakasi.kakasi()
JAM = Jamdict()


class _O:  # tiny picklable stand-in for a JMdict record (used only for the optional lookup cache)
    def __init__(self, **kw):
        self.__dict__.update(kw)


class CachedJam:
    """Optional speed-up for repeated runs: set the environment variable JM_CACHE to a file name."""

    def __init__(self, jam, path):
        import os, pickle
        self.jam, self.path, self.cache = jam, path, {}
        if os.path.exists(path):
            self.cache = pickle.load(open(path, "rb"))

    def lookup(self, q):
        if q not in self.cache:
            ents = [_O(kana_forms=[_O(text=k.text, pri=list(k.pri)) for k in e.kana_forms],
                       kanji_forms=[_O(text=k.text, pri=list(k.pri)) for k in e.kanji_forms],
                       senses=[_O(gloss=[_O(text=g.text) for g in sn.gloss]) for sn in e.senses])
                    for e in self.jam.lookup(q).entries]
            self.cache[q] = _O(entries=ents)
        return self.cache[q]

    def save(self):
        import pickle
        pickle.dump(self.cache, open(self.path, "wb"))


import os as _os
if _os.environ.get("JM_CACHE"):
    JAM = CachedJam(JAM, _os.environ["JM_CACHE"])
    import atexit
    atexit.register(JAM.save)


def sudachi_tokens(text, mode=MODE):
    out = []
    for m in SUD.tokenize(text, mode):
        pos = m.part_of_speech()
        rd = m.surface() if pos[0] == "補助記号" else hira(m.reading_form())
        out.append({"surf": m.surface(), "rd": rd, "pos": pos})
    return out


def read_sudachi(t):
    return norm("".join(x["rd"] for x in sudachi_tokens(t)))


def read_janome(t):
    return norm("".join(x.surface if x.reading == "*" else x.reading for x in JAN.tokenize(t)))


def read_pykakasi(t):
    return norm("".join(x["hira"] for x in KKS.convert(t)))


ENGINES = [("Sudachi", read_sudachi), ("Janome", read_janome), ("pykakasi", read_pykakasi)]

# ----------------------------------------------------------------------------- data under test
stories = load_stories()
LINES = []  # (label, my hiragana, reference orthography, my english)
for s in stories:
    LINES.append((f'{s["title"]} (title)', s["title"], TITLES[s["id"]], s["title_en"]))
    for i, (jp, en) in enumerate(s["pages"]):
        LINES.append((f'{s["title"]} p{i + 1}', jp, PAGES[s["id"]][i], en))
check("reference spelling exists for every title and page",
      all(len(PAGES[s["id"]]) == len(s["pages"]) for s in stories) and set(TITLES) == {s["id"] for s in stories})

# ============================================================================= 1. READING
print("\n-- 1. reading: 3 analyzers vs the app's hiragana")
engine_hits = {n: 0 for n, _ in ENGINES}
weak, notes = [], []
for label, mine, ref, _ in LINES:
    want = norm(mine)
    ref2 = apply_overrides(ref)
    votes = 0
    for name, fn in ENGINES:
        got = fn(ref2)
        if got == want:
            engine_hits[name] += 1
            votes += 1
        else:
            sm = difflib.SequenceMatcher(None, want, got)
            d = [f"{want[a:b] or '∅'}→{got[c:d_] or '∅'}" for tag, a, b, c, d_ in sm.get_opcodes() if tag != "equal"]
            notes.append(f"{label}: {name} reads {', '.join(d)}")
    if votes < 2:
        weak.append((label, votes))
for name, _ in ENGINES:
    info(f"{name}: {engine_hits[name]}/{len(LINES)} lines identical to the app's hiragana")
check(f"every one of the {len(LINES)} titles/lines is confirmed by at least 2 of 3 analyzers", not weak, weak)
for n in notes:
    info("analyzer quirk, outvoted: " + n)

# ============================================================================= 2. SPACING
print("\n-- 2. spacing (word breaks)")
MODE_A = tokenizer.Tokenizer.SplitMode.A


def patch_reading(toks):
    """Apply the JMdict-verified readings (see OVERRIDES) to analyzer tokens."""
    for k, t in enumerate(toks):
        nxt = toks[k + 1]["surf"] if k + 1 < len(toks) else ""
        if t["surf"] == "七" and nxt == "時":
            t["rd"] = "しち"
        elif t["surf"] == "四" and nxt == "人":
            t["rd"] = "よ"
        elif t["surf"] == "蛙":
            t["rd"] = "かえる"
        elif t["surf"] == "宝物":
            t["rd"] = "たからもの"
        elif t["surf"] == "空い" and k > 0 and toks[k - 1]["surf"] == "が":
            t["rd"] = "すい"
    return toks


def align(ref, mine):
    """Match the analyzer's tokens to the app's text. Returns (tokens with a 'space' flag, error)."""
    queue = patch_reading(sudachi_tokens(ref))
    i, out = 0, []
    while queue:
        t = queue.pop(0)
        sp, j = False, i
        while j < len(mine) and mine[j] == " ":
            sp, j = True, j + 1
        if mine[j:j + len(t["rd"])] != t["rd"]:
            parts = [] if t.get("split") else sudachi_tokens(t["surf"], MODE_A)
            if len(parts) > 1:                          # a long fixed phrase such as 犬と猿: look at its parts
                for x in parts:
                    x["split"] = True
                queue = patch_reading(parts) + queue
                continue
            return None, (t["surf"], t["rd"], mine[j:j + len(t["rd"]) + 2])
        out.append({**t, "space": sp})
        i = j + len(t["rd"])
    return out, None


_jm_cache = {}


def in_jmdict(word):
    if word not in _jm_cache:
        _jm_cache[word] = any(word in [k.text for k in e.kanji_forms] + [k.text for k in e.kana_forms]
                              for e in JAM.lookup(word).entries)
    return _jm_cache[word]


NOUNISH = ("名詞", "代名詞")
space_problems, join_problems, misaligned, joins = [], [], [], set()
for label, mine, ref, _ in LINES:
    aligned, err = align(ref, mine)
    if err:
        misaligned.append((label,) + err)
        continue
    for k, t in enumerate(aligned):
        p0, p1 = t["pos"][0], t["pos"][1]
        prev = aligned[k - 1] if k else None
        if t["space"]:
            if p0 in ("助詞", "助動詞", "接尾辞") or (p0 == "補助記号" and t["surf"] != "「"):
                space_problems.append((label, "space before particle/ending/closing mark", t["surf"]))
            if prev is not None and prev["pos"][0] in NOUNISH and p0 in NOUNISH and in_jmdict(prev["surf"] + t["surf"]):
                space_problems.append((label, "space inside one dictionary word", prev["surf"] + t["surf"]))
        elif prev is not None:
            pp0, pp1 = prev["pos"][0], prev["pos"][1]
            if pp0 == "助詞" and pp1 != "接続助詞" and p0 not in ("助詞", "助動詞", "接尾辞", "補助記号"):
                space_problems.append((label, "missing space after particle", prev["surf"] + "|" + t["surf"]))
            if pp0 == "助動詞" and p0 not in ("助詞", "助動詞", "接尾辞", "補助記号"):
                space_problems.append((label, "missing space after ending", prev["surf"] + "|" + t["surf"]))
            if pp0 in NOUNISH and p0 in NOUNISH and prev["surf"] != "お" and t["surf"] != "お":
                joined = prev["surf"] + t["surf"]
                joins.add(joined)
                if not (pp1 == "数詞" or "固有名詞" in (pp1, p1) or in_jmdict(joined)):
                    join_problems.append((label, joined))
check("every token of every line lines up with the app's text (no space inside a word, no stray letters)",
      not misaligned, misaligned[:5])
check("spaces only between words: none before a particle/ending or inside a dictionary word, none missing after a particle",
      not space_problems, space_problems[:8])
check("words written together without a space are real dictionary words, names, or number+counter (六時, 三時間)",
      not join_problems, join_problems[:8])
info(f"{len(joins)} unspaced joins checked: " + ", ".join(sorted(joins)))

# ============================================================================= 3. DICTIONARY
print("\n-- 3. dictionary (JMdict)")
COMMON = {"ichi1", "news1", "spec1", "spec2", "gai1"}


def jm_find(query, kana, gloss_kw):
    for e in JAM.lookup(query).entries:
        kana_forms = {k.text: k for k in e.kana_forms}
        if kana not in kana_forms:
            continue
        glosses = [g.text.lower() for s in e.senses for g in s.gloss]
        if any(kw in g for kw in gloss_kw for g in glosses):
            pri = set(kana_forms[kana].pri) | {p for k in e.kanji_forms for p in k.pri}
            return {"glosses": glosses, "common": bool(pri & COMMON), "pri": sorted(pri)}
    return None


# key in the reference line, JMdict headword, reading, JMdict gloss keywords, English keywords ('*' = prefix), concrete noun?
W = [
    ("わたし", "私", "わたし", ["i", "me"], ["i", "my", "me"], False),
    ("名前", "名前", "なまえ", ["name"], ["name"], True),
    ("毎朝", "毎朝", "まいあさ", ["every morning"], ["every morning"], False),
    ("毎日", "毎日", "まいにち", ["every day", "everyday", "daily"], ["every day"], False),
    ("六時", "六時", "ろくじ", ["six o'clock"], ["six o'clock", "six"], False),
    ("七時", "七時", "しちじ", ["seven o'clock"], ["seven o'clock"], False),
    ("朝ご飯", "朝ご飯", "あさごはん", ["breakfast"], ["breakfast"], True),
    ("晩ご飯", "晩ご飯", "ばんごはん", ["dinner", "evening meal"], ["dinner"], True),
    ("お茶", "お茶", "おちゃ", ["tea"], ["tea"], True),
    ("歯", "歯", "は", ["tooth"], ["tooth", "teeth"], True),
    ("うち", "家", "うち", ["house", "home"], ["house", "~home"], True),   # "~" = forward check only
    ("学校", "学校", "がっこう", ["school"], ["school"], True),
    ("お母さん", "お母さん", "おかあさん", ["mother"], ["mother"], True),
    ("お父さん", "お父さん", "おとうさん", ["father"], ["father"], True),
    ("妹", "妹", "いもうと", ["younger sister", "little sister"], ["little sister", "younger sister", "sister"], True),
    ("先生", "先生", "せんせい", ["teacher"], ["teacher"], True),
    ("猫", "猫", "ねこ", ["cat"], ["cat"], True),
    ("魚", "魚", "さかな", ["fish"], ["fish"], True),
    ("夜", "夜", "よる", ["night"], ["night"], True),
    ("そば", "そば", "そば", ["near", "beside", "side", "vicinity"], ["next to", "near", "beside"], False),
    ("今日", "今日", "きょう", ["today"], ["today"], True),
    ("日曜日", "日曜日", "にちようび", ["sunday"], ["sunday"], True),
    ("天気", "天気", "てんき", ["weather"], ["weather"], True),
    ("犬", "犬", "いぬ", ["dog"], ["dog"], True),
    ("公園", "公園", "こうえん", ["park"], ["park"], True),
    ("木", "木", "き", ["tree"], ["tree"], True),
    ("亀", "亀", "かめ", ["tortoise", "turtle"], ["tortoise", "turtle"], True),
    ("うさぎ", "兎", "うさぎ", ["rabbit", "hare"], ["hare", "rabbit"], True),
    ("蛙", "蛙", "かえる", ["frog"], ["frog"], True),
    ("雨", "雨", "あめ", ["rain"], ["rain", "rainy"], True),
    ("傘", "傘", "かさ", ["umbrella"], ["umbrella"], True),
    ("道", "道", "みち", ["road", "path", "way", "street"], ["road", "path", "way"], True),
    ("音", "音", "おと", ["sound", "noise"], ["sound", "noise"], True),
    ("家族", "家族", "かぞく", ["family"], ["family"], True),
    ("朝", "朝", "あさ", ["morning"], ["morning"], False),
    ("日", "日", "ひ", ["day"], ["day"], False),
    ("四人", "四人", "よにん", ["four people"], ["four"], False),
    ("五歳", None, None, None, ["five"], False),
    ("午後", "午後", "ごご", ["afternoon", "p.m."], ["evening", "afternoon", "p.m."], False),
    ("料理", "料理", "りょうり", ["cooking", "cuisine"], ["cooking", "cook"], False),
    ("みんな", "皆", "みんな", ["everyone", "all"], ["all", "everyone"], False),
    ("一緒", "一緒", "いっしょ", ["together"], ["together"], False),
    ("かけっこをしましょう", "駆けっこ", "かけっこ", ["race"], ["race"], False),
    ("昔々", "昔々", "むかしむかし", ["long ago", "once upon a time"], ["long ago", "once upon a time"], False),
    ("とても", "とても", "とても", ["very"], ["very", "so", "a lot", "really"], False),
    ("少し", "少し", "すこし", ["little", "few"], ["a little", "a bit"], False),
    ("ずっと", "ずっと", "ずっと", ["continuous", "all along", "whole time", "all the way"],
     ["kept on", "kept", "continu*", "whole time", "all the time"], False),
    ("ゆっくり", "ゆっくり", "ゆっくり", ["slowly"], ["slowly"], False),
    ("びっくりしました", "びっくり", "びっくり", ["surprised"], ["surprised"], False),
    ("それから", "それから", "それから", ["then", "after that"], ["then", "after that"], False),
    ("起き", "起きる", "おきる", ["get up", "wake up", "rise"], ["get up", "wake up"], False),
    ("食べ", "食べる", "たべる", ["eat"], ["eat"], False),
    ("飲み", "飲む", "のむ", ["drink"], ["drink"], False),
    ("磨き", "磨く", "みがく", ["brush", "polish"], ["brush"], False),
    ("出かけ", "出かける", "でかける", ["go out", "leave", "set out"], ["go out"], False),
    ("出ます", "出る", "でる", ["leave", "exit", "go out"], ["leave"], False),
    ("行きます", "行く", "いく", ["to go"], ["go"], False),
    ("行ってきます", "行ってきます", "いってきます", ["i'm off", "see you later"], ["off"], False),
    ("行ってらっしゃい", "行ってらっしゃい", "いってらっしゃい", ["have a good day", "take care", "see you"],
     ["good day", "take care", "see you"], False),
    ("言い", "言う", "いう", ["to say"], ["say", "said"], False),
    ("寝", "寝る", "ねる", ["sleep", "go to bed"], ["sleep", "slept"], False),
    ("遊び", "遊ぶ", "あそぶ", ["to play"], ["play"], False),
    ("走り", "走る", "はしる", ["to run"], ["run", "ran"], False),
    ("歩き", "歩く", "あるく", ["to walk"], ["walk"], False),
    ("勝ち", "勝つ", "かつ", ["to win"], ["win", "won"], False),
    ("持って", "持つ", "もつ", ["to hold", "to carry", "to have", "to take"], ["take", "carry", "hold"], False),
    ("がいます", "居る", "いる", ["to be", "to exist"], ["there is", "there are"], False),
    ("がいました", "居る", "いる", ["to be", "to exist"], ["there lived", "there was", "there were"], False),
    ("があります", "有る", "ある", ["to be", "to exist", "to have"], ["there is", "there are"], False),
    ("白い", "白い", "しろい", ["white"], ["white"], False),
    ("小さい", "小さい", "ちいさい", ["small", "little"], ["small"], False),
    ("大きい", "大きい", "おおきい", ["big", "large"], ["big", "large"], False),
    ("速い", "速い", "はやい", ["fast", "quick"], ["fast"], False),
    ("遅い", "遅い", "おそい", ["slow"], ["slow"], False),
    ("楽しい", "楽しい", "たのしい", ["fun", "enjoyable"], ["fun", "enjoy*"], False),
    ("可愛い", "可愛い", "かわいい", ["cute", "adorable"], ["cute"], False),
    ("いい", "いい", "いい", ["good", "nice"], ["nice", "good"], False),
    ("大好き", "大好き", "だいすき", ["love", "like very much"], ["love", "like very much"], False),
    ("好き", "好き", "すき", ["lik", "fond", "love"], ["like"], False),
    ("嬉しく", "嬉しい", "うれしい", ["happy", "glad", "pleased"], ["happy"], False),
    ("なりました", "成る", "なる", ["to become"], ["became", "become", "grew"], False),
    ("元気", "元気", "げんき", ["lively", "energetic", "healthy"], ["lively", "energy", "energetic"], False),
    ("素敵", "素敵", "すてき", ["lovely", "wonderful", "nice"], ["lovely", "wonderful", "nice"], False),
    ("上手", "上手", "じょうず", ["skillful", "skilled", "good (at)"], ["good at", "skilled", "skillful"], False),
    # ---- zoo
    ("動物園", "動物園", "どうぶつえん", ["zoo"], ["zoo"], True),
    ("動物", "動物", "どうぶつ", ["animal"], ["animal"], True),
    ("いろいろ", "色々", "いろいろ", ["various", "variety"], ["many kinds", "various", "many"], False),
    ("初めに", "初め", "はじめ", ["beginning", "first"], ["first"], False),
    ("象", "象", "ぞう", ["elephant"], ["elephant"], True),
    ("長い", "長い", "ながい", ["long"], ["long"], False),
    ("長かった", "長い", "ながい", ["long"], ["long"], False),
    ("鼻", "鼻", "はな", ["nose", "trunk"], ["trunk", "nose"], True),
    ("水", "水", "みず", ["water"], ["water"], True),
    ("次に", "次", "つぎ", ["next"], ["next"], False),
    ("猿", "猿", "さる", ["monkey"], ["monkey"], True),
    ("登っていました", "登る", "のぼる", ["climb"], ["climbing", "climb*"], False),
    ("キリン", "麒麟", "きりん", ["giraffe"], ["giraffe"], True),
    ("首", "首", "くび", ["neck"], ["neck"], True),
    ("昼ご飯", "昼ご飯", "ひるごはん", ["lunch"], ["lunch"], True),
    ("お弁当", "お弁当", "おべんとう", ["bento", "lunch"], ["bento"], True),
    ("美味しい", "美味しい", "おいしい", ["delicious", "tasty"], ["delicious", "tasty"], False),
    ("美味しかった", "美味しい", "おいしい", ["delicious", "tasty"], ["delicious", "tasty"], False),
    ("そのあと", "其の後", "そのあと", ["after that", "afterwards"], ["after that"], False),
    ("熊", "熊", "くま", ["bear"], ["bear"], True),
    ("寝ていました", "寝る", "ねる", ["sleep", "go to bed"], ["sleeping", "asleep", "sleep"], False),
    ("最後に", "最後", "さいご", ["last", "final", "end"], ["finally", "last"], False),
    ("たくさん", "沢山", "たくさん", ["many", "a lot", "much"], ["many", "a lot"], False),
    ("泳いでいました", "泳ぐ", "およぐ", ["swim"], ["swimming", "swim"], False),
    ("夕方", "夕方", "ゆうがた", ["evening"], ["evening"], False),
    ("帰りました", "帰る", "かえる", ["return", "go home", "go back"], ["home", "return", "back"], False),
    ("帰って", "帰る", "かえる", ["return", "go home", "go back"], ["home", "return", "back"], False),
    ("疲れました", "疲れる", "つかれる", ["tired"], ["tired"], False),
    ("楽しかった", "楽しい", "たのしい", ["fun", "enjoyable"], ["fun", "enjoy*"], False),
    ("また", "又", "また", ["again"], ["again"], False),
    ("行きたいです", "行く", "いく", ["to go"], ["want to go", "want"], False),
    ("行きました", "行く", "いく", ["to go"], ["went", "go"], False),
    ("見ました", "見る", "みる", ["to see", "to watch", "to look"], ["saw", "see", "watch*"], False),
    ("大きかった", "大きい", "おおきい", ["big", "large"], ["big", "large"], False),
    ("大きく", "大きい", "おおきい", ["big", "large"], ["big", "large", "grew"], False),
    # ---- summer vacation
    ("夏休み", "夏休み", "なつやすみ", ["summer vacation", "summer holiday"], ["summer vacation", "vacation", "holiday"], False),
    ("海", "海", "うみ", ["sea", "ocean"], ["sea", "ocean"], True),
    ("車", "車", "くるま", ["car"], ["car"], True),
    ("三時間", None, None, None, ["three hours"], False),
    ("かかりました", "掛かる", "かかる", ["to take", "to cost"], ["took", "take"], False),
    ("きれい", "綺麗", "きれい", ["beautiful", "pretty", "clean"], ["beautiful", "pretty", "clean"], False),
    ("泳ぎました", "泳ぐ", "およぐ", ["swim"], ["swam", "swim"], False),
    ("冷たかった", "冷たい", "つめたい", ["cold"], ["cold"], False),
    ("弟", "弟", "おとうと", ["younger brother", "little brother"], ["younger brother", "little brother", "brother"], True),
    ("砂", "砂", "すな", ["sand"], ["sand"], True),
    ("お城", "城", "しろ", ["castle"], ["castle"], True),   # お + 城
    ("作りました", "作る", "つくる", ["to make"], ["made", "make"], False),
    ("西瓜", "西瓜", "すいか", ["watermelon"], ["watermelon"], True),
    ("切りました", "切る", "きる", ["to cut"], ["cut"], False),
    ("甘くて", "甘い", "あまい", ["sweet"], ["sweet"], False),
    ("花火", "花火", "はなび", ["fireworks"], ["fireworks"], True),
    ("音がしました", "音", "おと", ["sound", "noise"], ["noise", "sound"], False),
    ("来年", "来年", "らいねん", ["next year"], ["next year"], False),
    # ---- snowy day
    ("窓", "窓", "まど", ["window"], ["window"], True),
    ("開けました", "開ける", "あける", ["to open"], ["opened", "open"], False),
    ("外", "外", "そと", ["outside"], ["outside"], True),
    ("真っ白", "真っ白", "まっしろ", ["pure white", "snow-white"], ["white"], False),
    ("雪だるま", "雪だるま", "ゆきだるま", ["snowman"], ["snowman"], True),
    ("雪", "雪", "ゆき", ["snow"], ["snow", "snowy", "snowing"], True),
    ("降っていました", "降る", "ふる", ["to fall", "to rain", "to snow"], ["falling", "fall", "fell", "snowing"], False),
    ("手袋をして", "手袋", "てぶくろ", ["glove"], ["glove", "gloves"], True),
    ("手袋", "手袋", "てぶくろ", ["glove"], ["glove", "gloves"], True),
    ("出ました", "出る", "でる", ["to leave", "to go out", "to exit"], ["went out", "went", "left"], False),
    ("寒かった", "寒い", "さむい", ["cold"], ["cold"], False),
    ("友達", "友達", "ともだち", ["friend"], ["friend"], True),
    ("来ました", "来る", "くる", ["to come"], ["came", "come"], False),
    ("出来ました", "出来る", "できる", ["to be able", "to be made", "to be completed", "to be finished"], ["made", "finished", "completed", "done"], False),
    ("付けました", "付ける", "つける", ["to attach", "to put on", "to affix"], ["put on", "put", "attach*"], False),
    ("顔をしていました", "顔", "かお", ["face"], ["face"], False),
    ("顔をしました", "顔", "かお", ["face"], ["face"], False),
    ("暖かい", "暖かい", "あたたかい", ["warm"], ["warm"], False),
    # ---- the ant and the grasshopper
    ("夏", "夏", "なつ", ["summer"], ["summer"], False),
    ("ある日", "或る日", "あるひ", ["one day", "a certain day"], ["one day"], False),
    ("歌っていました", "歌う", "うたう", ["to sing"], ["singing", "sing"], False),
    ("歌いましょう", "歌う", "うたう", ["to sing"], ["sing"], False),
    ("歌", "歌", "うた", ["song"], ["song"], True),
    ("キリギリス", "螽斯", "きりぎりす", ["grasshopper", "katydid", "cricket"], ["grasshopper"], True),
    ("あそこ", "彼処", "あそこ", ["there", "that place"], ["over there", "there"], False),
    ("蟻", "蟻", "あり", ["ant"], ["ant", "ants"], True),
    ("働いていました", "働く", "はたらく", ["to work"], ["working", "work", "worked"], False),
    ("でも", "でも", "でも", ["but", "however"], ["but"], False),
    ("いいえ", "いいえ", "いいえ", ["no", "nay"], ["no"], False),
    ("わたしたち", "私達", "わたしたち", ["we", "us"], ["we", "us"], False),
    ("働きます", "働く", "はたらく", ["to work"], ["work"], False),
    ("働きました", "働く", "はたらく", ["to work"], ["worked", "work"], False),
    ("食べ物", "食べ物", "たべもの", ["food"], ["food"], True),
    ("集めました", "集める", "あつめる", ["to collect", "to gather"], ["collect*", "gather*"], False),
    ("そして", "然して", "そして", ["and then", "and", "then"], ["then", "and"], False),
    ("冬", "冬", "ふゆ", ["winter"], ["winter"], True),
    ("寒い", "寒い", "さむい", ["cold"], ["cold"], False),
    ("ありませんでした", "有る", "ある", ["to be", "to exist", "to have"], ["no", "not", "didn't have"], False),
    ("お腹が空いています", "お腹が空く", "おなかがすく", ["hungry"], ["hungry"], False),
    ("ください", "下さい", "ください", ["please"], ["please"], False),
    ("食べましょう", "食べる", "たべる", ["to eat"], ["eat"], False),
    ("これから", "此れから", "これから", ["from now on", "after this"], ["from now on"], False),
    ("ありがとう", "有難う", "ありがとう", ["thank you", "thanks"], ["thank you", "thanks"], False),
    # ---- the north wind and the sun
    ("北風", "北風", "きたかぜ", ["north wind"], ["north wind"], True),
    ("太陽", "太陽", "たいよう", ["sun"], ["sun"], True),
    ("話していました", "話す", "はなす", ["to talk", "to speak"], ["talking", "talk", "speak*"], False),
    ("強い", "強い", "つよい", ["strong", "powerful"], ["strong"], False),
    ("強く", "強い", "つよい", ["strong", "powerful"], ["hard", "strong*"], False),
    ("その時", "其の時", "そのとき", ["at that time", "then"], ["at that time", "then"], False),
    ("旅人", "旅人", "たびびと", ["traveler", "traveller"], ["traveler", "traveller"], True),
    ("歩いて来ました", "歩く", "あるく", ["to walk"], ["walking", "walk*"], False),
    ("上着", "上着", "うわぎ", ["jacket", "coat"], ["jacket", "coat"], True),
    ("着ていました", "着る", "きる", ["to wear", "to put on"], ["wearing", "wore", "wear"], False),
    ("吹きます", "吹く", "ふく", ["to blow"], ["blow"], False),
    ("吹きました", "吹く", "ふく", ["to blow"], ["blew", "blow"], False),
    ("脱ぐでしょう", "脱ぐ", "ぬぐ", ["to take off", "to undress"], ["take off"], False),
    ("脱ぎました", "脱ぐ", "ぬぐ", ["to take off", "to undress"], ["took off", "take off"], False),
    ("しっかり", "確り", "しっかり", ["firmly", "tightly", "securely"], ["tightly", "firmly"], False),
    ("持ちました", "持つ", "もつ", ["to hold", "to carry", "to have"], ["held", "hold", "carry"], False),
    ("次は", "次", "つぎ", ["next"], ["next"], False),
    ("番", "番", "ばん", ["turn"], ["turn"], False),
    ("光", "光", "ひかり", ["light"], ["light"], True),
    ("出しました", "出す", "だす", ["to put out", "to take out", "to emit", "to give off"], ["gave out", "gave off", "put out"], False),
    ("暑く", "暑い", "あつい", ["hot"], ["hot"], False),
    ("悲しい", "悲しい", "かなしい", ["sad", "sorrowful"], ["sad"], False),
    # ---- Momotaro
    ("おじいさん", "お爺さん", "おじいさん", ["old man", "grandfather"], ["old man", "grandfather"], True),
    ("おばあさん", "お婆さん", "おばあさん", ["old woman", "grandmother"], ["old woman", "grandmother"], True),
    ("ある所", "所", "ところ", ["place"], ["certain place", "a place", "somewhere"], False),
    ("山", "山", "やま", ["mountain"], ["mountain"], True),
    ("川", "川", "かわ", ["river"], ["river"], True),
    ("桃", "桃", "もも", ["peach"], ["peach"], True),
    ("見つけました", "見つける", "みつける", ["to find", "to discover"], ["found", "find"], False),
    ("中から", "中", "なか", ["inside", "middle", "in"], ["out of", "from inside", "inside"], False),
    ("男の子", "男の子", "おとこのこ", ["boy"], ["boy"], False),
    ("出てきました", "出て来る", "でてくる", ["to come out", "to emerge"], ["came out", "come out"], False),
    ("にしましょう", "為る", "する", ["to decide on", "to do"], ["let's"], False),
    ("子", "子", "こ", ["child"], ["child", "boy", "kid"], False),
    ("鬼", "鬼", "おに", ["ogre", "demon"], ["ogre", "ogres", "demon"], True),
    ("島", "島", "しま", ["island"], ["island"], True),
    ("団子", "団子", "だんご", ["dumpling"], ["dumpling", "dumplings"], True),
    ("雉", "雉", "きじ", ["pheasant"], ["pheasant"], True),
    ("会いました", "会う", "あう", ["to meet"], ["met", "meet"], False),
    ("戦いました", "戦う", "たたかう", ["to fight", "to battle"], ["fought", "fight"], False),
    ("強かった", "強い", "つよい", ["strong", "powerful"], ["strong"], False),
    ("逃げました", "逃げる", "にげる", ["to flee", "to escape", "to run away"], ["ran away", "escape*", "flee*", "fled"], False),
    ("宝物", "宝物", "たからもの", ["treasure"], ["treasure"], True),
    ("嬉しかった", "嬉しい", "うれしい", ["happy", "glad"], ["happy"], False),
    ("おしまい", "お仕舞い", "おしまい", ["the end", "end"], ["the end", "end"], False),
    # names: only their English spelling is checked
    ("花子", None, None, None, ["hanako"], False),
    ("コロ", None, None, None, ["koro"], False),
    ("たま", None, None, None, ["tama"], False),
    ("桃太郎", None, None, None, ["momotaro"], False),
    ("太郎", None, None, None, ["taro"], False),
]
# dictionary-only checks (parts of counters / basic verbs seen inside fixed phrases)
DICT_ONLY = [("五", "五", "ご", ["five"]), ("歳", "歳", "さい", ["years-old"]), ("三", "三", "さん", ["three"]),
             ("時間", "時間", "じかん", ["hour", "time"]), ("ある", "或る", "ある", ["certain", "some"]),
             ("する", "為る", "する", ["to do"]), ("来る", "来る", "くる", ["to come"])]

missing, uncommon = [], []
for key, q, kana, gloss, en, noun in W:
    if q is None:
        continue
    hit = jm_find(q, kana, gloss)
    if hit is None:
        missing.append((key, q, kana, gloss))
    elif not hit["common"]:
        uncommon.append(f"{kana}({q})")
for key, q, kana, gloss in DICT_ONLY:
    if jm_find(q, kana, gloss) is None:
        missing.append((key, q, kana, gloss))
n_dict = sum(1 for w in W if w[1]) + len(DICT_ONLY)
check(f"JMdict agrees on kanji + reading + English meaning for all {n_dict} dictionary entries used", not missing, missing)
info(f"{n_dict - len(uncommon)}/{n_dict} carry JMdict common-word tags; not tagged (still ordinary words): " + ", ".join(uncommon))
OV_JMDICT = {"七時": ("七時", "しちじ"), "四人": ("四人", "よにん"), "蛙": ("蛙", "かえる"), "宝物": ("宝物", "たからもの"),
             "お腹が空い": ("お腹が空く", "おなかがすく")}
bad_ov = []
for k, v in OVERRIDES.items():
    head, kana = OV_JMDICT[k]
    ok = jm_find(head, kana, [""]) is not None and v[:-1] == kana[:-1]      # stem of the dictionary reading
    if not ok:
        bad_ov.append((k, v))
check("the 5 analyzer-default exceptions (七時 しちじ, 四人 よにん, 蛙 かえる, 宝物 たからもの, お腹が空く おなかがすく) "
      "are the dictionary readings", not bad_ov, bad_ov)
frog = {k.text: k.pri for e in JAM.lookup("蛙").entries for k in e.kana_forms if "frog" in " ".join(g.text for s in e.senses for g in s.gloss)}
check("蛙: かえる is the common reading (かわず is the rare literary one)", bool(frog.get("かえる")) and not frog.get("かわず"), frog)

# ============================================================================= 4. MEANING (JP <-> EN)
print("\n-- 4. meaning: Japanese <-> English")
IRREGULAR = {"won": "win", "ran": "run", "slept": "sleep", "said": "say", "kept": "keep", "became": "become", "went": "go",
             "came": "come", "saw": "see", "took": "take", "made": "make", "ate": "eat", "drank": "drink", "swam": "swim",
             "found": "find", "met": "meet", "fought": "fight", "blew": "blow", "held": "hold", "gave": "give", "grew": "grow",
             "wore": "wear", "left": "leave"}


def en_forms(text):
    t = text.lower().replace("’", "'").replace("“", " ").replace("”", " ")
    words = re.findall(r"[a-z']+", t)
    lem = [IRREGULAR.get(w) or simplemma.lemmatize(w, lang="en") for w in words]
    return " " + " ".join(words) + " ", " " + " ".join(lem) + " "


def en_has(text, kw):
    raw, lem = en_forms(text)
    if kw.endswith("*"):
        return re.search(r"\b" + re.escape(kw[:-1]), raw) is not None
    return (" " + kw + " ") in raw or (" " + kw + " ") in lem


KEYS = sorted(W, key=lambda w: -len(w[0]))


def match_keys(ref):
    taken, found = [False] * len(ref), []
    for w in KEYS:
        for m in re.finditer(re.escape(w[0]), ref):
            if not any(taken[m.start():m.end()]):
                for j in range(m.start(), m.end()):
                    taken[j] = True
                found.append(w)
    return found, taken


fwd, rev = [], []
for label, mine, ref, en in LINES:
    found, _ = match_keys(ref)
    keys_found = {w[0] for w in found}
    heads_found = {w[1] for w in found if w[1]}
    for w in found:
        if not any(en_has(en, kw.lstrip("~")) for kw in w[4]):
            fwd.append((label, w[0], w[4], en))
    for w in W:
        if (w[5] and w[0] not in keys_found and (w[1] is None or w[1] not in heads_found)
                and any(en_has(en, kw) for kw in w[4] if not kw.startswith("~"))):
            rev.append((label, w[0], en))
check("every Japanese word has its English counterpart in the English line", not fwd, fwd[:6])
check("every concrete noun in the English line exists in the Japanese line (nothing invented)", not rev, rev[:6])

IRREGULAR_PAST = set("""was were had did went came saw ate drank took got made said ran slept won kept became sat stood told
gave found thought knew felt left met wrote began brought bought lost sold sent spent swam flew fell grew drew drove rode rose woke
wore broke chose forgot heard held hid lay led meant paid shook sang sank spoke spun stole taught tore threw understood wept
fought blew put cut""".split())
NOT_PAST_ED = {"need", "feed", "red", "bed", "speed", "seed", "weed", "bleed", "breed", "indeed", "hundred", "shed", "sled", "reed",
               "wed", "fed", "bred"}


def en_is_past(text):
    words = re.findall(r"[a-z']+", text.lower().replace("’", "'"))
    be_now = {"is", "are", "am", "be", "been", "being", "it's", "he's", "she's"}
    return any(w in IRREGULAR_PAST or (w.endswith("ed") and w not in NOT_PAST_ED and (i == 0 or words[i - 1] not in be_now))
               for i, w in enumerate(words))   # "is surprised" is present tense, "was surprised" is past


tense = []
for label, mine, ref, en in LINES:
    if label.endswith("(title)"):
        continue
    if any(m in mine for m in ("ました", "でした", "かった")) != en_is_past(en):
        tense.append((label, mine, en))
check("past tense (〜ました 〜でした 〜かった) matches past tense in English, present (〜ます 〜です) matches present", not tense, tense)
marks = [(label, mine, en) for label, mine, ref, en in LINES
         if mine.count("「") != en.count("“") or mine.count("！") != en.count("!") or mine.count("？") != en.count("?")]
check("quotation marks, ! and ? counts agree between Japanese and English", not marks, marks)

# ============================================================================= 5. COVERAGE
print("\n-- 5. coverage")
uncovered = []
for label, mine, ref, en in LINES:
    _, taken = match_keys(ref)
    pos_i = 0
    for m in SUD.tokenize(ref, MODE_A):
        s, e = pos_i, pos_i + len(m.surface())
        pos_i = e
        p0 = m.part_of_speech()[0]
        if p0 in ("助詞", "助動詞", "補助記号", "接尾辞", "空白"):
            continue
        if not all(taken[s:e]):
            uncovered.append((label, m.surface(), p0))
check("no word in any line escapes the dictionary and meaning checks", not uncovered, uncovered)

# ============================================================================= 6. LABELS and English
print("\n-- 6. app labels and English text")
main = read("MainActivity.kt")
pairs = re.findall(r'label\("([^"]*)",\s*"([^"]*)"\)', main)
pairs += [(jp, en) for jp, en in re.findall(r'label\("([^"]*)",\s*if \(showEn\) "([^"]*)" else', main)]
pairs += re.findall(r'"([^"()]*[ぁ-ん][^"()]*?)\s*\(([A-Za-z ’\']+)\)"', main)
# JP label as written, reference spelling, JMdict headword + reading + gloss keyword, English keyword
UI = {
    "よむ": ("読む", "読む", "よむ", "to read", "read"),
    "かく": ("書く", "書く", "かく", "to write", "write"),
    "まえ": ("前", "前", "まえ", "previous", "previous"),
    "つぎ": ("次", "次", "つぎ", "next", "next"),
    "えいご": ("英語", "英語", "えいご", "english", "english"),
    "おわり": ("終わり", "終わる", "おわる", "to finish", "finish"),
    "へんしゅう": ("編集", "編集", "へんしゅう", "editing", "edit"),
    "けす": ("消す", "消す", "けす", "to delete", "delete"),
    "ほんとうに": ("本当に", "本当に", "ほんとうに", "really", "really"),
    "くうはく": ("空白", "空白", "くうはく", "blank space", "space"),
    "かいぎょう": ("改行", "改行", "かいぎょう", "new line", "new line"),
    "ほぞん": ("保存", "保存", "ほぞん", "saving", "sav*"),
    "ほぞん しました": ("保存しました", "保存", "ほぞん", "saving", "sav*"),
    "けしました": ("消しました", "消す", "けす", "to delete", "delete"),
    "だいめい": ("題名", "題名", "だいめい", "title", "title"),
    "ここに おはなしを かいてね": ("ここにお話を書いてね", "書く", "かく", "to write", "write"),
    "まず おはなしを かいてね": ("まずお話を書いてね", "書く", "かく", "to write", "write"),
    "わたしの おはなし": ("わたしのお話", "話", "はなし", "story", "stories"),
    "ひらがな ものがたり": ("平仮名物語", "物語", "ものがたり", "story", "stories"),
}
bad_ui, seen = [], set()
for jp, en in pairs:
    jp_clean = re.sub(r"[←→？！ ]", "", jp) if jp.strip("←→ ") not in UI else jp.strip("←→ ")
    key = jp.replace("←", "").replace("→", "").replace("？", "").strip()
    if key and all(ud.name(c, "").startswith("HIRAGANA LETTER SMALL") for c in key):
        seen.add(key)
        if not en_has(en, "small"):
            bad_ui.append((jp, "English text does not say small", en))
        continue
    if key not in UI:
        bad_ui.append((jp, "not covered by the test table"))
        continue
    seen.add(key)
    ref, q, kana, g, enkw = UI[key]
    got = [fn(ref) for _, fn in ENGINES]
    votes = sum(1 for x in got if x == norm(key))
    if votes < 2:
        bad_ui.append((jp, "reading", got))
    if jm_find(q, kana, [g]) is None:
        bad_ui.append((jp, "JMdict has no", q, kana, g))
    if not en_has(en, enkw):
        bad_ui.append((jp, "English text does not say", enkw, "->", en))
check(f"{len(seen)} app labels: reading (2 of 3 analyzers), JMdict meaning and English text all agree", not bad_ui, bad_ui)

all_en = [en for _, _, _, en in LINES]
curly = [e for e in all_en if re.search(r"[\"']", e) or e.count("“") != e.count("”") or "  " in e]
check("English text: curly quotes/apostrophes only, quotes balanced, no double spaces", not curly, curly)
def shape_ok(label, e):
    first = e.lstrip("“")[0]
    return first.isupper() and (label.endswith("(title)") or e[-1] in ".!?”")


check("English text: every line starts with a capital; every sentence line ends with . ! ? or a closing quote",
      all(shape_ok(l, e) for l, _, _, e in LINES), [e for l, _, _, e in LINES if not shape_ok(l, e)])
if SpellChecker:
    spell = SpellChecker()
    words = set(re.findall(r"[a-z]+", " ".join(all_en).lower().replace("’", " ")))
    unknown = spell.unknown(words) - {"hanako", "tama", "koro", "momotaro", "taro", "bento", "o", "s", "m"}
    check("English text: no spelling mistakes (names Hanako, Tama, Koro allowed)", not unknown, sorted(unknown))

if SpellChecker:
    ui_text = " ".join(re.sub(r"\$\{[^}]*\}|\\u[0-9A-Fa-f]{4}", " ", lit) for lit in
                       re.findall(r'"((?:[^"\\]|\\.)*)"', read("MainActivity.kt")))
    ui_words = {w for w in re.findall(r"[a-z]+", ui_text.lower())}
    ui_unknown = spell.unknown(ui_words) - {"ok", "kana", "hiragana", "o", "s", "m"}
    check("English text on the app's own screens: no spelling mistakes", not ui_unknown, sorted(ui_unknown))

# ============================================================================= optional: beginner level
if "--jlpt" in sys.argv:
    i = sys.argv.index("--jlpt")
    levels = {}
    for lvl, path in (("N5", sys.argv[i + 1]), ("N4", sys.argv[i + 2])):
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                for field in ("expression", "reading"):
                    for part in row[field].split(";"):
                        levels.setdefault(part.strip().lstrip("～~"), lvl)
    tally = {"N5": [], "N4": [], "other": []}
    for key, q, kana, gloss, en, noun in W:
        if q is None:
            continue
        lvl = None
        for cand in (q, kana, key):
            lvl = lvl or levels.get(cand) or levels.get(cand + "と") or levels.get(cand + "する")
        parts = {"六時": "六時", "七時": "七時", "四人": "四人"}.get(key)
        if lvl is None and parts:                      # number + counter: judge by the parts (all N5)
            lv = [levels.get(c) for c in parts]
            lvl = "N5" if all(x == "N5" for x in lv) else None
        tally[lvl or "other"].append(kana)
    total = sum(len(v) for v in tally.values())
    info(f"JLPT level of the {total} dictionary words: N5 {len(tally['N5'])}, N4 {len(tally['N4'])}, "
         f"not on the N5/N4 lists {len(tally['other'])}")
    info("not on the N5/N4 lists (everyday story words): " + ", ".join(tally["other"]))

failed = [n for n, ok in results if not ok]
print(f"\nWORD TEST: {len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
