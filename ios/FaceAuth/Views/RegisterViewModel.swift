import Foundation

@MainActor
final class RegisterViewModel: ObservableObject {
    enum State: Equatable {
        case idle
        case submitting
        case error(String)
    }

    @Published var state: State = .idle

    func submit(
        name: String,
        age: Int,
        nickname: String,
        gender: String,
        heightCm: Double,
        weightKg: Double?,
        consent: Bool,
        imageData: Data,
        onSuccess: @escaping (String, String) -> Void
    ) {
        state = .submitting

        Task {
            let result = await APIClient.shared.registerUser(
                name: name,
                age: age,
                nickname: nickname,
                gender: gender,
                heightCm: heightCm,
                weightKg: weightKg,
                consent: consent,
                imageData: imageData
            )

            switch result {
            case .success(let response):
                state = .idle
                onSuccess(response.name, nickname)
            case .failure(let message):
                state = .error(message)
            }
        }
    }
}
