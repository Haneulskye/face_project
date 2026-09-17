import Foundation

struct FaceAuthResponse: Codable {
    let authenticated: Bool
    let name: String?
    let score: Double
    let profile: UserProfile?
    let reason: String?
    let iris: IrisAuthInfo?
}

/// 얼굴과 같은 사진에서 함께 인식되는 홍채 신호. 보조 지표일 뿐이며
/// 최종 인증 여부(authenticated)는 얼굴 인식 결과만으로 결정된다 —
/// 홍채 모델은 아직 프로토타입 단계라 최종 판정을 좌우하지 않는다.
struct IrisAuthInfo: Codable {
    let matched: Bool
    let score: Double
    let reason: String?
}

struct RegisterResponse: Codable {
    let success: Bool
    let name: String
    let profile: UserProfile
}

struct HeartRateResponse: Codable {
    let available: Bool
    let bpm: Double?
    let status: String?
    let source: String?
}

struct HeartRateRecord: Codable, Identifiable {
    let bpm: Double
    let status: String
    let measuredAt: String
    let source: String?

    var id: String { measuredAt }

    enum CodingKeys: String, CodingKey {
        case bpm, status, source
        case measuredAt = "measured_at"
    }
}

struct HeartRateHistoryResponse: Codable {
    let available: Bool
    let records: [HeartRateRecord]
}

struct ApiErrorBody: Codable {
    let detail: String?
}
