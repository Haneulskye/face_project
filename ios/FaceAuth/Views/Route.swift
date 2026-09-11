import Foundation

enum Route: Hashable {
    case scan
    case register
    case registerSuccess(name: String, nickname: String)
    case profile(name: String)
    case history(name: String)
}
