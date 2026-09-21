package com.faceproject.android.ui.screens.history

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.faceproject.android.network.dto.HeartRateRecord
import com.faceproject.android.ui.theme.NavyPrimary

@Composable
fun HistoryScreen(
    padding: PaddingValues,
    name: String,
    viewModel: HistoryViewModel
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
            is HistoryUiState.Loading -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }

            is HistoryUiState.Error -> {
                Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                    Text(state.message, color = MaterialTheme.colorScheme.error)
                }
            }

            is HistoryUiState.Loaded -> {
                if (!state.available || state.records.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                "아직 심박수 기록이 없습니다.",
                                style = MaterialTheme.typography.titleMedium
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                "심박수 측정 기능이 연결되면 이곳에서 기록을 확인할 수 있어요.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                } else {
                    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                        item {
                            HeartRateHistoryChart(
                                // 서버는 최신순(내림차순)으로 주므로 그래프는 시간순으로 뒤집어서 그린다.
                                records = state.records.asReversed(),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(180.dp)
                                    .padding(bottom = 20.dp)
                            )
                        }

                        items(state.records) { record ->
                            Card(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                                Column(modifier = Modifier.padding(16.dp)) {
                                    Text("${record.bpm.toInt()} bpm · ${record.status}")
                                    Text(
                                        record.measuredAt,
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

/**
 * 시간순 bpm 꺾은선 그래프. 별도 차트 라이브러리 없이 Canvas로 직접 그린다 —
 * 항목 몇 개짜리 이력 그래프치고는 라이브러리를 추가할 만큼의 값어치가 없다.
 */
@Composable
private fun HeartRateHistoryChart(records: List<HeartRateRecord>, modifier: Modifier = Modifier) {
    if (records.size < 2) {
        Box(modifier = modifier, contentAlignment = Alignment.Center) {
            Text(
                "그래프를 그리려면 2회 이상의 측정 기록이 필요합니다.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        return
    }

    val normalColor = Color(0xFF2E7D32)
    val warningColor = Color(0xFFEF6C00)
    val surfaceColor = MaterialTheme.colorScheme.surface
    val bpmValues = records.map { it.bpm }
    val minBpm = (bpmValues.min() - 5).coerceAtLeast(0.0)
    val maxBpm = bpmValues.max() + 5

    Column(modifier = modifier) {
        Text(
            "${bpmValues.min().toInt()}–${bpmValues.max().toInt()} bpm",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(4.dp))
        Canvas(modifier = Modifier.fillMaxWidth().weight(1f)) {
            val stepX = if (records.size > 1) size.width / (records.size - 1) else 0f
            fun yFor(bpm: Double): Float {
                val ratio = ((bpm - minBpm) / (maxBpm - minBpm)).coerceIn(0.0, 1.0)
                return size.height - (ratio * size.height).toFloat()
            }

            val points = records.mapIndexed { index, record ->
                Offset(index * stepX, yFor(record.bpm))
            }

            for (i in 0 until points.size - 1) {
                drawLine(
                    color = NavyPrimary,
                    start = points[i],
                    end = points[i + 1],
                    strokeWidth = 4f,
                    cap = androidx.compose.ui.graphics.StrokeCap.Round
                )
            }

            records.forEachIndexed { index, record ->
                val isNormal = record.bpm in 60.0..100.0
                drawCircle(
                    color = if (isNormal) normalColor else warningColor,
                    radius = 7f,
                    center = points[index],
                    style = Stroke(width = 3f)
                )
                drawCircle(
                    color = surfaceColor,
                    radius = 5f,
                    center = points[index]
                )
            }
        }
    }
}
