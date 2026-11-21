# Accuracy report: Hiragana Stories

Date of test: 21 November 2026. Everything below was run on the finished project in this zip:
12 stories, 117 pages, 12 titles (129 Japanese lines).

## Result

| Area | What was checked | Result |
|---|---|---|
| Letters | Keyboard has exactly the 46 basic hiragana, each in its correct consonant column and vowel row (checked with Unicode's own character names) | pass |
| Letters | The か→が, は→ぱ and つ→っ keys: tables equal Unicode's composition rules, and the app's real Kotlin code gives the correct result for all 86 hiragana (and leaves 265 other characters untouched) | pass |
| Letters | All 129 Japanese lines use only modern hiragana and 、。！？「」; small ゃゅょっ used correctly; spacing style consistent; no particle spelt by sound (わ/お/え) | pass |
| Letters | The on-screen keyboard can type every character of every story (65 different letters used); 34 Japanese labels in the app code are hiragana only | pass |
| Words: reading | Every line is also written in normal kanji and kana. Sudachi matched 129/129 lines, Janome 123/129, pykakasi 111/129. Every line is confirmed by at least 2 of 3 | pass |
| Words: reading | 七時 しちじ, 四人 よにん, 蛙 かえる, 宝物 たからもの, お腹が空く おなかがすく differ from analyzer defaults; the JMdict dictionary confirms the app's readings | pass |
| Words: spacing | Spaces fall only between words: none inside a word, none before a particle or ending, none missing after a particle; unspaced joins are real dictionary words or number+counter | pass |
| Words: dictionary | 230 dictionary entries: kanji, reading and English meaning all agree in JMdict (219 carry common-word tags) | pass |
| Meaning | Every Japanese word has its English counterpart; no concrete noun is invented in English; past/present tense (including ～でした and ～かったです), quotation marks and ! agree | pass |
| Meaning | 18 button/screen labels: reading, dictionary meaning and English text agree. English spelling correct everywhere | pass |
| Level | Of 223 dictionary words, 166 are on the JLPT N5 list and 22 on N4 (84%). The rest are everyday story words such as かめ, うさぎ, ゆきだるま, おに and だんご | info |
| Layout | In a drawn preview of the reading card, all 117 pages fit (116 at the largest text size, 1 slightly smaller), with lines broken only at spaces | pass |
| Code | All Kotlin sources compile against the Android 34 framework (0 errors, 0 warnings); 528 unit assertions pass | pass |
| Test quality | 24 deliberately planted errors (wrong vowel, lost small kana, lost ゛, katakana intruder, missing space, wrong word, wrong 7 o'clock, wrong translation, wrong number, wrong tense, typo on a button...) were all caught; the unchanged control passed | 24/24 |

## Problems found, now fixed

1. Story 6, page 5: the English said "very cheerful" for 元気. The dictionary meaning is "lively". Now "The frog is very lively."
2. The delete button's second press showed ほんとうに？ with the English "Press OK again". The Japanese means "Really?". Now "Really? Press OK".
3. Story 4, page 1: むかし むかし had a space inside one dictionary word. Now むかしむかし (the dictionary spelling).
4. Found while drawing a preview of the screens: the small-kana key put two lines of text in a key too short for them, so the lower line was cut off, and the ゛ ゜ key faces were tiny. The three bottom-row keys now show what they do: か→が, は→ぱ, つ→っ.
5. The delete confirmation's English text was wider than its button, and the reader could have split a word across two lines. Both fixed: the reader now starts a new line only at a space.
6. The new Story 10 (The Ant and the Grasshopper), page 1: the English "One summer day" had dropped the words for ある日 ("one day"). Now "One day in summer".

While the tests were being built, several checks first failed because of mistakes in the tests themselves (for example, a rule that did not know the English word "went", or analyzers that read 宝物 as ほうもつ instead of the everyday たからもの). Each was fixed, and the planted-error test above confirms the final tests catch real mistakes.

## What is not covered

- Grammar and naturalness (particle choice, politeness style, word choice) were reviewed by me, not by a tool. A native speaker's review is still the best final check before sharing widely.
- The English is checked against dictionary meanings, not for style.
- The folk tales are short retellings in beginner Japanese, not the full traditional texts.
- How the hiragana look on your TV depends on the TV's built-in font.
- The Android build itself (Gradle, APK) was not run here; the first GitHub build is the real test.

## Run it again

See tests/README.txt. Letters: `python3 tests/check_letters.py` (no installs).
Words: install the packages listed there, then `python3 tests/check_words.py`.
