import Foundation

struct FaceAuthResponse: Codable {
    let authenticated: Bool
    let name: String?
    let score: Double
    let profile: UserProfile?
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
}

struct HeartRateRecord: Codable, Identifiable {
    let bpm: Double
    let status: String
    let measuredAt: String

    var id: String { measuredAt }

    enum CodingKeys: String, CodingKey {
        case bpm, status
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
