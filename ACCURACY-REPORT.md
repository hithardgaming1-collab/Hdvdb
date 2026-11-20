# Accuracy report: Hiragana Stories

Date of test: 20 November 2026. Everything below was run on the finished project in this zip.

## Result

| Area | What was checked | Result |
|---|---|---|
| Letters | Keyboard has exactly the 46 basic hiragana, each in its correct consonant column and vowel row (checked with Unicode's own character names) | pass |
| Letters | ゛ ゜ and small-kana keys: tables equal Unicode's composition rules, and the app's real Kotlin code gives the correct result for all 86 hiragana (and leaves 265 other characters untouched) | pass |
| Letters | 48 Japanese lines (6 titles, 42 pages) use only modern hiragana and 、。！？「」; small ゃゅょっ used correctly; spacing style consistent; no particle spelt by sound (わ/お/え) | pass |
| Letters | The on-screen keyboard can type every character of every story (58 different letters used) | pass |
| Letters | 34 Japanese labels in the app code are hiragana only | pass |
| Words: reading | Every line is also written in normal kanji and kana. Sudachi matched 48/48 lines, Janome 44/48, pykakasi 39/48. Every line is confirmed by at least 2 of 3 | pass |
| Words: reading | 七時 しちじ, 四人 よにん, 蛙 かえる differ from analyzer defaults; the JMdict dictionary confirms the app's readings | pass |
| Words: spacing | Spaces fall only between words: none inside a word, none before a particle or ending, none missing after a particle | pass |
| Words: dictionary | 87 dictionary entries: kanji, reading and English meaning all agree in JMdict (85 carry common-word tags) | pass |
| Meaning | Every Japanese word has its English counterpart; no concrete noun is invented in English; past/present tense, quotation marks and ! agree | pass |
| Meaning | 18 button/screen labels: reading, dictionary meaning and English text agree. English spelling correct everywhere | pass |
| Level | Of 83 dictionary words, 70 are on the JLPT N5 list and 5 on N4. The other 8 are everyday story words: かめ, うさぎ, かけっこ, むかしむかし, ずっと, いってきます, いってらっしゃい, すてき | info |
| Code | All Kotlin sources compile against the Android 34 framework (0 errors, 0 warnings); 210 unit assertions pass | pass |
| Test quality | 18 deliberately planted errors (wrong vowel, lost small kana, katakana intruder, missing space, wrong word, wrong 7 o'clock, wrong translation, wrong tense, typo on a button...) were all caught; the unchanged control passed | 18/18 |

## Problems found, now fixed

1. Story 6, page 5: the English said "very cheerful" for 元気. The dictionary meaning is "lively". Now "The frog is very lively."
2. The delete button's second press showed ほんとうに？ with the English "Press OK again". The Japanese means "Really?". Now "Really? Press OK again".
3. Story 4, page 1: むかし むかし had a space inside one dictionary word. Now むかしむかし (the dictionary spelling).
4. Found while drawing a preview of the screens: the small-kana key put two lines of text in a key too short for them, so the lower line was cut off, and the ゛ ゜ key faces were tiny. The three bottom-row keys now show what they do: か→が, は→ぱ, つ→っ.
5. The delete confirmation's English text was wider than its button. Shortened to "Really? Press OK". The reader now also starts a new line only at a space, so a word is never split across two lines.

While the tests were being built, several checks first failed because of mistakes in the tests themselves (for example, a rule that did not know the English word "went"). Each was fixed, and the planted-error test above confirms the final tests catch real mistakes.

## What is not covered

- Grammar and naturalness (particle choice, politeness style, word choice) were reviewed by me, not by a tool. A native speaker's review is still the best final check before sharing widely.
- The English is checked against dictionary meanings, not for style.
- How the hiragana look on your TV depends on the TV's built-in font.
- The Android build itself (Gradle, APK) was not run here; the first GitHub build is the real test.

## Run it again

See tests/README.txt. Letters: `python3 tests/check_letters.py` (no installs).
Words: install the packages listed there, then `python3 tests/check_words.py`.
