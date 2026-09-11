import SwiftUI

/// Toolbar menu shown on every screen — the iOS-idiomatic equivalent of the
/// Android app's hamburger drawer (홈 / 정보).
struct AppMenuModifier: ViewModifier {
    @Binding var path: NavigationPath
    @Binding var showAbout: Bool

    func body(content: Content) -> some View {
        content.toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Menu {
                    Button {
                        path = NavigationPath()
                    } label: {
                        Label("홈", systemImage: "house")
                    }
                    Button {
                        showAbout = true
                    } label: {
                        Label("정보", systemImage: "info.circle")
                    }
                } label: {
                    Image(systemName: "line.3.horizontal")
                }
            }
        }
    }
}

extension View {
    func appMenu(path: Binding<NavigationPath>, showAbout: Binding<Bool>) -> some View {
        modifier(AppMenuModifier(path: path, showAbout: showAbout))
    }
}
