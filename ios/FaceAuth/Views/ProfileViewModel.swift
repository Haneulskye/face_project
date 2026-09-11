import Foundation

struct HeartRateUiState {
    var available: Bool = false
    var bpm: Double? = nil
    var status: HeartRateStatus = .unknown
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

    func measure(name: String) {
        heartRate.isMeasuring = true

        Task {
            switch await APIClient.shared.measureHeartRate(name: name) {
            case .success(let response):
                heartRate = Self.mapHeartRate(response)
            case .failure:
                heartRate.isMeasuring = false
            }
        }
    }

    private static func mapHeartRate(_ response: HeartRateResponse) -> HeartRateUiState {
        let status = response.bpm.map(HeartRateStatus.from(bpm:)) ?? .unknown
        return HeartRateUiState(available: response.available, bpm: response.bpm, status: status, isMeasuring: false)
    }
}
