# Hiragana Stories for Android TV (ひらがな ものがたり)

Read short beginner stories written only in hiragana, or write your own with an on-screen hiragana keyboard.
Made for a 32-inch Android TV (HD or Full HD) and a normal remote: arrow keys, OK and Back.

## What is inside the app

- **Read (よむ)**: 6 built-in stories (Beginner 1 and 2), 7 pages each. Large hiragana with spaces between phrases,
  and an English line you can switch on or off (えいご). Every Japanese line is hiragana only, polite です/ます style.
- **Write (かく)**: a title box, a story box and a hiragana keyboard you drive with the remote.
  Only valid hiragana can be typed, so a story never contains stray letters.
  - The bottom-row keys change the last letter you typed: か→が adds ゛ (し→じ, は→ば), は→ぱ adds ゜, つ→っ makes small kana (や→ゃ). Press again to undo.
  - Press **up** from the keyboard to pick the title box or the story box. New line in the title jumps to the story.
  - Each line you write becomes one page when reading.
  - **Save (ほぞん)** saves and opens the story. **Back** also saves (nothing you wrote is lost).
- Your stories appear at the bottom of the story list. Open one to **Edit (へんしゅう)** or **Delete (けす)**; delete asks you to press OK twice.
- The layout is drawn on a 960 x 540 canvas and stretched to the screen, with 5% clear on every side for TV overscan.

## Get the APK with GitHub (no Android Studio needed)

1. On github.com create a new repository (any name).
2. Upload everything **inside** the `HiraganaStoriesTV` folder to the repository root, including the hidden `.github` folder.
   `settings.gradle.kts` must be at the top level of the repository.
3. Open the **Actions** tab, choose **Build APK**, press **Run workflow**. It also runs on every push to `main` or `master`.
4. After about 3 to 6 minutes, open the finished run, download the artifact **HiraganaStories-APK** and unzip it.
   Inside is `app-debug.apk`.

Cannot see or upload `.github`? On GitHub press **Add file, Create new file**, type the name
`.github/workflows/build-apk.yml` and paste this:

```yaml
name: Build APK

on:
  push:
    branches: [main, master]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"

      - name: Set up Gradle 8.9
        uses: gradle/actions/setup-gradle@v4
        with:
          gradle-version: "8.9"

      - name: Build debug APK
        run: gradle :app:assembleDebug --stacktrace

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: HiraganaStories-APK
          path: app/build/outputs/apk/debug/*.apk
          if-no-files-found: error
```

If the build fails, open the failed step in the run log and read the first red error line.

## Install on the TV

- USB stick: copy `app-debug.apk`, open it with a file manager on the TV and allow installs from unknown sources when asked.
- Or use the "Send Files to TV" app, or from a computer on the same network: `adb connect <tv-ip>:5555` then `adb install app-debug.apk`.
- Open **Hiragana Stories** from the Apps row of the TV home screen.

The APK is signed with the standard debug key, which is fine for installing on your own TV.

## Add or change stories

Edit `app/src/main/java/com/hiraganatv/stories/Stories.kt`. Copy one `Story(...)` block, give it a new unique number,
and write each page as `p("japanese", "English")`. Keep Japanese lines to hiragana, spaces, and 、。！？「」.

## Accuracy tests

`ACCURACY-REPORT.md` has the results of the letter and word tests (all passed). The tests live in `tests/` and can be
re-run after you edit a story; see `tests/README.txt`. They are not part of the Android build.

## Technical notes

Kotlin, Android framework views only (no extra libraries), minSdk 21, targetSdk 34, compileSdk 35.
Android Gradle Plugin 8.7.3, Gradle 8.9, Kotlin 2.0.21, JDK 17.
You can also open the folder in Android Studio and run it on an Android TV emulator.
