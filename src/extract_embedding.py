import os
import pickle
import cv2
import numpy as np
from glob import glob

import onnxruntime as ort

# -----------------------------
# ArcFace ONNX 모델
# -----------------------------
MODEL_PATH = "models/w600k_r50.onnx"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model not found : {MODEL_PATH}"
    )

session = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)

input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

# -----------------------------
# 입력 이미지
# -----------------------------
image_dir = "output/final_dataset"

image_list = sorted(
    glob(
        os.path.join(image_dir, "*.jpg")
    )
)

print(f"Images : {len(image_list)}")

# -----------------------------
# 저장 폴더
# -----------------------------
save_dir = "output/embeddings"

os.makedirs(save_dir, exist_ok=True)

# -----------------------------
# 반복
# -----------------------------
for idx, image_path in enumerate(image_list):

    img = cv2.imread(image_path)

    if img is None:
        continue

    img = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )

    img = img.astype(np.float32)

    # ArcFace 입력 정규화
    img = (img - 127.5) / 127.5

    img = np.transpose(
        img,
        (2, 0, 1)
    )

    img = np.expand_dims(
        img,
        axis=0
    )

    embedding = session.run(
        [output_name],
        {input_name: img}
    )[0][0]

    # L2 Normalize
    embedding = embedding / np.linalg.norm(embedding)

    filename = os.path.splitext(
        os.path.basename(image_path)
    )[0]

    save_path = os.path.join(
        save_dir,
        filename + ".pkl"
    )

    with open(save_path, "wb") as f:
        pickle.dump(
            embedding,
            f
        )

    if idx % 100 == 0:
        print(f"{idx}/{len(image_list)}")

print("\nFinished!")
print(f"Saved : {len(image_list)} embeddings")