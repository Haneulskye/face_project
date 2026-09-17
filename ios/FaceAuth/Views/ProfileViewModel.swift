import Foundation

struct HeartRateUiState {
    var available: Bool = false
    var bpm: Double? = nil
    var status: HeartRateStatus = .unknown
    var source: String? = nil
    var isMeasuring: Bool = false
}

@MainActor
final class ProfileViewModel: ObservableObject {
    enum State {
        case loading
        case loaded(UserProfile)
        case error(String)
    }

    @Published var state: State = .loading
    @Published var heartRate = HeartRateUiState()

    private let healthKit = HealthKitManager()

    func load(name: String) {
        state = .loading

        Task {
            switch await APIClient.shared.getUser(name: name) {
            case .success(let profile):
                state = .loaded(profile)
            case .failure(let message):
                state = .error(message)
            }
        }

        Task {
            switch await APIClient.shared.latestHeartRate(name: name) {
            case .success(let response):
                heartRate = Self.mapHeartRate(response)
            case .failure:
                heartRate = HeartRateUiState()
            }
        }
    }

    func measureFromWatch(name: String) {
        heartRate.isMeasuring = true

        Task {
            let bpm: Double?
            let source: String?

            switch await healthKit.readLatestHeartRate() {
            case .success(let value, _):
                bpm = value
                source = "apple_watch"
            // HealthKit 미지원(예: 시뮬레이터)이거나 워치에서 동기화된 값이
            // 없는 경우 — 기존 "측정 준비 중" 응답으로 자연스럽게 대체된다.
            case .noData, .notAvailable, .failure:
                bpm = nil
                source = nil
            }

            switch await APIClient.shared.measureHeartRate(name: name, bpm: bpm, source: source) {
            case .success(let response):
                heartRate = Self.mapHeartRate(response)
            case .failure:
                heartRate.isMeasuring = false
            }
        }
    }

    private static func mapHeartRate(_ response: HeartRateResponse) -> HeartRateUiState {
        let status = response.bpm.map(HeartRateStatus.from(bpm:)) ?? .unknown
        return HeartRateUiState(
            available: response.available,
            bpm: response.bpm,
            status: status,
            source: response.source,
            isMeasuring: false
        )
    }
}
