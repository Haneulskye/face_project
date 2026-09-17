import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

import '../models/models.dart';
import 'db_service.dart';

/// 얼굴 검출(ML Kit) → 얼굴 crop → 임베딩(MobileFaceNet) → 코사인 유사도 매칭
class FaceService {
  FaceService._();
  static final FaceService instance = FaceService._();

  static const int _inputSize = 112; // MobileFaceNet 입력
  static const int _embeddingSize = 192;

  /// 이 값보다 유사도가 높으면 "저장된 대상"으로 판단.
  /// 실제 기기에서 테스트하며 0.6 ~ 0.8 사이로 조정하세요.
  static const double matchThreshold = 0.70;

  final FaceDetector _detector = FaceDetector(
    options: FaceDetectorOptions(
      performanceMode: FaceDetectorMode.accurate,
      enableLandmarks: true,
    ),
  );

  Interpreter? _interpreter;

  Future<void> init() async {
    _interpreter ??= await Interpreter.fromAsset(
      'assets/models/mobilefacenet.tflite',
    );
  }

  Future<void> dispose() async {
    await _detector.close();
    _interpreter?.close();
  }

  /// 사진 파일에서 가장 큰 얼굴을 찾아 임베딩을 만든다.
  /// 얼굴이 없으면 null.
  Future<FaceResult?> analyzeFile(String path) async {
    await init();

    final faces = await _detector.processImage(InputImage.fromFilePath(path));
    if (faces.isEmpty) return null;

    // 가장 크게 잡힌 얼굴 하나만 사용
    faces.sort((a, b) =>
        (b.boundingBox.width * b.boundingBox.height)
            .compareTo(a.boundingBox.width * a.boundingBox.height));
    final box = faces.first.boundingBox;

    final decoded = img.decodeImage(await File(path).readAsBytes());
    if (decoded == null) return null;

    final x = box.left.clamp(0, decoded.width - 1).toInt();
    final y = box.top.clamp(0, decoded.height - 1).toInt();
    final w = box.width.clamp(1, decoded.width - x).toInt();
    final h = box.height.clamp(1, decoded.height - y).toInt();

    final cropped = img.copyResize(
      img.copyCrop(decoded, x: x, y: y, width: w, height: h),
      width: _inputSize,
      height: _inputSize,
    );

    return FaceResult(
      embedding: _embed(cropped),
      croppedFacePath: await _saveCrop(cropped, path),
    );
  }

  List<double> _embed(img.Image face) {
    // [1, 112, 112, 3] 형태로 정규화 (-1 ~ 1)
    final input = List.generate(
      1,
      (_) => List.generate(
        _inputSize,
        (yy) => List.generate(_inputSize, (xx) {
          final p = face.getPixel(xx, yy);
          return [
            (p.r - 127.5) / 127.5,
            (p.g - 127.5) / 127.5,
            (p.b - 127.5) / 127.5,
          ];
        }),
      ),
    );

    final output = List.generate(1, (_) => List.filled(_embeddingSize, 0.0));
    _interpreter!.run(input, output);
    return _l2Normalize(output.first);
  }

  Future<String> _saveCrop(img.Image face, String sourcePath) async {
    final dir = Directory(sourcePath).parent.path;
    final out =
        File('$dir/face_${DateTime.now().millisecondsSinceEpoch}.jpg');
    await out.writeAsBytes(Uint8List.fromList(img.encodeJpg(face, quality: 90)));
    return out.path;
  }

  /// DB의 모든 사용자와 비교해 가장 비슷한 사람을 찾는다.
  /// 임계값 미만이면 null → "저장 x 첫 접속 대상" 흐름으로.
  Future<UserProfile?> identify(List<double> embedding) async {
    final users = await DbService.instance.allUsers();
    UserProfile? best;
    double bestScore = -1;

    for (final u in users) {
      final score = cosineSimilarity(embedding, u.embedding);
      if (score > bestScore) {
        bestScore = score;
        best = u;
      }
    }
    return bestScore >= matchThreshold ? best : null;
  }

  static List<double> _l2Normalize(List<double> v) {
    final norm = math.sqrt(v.fold<double>(0, (s, e) => s + e * e));
    if (norm == 0) return v;
    return v.map((e) => e / norm).toList();
  }

  static double cosineSimilarity(List<double> a, List<double> b) {
    if (a.length != b.length) return -1;
    double dot = 0;
    for (var i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
    }
    return dot; // 둘 다 L2 정규화된 벡터이므로 내적 = 코사인 유사도
  }
}

class FaceResult {
  final List<double> embedding;
  final String croppedFacePath;

  FaceResult({required this.embedding, required this.croppedFacePath});
}
