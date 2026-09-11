package com.faceproject.android.model

import androidx.compose.ui.graphics.Color
import com.faceproject.android.ui.theme.StatusNormalBg
import com.faceproject.android.ui.theme.StatusWarningBg

/**
 * 서맥 / 정상 / 빈맥 상태.
 *
 * rPPG(심박수 측정) 모듈이 아직 연결되지 않아 현재는 항상 UNKNOWN으로
 * 표시된다. B팀 모듈이 통합되면 실제 bpm 값을 이 enum으로 매핑하면 된다.
 */
enum class HeartRateStatus(val label: String, val background: Color) {
    BRADYCARDIA("서맥", StatusWarningBg),
    NORMAL("정상", StatusNormalBg),
    TACHYCARDIA("빈맥", StatusWarningBg),
    UNKNOWN("측정 전", Color(0xFFEDEDED));

    companion object {
        fun fromBpm(bpm: Double): HeartRateStatus = when {
            bpm < 60 -> BRADYCARDIA
            bpm > 100 -> TACHYCARDIA
            else -> NORMAL
        }
    }
}

fun solutionMessageFor(status: HeartRateStatus): String = when (status) {
    HeartRateStatus.BRADYCARDIA -> "숨을 고르며 잠시 휴식을 취해보세요."
    HeartRateStatus.TACHYCARDIA -> "운동 중이신가요? 당뇨 등 지병이 있다면 주의하세요."
    HeartRateStatus.NORMAL -> "현재 심박수는 정상 범위입니다."
    HeartRateStatus.UNKNOWN -> "심박수 측정 기능은 준비 중입니다."
}
