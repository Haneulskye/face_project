package com.faceproject.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.faceproject.android.navigation.FaceAuthNavGraph
import com.faceproject.android.ui.theme.FaceAuthTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            FaceAuthTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    FaceAuthNavGraph()
                }
            }
        }
    }
}
