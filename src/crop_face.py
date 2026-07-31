import cv2
import mediapipe as mp
import numpy as np
import os

# -----------------------------
# Face Mesh
# -----------------------------
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True
)

image_path = "datasets/CASIA-WebFace_crop/0000045_001.jpg"

img = cv2.imread(image_path)

if img is None:
    print("이미지를 읽을 수 없습니다.")
    exit()

h, w, _ = img.shape

rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

results = face_mesh.process(rgb)

if not results.multi_face_landmarks:
    print("얼굴 없음")
    exit()

landmarks = results.multi_face_landmarks[0]

# -----------------------------
# 눈 좌표
# -----------------------------
left = landmarks.landmark[33]
right = landmarks.landmark[263]

left = (int(left.x*w), int(left.y*h))
right = (int(right.x*w), int(right.y*h))

# -----------------------------
# 회전
# -----------------------------
dy = right[1]-left[1]
dx = right[0]-left[0]

angle = np.degrees(np.arctan2(dy,dx))

center = (
    (left[0]+right[0])//2,
    (left[1]+right[1])//2
)

M = cv2.getRotationMatrix2D(center, angle, 1.0)

aligned = cv2.warpAffine(
    img,
    M,
    (w,h)
)

# -----------------------------
# 얼굴 Crop
# -----------------------------
x1 = max(center[0]-80,0)
y1 = max(center[1]-90,0)

x2 = min(center[0]+80,w)
y2 = min(center[1]+110,h)

crop = aligned[y1:y2, x1:x2]

# -----------------------------
# 112x112
# -----------------------------
crop = cv2.resize(
    crop,
    (112,112)
)

# -----------------------------
# 저장
# -----------------------------
os.makedirs(
    "output/crop",
    exist_ok=True
)

save_path = "output/crop/0000045_001.jpg"

cv2.imwrite(
    save_path,
    crop
)

print("Saved :", save_path)

cv2.imshow("Crop",crop)

cv2.waitKey(3000)

cv2.destroyAllWindows()

face_mesh.close()
