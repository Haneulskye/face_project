package com.faceproject.android.ui.screens.register

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.faceproject.android.data.ApiResult
import com.faceproject.android.data.AuthRepository
import kotlinx.coroutines.launch
import java.io.File

sealed class RegisterUiState {
    data object Idle : RegisterUiState()
    data object Submitting : RegisterUiState()
    data class Error(val message: String) : RegisterUiState()
}

class RegisterViewModel(
    private val repository: AuthRepository = AuthRepository()
) : ViewModel() {

    var uiState by mutableStateOf<RegisterUiState>(RegisterUiState.Idle)
        private set

    fun submit(
        name: String,
        age: Int,
        nickname: String,
        gender: String,
        heightCm: Double,
        weightKg: Double?,
        consent: Boolean,
        imageFile: File,
        onSuccess: (name: String, nickname: String) -> Unit
    ) {
        uiState = RegisterUiState.Submitting

        viewModelScope.launch {
            when (
                val result = repository.registerUser(
                    name = name,
                    age = age,
                    nickname = nickname,
                    gender = gender,
                    heightCm = heightCm,
                    weightKg = weightKg,
                    consent = consent,
                    imageFile = imageFile
                )
            ) {
                is ApiResult.Success -> {
                    uiState = RegisterUiState.Idle
                    onSuccess(result.data.name, nickname)
                }

                is ApiResult.Error -> {
                    uiState = RegisterUiState.Error(result.message)
                }
            }
        }
    }
}
