import SwiftUI

struct ProfileView: View {
    let name: String
    let onViewHistory: (String) -> Void

    @StateObject private var viewModel = ProfileViewModel()

    var body: some View {
        Group {
            switch viewModel.state {
            case .loading:
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

            case .error(let message):
                Text(message)
                    .foregroundStyle(.red)
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

            case .loaded(let profile):
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        HStack(spacing: 16) {
                            ZStack {
                                Circle().fill(FaceAuthColor.iceBlue)
                                Image(systemName: "person.fill")
                                    .foregroundStyle(FaceAuthColor.navyPrimary)
                            }
                            .frame(width: 64, height: 64)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(profile.nickname?.isEmpty == false ? profile.nickname! : profile.name)
                                    .font(.title3.bold())
                                Text("\(profile.name) · \(profile.age)세 · \(profile.gender == "M" ? "남성" : "여성")")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                        }

                        HStack {
                            statTile(value: "\(Int(profile.heightCm))cm", label: "키")
                            Spacer()
                            statTile(
                                value: profile.weightKg.map { "\(Int($0))kg" } ?? "-",
                                label: "몸무게"
                            )
                        }
                        .padding(16)
                        .background(RoundedRectangle(cornerRadius: 14).fill(Color(.secondarySystemBackground)))

                        heartRateCard

                        Button {
                            onViewHistory(name)
                        } label: {
                            Text("전체기록")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.large)
                    }
                    .padding(24)
                }
            }
        }
        .task { viewModel.load(name: name) }
    }

    private func statTile(value: String, label: String) -> some View {
        VStack(spacing: 2) {
            Text(value).font(.title3.bold())
            Text(label).font(.subheadline).foregroundStyle(.secondary)
        }
    }

    private var heartRateCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("오늘의 심박수", systemImage: "heart.fill")
                .font(.headline)

            if viewModel.heartRate.available, let bpm = viewModel.heartRate.bpm {
                Text("\(Int(bpm)) bpm · \(viewModel.heartRate.status.label)")
                    .font(.title2.bold())
            } else {
                Text("측정 준비 중입니다")
                    .font(.title3.bold())
            }

            Text(solutionMessage(for: viewModel.heartRate.status))
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Button {
                viewModel.measure(name: name)
            } label: {
                if viewModel.heartRate.isMeasuring {
                    ProgressView().tint(.white)
                } else {
                    Text("심박수 측정")
                }
            }
            .buttonStyle(.borderedProminent)
            .tint(FaceAuthColor.navyPrimary)
            .disabled(viewModel.heartRate.isMeasuring)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 16).fill(viewModel.heartRate.status.background))
    }
}
