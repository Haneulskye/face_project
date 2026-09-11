package com.faceproject.android.data

import androidx.lifecycle.ViewModel
import java.io.File

/**
 * Activity-scoped holder for the most recently captured face photo.
 * A [File] path survives process/config changes better than passing a
 * Bitmap through Navigation-Compose arguments.
 */
class CapturedImageHolder : ViewModel() {
    var capturedImageFile: File? = null
}
