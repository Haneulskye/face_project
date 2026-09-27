package com.faceproject.android.health

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.HeartRateRecord
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import java.time.Instant
import java.time.temporal.ChronoUnit

/**
 * Reads the most recent heart-rate sample from Health Connect — the
 * on-device store a paired watch's companion app (e.g. Samsung Health for
 * a Galaxy Watch) writes to. This app never talks to the watch directly.
 */
sealed class HeartRateReadResult {
    data class Success(val bpm: Long, val measuredAt: Instant) : HeartRateReadResult()
    data object NoData : HeartRateReadResult()
    data object PermissionRequired : HeartRateReadResult()
    data object NotAvailable : HeartRateReadResult()
    data class Failure(val message: String) : HeartRateReadResult()
}

class HealthConnectManager(context: Context) {

    private val appContext = context.applicationContext

    val permissions = setOf(HealthPermission.getReadPermission(HeartRateRecord::class))

    fun isAvailable(): Boolean =
        try {
            HealthConnectClient.getSdkStatus(appContext) == HealthConnectClient.SDK_AVAILABLE
        } catch (e: Exception) {
            false
        }

    private val client: HealthConnectClient? by lazy {
        try {
            if (isAvailable()) HealthConnectClient.getOrCreate(appContext) else null
        } catch (e: Exception) {
            null
        }
    }

    suspend fun hasPermission(): Boolean {
        return try {
            val c = client ?: return false
            c.permissionController.getGrantedPermissions().containsAll(permissions)
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Every device/provider call in here is wrapped — a Health Connect quirk on
     * a specific phone (a bad provider state, a permission-controller hiccup,
     * ...) must turn into a Failure result, never an uncaught exception. An
     * uncaught exception here previously crashed the caller's coroutine
     * silently: the "심박수 측정" button looked like it did nothing at all.
     */
    suspend fun readLatestHeartRate(): HeartRateReadResult {
        return try {
            val c = client ?: return HeartRateReadResult.NotAvailable

            if (!hasPermission()) {
                return HeartRateReadResult.PermissionRequired
            }

            val now = Instant.now()
            val response = c.readRecords(
                ReadRecordsRequest(
                    recordType = HeartRateRecord::class,
                    timeRangeFilter = TimeRangeFilter.between(now.minus(24, ChronoUnit.HOURS), now)
                )
            )

            val latestSample = response.records
                .flatMap { it.samples }
                .maxByOrNull { it.time }

            if (latestSample == null) {
                HeartRateReadResult.NoData
            } else {
                HeartRateReadResult.Success(latestSample.beatsPerMinute, latestSample.time)
            }
        } catch (e: Exception) {
            HeartRateReadResult.Failure(e.message ?: "심박수를 불러오지 못했습니다.")
        }
    }
}
