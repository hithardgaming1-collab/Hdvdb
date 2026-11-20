package com.hiraganatv.stories

/** Helpers for the on-screen hiragana keyboard: each changes the last typed letter. */
object Kana {
    private const val PLAIN = "かきくけこさしすせそたちつてとはひふへほ"
    private const val VOICED = "がぎぐげござじずぜぞだぢづでどばびぶべぼ"
    private const val H_PLAIN = "はひふへほ"
    private const val H_SEMI = "ぱぴぷぺぽ"
    private const val BIG = "あいうえおつやゆよ"
    private const val SMALL = "ぁぃぅぇぉっゃゅょ"

    /** か→が, が→か, ぱ→ば */
    fun voice(c: Char): Char {
        var i = PLAIN.indexOf(c)
        if (i >= 0) return VOICED[i]
        i = VOICED.indexOf(c)
        if (i >= 0) return PLAIN[i]
        i = H_SEMI.indexOf(c)
        if (i >= 0) return VOICED[PLAIN.indexOf(H_PLAIN[i])]
        return c
    }

    /** は→ぱ, ぱ→は, ば→ぱ */
    fun semi(c: Char): Char {
        var i = H_PLAIN.indexOf(c)
        if (i >= 0) return H_SEMI[i]
        i = H_SEMI.indexOf(c)
        if (i >= 0) return H_PLAIN[i]
        i = VOICED.indexOf(c)
        if (i >= 0) {
            val j = H_PLAIN.indexOf(PLAIN[i])
            if (j >= 0) return H_SEMI[j]
        }
        return c
    }

    /** つ→っ, や→ゃ, あ→ぁ ... and back */
    fun small(c: Char): Char {
        var i = BIG.indexOf(c)
        if (i >= 0) return SMALL[i]
        i = SMALL.indexOf(c)
        if (i >= 0) return BIG[i]
        return c
    }
}
