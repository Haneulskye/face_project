import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

import '../services/heart_rate_service.dart';

/// 스마트워치·심박 센서(BLE Heart Rate Service) 검색 및 연결
class DeviceScreen extends StatefulWidget {
  const DeviceScreen({super.key});

  @override
  State<DeviceScreen> createState() => _DeviceScreenState();
}

class _DeviceScreenState extends State<DeviceScreen> {
  List<ScanResult> _results = [];
  bool _scanning = false;

  Future<void> _scan() async {
    setState(() => _scanning = true);
    final r = await HeartRateService.instance.scanDevices();
    if (!mounted) return;
    setState(() {
      _results = r;
      _scanning = false;
    });
  }

  Future<void> _connect(BluetoothDevice d) async {
    try {
      await HeartRateService.instance.connect(d);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${d.platformName} 연결됨')),
      );
      setState(() {});
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('연결 실패: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final hr = HeartRateService.instance;

    return Scaffold(
      appBar: AppBar(title: const Text('심박 센서 연결')),
      body: Column(
        children: [
          if (hr.isConnected)
            ListTile(
              leading: const Icon(Icons.favorite, color: Colors.red),
              title: Text('연결됨: ${hr.deviceName}'),
              trailing: TextButton(
                onPressed: () async {
                  await hr.disconnect();
                  setState(() {});
                },
                child: const Text('연결 해제'),
              ),
            ),
          if (hr.isConnected)
            StreamBuilder<int>(
              stream: hr.bpmStream,
              builder: (_, s) => Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  s.hasData ? '실시간: ${s.data} bpm' : '데이터 수신 대기 중...',
                  style: const TextStyle(fontSize: 18),
                ),
              ),
            ),
          const Divider(),
          Expanded(
            child: _results.isEmpty
                ? Center(
                    child: Text(_scanning ? '검색 중...' : '검색 버튼을 눌러 주세요'),
                  )
                : ListView(
                    children: _results
                        .map((r) => ListTile(
                              title: Text(r.device.platformName.isEmpty
                                  ? '(이름 없음)'
                                  : r.device.platformName),
                              subtitle: Text(r.device.remoteId.str),
                              trailing: Text('${r.rssi} dBm'),
                              onTap: () => _connect(r.device),
                            ))
                        .toList(),
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _scanning ? null : _scan,
        icon: const Icon(Icons.search),
        label: const Text('기기 검색'),
      ),
    );
  }
}
