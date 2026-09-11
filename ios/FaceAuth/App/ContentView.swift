import SwiftUI

struct ContentView: View {
    @StateObject private var capturedImageHolder = CapturedImageHolder()
    @State private var path = NavigationPath()
    @State private var showAbout = false

    var body: some View {
        NavigationStack(path: $path) {
            MainView(onStart: { path.append(Route.scan) })
                .navigationTitle("메인화면")
                .navigationBarTitleDisplayMode(.inline)
                .appMenu(path: $path, showAbout: $showAbout)
                .navigationDestination(for: Route.self) { route in
                    destination(for: route)
                }
        }
        .alert("정보", isPresented: $showAbout) {
            Button("확인", role: .cancel) {}
        } message: {
            Text("얼굴·홍채·rPPG 기반 멀티모달 인증 시스템 데모 앱")
        }
    }

    @ViewBuilder
    private func destination(for route: Route) -> some View {
        switch route {
        case .scan:
            FaceScanView(
                capturedImageHolder: capturedImageHolder,
                onAuthenticated: { name in path.append(Route.profile(name: name)) },
                onUnregistered: { path.append(Route.register) }
            )
            .navigationTitle("얼굴 인식 중")
            .navigationBarTitleDisplayMode(.inline)
            .appMenu(path: $path, showAbout: $showAbout)

        case .register:
            RegisterView(
                capturedImageHolder: capturedImageHolder,
                onRegistered: { name, nickname in
                    path.append(Route.registerSuccess(name: name, nickname: nickname))
                }
            )
            .navigationTitle("회원가입")
            .navigationBarTitleDisplayMode(.inline)
            .appMenu(path: $path, showAbout: $showAbout)

        case .registerSuccess(let name, let nickname):
            RegisterSuccessView(
                nickname: nickname,
                onConfirm: { path.append(Route.profile(name: name)) }
            )
            .navigationTitle("등록 완료")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarBackButtonHidden(true)
            .appMenu(path: $path, showAbout: $showAbout)

        case .profile(let name):
            ProfileView(
                name: name,
                onViewHistory: { userName in path.append(Route.history(name: userName)) }
            )
            .navigationTitle("얼굴 인식 완료")
            .navigationBarTitleDisplayMode(.inline)
            .appMenu(path: $path, showAbout: $showAbout)

        case .history(let name):
            HistoryView(name: name)
                .navigationTitle("전체기록")
                .navigationBarTitleDisplayMode(.inline)
                .appMenu(path: $path, showAbout: $showAbout)
        }
    }
}
