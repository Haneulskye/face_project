import SwiftUI

struct MainView: View {
    let onStart: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Spacer()

            ZStack {
                Circle()
                    .fill(FaceAuthColor.iceBlue)
                    .frame(width: 120, height: 120)
                Image(systemName: "face.smiling")
                    .font(.system(size: 48))
                    .foregroundStyle(FaceAuthColor.navyPrimary)
            }

            VStack(spacing: 8) {
                Text("얼굴 인식으로\n간편하게 인증하세요")
                    .font(.system(size: 26, weight: .bold))
                    .multilineTextAlignment(.center)

                Text("얼굴 인식 후 심박수까지 함께 확인할 수 있어요")
                    .font(.body)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.top, 8)

            Spacer()

            Button(action: onStart) {
                Label("얼굴 인식 시작하기", systemImage: "face.smiling")
                    .font(.system(size: 17, weight: .semibold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
            }
            .buttonStyle(.borderedProminent)
            .tint(FaceAuthColor.navyPrimary)
        }
        .padding(24)
    }
}
