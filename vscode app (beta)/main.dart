import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import 'screens/main_screen.dart';

late List<CameraDescription> cameras;

const Color kPrimary = Color(0xFF1B5E80); // PPT 원형 버튼 색
const Color kNormalBg = Color(0xFFE6F4EA); // 정상 = 초록 배경
const Color kAlertBg = Color(0xFFFFE9D6); // 서맥/빈맥 = 주황 배경
const Color kNormalFg = Color(0xFF1E7B34);
const Color kAlertFg = Color(0xFFC25400);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  cameras = await availableCameras();
  runApp(const FacePjApp());
}

class FacePjApp extends StatelessWidget {
  const FacePjApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FACE PJ',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: kPrimary),
        scaffoldBackgroundColor: Colors.white,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black87,
          elevation: 0,
        ),
      ),
      home: const MainScreen(),
    );
  }
}
