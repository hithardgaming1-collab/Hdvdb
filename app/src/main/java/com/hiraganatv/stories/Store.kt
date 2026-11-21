package com.hiraganatv.stories

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Saves the stories the viewer writes (kept on the TV, private to the app). */
class Store(ctx: Context) {
    private val prefs = ctx.getSharedPreferences("hiragana_tv", Context.MODE_PRIVATE)

    fun userStories(): MutableList<Story> {
        val out = mutableListOf<Story>()
        try {
            val arr = JSONArray(prefs.getString("mine", "[]"))
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                out.add(Story.fromUser(o.getLong("id"), o.getString("title"), o.getString("body")))
            }
        } catch (e: Exception) {
            // unreadable data: start with an empty list rather than crash
        }
        return out
    }

    fun saveUserStories(list: List<Story>) {
        val arr = JSONArray()
        for (s in list) {
            arr.put(JSONObject().put("id", s.id).put("title", s.title).put("body", s.body))
        }
        prefs.edit().putString("mine", arr.toString()).apply()
    }

    var showEnglish: Boolean
        get() = prefs.getBoolean("en", true)
        set(v) {
            prefs.edit().putBoolean("en", v).apply()
        }
}
