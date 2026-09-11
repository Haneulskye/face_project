import Foundation

@MainActor
final class HistoryViewModel: ObservableObject {
    enum State {
        case loading
        case loaded(available: Bool, records: [HeartRateRecord])
        case error(String)
    }

    @Published var state: State = .loading

    func load(name: String) {
        state = .loading

        Task {
            switch await APIClient.shared.heartRateHistory(name: name) {
            case .success(let response):
                state = .loaded(available: response.available, records: response.records)
            case .failure(let message):
                state = .error(message)
            }
        }
    }
}
