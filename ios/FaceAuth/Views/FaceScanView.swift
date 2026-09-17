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

                    // FaceID 스타일 가이드: 얼굴(과 눈)을 맞춰야 하는 타원 표시.
                    FaceAlignmentGuideOverlay()

                    VStack {
                        Spacer()
                        Text("타원 안에 얼굴과 눈이 오도록 맞춰주세요")
                            .foregroundStyle(.white)
                            .multilineTextAlignment(.center)
                            .padding(.bottom, 28)
                    }

                    if viewModel.state == .authenticating {
                        ZStack {
                            Color.black.opacity(0.45)
                            VStack(spacing: 12) {
                                ProgressView().tint(.white)
                                Text("얼굴+홍채 인식 중...").foregroundStyle(.white)
                            }
                        }
                    }

                    if case .success(_, let irisMatched) = viewModel.state {
                        ZStack {
                            Color.black.opacity(0.55)
                            VStack(spacing: 8) {
                                matchRow(label: "얼굴 인증", matched: true)
                                matchRow(label: "홍채 인증", matched: irisMatched)
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
            .disabled(!camera.isReadyToCapture || isBusy)
            .padding(24)
            .background(.regularMaterial)
        }
        .task {
            await camera.requestAccessIfNeeded()
        }
        .onDisappear {
            camera.stopSession()
        }
        .onChange(of: viewModel.state) { newState in
            guard case .success(let name, _) = newState else { return }
            Task {
                try? await Task.sleep(nanoseconds: 700_000_000)
                onAuthenticated(name)
                viewModel.resetError()
            }
        }
    }

    private var isBusy: Bool {
        viewModel.state == .authenticating || {
            if case .success = viewModel.state { return true }
            return false
        }()
    }

    private func capture() {
        viewModel.resetError()
        camera.capturePhoto { data in
            guard let data else { return }
            capturedImageHolder.imageData = data
            viewModel.authenticate(imageData: data, onUnregistered: onUnregistered)
        }
    }

    private func matchRow(label: String, matched: Bool) -> some View {
        HStack(spacing: 8) {
            Image(systemName: matched ? "checkmark.circle.fill" : "xmark.circle.fill")
                .foregroundStyle(matched ? Color.green : Color.gray)
            Text("\(label) \(matched ? "일치" : "불일치")")
                .foregroundStyle(.white)
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

/// FaceID처럼 카메라 미리보기 위에 얼굴을 맞출 타원 가이드를 그린다.
/// 실시간으로 얼굴 위치를 감지하지는 않는 정적 가이드다 — 사용자가
/// 눈으로 보고 맞추는 용도.
private struct FaceAlignmentGuideOverlay: View {
    var body: some View {
        GeometryReader { proxy in
            let ovalWidth = proxy.size.width * 0.62
            let ovalHeight = ovalWidth * 1.35
            let ovalRect = CGRect(
                x: (proxy.size.width - ovalWidth) / 2,
                y: (proxy.size.height - ovalHeight) / 2,
                width: ovalWidth,
                height: ovalHeight
            )

            ZStack {
                Path { path in
                    path.addRect(CGRect(origin: .zero, size: proxy.size))
                    path.addEllipse(in: ovalRect)
                }
                .fill(Color.black.opacity(0.45), style: FillStyle(eoFill: true))

                Ellipse()
                    .strokeBorder(style: StrokeStyle(lineWidth: 4, dash: [18, 14]))
                    .foregroundStyle(.white)
                    .frame(width: ovalWidth, height: ovalHeight)
                    .position(x: proxy.size.width / 2, y: proxy.size.height / 2)
            }
        }
        .allowsHitTesting(false)
    }
}
