#!/usr/bin/env python3
"""
Letter-level accuracy test for Hiragana Stories (standard library only).
Run from the project folder:   python3 tests/check_letters.py
Optional:  --kotlin-dump FILE   also verify the app's real Kotlin code (see tests/README.txt)
"""
import re
import sys
import unicodedata as ud

from common import keyboard_grid, kana_tables, load_stories, read

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    line = ("PASS  " if ok else "FAIL  ") + name
    if detail and not ok:
        line += "\n        " + str(detail)
    print(line)


def nfc(s):
    return ud.normalize("NFC", s)


def syllable(ch):
    """'か' -> 'KA' using the official Unicode character name (Nihon-shiki spelling)."""
    return ud.name(ch).replace("HIRAGANA LETTER ", "")


# ---------------------------------------------------------------- 1. keyboard
grid = keyboard_grid()
check("keyboard: 5 rows of 10 cells", len(grid) == 5 and all(len(r) == 10 for r in grid), grid)

kana = [(r, c, ch) for r, row in enumerate(grid) for c, ch in enumerate(row) if ch != "."]
check("keyboard: exactly 46 kana, no repeats", len(kana) == 46 and len({k[2] for k in kana}) == 46)

EXPECTED_46 = set("A I U E O KA KI KU KE KO SA SI SU SE SO TA TI TU TE TO NA NI NU NE NO "
                  "HA HI HU HE HO MA MI MU ME MO YA YU YO RA RI RU RE RO WA WO N".split())
check("keyboard: kana are exactly the 46 basic hiragana (by Unicode name)",
      {syllable(ch) for _, _, ch in kana} == EXPECTED_46)
check("keyboard: every kana is one plain code point (no voiced/small/look-alike)",
      all(len(nfc(ch)) == 1 and ud.name(ch).startswith("HIRAGANA LETTER ") and "SMALL" not in ud.name(ch)
          and "\u3041" <= ch <= "\u3093" for _, _, ch in kana))

COLS = ["", "K", "S", "T", "N", "H", "M", "Y", "R", "W"]
ROWS = "AIUEO"
misplaced = []
for r, c, ch in kana:
    s = syllable(ch)
    if s == "N":
        if (r, c) != (2, 9):
            misplaced.append((ch, r, c))
    elif s[:-1] != COLS[c] or s[-1] != ROWS[r]:
        misplaced.append((ch, r, c, s))
check("keyboard: every kana sits in its correct consonant column and vowel row", not misplaced, misplaced)
blanks = {(r, c) for r, row in enumerate(grid) for c, ch in enumerate(row) if ch == "."}
check("keyboard: empty cells only where the real chart has gaps (ya/wa columns)",
      blanks == {(1, 7), (3, 7), (1, 9), (3, 9)}, blanks)

# ------------------------------------------------- 2. dakuten / handakuten / small tables
t = kana_tables()
PLAIN, VOICED, H_PLAIN, H_SEMI, BIG, SMALL = (t[k] for k in ("PLAIN", "VOICED", "H_PLAIN", "H_SEMI", "BIG", "SMALL"))

check("voiced table: each pair equals Unicode's own composition (base + U+3099)",
      len(PLAIN) == len(VOICED) and all(nfc(p + "\u3099") == v for p, v in zip(PLAIN, VOICED)))
check("semi-voiced table: each pair equals Unicode's own composition (base + U+309A)",
      len(H_PLAIN) == len(H_SEMI) and all(nfc(p + "\u309A") == v for p, v in zip(H_PLAIN, H_SEMI)))
unicode_voiced = {chr(c) for c in range(0x3041, 0x3097) if len(nfc(chr(c) + "\u3099")) == 1 and nfc(chr(c) + "\u3099") != chr(c) + "\u3099"}
check("voiced table: covers every letter that can take ゛ (only う→ゔ and ゝ→ゞ left out on purpose)",
      set(PLAIN) == unicode_voiced - {"う", "ゝ"}, sorted(unicode_voiced ^ set(PLAIN)))
check("semi-voiced table: covers every letter that can take ゜ (は ひ ふ へ ほ)",
      set(H_PLAIN) == {chr(c) for c in range(0x3041, 0x3097) if len(nfc(chr(c) + "\u309A")) == 1 and nfc(chr(c) + "\u309A") != chr(c) + "\u309A"})
