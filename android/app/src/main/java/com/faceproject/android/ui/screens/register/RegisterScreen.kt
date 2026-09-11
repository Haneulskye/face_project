package com.faceproject.android.ui.screens.register

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.faceproject.android.data.CapturedImageHolder

private const val MINIMUM_AGE = 14

@Composable
fun RegisterScreen(
    padding: PaddingValues,
    viewModel: RegisterViewModel,
    capturedImageHolder: CapturedImageHolder,
    onRegistered: (name: String, nickname: String) -> Unit
) {
    val imageFile = capturedImageHolder.capturedImageFile

    var name by remember { mutableStateOf("") }
    var age by remember { mutableStateOf("") }
    var nickname by remember { mutableStateOf("") }
    var gender by remember { mutableStateOf("M") }
    var height by remember { mutableStateOf("") }
    var weight by remember { mutableStateOf("") }
    var consent by remember { mutableStateOf(false) }

    val isSubmitting = viewModel.uiState is RegisterUiState.Submitting
    val errorMessage = (viewModel.uiState as? RegisterUiState.Error)?.message

    val ageValue = age.toIntOrNull()
    val isUnderAge = ageValue != null && ageValue < MINIMUM_AGE
    val isWeightValid = weight.isBlank() || weight.toDoubleOrNull() != null

    val isFormValid = name.isNotBlank() &&
        nickname.isNotBlank() &&
        ageValue != null && !isUnderAge &&
        height.toDoubleOrNull() != null &&
        isWeightValid &&
        consent &&
        imageFile != null

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding)
            .verticalScroll(rememberScrollState())
            .padding(24.dp)
    ) {
        Text(
            text = "처음 뵙는 얼굴이에요",
            style = MaterialTheme.typography.titleLarge
        )
        Text(
            text = "정보를 입력하면 다음부터는 얼굴 인식만으로 확인할 수 있어요.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(24.dp))

        OutlinedTextField(
            value = name,
            onValueChange = { name = it },
            label = { Text("이름 (사용자 ID)") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedTextField(
            value = age,
            onValueChange = { age = it.filter { c -> c.isDigit() } },
            label = { Text("나이") },
            singleLine = true,
            isError = isUnderAge,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        if (isUnderAge) {
            Text(
                text = "만 14세 미만은 가입할 수 없습니다.",
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = 4.dp)
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedTextField(
            value = nickname,
            onValueChange = { nickname = it },
            label = { Text("불리고 싶은 닉네임") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text("성별", style = MaterialTheme.typography.labelLarge)
        Row(verticalAlignment = Alignment.CenterVertically) {
            RadioButton(selected = gender == "M", onClick = { gender = "M" })
            Text("남성")
            Spacer(modifier = Modifier.width(16.dp))
            RadioButton(selected = gender == "F", onClick = { gender = "F" })
            Text("여성")
        }

        Row(modifier = Modifier.fillMaxWidth()) {
            OutlinedTextField(
                value = height,
                onValueChange = { height = it.filter { c -> c.isDigit() || c == '.' } },
                label = { Text("키(cm)") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                modifier = Modifier.weight(1f)
            )
            Spacer(modifier = Modifier.width(12.dp))
            OutlinedTextField(
                value = weight,
                onValueChange = { weight = it.filter { c -> c.isDigit() || c == '.' } },
                label = { Text("몸무게(kg, 선택)") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(checked = consent, onCheckedChange = { consent = it })
            Text("개인정보 수집 및 이용에 동의합니다.")
        }

        if (imageFile == null) {
            Text(
                text = "촬영된 얼굴 사진이 없습니다. 이전 화면에서 다시 촬영해주세요.",
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = 8.dp)
            )
        }

        if (errorMessage != null) {
            Text(
                text = errorMessage,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = 8.dp)
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                viewModel.submit(
                    name = name.trim(),
                    age = ageValue!!,
                    nickname = nickname.trim(),
                    gender = gender,
                    heightCm = height.toDouble(),
                    weightKg = weight.toDoubleOrNull(),
                    consent = consent,
                    imageFile = imageFile!!,
                    onSuccess = onRegistered
                )
            },
            enabled = isFormValid && !isSubmitting,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp)
        ) {
            if (isSubmitting) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text("저장하기")
            }
        }
    }
}
