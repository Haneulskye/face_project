import AVFoundation
import UIKit

final class CameraController: NSObject, ObservableObject {
    @Published var authorizationStatus: AVAuthorizationStatus = AVCaptureDevice.authorizationStatus(for: .video)
    /// True once the session has a working input connected. The Simulator has
    /// no real front camera, so this can stay false even when authorized —
    /// used to avoid crashing `AVCapturePhotoOutput` on a connection-less session.
    @Published var isReadyToCapture = false

    let session = AVCaptureSession()
    private let photoOutput = AVCapturePhotoOutput()
    private let sessionQueue = DispatchQueue(label: "com.faceproject.ios.camera-session")

    /// Only ever touched on `sessionQueue`.
    private var didConfigure = false
    private var captureCompletion: ((Data?) -> Void)?

    func requestAccessIfNeeded() async {
        let currentStatus = AVCaptureDevice.authorizationStatus(for: .video)

        let resolvedStatus: AVAuthorizationStatus
        if currentStatus == .notDetermined {
            let granted = await AVCaptureDevice.requestAccess(for: .video)
            resolvedStatus = granted ? .authorized : .denied
        } else {
            resolvedStatus = currentStatus
        }

        await MainActor.run {
            self.authorizationStatus = resolvedStatus
        }

        if resolvedStatus == .authorized {
            startSession()
        }
    }

    func startSession() {
        sessionQueue.async { [weak self] in
            guard let self else { return }

            if !self.didConfigure {
                self.configureSession()
                self.didConfigure = true
            }

            if !self.session.isRunning {
                self.session.startRunning()
            }
        }
    }

    func stopSession() {
        sessionQueue.async { [weak self] in
            guard let self, self.session.isRunning else { return }
            self.session.stopRunning()
        }
    }

    private func configureSession() {
        session.beginConfiguration()
        session.sessionPreset = .photo

        // The Simulator doesn't expose a real `.front`-positioned camera, so
        // fall back to whatever video capture device is available (real
        // devices always resolve the first `default` call).
        let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front)
            ?? AVCaptureDevice.default(for: .video)

        var inputAdded = false
        if let device, let input = try? AVCaptureDeviceInput(device: device), session.canAddInput(input) {
            session.addInput(input)
            inputAdded = true
        }

        if session.canAddOutput(photoOutput) {
            session.addOutput(photoOutput)
        }

        session.commitConfiguration()

        DispatchQueue.main.async { [weak self] in
            self?.isReadyToCapture = inputAdded
        }
    }

    func capturePhoto(completion: @escaping (Data?) -> Void) {
        sessionQueue.async { [weak self] in
            guard let self else { return }

            // Calling capturePhoto with no active video connection throws an
            // uncaught NSInvalidArgumentException and crashes the app.
            guard self.photoOutput.connection(with: .video)?.isActive == true else {
                DispatchQueue.main.async { completion(nil) }
                return
            }

            self.captureCompletion = completion
            let settings = AVCapturePhotoSettings()
            self.photoOutput.capturePhoto(with: settings, delegate: self)
        }
    }
}

extension CameraController: AVCapturePhotoCaptureDelegate {
    func photoOutput(
        _ output: AVCapturePhotoOutput,
        didFinishProcessingPhoto photo: AVCapturePhoto,
        error: Error?
    ) {
        let data = error == nil ? photo.fileDataRepresentation() : nil
        DispatchQueue.main.async { [weak self] in
            self?.captureCompletion?(data)
            self?.captureCompletion = nil
        }
    }
}
