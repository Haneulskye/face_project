package com.faceproject.android.ui.screens.scan

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.faceproject.android.data.ApiResult
import com.faceproject.android.data.AuthRepository
import kotlinx.coroutines.launch
import java.io.File

sealed class FaceScanUiState {
    data object Idle : FaceScanUiState()
    data object Authenticating : FaceScanUiState()
    data class Error(val message: String) : FaceScanUiState()
}

class FaceScanViewModel(
    private val repository: AuthRepository = AuthRepository()
) : ViewModel() {

    var uiState by mutableStateOf<FaceScanUiState>(FaceScanUiState.Idle)
        private set

    fun authenticate(
        imageFile: File,
        onRegisteredUser: (name: String) -> Unit,
        onUnregisteredFace: () -> Unit
    ) {
        uiState = FaceScanUiState.Authenticating

        viewModelScope.launch {
            when (val result = repository.authenticateFace(imageFile)) {
                is ApiResult.Success -> {
                    val response = result.data
                    when {
                        response.authenticated && response.name != null -> {
                            uiState = FaceScanUiState.Idle
                            onRegisteredUser(response.name)
                        }

                        response.reason == "face_not_detected" -> {
                            uiState = FaceScanUiState.Error(
                                "얼굴을 인식하지 못했습니다. 정면을 바라보고 다시 촬영해주세요."
                            )
                        }

                        else -> {
                            uiState = FaceScanUiState.Idle
                            onUnregisteredFace()
                        }
                    }
                }

                is ApiResult.Error -> {
                    uiState = FaceScanUiState.Error(result.message)
                }
            }
        }
    }

    fun resetError() {
        uiState = FaceScanUiState.Idle
    }
}
