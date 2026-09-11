import Foundation

/// Shared across the scan screen (captures the photo) and the registration
/// screen (uploads it), so the JPEG survives the navigation push between them.
final class CapturedImageHolder: ObservableObject {
    @Published var imageData: Data?
}
