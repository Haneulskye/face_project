import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import numpy as np

# 1. 홍채 임베딩 모델 로드 (ResNet18 기반 백본 예시)
class IrisEmbeddingModel:
    def __init__(self):
        self.model = models.resnet18(pretrained=True)
        # 마지막 분류 레이어(fc)를 임베딩 백터 추출용으로 변경 (예: 512차원)
        self.model.fc = torch.nn.Identity()
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