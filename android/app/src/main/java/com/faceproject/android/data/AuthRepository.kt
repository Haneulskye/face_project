package com.faceproject.android.data

import com.faceproject.android.model.UserProfile
import com.faceproject.android.network.ApiService
import com.faceproject.android.network.NetworkModule
import com.faceproject.android.network.dto.ApiErrorBody
import com.faceproject.android.network.dto.FaceAuthResponse
import com.faceproject.android.network.dto.HeartRateHistoryResponse
import com.faceproject.android.network.dto.HeartRateResponse
import com.faceproject.android.network.dto.RegisterResponse
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.HttpException
import java.io.File
import java.io.IOException

class AuthRepository(
    private val api: ApiService = NetworkModule.apiService
) {

    suspend fun authenticateFace(imageFile: File): ApiResult<FaceAuthResponse> =
        safeCall { api.authenticateFace(imagePart(imageFile)) }

    suspend fun registerUser(
        name: String,
        age: Int,
        nickname: String,
        gender: String,
        heightCm: Double,
        weightKg: Double?,
        consent: Boolean,
        imageFile: File
    ): ApiResult<RegisterResponse> = safeCall {
        api.registerUser(
            name = name.toPlainRequestBody(),
            age = age.toString().toPlainRequestBody(),
            nickname = nickname.toPlainRequestBody(),
            gender = gender.toPlainRequestBody(),
            heightCm = heightCm.toString().toPlainRequestBody(),
            weightKg = weightKg?.toString()?.toPlainRequestBody(),
            consent = consent.toString().toPlainRequestBody(),
            image = imagePart(imageFile)
        )
    }

    suspend fun getUser(name: String): ApiResult<UserProfile> =
        safeCall { api.getUser(name) }

    suspend fun latestHeartRate(name: String): ApiResult<HeartRateResponse> =
        safeCall { api.latestHeartRate(name) }

    suspend fun heartRateHistory(name: String): ApiResult<HeartRateHistoryResponse> =
        safeCall { api.heartRateHistory(name) }

    suspend fun measureHeartRate(name: String): ApiResult<HeartRateResponse> =
        safeCall { api.measureHeartRate(name) }

    private fun imagePart(file: File): MultipartBody.Part {
        val body = file.asRequestBody("image/jpeg".toMediaType())
        return MultipartBody.Part.createFormData("image", file.name, body)
    }

    private fun String.toPlainRequestBody() = toRequestBody("text/plain".toMediaType())

    private suspend fun <T> safeCall(block: suspend () -> T): ApiResult<T> =
        withContext(Dispatchers.IO) {
            try {
                ApiResult.Success(block())
            } catch (e: HttpException) {
                ApiResult.Error(e.toUserMessage())
            } catch (e: IOException) {
                ApiResult.Error("서버에 연결할 수 없습니다. 네트워크와 서버 주소를 확인해주세요.")
            } catch (e: Exception) {
                ApiResult.Error(e.message ?: "알 수 없는 오류가 발생했습니다.")
            }
        }

    private fun HttpException.toUserMessage(): String {
        val detail = try {
            response()?.errorBody()?.string()?.let {
                Gson().fromJson(it, ApiErrorBody::class.java).detail
            }
        } catch (e: Exception) {
            null
        }

        return when (detail) {
            "face_not_detected" -> "얼굴을 인식하지 못했습니다. 정면을 바라보고 다시 시도해주세요."
            "consent_required" -> "개인정보 수집에 동의해야 등록할 수 있습니다."
            "age_restricted" -> "만 14세 미만은 가입할 수 없습니다."
            "name_already_registered" -> "이미 등록된 사용자 ID입니다."
            "user_not_found" -> "등록된 사용자 정보를 찾을 수 없습니다."
            "invalid_image" -> "이미지를 처리할 수 없습니다. 다시 촬영해주세요."
            else -> detail ?: "요청을 처리하지 못했습니다. (HTTP ${code()})"
        }
    }
}
