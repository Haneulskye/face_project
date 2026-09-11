package com.faceproject.android.network.dto

import com.faceproject.android.model.UserProfile
import com.google.gson.annotations.SerializedName

data class FaceAuthResponse(
    @SerializedName("authenticated") val authenticated: Boolean,
    @SerializedName("name") val name: String?,
    @SerializedName("score") val score: Double,
    @SerializedName("profile") val profile: UserProfile?,
    @SerializedName("reason") val reason: String?
)

data class RegisterResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("name") val name: String,
    @SerializedName("profile") val profile: UserProfile
)

data class HeartRateResponse(
    @SerializedName("available") val available: Boolean,
    @SerializedName("bpm") val bpm: Double?,
    @SerializedName("status") val status: String?
)

data class HeartRateHistoryResponse(
    @SerializedName("available") val available: Boolean,
    @SerializedName("records") val records: List<HeartRateRecord>
)

data class HeartRateRecord(
    @SerializedName("bpm") val bpm: Double,
    @SerializedName("status") val status: String,
    @SerializedName("measured_at") val measuredAt: String
)

/** Parsed shape of FastAPI's default error body: {"detail": "..."} */
data class ApiErrorBody(
    @SerializedName("detail") val detail: String?
)
