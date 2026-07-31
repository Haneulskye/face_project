import cv2
import mediapipe as mp
import numpy as np

# Face Mesh
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True
)

# 이미지
image_path = "datasets/CASIA-WebFace_crop/0000045_001.jpg"

img = cv2.imread(image_path)

if img is None:
    print("이미지를 읽을 수 없습니다.")
    exit()

h, w, _ = img.shape

rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

results = face_mesh.process(rgb)

if not results.multi_face_landmarks:
    print("얼굴을 찾지 못했습니다.")
    exit()

landmarks = results.multi_face_landmarks[0]

# 눈 좌표
left_eye = landmarks.landmark[33]
right_eye = landmarks.landmark[263]

left = (
    int(left_eye.x * w),
    int(left_eye.y * h)
)

right = (
    int(right_eye.x * w),
    int(right_eye.y * h)
)

# 눈 표시
cv2.circle(img, left, 4, (255,0,0), -1)
cv2.circle(img, right, 4, (255,0,0), -1)

# 회전각 계산
dy = right[1] - left[1]
dx = right[0] - left[0]

angle = np.degrees(np.arctan2(dy, dx))

print("Rotation angle :", angle)

# 회전 중심
center = (
    (left[0] + right[0]) // 2,
    (left[1] + right[1]) // 2
)

# 회전행렬
M = cv2.getRotationMatrix2D(
    center,
    angle,
    1.0
)

aligned = cv2.warpAffine(
    img,
    M,
    (w, h)
)

cv2.imshow("Original", img)
cv2.imshow("Aligned", aligned)

cv2.waitKey(3000)

cv2.destroyAllWindows()

face_mesh.close()