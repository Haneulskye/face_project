import os
import cv2
import pickle
import numpy as np
import mediapipe as mp
import onnxruntime as ort
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Database Load
# -----------------------------
with open("output/database/database.pkl", "rb") as f:
    database = pickle.load(f)

print(f"Database : {len(database)}")

# -----------------------------
# ArcFace
# -----------------------------
session = ort.InferenceSession(
    "models/w600k_r50.onnx",
    providers=["CPUExecutionProvider"]
)

input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

# -----------------------------
# MediaPipe
# -----------------------------
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True
)

# -----------------------------
# Camera
# -----------------------------
cap = cv2.VideoCapture(0)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:

        lm = results.multi_face_landmarks[0]

        left_eye = lm.landmark[33]
        right_eye = lm.landmark[263]

        lx = int(left_eye.x * w)
        ly = int(left_eye.y * h)

        rx = int(right_eye.x * w)
        ry = int(right_eye.y * h)

        center = (
            (lx + rx) // 2,
            (ly + ry) // 2
        )

        x1 = max(center[0] - 80, 0)
        y1 = max(center[1] - 90, 0)

        x2 = min(center[0] + 80, w)
        y2 = min(center[1] + 110, h)

        crop = frame[y1:y2, x1:x2]

        if crop.size != 0:

            crop = cv2.resize(crop, (112, 112))

            img = cv2.cvtColor(
                crop,
                cv2.COLOR_BGR2RGB
            )

            img = img.astype(np.float32)

            img = (img - 127.5) / 127.5

            img = np.transpose(img, (2, 0, 1))

            img = np.expand_dims(img, axis=0)

            embedding = session.run(
                [output_name],
                {input_name: img}
            )[0][0]

            embedding /= np.linalg.norm(embedding)

            best_name = "Unknown"
            best_score = -1

            for name, db_emb in database.items():

                score = cosine_similarity(
                    embedding.reshape(1, -1),
                    db_emb.reshape(1, -1)
                )[0][0]

                if score > best_score:
                    best_score = score
                    best_name = name

            if best_score < 0.45:
                best_name = "Unknown"

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0,255,0),
                2
            )

            cv2.putText(
                frame,
                f"{best_name} ({best_score:.2f})",
                (x1, y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,255,0),
                2
            )

    cv2.imshow("Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()

cv2.destroyAllWindows()

face_mesh.close()
