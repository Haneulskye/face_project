import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

import '../models/models.dart';

class DbService {
  DbService._();
  static final DbService instance = DbService._();

  Database? _db;

  Future<Database> get db async {
    _db ??= await _open();
    return _db!;
  }

  Future<Database> _open() async {
    final path = join(await getDatabasesPath(), 'face_pj.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (d, _) async {
        await d.execute('''
          CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            height_cm INTEGER NOT NULL,
            weight_kg INTEGER NOT NULL,
            note TEXT,
            face_photo_path TEXT,
            embedding TEXT NOT NULL,
            created_at TEXT NOT NULL
          )
        ''');
        await d.execute('''
          CREATE TABLE heart_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bpm INTEGER NOT NULL,
            measured_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
          )
        ''');
      },
    );
  }

  // ---------- 사용자 ----------

  Future<int> insertUser(UserProfile u) async =>
      (await db).insert('users', u.toMap()..remove('id'));

  Future<List<UserProfile>> allUsers() async {
    final rows = await (await db).query('users');
    return rows.map(UserProfile.fromMap).toList();
  }

  Future<UserProfile?> userById(int id) async {
    final rows =
        await (await db).query('users', where: 'id = ?', whereArgs: [id], limit: 1);
    return rows.isEmpty ? null : UserProfile.fromMap(rows.first);
  }

  // ---------- 심박수 ----------

  Future<int> insertHeartRate(HeartRateRecord r) async =>
      (await db).insert('heart_rates', r.toMap()..remove('id'));

  /// 최신순 기록. [limit] 을 주면 그만큼만.
  Future<List<HeartRateRecord>> heartRates(int userId, {int? limit}) async {
    final rows = await (await db).query(
      'heart_rates',
      where: 'user_id = ?',
      whereArgs: [userId],
      orderBy: 'measured_at DESC',
      limit: limit,
    );
    return rows.map(HeartRateRecord.fromMap).toList();
  }

  /// PPT 8번의 "오늘의 심박수" / "지난 심박수"
  Future<(HeartRateRecord? today, HeartRateRecord? previous)> latestPair(
      int userId) async {
    final list = await heartRates(userId, limit: 2);
    return (
      list.isNotEmpty ? list[0] : null,
      list.length > 1 ? list[1] : null,
    );
  }
}
