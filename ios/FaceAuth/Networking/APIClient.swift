import Foundation

enum APIResult<T> {
    case success(T)
    case failure(String)
}

/// Talks to the same FastAPI backend (`backend/api.py`) the Android app uses.
///
/// The iOS Simulator shares the host Mac's network stack, so it can reach
/// this LAN IP directly. A real iPhone needs to be on the same Wi-Fi as the
/// Mac running `uvicorn backend.api:app`. Rebuild if that IP changes.
enum APIConfig {
    static let baseURL = URL(string: "http://192.168.45.205:8000")!
}

final class APIClient {
    static let shared = APIClient()

    private let session: URLSession

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        session = URLSession(configuration: config)
    }

    // MARK: - Endpoints

    func authenticateFace(imageData: Data) async -> APIResult<FaceAuthResponse> {
        var body = MultipartBody()
        body.addFile(name: "image", filename: "face.jpg", mimeType: "image/jpeg", data: imageData)
        return await send(path: "auth/face", method: "POST", multipart: body)
    }

    func registerUser(
        name: String,
        age: Int,
        nickname: String,
        gender: String,
        heightCm: Double,
        weightKg: Double?,
        consent: Bool,
        imageData: Data
    ) async -> APIResult<RegisterResponse> {
        var body = MultipartBody()
        body.addField(name: "name", value: name)
        body.addField(name: "age", value: String(age))
        body.addField(name: "nickname", value: nickname)
        body.addField(name: "gender", value: gender)
        body.addField(name: "height_cm", value: String(heightCm))
        if let weightKg {
            body.addField(name: "weight_kg", value: String(weightKg))
        }
        body.addField(name: "consent", value: consent ? "true" : "false")
        body.addFile(name: "image", filename: "face.jpg", mimeType: "image/jpeg", data: imageData)
        return await send(path: "users/register", method: "POST", multipart: body)
    }

    func getUser(name: String) async -> APIResult<UserProfile> {
        await send(path: "users/\(name)", method: "GET")
    }

    func latestHeartRate(name: String) async -> APIResult<HeartRateResponse> {
        await send(path: "users/\(name)/heart-rate/latest", method: "GET")
    }

    func heartRateHistory(name: String) async -> APIResult<HeartRateHistoryResponse> {
        await send(path: "users/\(name)/heart-rate/history", method: "GET")
    }

    func measureHeartRate(name: String) async -> APIResult<HeartRateResponse> {
        await send(path: "users/\(name)/heart-rate/measure", method: "POST")
    }

    // MARK: - Core request handling

    private func send<T: Decodable>(
        path: String,
        method: String,
        multipart: MultipartBody? = nil
    ) async -> APIResult<T> {
        var request = URLRequest(url: APIConfig.baseURL.appendingPathComponent(path))
        request.httpMethod = method

        if let multipart {
            request.setValue("multipart/form-data; boundary=\(multipart.boundary)", forHTTPHeaderField: "Content-Type")
            request.httpBody = multipart.build()
        }

        do {
            let (data, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                return .failure("서버 응답을 확인할 수 없습니다.")
            }

            if (200...299).contains(httpResponse.statusCode) {
                do {
                    let decoded = try JSONDecoder().decode(T.self, from: data)
                    return .success(decoded)
                } catch {
                    return .failure("서버 응답을 해석하지 못했습니다.")
                }
            } else {
                let detail = try? JSONDecoder().decode(ApiErrorBody.self, from: data).detail
                return .failure(Self.userMessage(for: detail, statusCode: httpResponse.statusCode))
            }
        } catch {
            return .failure("서버에 연결할 수 없습니다. 네트워크와 서버 주소를 확인해주세요.")
        }
    }

    private static func userMessage(for detail: String?, statusCode: Int) -> String {
        switch detail {
        case "face_not_detected":
            return "얼굴을 인식하지 못했습니다. 정면을 바라보고 다시 시도해주세요."
        case "consent_required":
            return "개인정보 수집에 동의해야 등록할 수 있습니다."
        case "age_restricted":
            return "만 14세 미만은 가입할 수 없습니다."
        case "name_already_registered":
            return "이미 등록된 사용자 ID입니다."
        case "user_not_found":
            return "등록된 사용자 정보를 찾을 수 없습니다."
        case "invalid_image":
            return "이미지를 처리할 수 없습니다. 다시 촬영해주세요."
        default:
            return detail ?? "요청을 처리하지 못했습니다. (HTTP \(statusCode))"
        }
    }
}

/// Minimal multipart/form-data body builder (Foundation has no built-in one).
struct MultipartBody {
    let boundary = "FaceAuthBoundary-\(UUID().uuidString)"
    private var parts: [Data] = []

    mutating func addField(name: String, value: String) {
        var part = "--\(boundary)\r\n"
        part += "Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n"
        part += "\(value)\r\n"
        parts.append(Data(part.utf8))
    }

    mutating func addFile(name: String, filename: String, mimeType: String, data: Data) {
        var header = "--\(boundary)\r\n"
        header += "Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(filename)\"\r\n"
        header += "Content-Type: \(mimeType)\r\n\r\n"
        parts.append(Data(header.utf8))
        parts.append(data)
        parts.append(Data("\r\n".utf8))
    }

    func build() -> Data {
        var result = Data()
        for part in parts { result.append(part) }
        result.append(Data("--\(boundary)--\r\n".utf8))
        return result
    }
}
