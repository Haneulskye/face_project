package com.faceproject.android.network.dto

import com.faceproject.android.model.UserProfile
import com.google.gson.annotations.SerializedName

data class FaceAuthResponse(
    @SerializedName("authenticated") val authenticated: Boolean,
    @SerializedName("name") val name: String?,
    @SerializedName("score") val score: Double,
    @SerializedName("profile") val profile: UserProfile?,
    @SerializedName("reason") val reason: String?,
    @SerializedName("iris") val iris: IrisAuthInfo?
)

/**
 * 얼굴과 같은 사진에서 함께 인식되는 홍채 신호. 보조 지표일 뿐이며
 * 최종 인증 여부(authenticated)는 얼굴 인식 결과만으로 결정된다 —
 * 홍채 모델은 아직 프로토타입 단계라 최종 판정을 좌우하지 않는다.
 */
data class IrisAuthInfo(
    @SerializedName("matched") val matched: Boolean,
    @SerializedName("score") val score: Double,
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
    @SerializedName("status") val status: String?,
    @SerializedName("source") val source: String? = null
)

data class HeartRateHistoryResponse(
    @SerializedName("available") val available: Boolean,
    @SerializedName("records") val records: List<HeartRateRecord>
)

data class HeartRateRecord(
    @SerializedName("bpm") val bpm: Double,
    @SerializedName("status") val status: String,
    @SerializedName("measured_at") val measuredAt: String,
    @SerializedName("source") val source: String? = null
)

/** Parsed shape of FastAPI's default error body: {"detail": "..."} */
data class ApiErrorBody(
    @SerializedName("detail") val detail: String?
)
