import SwiftUI

struct RegisterSuccessView: View {
    let nickname: String
    let onConfirm: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundStyle(Color(hex: 0x2E7D32))

            Text("저장 완료!")
                .font(.title.bold())

            Text("환영합니다, \(nickname)님")
                .font(.title3)
                .multilineTextAlignment(.center)

            Spacer()

            Button(action: onConfirm) {
                Text("확인")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(FaceAuthColor.navyPrimary)
            .controlSize(.large)
        }
        .padding(24)
    }
}
