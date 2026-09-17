import 'package:flutter/material.dart';

import '../main.dart';
import '../models/models.dart';

/// PPT 8~9번의 하늘색 박스 + 솔루션 박스.
/// 정상이면 초록 배경, 서맥/빈맥이면 주황 배경. 탭하면 재측정.
class HeartRateCard extends StatelessWidget {
  final HeartRateRecord? record;
  final bool measuring;
  final VoidCallback onTap;

  const HeartRateCard({
    super.key,
    required this.record,
    required this.measuring,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final status = record?.status;
    final normal = status?.isNormal ?? true;
    final bg = record == null
        ? const Color(0xFFF1F3F5)
        : (normal ? kNormalBg : kAlertBg);
    final fg = record == null
        ? Colors.black54
        : (normal ? kNormalFg : kAlertFg);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        InkWell(
          onTap: measuring ? null : onTap,
          borderRadius: BorderRadius.circular(10),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 22, horizontal: 16),
            decoration: BoxDecoration(
              color: bg,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              children: [
                const Text('< 오늘의 심박수 >',
                    style: TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                if (measuring)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: CircularProgressIndicator(),
                  )
                else
                  Text(
                    record == null
                        ? '측정 기록이 없습니다'
                        : '${record!.bpm} bpm · ${status!.label}',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: fg,
                    ),
                  ),
                const SizedBox(height: 8),
                Text(
                  measuring ? '측정 중...' : '탭하면 심박수를 다시 측정합니다',
                  style: const TextStyle(fontSize: 12, color: Colors.black54),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        if (record != null)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.black26),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: status!.solutions
                  .map((s) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Text('· $s'),
                      ))
                  .toList(),
            ),
          ),
      ],
    );
  }
}
