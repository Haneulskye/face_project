import 'package:flutter/material.dart';

import '../main.dart';
import '../models/models.dart';
import '../services/db_service.dart';
import 'profile_screen.dart';

/// PPT 슬라이드 5: 이름 → 나이 → 성별 → 키/몸무게 → 특이사항 → 개인정보 동의 → [저장]
class RegisterScreen extends StatefulWidget {
  final List<double> embedding;
  final String facePhotoPath;

  const RegisterScreen({
    super.key,
    required this.embedding,
    required this.facePhotoPath,
  });

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _age = TextEditingController();
  final _height = TextEditingController();
  final _weight = TextEditingController();
  final _note = TextEditingController();
  String _gender = 'M';
  bool _agreed = false;

  @override
  void dispose() {
    for (final c in [_name, _age, _height, _weight, _note]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    if (!_agreed) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('개인정보 수집에 동의해 주세요')),
      );
      return;
    }

    final user = UserProfile(
      name: _name.text.trim(),
      age: int.parse(_age.text),
      gender: _gender,
      heightCm: int.parse(_height.text),
      weightKg: int.parse(_weight.text),
      note: _note.text.trim(),
      facePhotoPath: widget.facePhotoPath,
      embedding: widget.embedding,
      createdAt: DateTime.now(),
    );

    final id = await DbService.instance.insertUser(user);
    final saved = await DbService.instance.userById(id);
    if (!mounted || saved == null) return;

    // 슬라이드 6: 저장 완료! 환영합니다, OOO님
    await showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('저장 완료!'),
        content: Text('환영합니다, ${saved.name}님'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('확인'),
          ),
        ],
      ),
    );

    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => ProfileScreen(user: saved)),
    );
  }

  String? _required(String? v) =>
      (v == null || v.trim().isEmpty) ? '필수 입력입니다' : null;

  String? _number(String? v) {
    if (_required(v) != null) return '필수 입력입니다';
    return int.tryParse(v!.trim()) == null ? '숫자만 입력해 주세요' : null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('신상 정보 기록')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            _field('이름을 기록해 주세요', _name, validator: _required),
            _field('나이를 기록해 주세요', _age,
                validator: _number, keyboard: TextInputType.number),
            const SizedBox(height: 8),
            const Text('성별을 기록해 주세요'),
            const SizedBox(height: 4),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'M', label: Text('남성 (M)')),
                ButtonSegment(value: 'F', label: Text('여성 (F)')),
              ],
              selected: {_gender},
              onSelectionChanged: (s) => setState(() => _gender = s.first),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _field('키 (cm)', _height,
                      validator: _number, keyboard: TextInputType.number),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _field('몸무게 (kg)', _weight,
                      validator: _number, keyboard: TextInputType.number),
                ),
              ],
            ),
            _field('특이사항을 기록해 주세요', _note, maxLines: 3),
            const SizedBox(height: 8),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              value: _agreed,
              onChanged: (v) => setState(() => _agreed = v ?? false),
              title: const Text('개인정보 수집 동의'),
              subtitle: const Text(
                '얼굴 특징값과 입력한 정보는 이 기기 안에만 저장됩니다.',
                style: TextStyle(fontSize: 12),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 52,
              child: FilledButton(
                style: FilledButton.styleFrom(backgroundColor: kPrimary),
                onPressed: _save,
                child: const Text('저장'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _field(
    String label,
    TextEditingController c, {
    String? Function(String?)? validator,
    TextInputType? keyboard,
    int maxLines = 1,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: c,
        validator: validator,
        keyboardType: keyboard,
        maxLines: maxLines,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
      ),
    );
  }
}
