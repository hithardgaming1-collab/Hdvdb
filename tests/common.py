"""Shared helpers: read the app's Kotlin source files (standard library only)."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "app" / "src" / "main" / "java" / "com" / "hiraganatv" / "stories"


def read(name):
    return (SRC / name).read_text(encoding="utf-8")


def load_stories():
    """Returns [{id, title, title_en, level, pages: [(jp, en), ...]}] from Stories.kt."""
    src = read("Stories.kt")
    stories = []
    pattern = r'Story\(\s*(\d+), "([^"]*)", "([^"]*)", "([^"]*)"|p\("([^"]*)",\s*"([^"]*)"\)'
    for m in re.finditer(pattern, src):
        if m.group(1):
            stories.append({"id": int(m.group(1)), "title": m.group(2),
                            "title_en": m.group(3), "level": m.group(4), "pages": []})
        else:
            stories[-1]["pages"].append((m.group(5), m.group(6)))
    return stories


def kana_tables():
    """The constant strings in Kana.kt."""
    src = read("Kana.kt")
    return {k: v for k, v in re.findall(r'private const val (\w+) = "([^"]*)"', src)}


def keyboard_grid():
    src = read("MainActivity.kt")
    block = re.search(r"private val GRID = arrayOf\((.*?)\)\n", src, re.S).group(1)
    return re.findall(r'"([^"]*)"', block)
