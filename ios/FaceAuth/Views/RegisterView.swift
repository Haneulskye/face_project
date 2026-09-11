import SwiftUI

private let minimumAge = 14

struct RegisterView: View {
    @ObservedObject var capturedImageHolder: CapturedImageHolder
    let onRegistered: (String, String) -> Void

    @StateObject private var viewModel = RegisterViewModel()

    @State private var name = ""
    @State private var age = ""
    @State private var nickname = ""
    @State private var gender = "M"
    @State private var height = ""
    @State private var weight = ""
    @State private var consent = false

    private var imageData: Data? { capturedImageHolder.imageData }

    private var ageValue: Int? { Int(age) }
    private var isUnderAge: Bool { (ageValue ?? minimumAge) < minimumAge }
    private var isWeightValid: Bool { weight.isEmpty || Double(weight) != nil }

    private var isFormValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty
            && !nickname.trimmingCharacters(in: .whitespaces).isEmpty
            && ageValue != nil && !isUnderAge
            && Double(height) != nil
            && isWeightValid
            && consent
            && imageData != nil
    }

    private var isSubmitting: Bool { viewModel.state == .submitting }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("처음 뵙는 얼굴이에요")
                        .font(.title2.bold())
                    Text("정보를 입력하면 다음부터는 얼굴 인식만으로 확인할 수 있어요.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.top, 8)

                TextField("이름 (사용자 ID)", text: $name)
                    .textFieldStyle(.roundedBorder)

                VStack(alignment: .leading, spacing: 4) {
                    TextField("나이", text: $age)
                        .keyboardType(.numberPad)
                        .textFieldStyle(.roundedBorder)

                    if isUnderAge {
                        Text("만 14세 미만은 가입할 수 없습니다.")
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }

                TextField("불리고 싶은 닉네임", text: $nickname)
                    .textFieldStyle(.roundedBorder)

                VStack(alignment: .leading, spacing: 8) {
                    Text("성별").font(.subheadline.weight(.medium))
                    Picker("성별", selection: $gender) {
                        Text("남성").tag("M")
                        Text("여성").tag("F")
                    }
                    .pickerStyle(.segmented)
                }

                HStack(spacing: 12) {
                    TextField("키(cm)", text: $height)
                        .keyboardType(.decimalPad)
                        .textFieldStyle(.roundedBorder)
                    TextField("몸무게(kg, 선택)", text: $weight)
                        .keyboardType(.decimalPad)
                        .textFieldStyle(.roundedBorder)
                }

                Toggle("개인정보 수집 및 이용에 동의합니다.", isOn: $consent)
                    .font(.subheadline)

                if imageData == nil {
                    Text("촬영된 얼굴 사진이 없습니다. 이전 화면에서 다시 촬영해주세요.")
                        .foregroundStyle(.red)
                        .font(.subheadline)
                }

                if case .error(let message) = viewModel.state {
                    Text(message)
                        .foregroundStyle(.red)
                        .font(.subheadline)
                }

                Button {
                    guard let imageData, let ageInt = ageValue,
                          let heightVal = Double(height) else { return }
                    viewModel.submit(
                        name: name.trimmingCharacters(in: .whitespaces),
                        age: ageInt,
                        nickname: nickname.trimmingCharacters(in: .whitespaces),
                        gender: gender,
                        heightCm: heightVal,
                        weightKg: Double(weight),
                        consent: consent,
                        imageData: imageData,
                        onSuccess: onRegistered
                    )
                } label: {
                    if isSubmitting {
                        ProgressView().tint(.white)
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("저장하기")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(FaceAuthColor.navyPrimary)
                .controlSize(.large)
                .disabled(!isFormValid || isSubmitting)
                .padding(.top, 8)
            }
            .padding(24)
        }
    }
}
