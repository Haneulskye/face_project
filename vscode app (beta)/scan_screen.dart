import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../main.dart';
import '../models/models.dart';
import '../services/face_service.dart';
import 'profile_screen.dart';
import 'register_screen.dart';

/// PPT 슬라이드 3~4, 7: "얼굴 인식 중" → 저장된 대상 / 첫 접속 대상 분기
class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  CameraController? _controller;
  bool _busy = false;
  String _status = '얼굴을 화면 중앙에 맞춰 주세요';

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    final front = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );
    final c = CameraController(front, ResolutionPreset.medium,
        enableAudio: false);
    await c.initialize();
    if (!mounted) return;
    setState(() => _controller = c);
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _capture() async {
    if (_busy || _controller == null) return;
    setState(() {
      _busy = true;
      _status = '얼굴 인식 중...';
    });

    try {
      final shot = await _controller!.takePicture();
      final result = await FaceService.instance.analyzeFile(shot.path);

      if (result == null) {
        setState(() {
          _busy = false;
          _status = '얼굴을 찾지 못했어요. 다시 시도해 주세요';
        });
        return;
      }

      final UserProfile? matched =
          await FaceService.instance.identify(result.embedding);

      if (!mounted) return;

      if (matched != null) {
        // [저장된 대상] 사전에 저장된 정보를 불러옴
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => ProfileScreen(user: matched)),
        );
      } else {
        // [저장 x 첫 접속 대상] 신상 정보 기록
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => RegisterScreen(
              embedding: result.embedding,
              facePhotoPath: result.croppedFacePath,
            ),
          ),
        );
      }
    } catch (e) {
      setState(() {
        _busy = false;
        _status = '인식 실패: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('얼굴 인식')),
      body: Column(
        children: [
          const SizedBox(height: 16),
          ClipOval(
            child: SizedBox(
              width: 240,
              height: 240,
              child: _controller == null
                  ? Container(color: kPrimary)
                  : FittedBox(
                      fit: BoxFit.cover,
                      child: SizedBox(
                        width: _controller!.value.previewSize!.height,
                        height: _controller!.value.previewSize!.width,
                        child: CameraPreview(_controller!),
                      ),
                    ),
            ),
          ),
          const SizedBox(height: 24),
          Text(_status, style: const TextStyle(fontSize: 15)),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.all(24),
            child: SizedBox(
              width: double.infinity,
              height: 52,
              child: FilledButton(
                style: FilledButton.styleFrom(backgroundColor: kPrimary),
                onPressed: _busy ? null : _capture,
                child: _busy
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('얼굴 인식하기'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
