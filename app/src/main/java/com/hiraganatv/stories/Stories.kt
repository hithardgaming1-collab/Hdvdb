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
        ),
        Story(
            7, "どうぶつえん", "The Zoo", "Beginner 2", listOf(
                p("にちようびに、かぞくで どうぶつえんへ いきました。", "On Sunday, my family went to the zoo."),
                p("どうぶつえんには いろいろな どうぶつが いました。", "There were many kinds of animals at the zoo."),
                p("はじめに ぞうを みました。 ぞうは とても おおきかったです。", "First, we saw an elephant. The elephant was very big."),
                p("ぞうは ながい はなで みずを のみました。", "The elephant drank water with its long trunk."),
                p("つぎに さるを みました。 さるは きに のぼって いました。", "Next, we saw a monkey. The monkey was climbing a tree."),
                p("きりんの くびは とても ながかったです。", "The neck of the giraffe was very long."),
                p("ひるごはんに おべんとうを たべました。", "For lunch, we ate bento."),
                p("おべんとうは とても おいしかったです。", "The bento was very delicious."),
                p("そのあと、くまを みました。 くまは ねて いました。", "After that, we saw a bear. The bear was sleeping."),
                p("さいごに さかなを みました。 たくさんの さかなが およいで いました。", "Finally, we saw fish. Many fish were swimming."),
                p("ゆうがた、うちへ かえりました。 つかれましたが、たのしかったです。", "In the evening, we went home. We were tired, but it was fun."),
                p("また どうぶつえんへ いきたいです。", "I want to go to the zoo again.")
            )
        ),
        Story(
            8, "なつやすみ", "Summer Vacation", "Beginner 2", listOf(
                p("なつやすみに、かぞくで うみへ いきました。", "During the summer vacation, my family went to the sea."),
                p("くるまで さんじかん かかりました。", "It took three hours by car."),
                p("うみは とても きれいでした。", "The sea was very beautiful."),
                p("わたしは うみで およぎました。", "I swam in the sea."),
                p("みずは すこし つめたかったです。", "The water was a little cold."),
                p("おとうとは すなで おしろを つくりました。", "My younger brother made a castle in the sand."),
                p("おかあさんは すいかを きりました。", "My mother cut a watermelon."),
                p("みんなで すいかを たべました。 あまくて おいしかったです。", "We all ate the watermelon. It was sweet and delicious."),
                p("よるは はなびを みました。", "At night, we watched the fireworks."),
                p("はなびは おおきい おとが しました。", "The fireworks made a big noise."),
                p("なつやすみは とても たのしかったです。", "The summer vacation was very fun."),
                p("らいねんも また うみへ いきたいです。", "Next year, too, I want to go to the sea again.")
            )
        ),
        Story(
            9, "ゆきの ひ", "A Snowy Day", "Beginner 2", listOf(
                p("あさ、まどを あけました。 そとは まっしろでした。", "In the morning, I opened the window. Outside was all white."),
                p("ゆきが たくさん ふって いました。", "A lot of snow was falling."),
                p("わたしは てぶくろを して そとへ でました。", "I put on gloves and went outside."),
                p("そとは とても さむかったです。", "It was very cold outside."),
                p("ともだちの たろうくんが きました。", "My friend Taro came."),
                p("わたしたちは ゆきだるまを つくりました。", "We made a snowman."),
                p("おおきい ゆきだるまが できました。", "A big snowman was made."),
                p("ゆきだるまに てぶくろを つけました。", "We put gloves on the snowman."),
                p("ゆきだるまは かわいい かおを して いました。", "The snowman had a cute face."),
                p("うちへ かえって、あたたかい おちゃを のみました。", "I went home and drank some warm tea."),
                p("ゆきの ひは たのしかったです。", "The snowy day was fun.")
            )
        ),
        Story(
            10, "ありと きりぎりす", "The Ant and the Grasshopper", "Beginner 3", listOf(
                p("なつの ある ひ、きりぎりすは うたを うたって いました。", "One day in summer, the grasshopper was singing a song."),
                p("あそこで ありたちは はたらいて いました。", "Over there, the ants were working."),
                p("きりぎりすは ありに いいました。 「いっしょに うたいましょう！」", "The grasshopper said to the ants, “Let’s sing together!”"),
                p("でも ありたちは いいました。 「いいえ、わたしたちは はたらきます。」", "But the ants said, “No, we will work.”"),
                p("ありたちは まいにち はたらきました。 たべものを あつめました。", "The ants worked every day. They collected food."),
                p("きりぎりすは まいにち あそびました。", "The grasshopper played every day."),
                p("そして ふゆが きました。 とても さむい ふゆでした。", "Then winter came. It was a very cold winter."),
                p("きりぎりすは たべものが ありませんでした。", "The grasshopper had no food."),
                p("きりぎりすは ありたちの うちへ いきました。", "The grasshopper went to the house of the ants."),
                p("「おなかが すいて います。 たべものを ください。」", "“I am hungry. Please give me some food.”"),
                p("ありたちは いいました。 「いっしょに たべましょう。」", "The ants said, “Let’s eat together.”"),
                p("きりぎりすは いいました。 「ありがとう。 これからは わたしも はたらきます。」", "The grasshopper said, “Thank you. From now on, I will work too.”")
            )
        ),
        Story(
            11, "きたかぜと たいよう", "The North Wind and the Sun", "Beginner 3", listOf(
                p("ある ひ、きたかぜと たいようが はなして いました。", "One day, the North Wind and the Sun were talking."),
                p("きたかぜは いいました。 「わたしは つよいです。」", "The North Wind said, “I am strong.”"),
                p("たいようも いいました。 「わたしも つよいです。」", "The Sun said, “I am strong too.”"),
                p("その とき、たびびとが あるいて きました。", "At that time, a traveler came walking along."),
                p("たびびとは あたたかい うわぎを きて いました。", "The traveler was wearing a warm jacket."),
                p("きたかぜは いいました。 「わたしが つよく ふきます。 たびびとは うわぎを ぬぐでしょう。」", "The North Wind said, “I will blow hard. The traveler will probably take off his jacket.”"),
                p("きたかぜは つよく ふきました。 たびびとは うわぎを しっかり もちました。", "The North Wind blew hard. The traveler held his jacket tightly."),
                p("たいようが いいました。 「つぎは わたしの ばんです。」", "The Sun said, “Next is my turn.”"),
                p("たいようは あたたかい ひかりを だしました。", "The Sun gave out warm light."),
                p("たびびとは あつく なりました。 そして うわぎを ぬぎました。", "The traveler became hot. Then he took off his jacket."),
                p("たいようが かちました！ きたかぜは かなしい かおを しました。", "The Sun won! The North Wind made a sad face.")
            )
        ),
        Story(
            12, "ももたろう", "Momotaro", "Beginner 3", listOf(
                p("むかしむかし、あるところに おじいさんと おばあさんが いました。", "Long, long ago, in a certain place, there lived an old man and an old woman."),
                p("おじいさんは やまへ いきました。 おばあさんは かわへ いきました。", "The old man went to the mountain. The old woman went to the river."),
                p("おばあさんは かわで おおきい ももを みつけました。", "The old woman found a big peach at the river."),
                p("おばあさんは ももを うちへ もって かえりました。", "The old woman took the peach home."),
                p("おじいさんと おばあさんは ももを きりました。", "The old man and the old woman cut the peach."),
                p("ももの なかから おとこのこが でて きました。", "A boy came out of the peach."),
                p("おじいさんと おばあさんは びっくり しました。", "The old man and the old woman were surprised."),
                p("「なまえは ももたろうに しましょう。」", "“Let’s name him Momotaro.”"),
                p("ももたろうは おおきく なりました。 つよい こに なりました。", "Momotaro grew big. He became a strong boy."),
                p("ある ひ、ももたろうは いいました。 「おにの しまへ いきます。」", "One day, Momotaro said, “I will go to the island of the ogres.”"),
                p("おばあさんは おいしい だんごを つくりました。", "The old woman made delicious dumplings."),
                p("ももたろうは いぬと さると きじに あいました。", "Momotaro met a dog, a monkey and a pheasant."),
                p("みんなは だんごを たべて、ももたろうと いっしょに いきました。", "They all ate the dumplings and went together with Momotaro."),
                p("おにの しまで みんなは おにと たたかいました。", "On the island of the ogres, they all fought the ogres."),
                p("ももたろうは とても つよかったです！ おには にげました。", "Momotaro was very strong! The ogres ran away."),
                p("ももたろうは たからものを もって かえりました。", "Momotaro took the treasure and went home."),
                p("おじいさんと おばあさんは とても うれしかったです。 おしまい。", "The old man and the old woman were very happy. The end.")
            )
        )
    )
}
