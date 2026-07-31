import cv2
import mediapipe as mp
import numpy as np
import os
from glob import glob
import csv

# -----------------------------
# Face Mesh
# -----------------------------
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True
)

# -----------------------------
# 입력 폴더
# -----------------------------
image_dir = "datasets/CASIA-WebFace_crop"

image_list = sorted(
    glob(os.path.join(image_dir, "*.jpg"))
)

print("Images :", len(image_list))

# -----------------------------
# 출력 폴더
# -----------------------------
pass_dir = "output/final_dataset"
fail_dir = "output/rejected"

os.makedirs(pass_dir, exist_ok=True)
os.makedirs(fail_dir, exist_ok=True)

log_dir = "output/logs"
os.makedirs(log_dir, exist_ok=True)

# -----------------------------
# 카운트
# -----------------------------
pass_count = 0
fail_count = 0

# -----------------------------
# CSV Log
# -----------------------------
log_path = os.path.join(log_dir, "preprocess_log.csv")

log_file = open(
    log_path,
    "w",
    newline="",
    encoding="utf-8"
)

writer = csv.writer(log_file)

writer.writerow([
    "Filename",
    "BlurScore",
    "FaceWidth",
    "Rotation",
    "Result"
])

# -----------------------------
# 반복
# -----------------------------
for idx, image_path in enumerate(image_list):

    img = cv2.imread(image_path)

    if img is None:
        continue

    h, w, _ = img.shape

    rgb = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )

    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        fail_count += 1
        continue

    landmarks = results.multi_face_landmarks[0]

    # -----------------------------
    # 양쪽 눈
    # -----------------------------
    left_eye = landmarks.landmark[33]
    right_eye = landmarks.landmark[263]

    left_eye = (
        int(left_eye.x * w),
        int(left_eye.y * h)
    )

    right_eye = (
        int(right_eye.x * w),
        int(right_eye.y * h)
    )

    # -----------------------------
    # 얼굴 기울기
    # -----------------------------
    dy = right_eye[1] - left_eye[1]
    dx = right_eye[0] - left_eye[0]

    angle = np.degrees(
        np.arctan2(dy, dx)
    )

    center = (
        (left_eye[0] + right_eye[0]) // 2,
        (left_eye[1] + right_eye[1]) // 2
    )

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

    # -----------------------------
    # 얼굴 전체 Landmark
    # -----------------------------
    xs = [
        int(lm.x * w)
        for lm in landmarks.landmark
    ]

    ys = [
        int(lm.y * h)
        for lm in landmarks.landmark
    ]

    face_width = max(xs) - min(xs)

    # -----------------------------
    # Crop
    # -----------------------------
    x1 = max(center[0] - 80, 0)
    y1 = max(center[1] - 90, 0)

    x2 = min(center[0] + 80, w)
    y2 = min(center[1] + 110, h)

    crop = aligned[y1:y2, x1:x2]

    if crop.size == 0:
        fail_count += 1
        continue

    crop = cv2.resize(
        crop,
        (112, 112)
    )

    # -----------------------------
    # Blur 검사
    # -----------------------------
    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY
    )

    blur_score = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    blur_ok = blur_score > 10

    # -----------------------------
    # Face Size 검사
    # -----------------------------
    size_ok = face_width > 60

    # -----------------------------
    # Rotation 검사
    # -----------------------------
    rotation_ok = abs(angle) < 20

    # -----------------------------
    # 저장
    # -----------------------------
    filename = os.path.basename(image_path)

    if blur_ok and size_ok and rotation_ok:

        result = "PASS"

        pass_count += 1

        save_path = os.path.join(
            pass_dir,
            filename
        )

    else:

        result = "FAIL"

        fail_count += 1

        save_path = os.path.join(
            fail_dir,
            filename
        )

    cv2.imwrite(
        save_path,
        crop
    )

    writer.writerow([
    filename,
    round(blur_score, 2),
    face_width,
    round(angle, 2),
    result])
    
    if idx % 100 == 0:
        print(f"{idx}/{len(image_list)}")

print("\n========== RESULT ==========")
print(f"PASS : {pass_count}")
print(f"FAIL : {fail_count}")
print(f"TOTAL: {pass_count + fail_count}")

print("\n========== RESULT ==========")
print(f"PASS : {pass_count}")
print(f"FAIL : {fail_count}")
print(f"TOTAL: {pass_count + fail_count}")

log_file.close()
face_mesh.close()