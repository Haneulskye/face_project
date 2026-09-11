package com.faceproject.android.ui.screens.profile

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.faceproject.android.data.ApiResult
import com.faceproject.android.data.AuthRepository
import com.faceproject.android.model.HeartRateStatus
import com.faceproject.android.model.UserProfile
import kotlinx.coroutines.launch

data class HeartRateUiState(
    val available: Boolean = false,
    val bpm: Double? = null,
    val status: HeartRateStatus = HeartRateStatus.UNKNOWN,
    val isMeasuring: Boolean = false
)

sealed class ProfileUiState {
    data object Loading : ProfileUiState()
    data class Loaded(val profile: UserProfile) : ProfileUiState()
    data class Error(val message: String) : ProfileUiState()
}

class ProfileViewModel(
    private val repository: AuthRepository = AuthRepository()
) : ViewModel() {

    var uiState by mutableStateOf<ProfileUiState>(ProfileUiState.Loading)
        private set

    var heartRate by mutableStateOf(HeartRateUiState())
        private set

    fun load(name: String) {
        uiState = ProfileUiState.Loading

        viewModelScope.launch {
            when (val result = repository.getUser(name)) {
                is ApiResult.Success -> uiState = ProfileUiState.Loaded(result.data)
                is ApiResult.Error -> uiState = ProfileUiState.Error(result.message)
            }
        }

        viewModelScope.launch {
            when (val result = repository.latestHeartRate(name)) {
                is ApiResult.Success -> {
                    val bpm = result.data.bpm
                    heartRate = HeartRateUiState(
                        available = result.data.available,
                        bpm = bpm,
                        status = bpm?.let { HeartRateStatus.fromBpm(it) } ?: HeartRateStatus.UNKNOWN
                    )
                }
                // Heart-rate is best-effort; a failure here shouldn't block the profile screen.
                is ApiResult.Error -> heartRate = HeartRateUiState()
            }
        }
    }

    fun measure(name: String) {
        heartRate = heartRate.copy(isMeasuring = true)

        viewModelScope.launch {
            val result = repository.measureHeartRate(name)
            heartRate = when (result) {
                is ApiResult.Success -> {
                    val bpm = result.data.bpm
                    HeartRateUiState(
                        available = result.data.available,
                        bpm = bpm,
                        status = bpm?.let { HeartRateStatus.fromBpm(it) } ?: HeartRateStatus.UNKNOWN
                    )
                }
                is ApiResult.Error -> heartRate.copy(isMeasuring = false)
            }
        }
    }
}
