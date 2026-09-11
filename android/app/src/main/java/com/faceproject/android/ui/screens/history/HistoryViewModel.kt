package com.faceproject.android.ui.screens.history

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.faceproject.android.data.ApiResult
import com.faceproject.android.data.AuthRepository
import com.faceproject.android.network.dto.HeartRateRecord
import kotlinx.coroutines.launch

sealed class HistoryUiState {
    data object Loading : HistoryUiState()
    data class Loaded(val available: Boolean, val records: List<HeartRateRecord>) : HistoryUiState()
    data class Error(val message: String) : HistoryUiState()
}

class HistoryViewModel(
    private val repository: AuthRepository = AuthRepository()
) : ViewModel() {

    var uiState by mutableStateOf<HistoryUiState>(HistoryUiState.Loading)
        private set

    fun load(name: String) {
        uiState = HistoryUiState.Loading

        viewModelScope.launch {
            uiState = when (val result = repository.heartRateHistory(name)) {
                is ApiResult.Success -> HistoryUiState.Loaded(result.data.available, result.data.records)
                is ApiResult.Error -> HistoryUiState.Error(result.message)
            }
        }
    }
}
