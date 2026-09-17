import Foundation
import HealthKit

/// Reads the most recent heart-rate sample from HealthKit — the on-device
/// store a paired Apple Watch writes to directly. This app never talks to
/// the watch itself.
enum HeartRateReadResult {
    case success(bpm: Double, measuredAt: Date)
    case noData
    case notAvailable
    case failure(String)
}

final class HealthKitManager {
    private let store = HKHealthStore()
    private let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate)!

    var isAvailable: Bool { HKHealthStore.isHealthDataAvailable() }

    func readLatestHeartRate() async -> HeartRateReadResult {
        guard isAvailable else { return .notAvailable }

        // HealthKit read permission is privacy-protected: apps are never told
        // whether the user granted or denied it. Requesting is safe to call
        // every time (a no-op if already answered), and a denial simply
        // yields an empty query result below.
        do {
            try await store.requestAuthorization(toShare: [], read: [heartRateType])
        } catch {
            return .failure(error.localizedDescription)
        }

        return await withCheckedContinuation { continuation in
            let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
            let query = HKSampleQuery(
                sampleType: heartRateType,
                predicate: nil,
                limit: 1,
                sortDescriptors: [sort]
            ) { _, samples, error in
                if let error {
                    continuation.resume(returning: .failure(error.localizedDescription))
                    return
                }
                guard let sample = samples?.first as? HKQuantitySample else {
                    continuation.resume(returning: .noData)
                    return
                }
                let unit = HKUnit.count().unitDivided(by: .minute())
                continuation.resume(
                    returning: .success(bpm: sample.quantity.doubleValue(for: unit), measuredAt: sample.endDate)
                )
            }
            store.execute(query)
        }
    }
}
