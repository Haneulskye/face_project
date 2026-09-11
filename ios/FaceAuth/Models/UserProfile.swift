import Foundation

struct UserProfile: Codable, Equatable {
    let name: String
    let age: Int
    let nickname: String?
    let gender: String
    let heightCm: Double
    let weightKg: Double?
    let registeredAt: String

    enum CodingKeys: String, CodingKey {
        case name, age, nickname, gender
        case heightCm = "height_cm"
        case weightKg = "weight_kg"
        case registeredAt = "registered_at"
    }
}
