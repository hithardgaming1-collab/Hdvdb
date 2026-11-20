Accuracy tests for Hiragana Stories
===================================

These tests read the app's own source files (Stories.kt, Kana.kt, MainActivity.kt) and fail loudly if a letter,
a word, a space or a translation is wrong. They are NOT part of the Android build; run them on a computer.

1) Letters (no installs, Python 3 only)
     python3 tests/check_letters.py

   Checks: the keyboard has exactly the 46 basic hiragana in the right consonant/vowel places (using Unicode's own
   character names), the dakuten / handakuten / small-kana tables equal Unicode's composition rules, every story
   uses only modern hiragana and the allowed punctuation, small kana are used correctly, spacing style is consistent,
   and the on-screen keyboard can type every character of every story.

   Optional extra: also test the app's real Kotlin key code. Compile Kana.kt with a dump program that prints
   "codepoint voiced semi small" (hex) for U+0020-U+007E and U+3000-U+30FF, then:
     python3 tests/check_letters.py --kotlin-dump dump.txt

2) Words (needs a few Python packages)
     pip install sudachipy sudachidict_core janome pykakasi simplemma jamdict jamdict-data pyspellchecker
     python3 tests/check_words.py

   Checks: every story line is also written in normal kanji+kana (tests/reference.py); three independent analyzers
   (Sudachi, Janome, pykakasi) must agree with the app's hiragana (two out of three, with the JMdict dictionary
   settling 七時, 四人 and 蛙); spaces fall only between words; every word is found in the JMdict dictionary with
   the same reading and English meaning; every Japanese word has its English counterpart and no concrete noun is
   invented in English; tense, quotes and ! agree; button labels and English spelling are right.

   Optional beginner-level report: add  --jlpt n5.csv n4.csv  (JLPT word lists in CSV form).

When you add a story
   - add its lines to Stories.kt (hiragana only),
   - add the same lines in normal kanji+kana to tests/reference.py (same story number, same page order),
   - if the test reports a word it does not know ("coverage"), add that word to the table W in check_words.py.
