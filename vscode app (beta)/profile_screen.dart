import 'dart:io';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../main.dart';
import '../models/models.dart';
import '../services/db_service.dart';
import '../services/heart_rate_service.dart';
import '../widgets/heart_rate_card.dart';
import 'device_screen.dart';
import 'history_screen.dart';

/// PPT 슬라이드 8~9: 얼굴 인식 완료 → 프로필 + 오늘/지난 심박수 + 솔루션
class ProfileScreen extends StatefulWidget {
  final UserProfile user;
  const ProfileScreen({super.key, required this.user});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  HeartRateRecord? _today;
  HeartRateRecord? _previous;
  bool _measuring = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final pair = await DbService.instance.latestPair(widget.user.id!);
    if (!mounted) return;
    setState(() {
      _today = pair.$1;
      _previous = pair.$2;
    });
  }

  /// 슬라이드 9: 카드 클릭 시 심박수 재측정
  Future<void> _measure() async {
    if (_measuring) return;

    if (!HeartRateService.instance.isConnected) {
      final go = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('센서가 연결되지 않았어요'),
          content: const Text('스마트워치 또는 심박 센서를 먼저 연결해 주세요.'),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('취소')),
            FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('기기 연결')),
          ],
        ),
      );
      if (go == true && mounted) {
        await Navigator.push(context,
            MaterialPageRoute(builder: (_) => const DeviceScreen()));
      }
      return;
    }

    setState(() => _measuring = true);
    final bpm = await HeartRateService.instance.measureOnce();
    if (!mounted) return;

    if (bpm == null) {
      setState(() => _measuring = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('측정에 실패했어요. 센서 착용 상태를 확인해 주세요')),
      );
      return;
    }

    await DbService.instance.insertHeartRate(HeartRateRecord(
      userId: widget.user.id!,
      bpm: bpm,
      measuredAt: DateTime.now(),
    ));
    await _load();
    if (mounted) setState(() => _measuring = false);
  }

  @override
  Widget build(BuildContext context) {
    final u = widget.user;
    final df = DateFormat('yyyy.MM.dd HH:mm');

    return Scaffold(
      appBar: AppBar(
        title: const Text('얼굴 인식 완료'),
        actions: [
          IconButton(
            icon: const Icon(Icons.watch),
            onPressed: () => Navigator.push(context,
                MaterialPageRoute(builder: (_) => const DeviceScreen())),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // 얼굴 사진 + 신상 정보
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 44,
                backgroundColor: kPrimary,
                backgroundImage: u.facePhotoPath != null
                    ? FileImage(File(u.facePhotoPath!))
                    : null,
                child: u.facePhotoPath == null
                    ? const Text('얼굴\n사진',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.white, fontSize: 12))
                    : null,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.black26),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('이름: ${u.name}'),
                      Text('나이: ${u.age}'),
                      Text('성별: ${u.gender}'),
                      Text('키: ${u.heightCm}cm'),
                      Text('몸무게: ${u.weightKg}kg'),
                      if (u.note.isNotEmpty) Text('특이사항: ${u.note}'),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // 오늘의 심박수 / 지난 심박수 + [전체기록]
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.black26),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('오늘의 심박수: '
                    '${_today != null ? '${_today!.bpm} bpm  (${df.format(_today!.measuredAt)})' : '-'}'),
                const SizedBox(height: 10),
                Text('지난 심박수: '
                    '${_previous != null ? '${_previous!.bpm} bpm  (${df.format(_previous!.measuredAt)})' : '-'}'),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => HistoryScreen(user: u)),
                    ),
                    child: const Text('[전체기록]'),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // 상태 카드 (초록/주황) — 탭하면 재측정
          HeartRateCard(
            record: _today,
            measuring: _measuring,
            onTap: _measure,
          ),
        ],
      ),
    );
  }
}
