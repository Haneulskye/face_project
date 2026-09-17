import 'dart:async';

import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

/// 표준 BLE Heart Rate Service(0x180D) 를 쓰는 스마트워치·체스트스트랩과 연동.
/// Galaxy Watch, Polar, Garmin, Wahoo, Mi Band(HR 브로드캐스트 모드) 등이 해당.
class HeartRateService {
  HeartRateService._();
  static final HeartRateService instance = HeartRateService._();

  static final Guid _hrService = Guid('0000180d-0000-1000-8000-00805f9b34fb');
  static final Guid _hrMeasurement =
      Guid('00002a37-0000-1000-8000-00805f9b34fb');

  BluetoothDevice? _device;
  StreamSubscription<List<int>>? _sub;

  final _bpmController = StreamController<int>.broadcast();

  /// 실시간 BPM 스트림
  Stream<int> get bpmStream => _bpmController.stream;

  bool get isConnected => _device?.isConnected ?? false;
  String? get deviceName => _device?.platformName;

  Future<bool> _ensurePermissions() async {
    final statuses = await [
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.locationWhenInUse,
    ].request();
    return statuses.values.every((s) => s.isGranted || s.isLimited);
  }

  /// 주변에서 HR 서비스를 광고하는 기기 검색
  Future<List<ScanResult>> scanDevices({
    Duration timeout = const Duration(seconds: 8),
  }) async {
    if (!await _ensurePermissions()) return [];

    await FlutterBluePlus.startScan(
      withServices: [_hrService],
      timeout: timeout,
    );
    final results = await FlutterBluePlus.scanResults
        .firstWhere((r) => r.isNotEmpty)
        .timeout(timeout, onTimeout: () => <ScanResult>[]);
    await FlutterBluePlus.stopScan();
    return results;
  }

  /// 연결 후 notify 구독 시작
  Future<void> connect(BluetoothDevice device) async {
    await disconnect();
    _device = device;
    await device.connect(timeout: const Duration(seconds: 15));

    final services = await device.discoverServices();
    final hr = services.firstWhere((s) => s.serviceUuid == _hrService);
    final ch =
        hr.characteristics.firstWhere((c) => c.characteristicUuid == _hrMeasurement);

    await ch.setNotifyValue(true);
    _sub = ch.onValueReceived.listen((data) {
      final bpm = _parseHeartRate(data);
      if (bpm != null) _bpmController.add(bpm);
    });
  }

  Future<void> disconnect() async {
    await _sub?.cancel();
    _sub = null;
    if (_device != null && _device!.isConnected) {
      await _device!.disconnect();
    }
    _device = null;
  }

  /// 한 번 측정: 안정적인 값을 얻기 위해 여러 샘플을 모아 중앙값 반환
  Future<int?> measureOnce({
    Duration window = const Duration(seconds: 10),
    int minSamples = 3,
  }) async {
    if (!isConnected) return null;

    final samples = <int>[];
    final done = Completer<void>();
    final sub = bpmStream.listen((bpm) {
      samples.add(bpm);
      if (samples.length >= 10 && !done.isCompleted) done.complete();
    });

    await Future.any([done.future, Future.delayed(window)]);
    await sub.cancel();

    if (samples.length < minSamples) return null;
    samples.sort();
    return samples[samples.length ~/ 2];
  }

  /// Heart Rate Measurement 특성 파싱 (Bluetooth SIG 규격)
  /// bit0 = 0 이면 BPM 이 uint8, 1 이면 uint16(little endian)
  static int? _parseHeartRate(List<int> data) {
    if (data.isEmpty) return null;
    final flags = data[0];
    final is16Bit = (flags & 0x01) == 0x01;
    if (is16Bit) {
      if (data.length < 3) return null;
      return data[1] | (data[2] << 8);
    }
    if (data.length < 2) return null;
    return data[1];
  }
}
