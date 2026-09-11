package com.faceproject.android.navigation

import java.net.URLEncoder

object Routes {
    const val MAIN = "main"
    const val SCAN = "scan"
    const val REGISTER = "register"

    const val REGISTER_SUCCESS = "register_success/{name}/{nickname}"
    fun registerSuccess(name: String, nickname: String) =
        "register_success/${name.urlEncoded()}/${nickname.urlEncoded()}"

    const val PROFILE = "profile/{name}"
    fun profile(name: String) = "profile/${name.urlEncoded()}"

    const val HISTORY = "history/{name}"
    fun history(name: String) = "history/${name.urlEncoded()}"

    const val ARG_NAME = "name"
    const val ARG_NICKNAME = "nickname"

    private fun String.urlEncoded() = URLEncoder.encode(this, "UTF-8")
}
