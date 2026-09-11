import SwiftUI

struct HistoryView: View {
    let name: String

    @StateObject private var viewModel = HistoryViewModel()

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

            case .loaded(let available, let records):
                if !available || records.isEmpty {
                    VStack(spacing: 6) {
                        Text("아직 심박수 기록이 없습니다.")
                            .font(.headline)
                        Text("심박수 측정 기능이 연결되면 이곳에서 기록을 확인할 수 있어요.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(24)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(records) { record in
                        VStack(alignment: .leading, spacing: 4) {
                            Text("\(Int(record.bpm)) bpm · \(record.status)")
                                .font(.body.weight(.medium))
                            Text(record.measuredAt)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .listStyle(.plain)
                }
            }
        }
        .task { viewModel.load(name: name) }
    }
}
