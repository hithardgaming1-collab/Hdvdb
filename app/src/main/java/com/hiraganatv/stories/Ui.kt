package com.hiraganatv.stories

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.StateListDrawable
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.RelativeSizeSpan
import android.util.TypedValue
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView

/** Classroom palette: green blackboard, chalk, notebook paper with blue-black ink. */
object Pal {
    val BOARD_TOP = Color.parseColor("#2B4538")
    val BOARD_BOTTOM = Color.parseColor("#1B2E26")
    val PANEL = Color.parseColor("#36594A")
    val CHALK = Color.parseColor("#F4F2E9")
    val YELLOW = Color.parseColor("#F5D547")
    val BLUE = Color.parseColor("#8EC3EA")
    val PAPER = Color.parseColor("#F7F4EA")
    val INK = Color.parseColor("#1E2A52")
    val SUB_INK = Color.parseColor("#5A6485")
    val PRIMARY = Color.parseColor("#B8483E")
    val MUTED = Color.parseColor("#B8C9BE")
    val ON_YELLOW = Color.parseColor("#1B2E26")
    val FOCUS_SUB = Color.parseColor("#3B4A35")
    val HINT = Color.parseColor("#8C9486")
}

/**
 * All sizes are "units" of a 960 x 540 design canvas that is stretched to the real screen,
 * so the layout looks the same on a 32" HD or Full HD TV whatever density the TV reports.
 */
object U {
    private var k = 1f

    fun init(c: Context) {
        val m = c.resources.displayMetrics
        k = maxOf(m.widthPixels, m.heightPixels) / 960f
    }

    fun px(v: Float): Int = (v * k + 0.5f).toInt()

    fun text(t: TextView, size: Float) = t.setTextSize(TypedValue.COMPLEX_UNIT_PX, size * k)
}

fun rounded(fill: Int, radius: Float, stroke: Int = 0, strokeW: Float = 0f): GradientDrawable {
    val g = GradientDrawable()
    g.setColor(fill)
    g.cornerRadius = U.px(radius).toFloat()
    if (strokeW > 0f) g.setStroke(U.px(strokeW), stroke)
    return g
}

/** Normal colour, and a chalk-yellow highlight with a white edge when focused by the remote. */
fun focusBg(normal: Int, radius: Float = 14f): StateListDrawable {
    val d = StateListDrawable()
    d.addState(intArrayOf(android.R.attr.state_focused), rounded(Pal.YELLOW, radius, Pal.CHALK, 3f))
    d.addState(intArrayOf(), rounded(normal, radius))
    return d
}

fun stateColor(normal: Int, focused: Int) = ColorStateList(
    arrayOf(intArrayOf(android.R.attr.state_focused), intArrayOf()),
    intArrayOf(focused, normal)
)

/** Japanese label with a smaller English line underneath. */
fun label(jp: String, en: String): CharSequence {
    if (en.isEmpty()) return jp
    val s = SpannableStringBuilder(jp)
    val start = s.length
    s.append('\n').append(en)
    s.setSpan(RelativeSizeSpan(0.7f), start, s.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    return s
}

fun tv(
    c: Context,
    text: CharSequence,
    size: Float,
    color: Int = Pal.CHALK,
    bold: Boolean = false,
    center: Boolean = false
): TextView {
    val t = TextView(c)
    t.text = text
    t.setTextColor(color)
    U.text(t, size)
    if (bold) t.typeface = Typeface.DEFAULT_BOLD
    if (center) t.gravity = Gravity.CENTER
    return t
}

fun button(
    c: Context,
    text: CharSequence,
    size: Float = 26f,
    fill: Int = Pal.PANEL,
    click: () -> Unit
): TextView {
    val t = tv(c, text, size, Pal.CHALK, bold = true, center = true)
    t.setTextColor(stateColor(Pal.CHALK, Pal.ON_YELLOW))
    t.isFocusable = true
    t.isClickable = true
    t.setPadding(U.px(10f), U.px(4f), U.px(10f), U.px(4f))
    t.background = focusBg(fill)
    t.setOnClickListener { click() }
    return t
}

fun lp(w: Int, h: Int, weight: Float = 0f) = LinearLayout.LayoutParams(w, h, weight)

/** Writing-box content: the text (or a grey hint when empty) plus a cursor in the active box. */
fun shown(buf: CharSequence, hint: String, cursor: Boolean): CharSequence {
    val s = SpannableStringBuilder()
    if (buf.isEmpty()) {
        if (cursor) {
            s.append("|")
            s.setSpan(ForegroundColorSpan(Pal.PRIMARY), 0, 1, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        }
        val a = s.length
        s.append(hint)
        s.setSpan(ForegroundColorSpan(Pal.HINT), a, s.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    } else {
        s.append(buf)
        if (cursor) {
            val a = s.length
            s.append("|")
            s.setSpan(ForegroundColorSpan(Pal.PRIMARY), a, a + 1, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        }
    }
    return s
}

/** Paper box for the title / story: yellow edge when the remote is on it, blue edge when it is the one being typed in. */
fun fieldBg(isActive: Boolean): StateListDrawable {
    val d = StateListDrawable()
    d.addState(intArrayOf(android.R.attr.state_focused), rounded(Pal.PAPER, 14f, Pal.YELLOW, 5f))
    d.addState(
        intArrayOf(),
        if (isActive) rounded(Pal.PAPER, 14f, Pal.BLUE, 3f) else rounded(Pal.PAPER, 14f)
    )
    return d
}
