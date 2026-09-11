import SwiftUI

extension Color {
    init(hex: UInt32, alpha: Double = 1.0) {
        let r = Double((hex >> 16) & 0xFF) / 255.0
        let g = Double((hex >> 8) & 0xFF) / 255.0
        let b = Double(hex & 0xFF) / 255.0
        self.init(red: r, green: g, blue: b, opacity: alpha)
    }
}

enum FaceAuthColor {
    static let navyPrimary = Color(hex: 0x1E2761)
    static let iceBlue = Color(hex: 0xCADCFC)
    static let background = Color(hex: 0xF7F8FC)
    static let statusNormalBg = Color(hex: 0xDFF5E1)
    static let statusWarningBg = Color(hex: 0xFFE6CC)
    static let statusUnknownBg = Color(hex: 0xEDEDED)
}
