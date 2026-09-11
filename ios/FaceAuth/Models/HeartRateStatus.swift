import SwiftUI

/// 서맥 / 정상 / 빈맥 상태.
///
/// rPPG(심박수 측정) 모듈이 아직 연결되지 않아 현재는 항상 unknown으로
/// 표시된다. 실제 bpm 값이 들어오면 이 enum으로 매핑하면 된다.
enum HeartRateStatus {
    case bradycardia
    case normal
    case tachycardia
    case unknown

    var label: String {
        switch self {
        case .bradycardia: return "서맥"
        case .normal: return "정상"
        case .tachycardia: return "빈맥"
        case .unknown: return "측정 전"
        }
    }

    var background: Color {
        switch self {
        case .bradycardia, .tachycardia: return FaceAuthColor.statusWarningBg
        case .normal: return FaceAuthColor.statusNormalBg
        case .unknown: return FaceAuthColor.statusUnknownBg
        }
    }

    static func from(bpm: Double) -> HeartRateStatus {
        switch bpm {
        case ..<60: return .bradycardia
        case 100...: return .tachycardia
        default: return .normal
        }
    }
}

func solutionMessage(for status: HeartRateStatus) -> String {
    switch status {
    case .bradycardia: return "숨을 고르며 잠시 휴식을 취해보세요."
    case .tachycardia: return "운동 중이신가요? 당뇨 등 지병이 있다면 주의하세요."
    case .normal: return "현재 심박수는 정상 범위입니다."
    case .unknown: return "심박수 측정 기능은 준비 중입니다."
    }
}
