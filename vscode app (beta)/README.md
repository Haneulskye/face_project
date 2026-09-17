# FACE PJ — 얼굴 인식 기반 심박수 관리 앱

PPT 기획안의 화면 흐름을 그대로 구현한 Flutter 앱입니다.

```
메인화면(원형 버튼)
  └─ 얼굴 인식 중
       ├─ 저장 x 첫 접속 → 신상 정보 기록 → 개인정보 동의 → [저장] → 저장 완료!
       └─ 저장된 대상   → 프로필 + 오늘/지난 심박수 + 솔루션 + [전체기록]
```

## 1. 프로젝트 만들기 (VS Code)

빈 폴더에서 Flutter 프로젝트 껍데기를 먼저 만들고, 이 저장소의 `lib/`, `pubspec.yaml` 로 덮어씁니다.

```bash
flutter create --org com.example --platforms=android,ios face_pj
cd face_pj
# 여기에 lib/ 와 pubspec.yaml 을 복사
flutter pub get
flutter run
```

VS Code 확장: **Flutter**, **Dart** 두 개만 설치하면 됩니다. `F5` 로 디버그 실행.

## 2. 얼굴 인식 모델 넣기

ML Kit는 얼굴 "검출"만 하고 동일인 판별은 못 합니다. 그래서 임베딩 모델을 하나 씁니다.

1. `MobileFaceNet` 또는 `FaceNet` 의 `.tflite` 파일을 구합니다 (출력 차원 192 기준).
2. `assets/models/mobilefacenet.tflite` 경로에 넣습니다.
3. 출력 차원이 128이면 `lib/services/face_service.dart` 의 `_embeddingSize` 를 128로 바꾸세요.

판별 임계값 `matchThreshold` 는 기본 0.70입니다. 실제 기기에서
같은 사람/다른 사람 유사도를 찍어 보며 0.6~0.8 사이로 조정하세요.

## 3. 권한 설정

### `android/app/src/main/AndroidManifest.xml`

`<application>` 위에 추가:

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN"
    android:usesPermissionFlags="neverForLocation" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

### `android/app/build.gradle`

```gradle
minSdkVersion 23   // flutter_blue_plus, ML Kit 요구사항
```

### `ios/Runner/Info.plist`

```xml
<key>NSCameraUsageDescription</key>
<string>얼굴 인식을 위해 카메라를 사용합니다.</string>
<key>NSBluetoothAlwaysUsageDescription</key>
<string>심박 센서 연결을 위해 블루투스를 사용합니다.</string>
```

## 4. 스마트워치 연동

표준 BLE **Heart Rate Service (0x180D)** 를 광고하는 기기면 그대로 붙습니다.
Polar, Garmin, Wahoo 같은 체스트스트랩·러닝워치는 대부분 지원하고,
갤럭시 워치·애플 워치는 기본으로는 이 서비스를 노출하지 않습니다.

- **갤럭시 워치**: Wear OS 컴패니언 앱을 따로 만들어 `Health Services` 의
  심박 데이터를 `MessageClient` 로 폰에 보내는 방식이 필요합니다.
- **애플 워치**: HealthKit(`healthkit` 패키지)으로 읽는 편이 현실적입니다.

즉 `HeartRateService` 의 `bpmStream` 에 값을 흘려보내는 부분만 갈아 끼우면
나머지 화면 코드는 그대로 씁니다. 센서 없이 UI를 먼저 보고 싶으면
`measureOnce()` 가 랜덤 값을 반환하도록 잠깐 바꿔서 테스트하세요.

## 5. 파일 구조

| 파일 | 역할 | PPT 슬라이드 |
|---|---|---|
| `screens/main_screen.dart` | 원형 메인 버튼 | 1, 2 |
| `screens/scan_screen.dart` | 얼굴 인식 + 신규/기존 분기 | 3, 4, 7 |
| `screens/register_screen.dart` | 신상 정보 입력·동의·저장 | 5, 6 |
| `screens/profile_screen.dart` | 프로필 + 심박수 요약 | 8, 9 |
| `screens/history_screen.dart` | 전체기록 | 8 |
| `screens/device_screen.dart` | BLE 기기 연결 | — |
| `widgets/heart_rate_card.dart` | 서맥/정상/빈맥 색상 카드 + 솔루션 | 8, 9 |
| `services/face_service.dart` | 얼굴 검출 → 임베딩 → 매칭 | — |
| `services/heart_rate_service.dart` | BLE 심박 수신 | — |
| `services/db_service.dart` | SQLite 저장 | — |

## 참고

심박수 구간(서맥 60 미만 / 정상 60~100 / 빈맥 100 초과)과 솔루션 문구는
일반적인 성인 안정 시 기준입니다. 이 앱은 의료기기가 아니며 진단 용도로
쓸 수 없다는 안내를 앱 안에 넣어 두는 편이 좋습니다.
