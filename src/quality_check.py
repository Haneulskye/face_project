import cv2
import mediapipe as mp
import numpy as np

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
# 이미지
# -----------------------------
image_path = "datasets/CASIA-WebFace_crop/0000045_001.jpg"

img = cv2.imread(image_path)

if img is None:
    print("Image not found.")
    exit()

h, w, _ = img.shape

rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

results = face_mesh.process(rgb)

if not results.multi_face_landmarks:
    print("No face detected.")
    exit()

landmarks = results.multi_face_landmarks[0]

# --------------------------------
# 1. Blur 검사
# --------------------------------
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

blur_score = cv2.Laplacian(
    gray,
    cv2.CV_64F
).var()

print("Blur Score :", blur_score)

if blur_score < 10:
    print("Blur : FAIL")
else:
    print("Blur : PASS")

# --------------------------------
# 2. Face Size 검사
# --------------------------------
xs = []
ys = []

for lm in landmarks.landmark:

    xs.append(int(lm.x*w))
    ys.append(int(lm.y*h))

face_width = max(xs)-min(xs)
face_height = max(ys)-min(ys)

print("Face Size :", face_width, face_height)

if face_width < 60:

    print("Face Size : FAIL")

else:

    print("Face Size : PASS")

# --------------------------------
# 3. Rotation 검사
# --------------------------------
left_eye = landmarks.landmark[33]
right_eye = landmarks.landmark[263]

left = (
    int(left_eye.x*w),
    int(left_eye.y*h)
)

right = (
    int(right_eye.x*w),
    int(right_eye.y*h)
)

dy = right[1]-left[1]
dx = right[0]-left[0]

angle = np.degrees(
    np.arctan2(dy,dx)
)

print("Rotation :", angle)

if abs(angle) > 20:

    print("Rotation : FAIL")

else:

    print("Rotation : PASS")

# --------------------------------
# Landmark 표시
# --------------------------------
for lm in landmarks.landmark:

    x = int(lm.x*w)
    y = int(lm.y*h)

    cv2.circle(
        img,
        (x,y),
        1,
        (0,0,255),
        -1
    )

cv2.imshow("Quality Check", img)

cv2.waitKey(3000)

cv2.destroyAllWindows()

face_mesh.close()