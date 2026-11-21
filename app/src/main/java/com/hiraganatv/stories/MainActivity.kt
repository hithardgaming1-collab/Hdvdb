package com.hiraganatv.stories

import android.app.Activity
import android.graphics.Color
import android.graphics.Paint
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup.LayoutParams.MATCH_PARENT
import android.view.ViewGroup.LayoutParams.WRAP_CONTENT
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Space
import android.widget.TextView
import android.widget.Toast

// Writing keyboard, laid out like the classic gojuon chart turned on its side:
// every column is a consonant row (a ka sa ta na ha ma ya ra wa), every row is a vowel. "." is an empty cell.
private val GRID = arrayOf(
    "あかさたなはまやらわ",
    "いきしちにひみ.り.",
    "うくすつぬふむゆるん",
    "えけせてねへめ.れ.",
    "おこそとのほもよろを"
)

private const val WRITER_HINT =
    "Bottom row: か→が adds \u309B, は→ぱ adds \u309C, つ→っ small kana. Press again to undo. Up arrow picks title or story."

class MainActivity : Activity() {

    private lateinit var holder: FrameLayout
    private lateinit var store: Store
    private var onBack: (() -> Unit)? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        U.init(this)
        store = Store(this)
        holder = FrameLayout(this)
        holder.background = GradientDrawable(
            GradientDrawable.Orientation.TOP_BOTTOM,
            intArrayOf(Pal.BOARD_TOP, Pal.BOARD_BOTTOM)
        )
        setContentView(holder)
        showHome()
    }

    @Suppress("DEPRECATION", "OVERRIDE_DEPRECATION")
    override fun onBackPressed() {
        val back = onBack
        if (back != null) back() else super.onBackPressed()
    }

    private fun show(content: View, back: (() -> Unit)?, focus: View?) {
        onBack = back
        holder.removeAllViews()
        holder.addView(content, FrameLayout.LayoutParams(MATCH_PARENT, MATCH_PARENT))
        (focus ?: content).requestFocus()
    }

    /** A page keeps 5% clear on every side so nothing is cut off by TV overscan. */
    private fun page(): LinearLayout {
        val p = LinearLayout(this)
        p.orientation = LinearLayout.VERTICAL
        p.setPadding(U.px(48f), U.px(27f), U.px(48f), U.px(27f))
        return p
    }

    /** Starts a new line only at a space, so a word is never cut in two (Android may otherwise break between kana). */
    private fun wrapAtSpaces(text: String, paint: Paint, maxWidth: Float): String {
        val out = StringBuilder()
        var line = ""
        for (word in text.split(' ')) {
            val next = if (line.isEmpty()) word else "$line $word"
            if (line.isNotEmpty() && paint.measureText(next) > maxWidth) {
                out.append(line).append('\n')
                line = word
            } else {
                line = next
            }
        }
        return out.append(line).toString()
    }

    private fun toast(msg: String) = Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()

    // ------------------------------------------------------------------ Home

    private fun showHome() {
        val p = page()
        p.orientation = LinearLayout.HORIZONTAL
        p.gravity = Gravity.CENTER_VERTICAL

        val ring = tv(this, "あ", 80f, Pal.YELLOW, bold = true, center = true)
        val chalkRing = GradientDrawable()
        chalkRing.setShape(GradientDrawable.OVAL)
        chalkRing.setColor(Color.TRANSPARENT)
        chalkRing.setStroke(U.px(6f), Pal.CHALK)
        ring.background = chalkRing
        p.addView(ring, lp(U.px(176f), U.px(176f)).apply { rightMargin = U.px(44f) })

        val col = LinearLayout(this)
        col.orientation = LinearLayout.VERTICAL
        col.addView(tv(this, "ひらがな ものがたり", 56f, Pal.CHALK, bold = true))
        col.addView(tv(this, "Hiragana stories for beginners", 24f, Pal.MUTED))

        val read = button(this, label("よむ", "Read stories"), 36f) { showList(null) }
        val write = button(this, label("かく", "Write a story"), 36f) { showWriter(null) }
        val row = LinearLayout(this)
        row.orientation = LinearLayout.HORIZONTAL
        row.addView(read, lp(U.px(260f), U.px(104f)).apply { rightMargin = U.px(16f) })
        row.addView(write, lp(U.px(260f), U.px(104f)))
        col.addView(row, lp(WRAP_CONTENT, WRAP_CONTENT).apply { topMargin = U.px(30f) })

        col.addView(
            tv(this, "Arrow keys move, OK chooses, Back returns.", 18f, Pal.MUTED),
            lp(WRAP_CONTENT, WRAP_CONTENT).apply { topMargin = U.px(22f) }
        )
        p.addView(col, lp(WRAP_CONTENT, WRAP_CONTENT))
        show(p, null, read)
    }

    // ------------------------------------------------------------ Story list

    private fun showList(focusId: Long?) {
        val all = Library.all + store.userStories()
        val p = page()

        val head = LinearLayout(this)
        head.orientation = LinearLayout.HORIZONTAL
        head.gravity = Gravity.BOTTOM
        head.addView(tv(this, "よむ", 40f, Pal.CHALK, bold = true))
        head.addView(
            tv(this, "Choose a story", 22f, Pal.MUTED),
            lp(WRAP_CONTENT, WRAP_CONTENT).apply { leftMargin = U.px(14f); bottomMargin = U.px(6f) }
        )
        p.addView(head)

        val list = LinearLayout(this)
        list.orientation = LinearLayout.VERTICAL
        var first: View? = null
        var target: View? = null
        for ((idx, s) in all.withIndex()) {
            if (s.mine && (idx == 0 || !all[idx - 1].mine)) {
                list.addView(
                    tv(this, "わたしの おはなし (My stories)", 22f, Pal.YELLOW, bold = true),
                    lp(WRAP_CONTENT, WRAP_CONTENT).apply { topMargin = U.px(16f) }
                )
            }
            val row = storyRow(idx + 1, s) { showReader(s, 0) }
            list.addView(row, lp(MATCH_PARENT, U.px(66f)).apply { topMargin = U.px(8f) })
            if (first == null) first = row
            if (s.id == focusId) target = row
        }
        val sv = ScrollView(this)
        sv.isVerticalScrollBarEnabled = false
        sv.addView(list)
        p.addView(sv, lp(MATCH_PARENT, 0, 1f))
        show(p, { showHome() }, target ?: first)
    }

    private fun storyRow(n: Int, s: Story, click: () -> Unit): View {
        val row = LinearLayout(this)
        row.orientation = LinearLayout.HORIZONTAL
        row.gravity = Gravity.CENTER_VERTICAL
        row.isFocusable = true
        row.isClickable = true
        row.background = focusBg(Pal.PANEL, 16f)
        row.setPadding(U.px(18f), 0, U.px(22f), 0)
        row.setOnClickListener { click() }

        val num = tv(this, n.toString(), 24f, Pal.YELLOW, bold = true, center = true)
        num.background = rounded(Pal.BOARD_BOTTOM, 19f)
        row.addView(num, lp(U.px(38f), U.px(38f)))

        val names = LinearLayout(this)
        names.orientation = LinearLayout.VERTICAL
        val jp = tv(this, s.title, 30f, Pal.CHALK, bold = true)
        jp.setTextColor(stateColor(Pal.CHALK, Pal.ON_YELLOW))
        val en = tv(this, s.titleEn, 18f, Pal.MUTED)
        en.setTextColor(stateColor(Pal.MUTED, Pal.FOCUS_SUB))
        jp.isDuplicateParentStateEnabled = true
        en.isDuplicateParentStateEnabled = true
        names.addView(jp)
        names.addView(en)
        row.addView(names, lp(0, WRAP_CONTENT, 1f).apply { leftMargin = U.px(16f) })

        val meta = LinearLayout(this)
        meta.orientation = LinearLayout.VERTICAL
        val level = tv(this, s.level, 20f, Pal.CHALK, bold = true)
        level.setTextColor(stateColor(Pal.CHALK, Pal.ON_YELLOW))
        val count = tv(this, "${s.pages.size} pages", 18f, Pal.MUTED)
        count.setTextColor(stateColor(Pal.MUTED, Pal.FOCUS_SUB))
        level.gravity = Gravity.END
        count.gravity = Gravity.END
        level.isDuplicateParentStateEnabled = true
        count.isDuplicateParentStateEnabled = true
        meta.addView(level, lp(MATCH_PARENT, WRAP_CONTENT))
        meta.addView(count, lp(MATCH_PARENT, WRAP_CONTENT))
        row.addView(meta, lp(WRAP_CONTENT, WRAP_CONTENT))
        return row
    }

    // ---------------------------------------------------------------- Reader

    private fun showReader(s: Story, start: Int) {
        val last = s.pages.size - 1
        var i = start.coerceIn(0, last)
        var showEn = store.showEnglish

        val p = page()

        val top = LinearLayout(this)
        top.orientation = LinearLayout.HORIZONTAL
        top.gravity = Gravity.CENTER_VERTICAL
        val counter = tv(this, "", 24f, Pal.MUTED)
        top.addView(tv(this, s.title, 28f, Pal.YELLOW, bold = true), lp(0, WRAP_CONTENT, 1f))
        top.addView(counter)
        p.addView(top, lp(MATCH_PARENT, U.px(44f)))

        val jp = tv(this, "", 44f, Pal.INK, center = true)
        jp.setLineSpacing(0f, 1.15f)
        jp.letterSpacing = 0.06f
        val en = tv(this, "", 24f, Pal.SUB_INK, center = true)
        val card = LinearLayout(this)
        card.orientation = LinearLayout.VERTICAL
        card.gravity = Gravity.CENTER
        card.background = rounded(Pal.PAPER, 28f)
        card.setPadding(U.px(36f), U.px(16f), U.px(36f), U.px(16f))
        card.addView(jp, lp(MATCH_PARENT, WRAP_CONTENT))
        card.addView(en, lp(MATCH_PARENT, WRAP_CONTENT).apply { topMargin = U.px(14f) })
        p.addView(card, lp(MATCH_PARENT, 0, 1f).apply { topMargin = U.px(10f); bottomMargin = U.px(12f) })

        val prev = button(this, label("← まえ", "Previous")) {}
        val next = button(this, "", 26f, Pal.PRIMARY) {}
        val enBtn = button(this, "", 26f) {}

        fun render() {
            val pg = s.pages[i]
            var shownJp = pg.jp
            for (size in floatArrayOf(44f, 38f, 32f, 28f, 24f, 20f)) {   // biggest size whose lines fit the card
                U.text(jp, size)
                shownJp = wrapAtSpaces(pg.jp, jp.paint, U.px(792f) * 0.97f)
                val lines = shownJp.count { it == '\n' } + 1
                if (lines * jp.paint.fontSpacing * 1.15f <= U.px(228f)) break
            }
            jp.text = shownJp
            en.text = pg.en
            en.visibility = if (showEn && pg.en.isNotEmpty()) View.VISIBLE else View.INVISIBLE
            counter.text = "${i + 1} / ${s.pages.size}"
            prev.alpha = if (i == 0) 0.35f else 1f
            next.text = if (i == last) label("おわり", "Finish") else label("つぎ →", "Next")
            enBtn.text = label("えいご", if (showEn) "English on" else "English off")
        }

        prev.setOnClickListener {
            if (i > 0) {
                i--
                render()
            }
        }
        next.setOnClickListener {
            if (i < last) {
                i++
                render()
            } else {
                showList(s.id)
            }
        }
        enBtn.setOnClickListener {
            showEn = !showEn
            store.showEnglish = showEn
            render()
        }

        val bar = LinearLayout(this)
        bar.orientation = LinearLayout.HORIZONTAL
        fun slot(v: View) =
            bar.addView(v, lp(0, U.px(76f), 1f).apply { setMargins(U.px(6f), 0, U.px(6f), 0) })

        slot(prev)
        if (s.mine) {
            val edit = button(this, label("へんしゅう", "Edit")) { showWriter(s) }
            val del = button(this, label("けす", "Delete")) {}
            var armed = false
            del.setOnClickListener {
                if (!armed) {
                    armed = true
                    del.text = label("ほんとうに？", "Really? Press OK")
                } else {
                    store.saveUserStories(store.userStories().filter { it.id != s.id })
                    toast("けしました (Deleted)")
                    showList(null)
                }
            }
            del.setOnFocusChangeListener { _, has ->
                if (!has && armed) {
                    armed = false
                    del.text = label("けす", "Delete")
                }
            }
            slot(edit)
            slot(del)
        } else {
            slot(enBtn)
        }
        slot(next)
        p.addView(bar, lp(MATCH_PARENT, U.px(76f)))

        render()
        show(p, { showList(s.id) }, next)
    }

    // ---------------------------------------------------------------- Writer

    private fun showWriter(existing: Story?) {
        val title = StringBuilder(existing?.title ?: "")
        val body = StringBuilder(existing?.body ?: "")
        var active = if (existing == null) 0 else 1 // 0 = title box, 1 = story box

        val titleBox = tv(this, "", 26f, Pal.INK)
        val bodyBox = tv(this, "", 28f, Pal.INK)
        titleBox.maxLines = 1
        titleBox.gravity = Gravity.CENTER_VERTICAL
        titleBox.setPadding(U.px(16f), U.px(4f), U.px(16f), U.px(4f))
        bodyBox.setPadding(U.px(16f), U.px(6f), U.px(16f), U.px(6f))
        titleBox.isFocusable = true
        bodyBox.isFocusable = true

        fun styleFields() {
            titleBox.background = fieldBg(active == 0)
            bodyBox.background = fieldBg(active == 1)
        }

        fun render() {
            titleBox.text = shown(title, "だいめい (Title)", active == 0)
            bodyBox.text = shown(body, "ここに おはなしを かいてね (Write your story here)", active == 1)
            val l = bodyBox.layout
            if (l != null && bodyBox.height > 0) {
                val visible = bodyBox.height - bodyBox.paddingTop - bodyBox.paddingBottom
                bodyBox.scrollTo(0, maxOf(0, l.getLineTop(l.lineCount) - visible))
            }
        }

        titleBox.setOnFocusChangeListener { _, has ->
            if (has) {
                active = 0
                styleFields()
                render()
            }
        }
        bodyBox.setOnFocusChangeListener { _, has ->
            if (has) {
                active = 1
                styleFields()
                render()
            }
        }

        fun current() = if (active == 0) title else body

        fun type(c: String) {
            val b = current()
            if (b.length < (if (active == 0) 20 else 3000)) b.append(c)
            render()
        }

        fun change(f: (Char) -> Char) {
            val b = current()
            if (b.isNotEmpty()) b.setCharAt(b.length - 1, f(b[b.length - 1]))
            render()
        }

        fun space() {
            val b = current()
            if (b.isNotEmpty() && b[b.length - 1] != ' ' && b[b.length - 1] != '\n') type(" ")
        }

        fun newline() {
            if (active == 0) {
                active = 1
                styleFields()
                render()
            } else if (body.isNotEmpty() && body[body.length - 1] != '\n') {
                type("\n")
            }
        }

        fun backspace() {
            val b = current()
            if (b.isNotEmpty()) b.setLength(b.length - 1)
            render()
        }

        fun commit(): Story? {
            val text = body.toString().trim()
            if (text.isEmpty()) return null
            var name = title.toString().trim()
            if (name.isEmpty()) name = text.lineSequence().first().trim().take(12)
            val story = Story.fromUser(existing?.id ?: System.currentTimeMillis(), name, text)
            val all = store.userStories()
            val at = all.indexOfFirst { it.id == story.id }
            if (at >= 0) all[at] = story else all.add(story)
            store.saveUserStories(all)
            return story
        }

        fun leave() {
            val saved = commit()
            if (saved != null) {
                toast("ほぞん しました (Saved)")
                showList(saved.id)
            } else if (existing != null) {
                showList(existing.id)
            } else {
                showHome()
            }
        }

        // keyboard
        val m = U.px(3f)
        fun cell() = LinearLayout.LayoutParams(0, MATCH_PARENT, 1f).apply { setMargins(m, m, m, m) }
        fun key(text: CharSequence, size: Float = 24f, click: () -> Unit): TextView {
            val k = button(this, text, size, Pal.PANEL, click)
            k.setPadding(0, 0, 0, 0)
            return k
        }

        var firstKey: View? = null
        val kbd = LinearLayout(this)
        kbd.orientation = LinearLayout.VERTICAL
        for (line in GRID) {
            val row = LinearLayout(this)
            row.orientation = LinearLayout.HORIZONTAL
            for (ch in line) {
                if (ch == '.') {
                    row.addView(Space(this), cell())
                } else {
                    val k = key(ch.toString()) { type(ch.toString()) }
                    if (firstKey == null) firstKey = k
                    row.addView(k, cell())
                }
            }
            kbd.addView(row, lp(MATCH_PARENT, U.px(42f)))
        }
        val marks = LinearLayout(this)
        marks.orientation = LinearLayout.HORIZONTAL
        marks.addView(key("か→が", 18f) { change { Kana.voice(it) } }, cell())
        marks.addView(key("は→ぱ", 18f) { change { Kana.semi(it) } }, cell())
        marks.addView(key("つ→っ", 18f) { change { Kana.small(it) } }, cell())
        for (c in listOf("ー", "、", "。", "！", "？", "「", "」")) {
            marks.addView(key(c) { type(c) }, cell())
        }
        kbd.addView(marks, lp(MATCH_PARENT, U.px(42f)))

        // actions
        val side = LinearLayout(this)
        side.orientation = LinearLayout.VERTICAL
        fun act(text: CharSequence, fill: Int, click: () -> Unit) {
            side.addView(
                button(this, text, 22f, fill, click),
                lp(MATCH_PARENT, 0, 1f).apply { setMargins(m, m, m, m) }
            )
        }
        act(label("くうはく", "Space"), Pal.PANEL) { space() }
        act(label("かいぎょう", "New line"), Pal.PANEL) { newline() }
        act(label("けす", "Delete"), Pal.PANEL) { backspace() }
        act(label("ほぞん", "Save"), Pal.PRIMARY) {
            val saved = commit()
            if (saved == null) {
                toast("まず おはなしを かいてね (Write your story first)")
            } else {
                toast("ほぞん しました (Saved)")
                showReader(saved, 0)
            }
        }

        val p = page()
        p.addView(titleBox, lp(MATCH_PARENT, U.px(42f)))
        p.addView(bodyBox, lp(MATCH_PARENT, U.px(132f)).apply { topMargin = U.px(8f) })
        val lower = LinearLayout(this)
        lower.orientation = LinearLayout.HORIZONTAL
        lower.addView(kbd, lp(0, WRAP_CONTENT, 1f))
        lower.addView(side, lp(U.px(190f), MATCH_PARENT).apply { leftMargin = U.px(8f) })
        p.addView(lower, lp(MATCH_PARENT, WRAP_CONTENT).apply { topMargin = U.px(6f) })
        p.addView(
            tv(this, WRITER_HINT, 16f, Pal.MUTED),
            lp(WRAP_CONTENT, WRAP_CONTENT).apply { topMargin = U.px(4f) }
        )

        styleFields()
        render()
        show(p, { leave() }, firstKey)
    }
}
