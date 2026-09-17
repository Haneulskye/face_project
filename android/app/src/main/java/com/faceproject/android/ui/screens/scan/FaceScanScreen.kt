package com.faceproject.android.ui.screens.scan

import android.Manifest
import androidx.camera.core.ImageCapture
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipPath
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
import kotlinx.coroutines.delay

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

    // 인증 성공 시 얼굴+홍채 결과를 잠깐 보여준 뒤 다음 화면으로 이동한다.
    val successState = viewModel.uiState as? FaceScanUiState.Success
    LaunchedEffect(successState) {
        if (successState != null) {
            delay(700)
            onAuthenticated(successState.name)
            viewModel.resetError()
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

                    // FaceID 스타일 가이드: 얼굴(과 눈)을 맞춰야 하는 타원 표시.
                    FaceAlignmentGuideOverlay(modifier = Modifier.fillMaxSize())

                    Text(
                        text = "타원 안에 얼굴과 눈이 오도록 맞춰주세요",
                        color = Color.White,
                        textAlign = TextAlign.Center,
                        modifier = Modifier
                            .fillMaxWidth()
                            .align(Alignment.BottomCenter)
                            .padding(bottom = 28.dp)
                    )

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
                                Text("얼굴+홍채 인식 중...", color = Color.White)
                            }
                        }
                    }

                    if (successState != null) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(Color.Black.copy(alpha = 0.55f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                MatchRow(label = "얼굴 인증", matched = true)
                                Spacer(modifier = Modifier.height(8.dp))
                                MatchRow(label = "홍채 인증", matched = successState.irisMatched)
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
                    enabled = imageCapture != null &&
                        viewModel.uiState !is FaceScanUiState.Authenticating &&
                        viewModel.uiState !is FaceScanUiState.Success,
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

/**
 * FaceID처럼 카메라 미리보기 위에 얼굴을 맞출 타원 가이드를 그린다.
 * 실시간으로 얼굴 위치를 감지하지는 않는 정적 가이드다 — 사용자가
 * 눈으로 보고 맞추는 용도.
 */
@Composable
private fun FaceAlignmentGuideOverlay(modifier: Modifier = Modifier) {
    Canvas(modifier = modifier) {
        val ovalWidth = size.width * 0.62f
        val ovalHeight = ovalWidth * 1.35f
        val left = (size.width - ovalWidth) / 2f
        val top = (size.height - ovalHeight) / 2f

        val ovalPath = Path().apply {
            addOval(androidx.compose.ui.geometry.Rect(left, top, left + ovalWidth, top + ovalHeight))
        }

        clipPath(ovalPath, clipOp = androidx.compose.ui.graphics.ClipOp.Difference) {
            drawRect(color = Color.Black.copy(alpha = 0.45f))
        }

        drawOval(
            color = Color.White,
            topLeft = Offset(left, top),
            size = Size(ovalWidth, ovalHeight),
            style = Stroke(
                width = 4.dp.toPx(),
                pathEffect = PathEffect.dashPathEffect(floatArrayOf(18f, 14f))
            )
        )
    }
}

@Composable
private fun MatchRow(label: String, matched: Boolean) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Surface(
            shape = CircleShape,
            color = if (matched) Color(0xFF2E7D32) else Color(0xFF9E9E9E)
        ) {
            Icon(
                imageVector = if (matched) Icons.Default.Check else Icons.Default.Close,
                contentDescription = null,
                tint = Color.White,
                modifier = Modifier.padding(4.dp)
            )
        }
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            "$label ${if (matched) "일치" else "불일치"}",
            color = Color.White,
            style = MaterialTheme.typography.bodyLarge
        )
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