small_ok = len(BIG) == len(SMALL) and all(
    ud.name(s) == ud.name(b).replace("LETTER ", "LETTER SMALL ") for b, s in zip(BIG, SMALL))
check("small-kana table: each pair is (letter, its SMALL form) by Unicode name", small_ok)
check("small-kana table: covers あいうえお つ やゆよ", set(BIG) == set("あいうえおつやゆよ"))

# ---------------------------------------------------------------- 3. real Kotlin code
if "--kotlin-dump" in sys.argv:
    dump = sys.argv[sys.argv.index("--kotlin-dump") + 1]
    LEFT_OUT = set("うゔゝゞ")
    bigs = {b: ud.lookup(ud.name(b).replace("LETTER ", "LETTER SMALL ")) for b in BIG}

    def exp_voice(c):
        if c in LEFT_OUT:
            return c
        v = nfc(c + "\u3099")
        if len(v) == 1 and v != c + "\u3099":
            return v
        d = ud.normalize("NFD", c)
        if len(d) == 2 and d[1] == "\u3099":
            return d[0]
        if len(d) == 2 and d[1] == "\u309A":
            v = nfc(d[0] + "\u3099")
            return v if len(v) == 1 else c
        return c

    def exp_semi(c):
        v = nfc(c + "\u309A")
        if len(v) == 1 and v != c + "\u309A":
            return v
        d = ud.normalize("NFD", c)
        if len(d) == 2 and d[1] == "\u309A":
            return d[0]
        if len(d) == 2 and d[1] == "\u3099":
            v = nfc(d[0] + "\u309A")
            return v if len(v) == 1 else c
        return c

    def exp_small(c):
        for b, s in bigs.items():
            if c == b:
                return s
            if c == s:
                return b
        return c

    bad, n = [], 0
    for line in open(dump):
        cp, v, s, m = (int(x, 16) for x in line.split())
        c = chr(cp)
        n += 1
        got = (chr(v), chr(s), chr(m))
        if 0x3041 <= cp <= 0x3096:
            want = (exp_voice(c), exp_semi(c), exp_small(c))
        else:
            want = (c, c, c)          # ASCII, punctuation and katakana: the keys must not touch them
        if got != want:
            bad.append((hex(cp), got, want))
    check(f"real Kotlin code: ゛ ゜ small keys give the Unicode-correct result for all hiragana "
          f"and leave the other {n - 86} tested characters (ASCII, punctuation, katakana) unchanged",
          not bad, bad[:5])

# ---------------------------------------------------------------- 4. story text
stories = load_stories()
texts = [("title: " + s["title"], s["title"]) for s in stories]
texts += [(f'{s["title"]} p{i + 1}', jp) for s in stories for i, (jp, _) in enumerate(s["pages"])]
PUNCT = "、。！？「」"
OBSOLETE = set("ゐゑゝゞゔゕゖゟ")


def bad_chars(text):
    return [ch for ch in text
            if not ("\u3041" <= ch <= "\u3093" or ch in PUNCT or ch == " ") or ch in OBSOLETE]


check(f"text: {len(texts)} Japanese strings use only modern hiragana, 、。！？「」 and a normal space",
      all(not bad_chars(x) for _, x in texts), [(n, bad_chars(x)) for n, x in texts if bad_chars(x)])
check("text: no katakana, kanji, romaji, digits, half-width kana or combining marks anywhere",
      all(nfc(x) == x and not re.search(r"[\u30A0-\u30FF\u4E00-\u9FFF\uFF10-\uFF19\uFF21-\uFF3A\uFF41-\uFF5A\uFF61-\uFF9FA-Za-z0-9\u3099\u309A]", x) for _, x in texts))
check("text: small ゃゅょ always follow an i-row kana (きしちにひみり + voiced)",
      all(m.start() > 0 and x[m.start() - 1] in "きぎしじちぢにひびぴみり" for _, x in texts for m in re.finditer("[ゃゅょ]", x)))
