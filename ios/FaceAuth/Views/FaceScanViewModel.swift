import Foundation

@MainActor
final class FaceScanViewModel: ObservableObject {
    enum State: Equatable {
        case idle
        case authenticating
        case success(name: String, irisMatched: Bool)
        case error(String)
    }

    @Published var state: State = .idle

    private let healthKit = HealthKitManager()

    func authenticate(
        imageData: Data,
        onUnregistered: @escaping () -> Void
    ) {
        state = .authenticating

        Task {
            let result = await APIClient.shared.authenticateFace(imageData: imageData)
            switch result {
            case .success(let response):
                if response.authenticated, let name = response.name {
                    // 얼굴 인증이 최종 판정을 내리고, 같은 사진에서 함께 계산된
                    // 홍채 일치 여부는 보조 정보로 잠깐 함께 보여준다.
                    state = .success(name: name, irisMatched: response.iris?.matched == true)
                    // 얼굴 인증과 동시에 워치 심박수도 자동으로 같이 기록한다 —
                    // 실패해도(워치 미연결 등) 인증 결과 자체에는 영향 없는 best-effort.
                    Task { await self.autoSyncHeartRate(name: name) }
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

    private func autoSyncHeartRate(name: String) async {
        switch await healthKit.readLatestHeartRate() {
        case .success(let bpm, _):
            _ = await APIClient.shared.measureHeartRate(name: name, bpm: bpm, source: "apple_watch")
        case .noData, .notAvailable, .failure:
            break
        }
    }
}
