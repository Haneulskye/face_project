"""
Fine-tunes the iris embedding backbone on CASIA-Iris-Interval instead of
using raw ImageNet features (see backend/iris_auth.py's note on why the
untrained model currently can't tell people apart).

Treats (subject, eye) as a class and trains a normalized-softmax
(CosFace-style) classifier on top of a ResNet18 backbone — the backbone's
penultimate 512-D features become the new iris embedding. Only the
backbone weights are saved; the classification head is training-only
scaffolding, same as how the existing ArcFace face model is used.

Run with:
    source .venv/bin/activate
    python -m src.train_iris_model
"""

import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import DataLoader, Dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "output" / "iris_preprocessed"
OUTPUT_PATH = PROJECT_ROOT / "models" / "iris_resnet18_finetuned.pt"

SEED = 42
EPOCHS = 40
BATCH_SIZE = 32
LR = 1e-4
SCALE = 30.0
MARGIN = 0.2  # CosFace-style additive margin

random.seed(SEED)
torch.manual_seed(SEED)

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")


TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

# Training-only augmentation. The biggest known weakness of this model is the
# domain gap between CASIA's infrared studio captures and a live phone
# camera's visible-light selfie — mild jitter in rotation/crop/brightness
# doesn't close that gap, but it does stop the backbone from overfitting to
# CASIA's exact framing/lighting, which should transfer somewhat better to
# less controlled captures. Kept mild: too aggressive and it stops looking
# like an eye crop at all (see backend/iris_auth.py's crop_iris()).
TRAIN_TRANSFORM = transforms.Compose(
    [
        transforms.RandomResizedCrop(224, scale=(0.85, 1.0), ratio=(0.9, 1.1)),
        transforms.RandomRotation(8),
        transforms.ColorJitter(brightness=0.25, contrast=0.25),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def load_dataset():
    """Returns (samples, class_names) where samples is [(path, class_idx), ...]."""

    classes = []
    class_samples = []

    for subject_dir in sorted(DATA_DIR.iterdir()):
        if not subject_dir.is_dir():
            continue
        for eye in ["L", "R"]:
            eye_dir = subject_dir / eye
            if not eye_dir.exists():
                continue
            paths = sorted(eye_dir.glob("*.jpg"))
            if not paths:
                continue
            classes.append(f"{subject_dir.name}_{eye}")
            class_samples.append(paths)

    return classes, class_samples


def split_train_val(class_samples):
    train, val = [], []
    for class_idx, paths in enumerate(class_samples):
        paths = list(paths)
        random.shuffle(paths)
        if len(paths) >= 2:
            val.append((paths[0], class_idx))
            train.extend((p, class_idx) for p in paths[1:])
        else:
            train.extend((p, class_idx) for p in paths)
    return train, val


class IrisDataset(Dataset):
    def __init__(self, samples, transform=TRANSFORM):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        # output/iris_preprocessed images are already grayscale + CLAHE'd
        # (see src/iris_preprocess.py) — duplicate to RGB, same as inference.
        image = Image.open(path).convert("L").convert("RGB")
        return self.transform(image), label


class NormalizedSoftmaxHead(nn.Module):
    """CosFace-style head: cosine logits with an additive margin on the
    target class, scaled up before cross-entropy. Only used during
    training — the embedding itself is the backbone's output, not this."""

    def __init__(self, in_features, num_classes):
        super().__init__()
        self.weight = nn.Parameter(torch.randn(num_classes, in_features) * 0.01)

    def forward(self, embeddings, labels):
        embeddings = F.normalize(embeddings, dim=1)
        weight = F.normalize(self.weight, dim=1)
        cosine = embeddings @ weight.t()

        margin_mask = F.one_hot(labels, num_classes=cosine.size(1)).float()
        logits = (cosine - margin_mask * MARGIN) * SCALE
        return logits


def build_backbone():
    backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    backbone.fc = nn.Identity()
    return backbone


@torch.no_grad()
def embed(backbone, images):
    backbone.eval()
    return backbone(images.to(DEVICE))


def evaluate_separation(backbone, val_samples):
    """Reports mean genuine (same-class) vs impostor (different-class)
    cosine similarity on the held-out split — the thing that actually
    matters for authentication, not classification accuracy."""

    if len(val_samples) < 2:
        print("Not enough validation samples to evaluate separation.")
        return

    loader = DataLoader(IrisDataset(val_samples), batch_size=64, shuffle=False)
    all_embeddings, all_labels = [], []
    for images, labels in loader:
        feats = F.normalize(embed(backbone, images), dim=1).cpu().numpy()
        all_embeddings.append(feats)
        all_labels.extend(labels.tolist())
    embeddings = np.concatenate(all_embeddings, axis=0)
    labels = np.array(all_labels)

    sims = embeddings @ embeddings.T
    genuine, impostor = [], []
    n = len(labels)
    for i in range(n):
        for j in range(i + 1, n):
            (genuine if labels[i] == labels[j] else impostor).append(sims[i, j])

    genuine = np.array(genuine)
    impostor = np.array(impostor)
    print(f"val genuine pairs: {len(genuine)}, impostor pairs: {len(impostor)}")
    if len(genuine):
        print(f"  genuine similarity  mean={genuine.mean():.4f} min={genuine.min():.4f}")
    print(f"  impostor similarity mean={impostor.mean():.4f} max={impostor.max():.4f}")


def main():
    classes, class_samples = load_dataset()
    print(f"classes: {len(classes)}")

    train_samples, val_samples = split_train_val(class_samples)
    print(f"train images: {len(train_samples)}, val images: {len(val_samples)}")

    train_loader = DataLoader(
        IrisDataset(train_samples, transform=TRAIN_TRANSFORM),
        batch_size=BATCH_SIZE, shuffle=True, num_workers=0
    )

    backbone = build_backbone().to(DEVICE)
    head = NormalizedSoftmaxHead(512, len(classes)).to(DEVICE)

    optimizer = torch.optim.Adam(
        list(backbone.parameters()) + list(head.parameters()), lr=LR
    )

    print("--- before fine-tuning ---")
    evaluate_separation(backbone, val_samples)

    for epoch in range(1, EPOCHS + 1):
        backbone.train()
        total_loss, total_correct, total_n = 0.0, 0, 0

        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)

            embeddings = backbone(images)
            logits = head(embeddings, labels)
            loss = F.cross_entropy(logits, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * images.size(0)
            total_correct += (logits.argmax(dim=1) == labels).sum().item()
            total_n += images.size(0)

        print(
            f"epoch {epoch:2d}/{EPOCHS}  loss={total_loss / total_n:.4f}  "
            f"train_acc={total_correct / total_n:.4f}"
        )

    print("--- after fine-tuning ---")
    evaluate_separation(backbone, val_samples)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(backbone.state_dict(), OUTPUT_PATH)
    print(f"saved backbone weights to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