check("text: small っ is always followed by a k/s/t/p-row kana (e.g. がっこう, いって, ずっと)",
      all(m.end() < len(x) and x[m.end()] in "かきくけこさしすせそたちつてとぱぴぷぺぽ" for _, x in texts for m in re.finditer("っ", x)))
check("text: small ぁぃぅぇぉ never used",
      all(not re.search("[ぁぃぅぇぉ]", x) for _, x in texts))
check("text: no word starts with を ん っ ゃ ゅ ょ ー",
      all(not re.match("[をんっゃゅょー]", w) for _, x in texts for w in x.split(" ") if w))
check("text: sentence ends are followed by exactly one space (or the closing 」), commas by none",
      all(not re.search(r"[。！？](?![」 ]|$)|[。！？] {2,}|、 | [。！？、」]|「 ", x) for _, x in texts))
check("text: 「 」 are balanced on every page", all(x.count("「") == x.count("」") for _, x in texts))
check("text: every page ends with 。 ！ ？ or 」", all(x[-1] in "。！？」" for n, x in texts if not n.startswith("title")))
check("text: no particle stands alone as its own word (は を が に で と も へ の)",
      all(w not in list("はをがにでともへの") for _, x in texts for w in x.split(" ")))
check("text: no particle misspelt by sound (わ for は, お for を, え for へ standing alone after a word)",
      all(not re.search(r"(?<![あ-ん])[わおえ]( |$)", x) for _, x in texts))
i_row_full = []
for n, x in texts:
    for w in x.split(" "):
        for m in re.finditer("[やゆよ]", w):
            if m.start() > 0 and w[m.start() - 1] in "きぎしじちぢにひびぴみり":
                i_row_full.append((n, w))
check("text: full-size や ゆ よ after an i-row kana only where it is a real two-sound spelling (にちようび)",
      all(w.startswith("にちようび") for _, w in i_row_full), i_row_full)
print(f"        (found {len(i_row_full)}: {sorted({w for _, w in i_row_full})})")

# ---------------------------------------------------------------- 5. keyboard can type every story
voiced_from = {v: p for p, v in zip(PLAIN, VOICED)}
semi_from = {v: p for p, v in zip(H_PLAIN, H_SEMI)}
small_from = {s: b for b, s in zip(BIG, SMALL)}
base46 = {ch for _, _, ch in kana}
keys_punct = set("ー、。！？「」") | {" "}


def typeable(ch):
    if ch in base46 or ch in keys_punct:
        return True
    if ch in voiced_from:
        return voiced_from[ch] in base46
    if ch in semi_from:
        return semi_from[ch] in base46
    if ch in small_from:
        return small_from[ch] in base46
    return False


untypeable = sorted({ch for _, x in texts for ch in x if not typeable(ch)})
check("keyboard can type every character used in every built-in story", not untypeable, untypeable)
used = {ch for _, x in texts for ch in x}
print(f"        (stories use {len({c for c in used if '\u3041' <= c <= '\u3093'})} different hiragana letters)")

# ---------------------------------------------------------------- 6. app labels
main = read("MainActivity.kt") + read("Ui.kt")
literals = re.findall(r'"((?:[^"\\]|\\.)*)"', main)
jp_literals = [s for s in literals if re.search(r"[\u3041-\u3096\u30A0-\u30FF\u4E00-\u9FFF]", s)]
bad_ui = []
for s in jp_literals:
    s2 = s.replace("\\u309B", "\u309B").replace("\\u309C", "\u309C")
    s2 = "".join(ch for ch in s2 if ord(ch) > 127)      # ASCII is English text; every non-ASCII character must be hiragana
    extra = [ch for ch in s2 if not ("\u3041" <= ch <= "\u3093" or ch in PUNCT + "→←\u309B\u309Cー’“”")]
    if extra:
        bad_ui.append((s, extra))
check(f"app labels: {len(jp_literals)} Japanese labels in the code are hiragana only (no kanji/katakana)",
      not bad_ui, bad_ui)
check("app labels: the hint examples か→が, は→ぱ, つ→っ match the key tables",
      VOICED[PLAIN.index("か")] == "が" and H_SEMI[H_PLAIN.index("は")] == "ぱ" and SMALL[BIG.index("つ")] == "っ")

failed = [n for n, ok in results if not ok]
print(f"\nLETTER TEST: {len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
