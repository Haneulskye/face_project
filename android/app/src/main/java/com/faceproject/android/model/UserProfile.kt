package com.faceproject.android.model

import com.google.gson.annotations.SerializedName

data class UserProfile(
    @SerializedName("name") val name: String,
    @SerializedName("age") val age: Int,
    @SerializedName("nickname") val nickname: String?,
    @SerializedName("gender") val gender: String,
    @SerializedName("height_cm") val heightCm: Double,
    @SerializedName("weight_kg") val weightKg: Double?,
    @SerializedName("registered_at") val registeredAt: String
)
