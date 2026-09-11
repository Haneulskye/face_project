package com.faceproject.android.ui.screens.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.faceproject.android.model.solutionMessageFor

@Composable
fun ProfileScreen(
    padding: PaddingValues,
    name: String,
    viewModel: ProfileViewModel,
    onViewHistory: (name: String) -> Unit
) {
    LaunchedEffect(name) {
        viewModel.load(name)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding)
    ) {
        when (val state = viewModel.uiState) {
            is ProfileUiState.Loading -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }

            is ProfileUiState.Error -> {
                Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                    Text(state.message, color = MaterialTheme.colorScheme.error)
                }
            }

            is ProfileUiState.Loaded -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(
                            shape = CircleShape,
                            color = MaterialTheme.colorScheme.primaryContainer,
                            modifier = Modifier.size(64.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Person,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onPrimaryContainer,
                                modifier = Modifier.padding(14.dp)
                            )
                        }

                        Spacer(modifier = Modifier.padding(start = 16.dp))

                        Column {
                            Text(
                                state.profile.nickname?.takeIf { it.isNotBlank() } ?: state.profile.name,
                                style = MaterialTheme.typography.titleLarge
                            )
                            Text(
                                "${state.profile.name} · ${state.profile.age}세 · ${if (state.profile.gender == "M") "남성" else "여성"}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    Card(modifier = Modifier.fillMaxWidth()) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            ProfileStat(label = "키", value = "${state.profile.heightCm.toInt()}cm")
                            ProfileStat(
                                label = "몸무게",
                                value = state.profile.weightKg?.let { "${it.toInt()}kg" } ?: "-"
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    HeartRateCard(
                        heartRate = viewModel.heartRate,
                        onMeasureClick = { viewModel.measure(name) }
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedButton(
                        onClick = { onViewHistory(name) },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("전체기록")
                    }
                }
            }
        }
    }
}

@Composable
private fun ProfileStat(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Text(label, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun HeartRateCard(
    heartRate: HeartRateUiState,
    onMeasureClick: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = heartRate.status.background),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Favorite, contentDescription = null)
                Spacer(modifier = Modifier.padding(start = 8.dp))
                Text("오늘의 심박수", style = MaterialTheme.typography.titleMedium)
            }

            Spacer(modifier = Modifier.height(12.dp))

            if (heartRate.available && heartRate.bpm != null) {
                Text(
                    "${heartRate.bpm.toInt()} bpm · ${heartRate.status.label}",
                    style = MaterialTheme.typography.headlineMedium
                )
            } else {
                Text(
                    "측정 준비 중입니다",
                    style = MaterialTheme.typography.titleMedium
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                solutionMessageFor(heartRate.status),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(16.dp))

            Button(
                onClick = onMeasureClick,
                enabled = !heartRate.isMeasuring
            ) {
                if (heartRate.isMeasuring) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp))
                } else {
                    Text("심박수 측정")
                }
            }
        }
    }
}
