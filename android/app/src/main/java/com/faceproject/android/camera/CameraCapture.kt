package com.faceproject.android.camera

import android.content.Context
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import java.io.File
import java.text.SimpleDateFormat
import java.util.Locale

/**
 * Live camera preview. Reports the bound [ImageCapture] use case back to the
 * caller via [onImageCaptureReady] so a capture button outside this
 * composable can trigger [capturePhoto].
 */
@Composable
fun CameraPreview(
    modifier: Modifier = Modifier,
    lensFacing: Int = CameraSelector.LENS_FACING_FRONT,
    onImageCaptureReady: (ImageCapture) -> Unit
) {
    val lifecycleOwner = LocalLifecycleOwner.current
    val imageCapture = remember { ImageCapture.Builder().build() }

    AndroidView(
        modifier = modifier.fillMaxSize(),
        factory = { ctx ->
            val previewView = PreviewView(ctx)
            val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)

            cameraProviderFuture.addListener({
                val cameraProvider = cameraProviderFuture.get()

                val preview = Preview.Builder().build().also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }

                val selector = CameraSelector.Builder()
                    .requireLensFacing(lensFacing)
                    .build()

                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    lifecycleOwner,
                    selector,
                    preview,
                    imageCapture
                )

                onImageCaptureReady(imageCapture)
            }, ContextCompat.getMainExecutor(ctx))

            previewView
        }
    )
}

/** Captures a JPEG into the app's cache dir and hands back the [File]. */
fun capturePhoto(
    imageCapture: ImageCapture,
    context: Context,
    onSuccess: (File) -> Unit,
    onError: (ImageCaptureException) -> Unit
) {
    val fileName = "face_" +
        SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(System.currentTimeMillis()) +
        ".jpg"
    val outputFile = File(context.cacheDir, fileName)
    val outputOptions = ImageCapture.OutputFileOptions.Builder(outputFile).build()

    imageCapture.takePicture(
        outputOptions,
        ContextCompat.getMainExecutor(context),
        object : ImageCapture.OnImageSavedCallback {
            override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                onSuccess(outputFile)
            }

            override fun onError(exception: ImageCaptureException) {
                onError(exception)
            }
        }
    )
}
