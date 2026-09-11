package com.faceproject.android.network

import com.faceproject.android.model.UserProfile
import com.faceproject.android.network.dto.FaceAuthResponse
import com.faceproject.android.network.dto.HeartRateHistoryResponse
import com.faceproject.android.network.dto.HeartRateResponse
import com.faceproject.android.network.dto.RegisterResponse
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

interface ApiService {

    @Multipart
    @POST("auth/face")
    suspend fun authenticateFace(
        @Part image: MultipartBody.Part
    ): FaceAuthResponse

    @Multipart
    @POST("users/register")
    suspend fun registerUser(
        @Part("name") name: RequestBody,
        @Part("age") age: RequestBody,
        @Part("nickname") nickname: RequestBody,
        @Part("gender") gender: RequestBody,
        @Part("height_cm") heightCm: RequestBody,
        @Part("weight_kg") weightKg: RequestBody?,
        @Part("consent") consent: RequestBody,
        @Part image: MultipartBody.Part
    ): RegisterResponse

    @GET("users/{name}")
    suspend fun getUser(@Path("name") name: String): UserProfile

    @GET("users/{name}/heart-rate/latest")
    suspend fun latestHeartRate(@Path("name") name: String): HeartRateResponse

    @GET("users/{name}/heart-rate/history")
    suspend fun heartRateHistory(@Path("name") name: String): HeartRateHistoryResponse

    @POST("users/{name}/heart-rate/measure")
    suspend fun measureHeartRate(@Path("name") name: String): HeartRateResponse
}
