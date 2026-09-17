import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from pathlib import Path

import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import numpy as np

# CASIA-Iris-Interval로 파인튜닝된 백본 (src/train_iris_model.py로 학습).
# 파일이 없으면(예: 학습 전 클론) ImageNet 사전학습 가중치로 조용히 폴백한다 —
# 동작은 하지만 실제 홍채 구분 능력은 거의 없다 (README/메모리 참고).
FINETUNED_WEIGHTS_PATH = (
    Path(__file__).resolve().parent.parent / "models" / "iris_resnet18_finetuned.pt"
)


# 1. 홍채 임베딩 모델 로드 (ResNet18 기반 백본)
class IrisEmbeddingModel:
    def __init__(self):
        self.model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        # 마지막 분류 레이어(fc)를 임베딩 백터 추출용으로 변경 (512차원)
        self.model.fc = torch.nn.Identity()

        if FINETUNED_WEIGHTS_PATH.exists():
            state_dict = torch.load(FINETUNED_WEIGHTS_PATH, map_location="cpu")
            self.model.load_state_dict(state_dict)

        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def extract_embedding(self, iris_img):
        """
        전처리된 홍채 이미지(numpy array 또는 PIL Image)를 받아
        512차원 임베딩 Vector(numpy)를 반환
        """
        if isinstance(iris_img, np.ndarray):
            iris_img = Image.fromarray(iris_img)

        tensor_img = self.transform(iris_img).unsqueeze(0)
        
        with torch.no_grad():
            embedding = self.model(tensor_img).squeeze().numpy()
            
        return embedding

# 싱글톤 형태의 extractor 객체
iris_extractor = IrisEmbeddingModel()

def extract_iris_embedding(iris_img):
    return iris_extractor.extract_embedding(iris_img)