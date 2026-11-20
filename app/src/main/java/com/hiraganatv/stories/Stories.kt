package com.hiraganatv.stories

/** One screen of a story: Japanese (hiragana only) and its English meaning. */
data class Page(val jp: String, val en: String = "")

data class Story(
    val id: Long,
    val title: String,
    val titleEn: String,
    val level: String,
    val pages: List<Page>,
    val mine: Boolean = false,
    val body: String = ""
) {
    companion object {
        fun fromUser(id: Long, title: String, body: String) =
            Story(id, title, "My story", "わたしの", splitPages(body), true, body)
    }
}

/** A written story becomes one page per line; long lines are cut after a sentence end. */
fun splitPages(body: String): List<Page> {
    val out = mutableListOf<Page>()
    for (line in body.split('\n')) {
        val t = line.trim()
        if (t.isEmpty()) continue
        if (t.length <= 60) {
            out.add(Page(t))
            continue
        }
        val sb = StringBuilder()
        var idx = 0
        while (idx < t.length) {
            val ch = t[idx]
            sb.append(ch)
            idx++
            if ((ch == '。' || ch == '！' || ch == '？') && sb.length >= 30) {
                if (idx < t.length && t[idx] == '」') {
                    sb.append('」')
                    idx++
                }
                out.add(Page(sb.toString().trim()))
                sb.setLength(0)
            }
        }
        if (sb.isNotBlank()) out.add(Page(sb.toString().trim()))
    }
    if (out.isEmpty()) out.add(Page(""))
    return out
}

/**
 * Built-in beginner stories. Every Japanese line is hiragana only (no kanji, no katakana),
 * polite です/ます style, with spaces between phrases.
 * To add a story, copy one block and give it a new unique id.
 */
object Library {
    private fun p(jp: String, en: String) = Page(jp, en)

    val all: List<Story> = listOf(
        Story(
            1, "わたしの あさ", "My Morning", "Beginner 1", listOf(
                p("わたしの なまえは はなこです。", "My name is Hanako."),
                p("まいあさ ろくじに おきます。", "Every morning I get up at six o’clock."),
                p("あさごはんを たべます。 おちゃを のみます。", "I eat breakfast. I drink tea."),
                p("それから はを みがきます。", "Then I brush my teeth."),
                p("しちじに うちを でます。", "At seven o’clock I leave the house."),
                p("がっこうへ いきます。 「いってきます！」", "I go to school. “I’m off!”"),
                p("「いってらっしゃい！」と おかあさんが いいます。", "“Have a good day!” says my mother.")
            )
        ),
        Story(
            2, "ねこの たま", "The Cat Tama", "Beginner 1", listOf(
                p("うちに ねこが います。", "There is a cat at my house."),
                p("なまえは たまです。", "Its name is Tama."),
                p("たまは しろい ねこです。 とても ちいさいです。", "Tama is a white cat. It is very small."),
                p("たまは さかなが すきです。", "Tama likes fish."),
                p("まいにち さかなを たべます。", "Every day it eats fish."),
                p("よるは わたしの そばで ねます。", "At night it sleeps next to me."),
                p("たまは とても かわいいです！", "Tama is so cute!")
            )
        ),
        Story(
            3, "こうえんで", "At the Park", "Beginner 1", listOf(
                p("きょうは にちようびです。", "Today is Sunday."),
                p("てんきが いいです。", "The weather is nice."),
                p("わたしは いぬと こうえんへ いきます。", "I go to the park with my dog."),
                p("いぬの なまえは ころです。", "The dog’s name is Koro."),
                p("こうえんに おおきい きが あります。", "There is a big tree in the park."),
                p("ころは きの そばで あそびます。", "Koro plays near the tree."),
                p("わたしと ころは とても たのしいです。", "Koro and I are having a lot of fun.")
            )
        ),
        Story(
            4, "うさぎと かめ", "The Hare and the Tortoise", "Beginner 2", listOf(
                p("むかしむかし、うさぎと かめが いました。", "Long, long ago, there lived a hare and a tortoise."),
                p("うさぎは はやいです。 かめは おそいです。", "The hare is fast. The tortoise is slow."),
                p("かめは いいました。 「いっしょに かけっこを しましょう！」", "The tortoise said, “Let’s race together!”"),
                p("うさぎは はしりました。 かめは ゆっくり あるきました。", "The hare ran. The tortoise walked slowly."),
                p("うさぎは きの そばで ねました。", "The hare slept near a tree."),
                p("かめは ずっと あるきました。", "The tortoise kept on walking."),
                p("かめが かちました！ うさぎは びっくり しました。", "The tortoise won! The hare was surprised.")
            )
        ),
        Story(
            5, "わたしの かぞく", "My Family", "Beginner 2", listOf(
                p("わたしの かぞくは よにんです。", "There are four people in my family."),
                p("おとうさんと おかあさんと いもうとと わたしです。", "My father, my mother, my little sister, and me."),
                p("おとうさんは せんせいです。", "My father is a teacher."),
                p("おかあさんは りょうりが じょうずです。", "My mother is good at cooking."),
                p("いもうとは ごさいです。", "My little sister is five years old."),
                p("ごご ろくじに みんなで ばんごはんを たべます。", "At six in the evening, we all eat dinner together."),
                p("わたしは かぞくが だいすきです。", "I love my family very much.")
            )
        ),
        Story(
            6, "あめの ひ", "A Rainy Day", "Beginner 2", listOf(
                p("きょうは あめです。", "Today it is raining."),
                p("わたしは かさを もって でかけます。", "I take an umbrella and go out."),
                p("みちに ちいさい かえるが います。", "There is a small frog on the road."),
                p("かえるは あめが すきです。", "The frog likes the rain."),
                p("かえるは とても げんきです。", "The frog is very lively."),
                p("わたしも すこし うれしく なりました。", "I became a little happy too."),
                p("あめの おとは すてきです。", "The sound of the rain is lovely.")
            )
        )
    )
}
