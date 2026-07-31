import cv2
import mediapipe as mp

# ==========================
# Face Detection
# ==========================
mp_face_detection = mp.solutions.face_detection

detector = mp_face_detection.FaceDetection(
    model_selection=1,
    min_detection_confidence=0.5
)

# ==========================
# Face Mesh
# ==========================
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# ==========================
# 이미지 읽기
# ==========================
image_path = "datasets/CASIA-WebFace_crop/0000045_001.jpg"

img = cv2.imread(image_path)

if img is None:
    print("이미지를 읽을 수 없습니다.")
    exit()

# 이미지 크기
h, w, _ = img.shape

# RGB 변환
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# ==========================
# 얼굴 검출
# ==========================
results = detector.process(rgb)

# ==========================
# Face Mesh
# ==========================
mesh_results = face_mesh.process(rgb)

# ==========================
# 얼굴 Bounding Box
# ==========================
if results.detections:

    print("Face detected!")

    for det in results.detections:

        bbox = det.location_data.relative_bounding_box

        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        bw = int(bbox.width * w)
        bh = int(bbox.height * h)

        cv2.rectangle(
            img,
            (x, y),
            (x + bw, y + bh),
            (0, 255, 0),
            2
        )

else:

    print("No face detected.")

# ==========================
# Face Mesh 랜드마크
# ==========================
if mesh_results.multi_face_landmarks:

    for face_landmarks in mesh_results.multi_face_landmarks:

        for landmark in face_landmarks.landmark:

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(
                img,
                (x, y),
                1,
                (0, 0, 255),
                -1
            )

# ==========================
# 결과 출력
# ==========================
cv2.imshow("Detection + Face Mesh", img)

cv2.waitKey(3000)

cv2.destroyAllWindows()

# 리소스 해제
face_mesh.close()
detector.close()