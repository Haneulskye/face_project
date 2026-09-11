package com.faceproject.android.ui.screens.scan

import android.Manifest
import androidx.camera.core.ImageCapture
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.faceproject.android.camera.CameraPreview
import com.faceproject.android.camera.capturePhoto
import com.faceproject.android.data.CapturedImageHolder
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import com.google.accompanist.permissions.shouldShowRationale

@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun FaceScanScreen(
    padding: PaddingValues,
    viewModel: FaceScanViewModel,
    capturedImageHolder: CapturedImageHolder,
    onCapturedForRegistration: () -> Unit,
    onAuthenticated: (name: String) -> Unit
) {
    val context = LocalContext.current
    val cameraPermissionState = rememberPermissionState(Manifest.permission.CAMERA)
    var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }

    LaunchedEffect(Unit) {
        if (!cameraPermissionState.status.isGranted) {
            cameraPermissionState.launchPermissionRequest()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding)
    ) {
        Text(
            text = "얼굴 인식 중",
            style = MaterialTheme.typography.titleLarge,
            modifier = Modifier.padding(16.dp)
        )

        Box(modifier = Modifier.weight(1f)) {
            when {
                cameraPermissionState.status.isGranted -> {
                    CameraPreview(onImageCaptureReady = { imageCapture = it })

                    if (viewModel.uiState is FaceScanUiState.Authenticating) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(Color.Black.copy(alpha = 0.45f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                CircularProgressIndicator(color = Color.White)
                                Spacer(modifier = Modifier.height(12.dp))
                                Text("인증 중...", color = Color.White)
                            }
                        }
                    }
                }

                cameraPermissionState.status.shouldShowRationale -> {
                    PermissionMessage(
                        message = "얼굴 인식을 위해 카메라 권한이 필요합니다.",
                        onRequest = { cameraPermissionState.launchPermissionRequest() }
                    )
                }

                else -> {
                    PermissionMessage(
                        message = "카메라 권한을 허용해주세요.",
                        onRequest = { cameraPermissionState.launchPermissionRequest() }
                    )
                }
            }
        }

        val errorState = viewModel.uiState as? FaceScanUiState.Error
        if (errorState != null) {
            Text(
                text = errorState.message,
                color = MaterialTheme.colorScheme.error,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            )
        }

        Surface(shadowElevation = 8.dp) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                contentAlignment = Alignment.Center
            ) {
                Button(
                    enabled = imageCapture != null && viewModel.uiState !is FaceScanUiState.Authenticating,
                    shape = CircleShape,
                    modifier = Modifier.height(72.dp),
                    onClick = {
                        val capture = imageCapture ?: return@Button
                        viewModel.resetError()
                        capturePhoto(
                            imageCapture = capture,
                            context = context,
                            onSuccess = { file ->
                                viewModel.authenticate(
                                    imageFile = file,
                                    onRegisteredUser = { name -> onAuthenticated(name) },
                                    onUnregisteredFace = {
                                        capturedImageHolder.capturedImageFile = file
                                        onCapturedForRegistration()
                                    }
                                )
                            },
                            onError = {
                                // Surface as a transient error state so the user can retry.
                            }
                        )
                    }
                ) {
                    Text("촬영")
                }
            }
        }
    }
}

@Composable
private fun PermissionMessage(message: String, onRequest: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(message, textAlign = TextAlign.Center)
            Spacer(modifier = Modifier.height(12.dp))
            Button(onClick = onRequest) {
                Text("권한 허용하기")
            }
        }
    }
}
