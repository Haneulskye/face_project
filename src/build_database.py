import os
import pickle
from glob import glob

# -----------------------------
# Embedding 폴더
# -----------------------------
embedding_dir = "output/embeddings"

embedding_files = sorted(
    glob(os.path.join(embedding_dir, "*.pkl"))
)

print(f"Embedding Files : {len(embedding_files)}")

# -----------------------------
# Database
# -----------------------------
database = {}

# -----------------------------
# Load
# -----------------------------
for idx, file_path in enumerate(embedding_files):

    with open(file_path, "rb") as f:
        embedding = pickle.load(f)

    name = os.path.splitext(
        os.path.basename(file_path)
    )[0]

    database[name] = embedding

    if idx % 1000 == 0:
        print(f"{idx}/{len(embedding_files)}")

# -----------------------------
# 저장
# -----------------------------
os.makedirs("output/database", exist_ok=True)

save_path = "output/database/database.pkl"

with open(save_path, "wb") as f:
    pickle.dump(database, f)

print("\n========== DONE ==========")
print(f"Total Embeddings : {len(database)}")
print(f"Saved : {save_path}")