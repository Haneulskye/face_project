import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../main.dart';
import '../models/models.dart';
import '../services/db_service.dart';

/// PPT 8번의 [전체기록]
class HistoryScreen extends StatelessWidget {
  final UserProfile user;
  const HistoryScreen({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    final df = DateFormat('yyyy.MM.dd (E) HH:mm', 'ko');

    return Scaffold(
      appBar: AppBar(title: Text('${user.name}님의 전체기록')),
      body: FutureBuilder<List<HeartRateRecord>>(
        future: DbService.instance.heartRates(user.id!),
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final list = snap.data!;
          if (list.isEmpty) {
            return const Center(child: Text('아직 측정 기록이 없습니다'));
          }
          return ListView.separated(
            itemCount: list.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (_, i) {
              final r = list[i];
              final normal = r.status.isNormal;
              return ListTile(
                leading: CircleAvatar(
                  backgroundColor: normal ? kNormalBg : kAlertBg,
                  child: Text(
                    '${r.bpm}',
                    style: TextStyle(
                      color: normal ? kNormalFg : kAlertFg,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
                title: Text(r.status.label),
                subtitle: Text(df.format(r.measuredAt)),
              );
            },
          );
        },
      ),
    );
  }
}
