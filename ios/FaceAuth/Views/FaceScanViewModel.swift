import Foundation

@MainActor
final class FaceScanViewModel: ObservableObject {
    enum State: Equatable {
        case idle
        case authenticating
        case error(String)
    }

    @Published var state: State = .idle

    func authenticate(
        imageData: Data,
        onRegistered: @escaping (String) -> Void,
        onUnregistered: @escaping () -> Void
    ) {
        state = .authenticating

        Task {
            let result = await APIClient.shared.authenticateFace(imageData: imageData)
            switch result {
            case .success(let response):
                if response.authenticated, let name = response.name {
                    state = .idle
                    onRegistered(name)
                } else if response.reason == "face_not_detected" {
                    state = .error("얼굴을 인식하지 못했습니다. 정면을 바라보고 다시 촬영해주세요.")
                } else {
                    state = .idle
                    onUnregistered()
                }

            case .failure(let message):
                state = .error(message)
            }
        }
    }

    func resetError() {
        state = .idle
    }
}
