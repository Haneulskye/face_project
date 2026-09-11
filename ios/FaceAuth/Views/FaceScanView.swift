import SwiftUI

struct FaceScanView: View {
    @ObservedObject var capturedImageHolder: CapturedImageHolder
    let onAuthenticated: (String) -> Void
    let onUnregistered: () -> Void

    @StateObject private var camera = CameraController()
    @StateObject private var viewModel = FaceScanViewModel()

    var body: some View {
        VStack(spacing: 0) {
            Text("얼굴 인식 중")
                .font(.title3.bold())
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()

            ZStack {
                Color.black

                switch camera.authorizationStatus {
                case .authorized where camera.isReadyToCapture:
                    CameraPreviewView(session: camera.session)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)

                    if viewModel.state == .authenticating {
                        ZStack {
                            Color.black.opacity(0.45)
                            VStack(spacing: 12) {
                                ProgressView().tint(.white)
                                Text("인증 중...").foregroundStyle(.white)
                            }
                        }
                    }

                case .denied, .restricted:
                    permissionMessage("카메라 권한이 꺼져 있습니다. 설정 > 얼굴·심박 인증에서 허용해주세요.")

                case .authorized:
                    // Authorized but no capture device connected (e.g. no camera hardware).
                    permissionMessage("이 기기에서는 카메라를 사용할 수 없습니다.")

                default:
                    permissionMessage("얼굴 인식을 위해 카메라 권한이 필요합니다.")
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            if case .error(let message) = viewModel.state {
                Text(message)
                    .foregroundStyle(.red)
                    .multilineTextAlignment(.center)
                    .padding()
            }

            Button {
                capture()
            } label: {
                Text("촬영")
                    .foregroundStyle(.white)
                    .frame(width: 72, height: 72)
                    .background(Circle().fill(FaceAuthColor.navyPrimary))
            }
            .disabled(!camera.isReadyToCapture || viewModel.state == .authenticating)
            .padding(24)
            .background(.regularMaterial)
        }
        .task {
            await camera.requestAccessIfNeeded()
        }
        .onDisappear {
            camera.stopSession()
        }
    }

    private func capture() {
        viewModel.resetError()
        camera.capturePhoto { data in
            guard let data else { return }
            capturedImageHolder.imageData = data
            viewModel.authenticate(
                imageData: data,
                onRegistered: onAuthenticated,
                onUnregistered: onUnregistered
            )
        }
    }

    @ViewBuilder
    private func permissionMessage(_ text: String) -> some View {
        VStack(spacing: 12) {
            Text(text)
                .multilineTextAlignment(.center)
                .foregroundStyle(.white)
            Button("권한 허용하기") {
                Task { await camera.requestAccessIfNeeded() }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
    }
}
