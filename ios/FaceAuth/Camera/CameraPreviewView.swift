import AVFoundation
import SwiftUI

struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> PreviewUIView {
        let view = PreviewUIView()
        view.videoPreviewLayer.videoGravity = .resizeAspectFill
        // 세션 대입을 다음 런루프로 미룬다 — 같은 트랜잭션에서 형제 GeometryReader가
        // 마운트되는 동안 이 대입이 프리뷰 레이어 레이아웃을 즉시 강제하면
        // AttributeGraph가 "cyclic graph" 크래시를 낸다.
        DispatchQueue.main.async {
            view.videoPreviewLayer.session = session
        }
        return view
    }

    func updateUIView(_ uiView: PreviewUIView, context: Context) {}

    final class PreviewUIView: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }

        var videoPreviewLayer: AVCaptureVideoPreviewLayer {
            // swiftlint:disable:next force_cast
            layer as! AVCaptureVideoPreviewLayer
        }
    }
}
