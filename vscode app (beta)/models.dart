import 'dart:convert';

/// PPT 5번 슬라이드의 입력 항목 + 얼굴 임베딩
class UserProfile {
  final int? id;
  final String name;
  final int age;
  final String gender; // 'M' | 'F'
  final int heightCm;
  final int weightKg;
  final String note; // 특이사항
  final String? facePhotoPath; // 프로필 얼굴 사진
  final List<double> embedding; // 얼굴 특징 벡터(192차원)
  final DateTime createdAt;

  UserProfile({
    this.id,
    required this.name,
    required this.age,
    required this.gender,
    required this.heightCm,
    required this.weightKg,
    this.note = '',
    this.facePhotoPath,
    required this.embedding,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() => {
        'id': id,
        'name': name,
        'age': age,
        'gender': gender,
        'height_cm': heightCm,
        'weight_kg': weightKg,
        'note': note,
        'face_photo_path': facePhotoPath,
        'embedding': jsonEncode(embedding),
        'created_at': createdAt.toIso8601String(),
      };

  factory UserProfile.fromMap(Map<String, dynamic> m) => UserProfile(
        id: m['id'] as int?,
        name: m['name'] as String,
        age: m['age'] as int,
        gender: m['gender'] as String,
        heightCm: m['height_cm'] as int,
        weightKg: m['weight_kg'] as int,
        note: (m['note'] ?? '') as String,
        facePhotoPath: m['face_photo_path'] as String?,
        embedding: (jsonDecode(m['embedding'] as String) as List)
            .map((e) => (e as num).toDouble())
            .toList(),
        createdAt: DateTime.parse(m['created_at'] as String),
      );
}

enum HeartRateStatus { bradycardia, normal, tachycardia }

extension HeartRateStatusX on HeartRateStatus {
  String get label => switch (this) {
        HeartRateStatus.bradycardia => '서맥',
        HeartRateStatus.normal => '정상',
        HeartRateStatus.tachycardia => '빈맥',
      };

  /// PPT 8번: 정상일 땐 초록 배경, 서맥/빈맥일 땐 주황 배경
  bool get isNormal => this == HeartRateStatus.normal;

  /// 상황에 맞는 솔루션 문구
  List<String> get solutions => switch (this) {
        HeartRateStatus.normal => [
            '좋은 상태예요. 지금 리듬을 유지해 보세요',
            '수분 섭취를 잊지 마세요',
          ],
        HeartRateStatus.tachycardia => [
            '운동 중이신가요?',
            '숨을 고르기',
            '카페인 섭취를 줄여보세요',
          ],
        HeartRateStatus.bradycardia => [
            '천천히 일어나 어지럼증을 확인하세요',
            '당뇨 조심하기',
            '증상이 반복되면 진료를 받아보세요',
          ],
      };
}

class HeartRateRecord {
  final int? id;
  final int userId;
  final int bpm;
  final DateTime measuredAt;

  HeartRateRecord({
    this.id,
    required this.userId,
    required this.bpm,
    required this.measuredAt,
  });

  /// 서맥 < 60 <= 정상 <= 100 < 빈맥
  HeartRateStatus get status {
    if (bpm < 60) return HeartRateStatus.bradycardia;
    if (bpm > 100) return HeartRateStatus.tachycardia;
    return HeartRateStatus.normal;
  }

  Map<String, dynamic> toMap() => {
        'id': id,
        'user_id': userId,
        'bpm': bpm,
        'measured_at': measuredAt.toIso8601String(),
      };

  factory HeartRateRecord.fromMap(Map<String, dynamic> m) => HeartRateRecord(
        id: m['id'] as int?,
        userId: m['user_id'] as int,
        bpm: m['bpm'] as int,
        measuredAt: DateTime.parse(m['measured_at'] as String),
      );
}
