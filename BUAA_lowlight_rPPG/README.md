# BUAA-MIHR EfficientPhys + BiGRU

BUAA-MIHR 저조도 rPPG 실험 코드입니다.

비교 모델:
1. EfficientPhys (Baseline)
2. EfficientPhys + BiGRU

---

## 1. 실험 환경

기존 실험에서 사용한 환경:

- GPU: NVIDIA GeForce RTX 5090
- Python: 3.13.13
- PyTorch: 2.12.0+cu130
- CUDA: 13.0
- torchvision: 0.27.0+cu130
- NumPy: 2.4.6

추가로 필요한 주요 패키지:

```bash
pip install opencv-python imageio-ffmpeg
```

---

## 2. 폴더 구조

코드 폴더:

```text
BUAA_share/
├── train.py
├── set_data_path.py
├── datasets/
│   └── buaa_dataset_fast.py
└── buaa_experiment/
    ├── labels.csv
    ├── train_subjects.txt
    └── val_subjects.txt
```

BUAA-MIHR 원본 데이터셋은 별도로 준비해야 합니다.

예:

```text
BUAA-MIHR/
├── Sub 01/
├── Sub 02/
├── Sub 03/
└── ...
```

---

## 3. BUAA-MIHR 경로 설정

먼저 코드 폴더로 이동합니다.

```bash
cd BUAA_share
```

자신의 BUAA-MIHR 데이터셋 위치를 지정합니다.

```bash
python set_data_path.py \
  --data_root /path/to/BUAA-MIHR
```

예:

```bash
python set_data_path.py \
  --data_root ~/research/BUAA-MIHR
```

이 작업은 `buaa_experiment/labels.csv`의 video_path를 현재 컴퓨터의 BUAA-MIHR 위치에 맞게 변경합니다.

---

## 4. Baseline: EfficientPhys

```bash
python -u train.py \
  --model efficientphys \
  --window_size 150 \
  --stride 75 \
  --frame_depth 10 \
  --batch_size 2 \
  --epochs 10 \
  --max_train_windows 120 \
  --max_val_windows 80 \
  --val_max_lux 4.0 \
  --seed 42 \
  --device cuda
```

---

## 5. EfficientPhys + BiGRU

```bash
python -u train.py \
  --model efficientphys_bigru \
  --window_size 150 \
  --stride 75 \
  --frame_depth 10 \
  --batch_size 2 \
  --epochs 10 \
  --max_train_windows 120 \
  --max_val_windows 80 \
  --val_max_lux 4.0 \
  --seed 42 \
  --device cuda
```

Baseline과 BiGRU는 동일한 학습 조건을 사용합니다.

---

## 6. 기본 Subject Split

Validation subjects:

```text
07
09
```

Training subjects:

```text
01
02
03
05
06
08
10
11
12
13
```

파일 위치:

```text
buaa_experiment/train_subjects.txt
buaa_experiment/val_subjects.txt
```

---

## 7. 주요 실험 설정

```text
window_size       = 150
stride            = 75
frame_depth       = 10
batch_size        = 2
epochs            = 10
max_train_windows = 120
max_val_windows   = 80
val_max_lux       = 4.0
seed              = 42
```

Validation은 4 lux 이하의 low-light 데이터를 대상으로 합니다.

평가 loss:

```text
Loss = 1 - Pearson correlation
```

따라서 Pearson correlation이 높을수록 성능이 좋습니다.

---

## 8. 출력

학습 중 다음과 같은 결과가 출력됩니다.

```text
train loss=...
VAL loss=... pearson=...
val lux loss: 1=... 1.6=... 2.5=... 4=...
```

마지막에는:

```text
FINAL MODEL: efficientphys
BEST VAL LOSS: ...
BEST VAL PEARSON: ...
```

또는:

```text
FINAL MODEL: efficientphys_bigru
BEST VAL LOSS: ...
BEST VAL PEARSON: ...
```

가 출력됩니다.

Checkpoint:

```text
checkpoint_buaa_efficientphys.pt
checkpoint_buaa_efficientphys_bigru.pt
```

---

## 9. 모델 비교

본 실험의 목적은 동일한 EfficientPhys backbone과 동일한 학습 조건에서
BiGRU temporal modeling 추가에 따른 저조도 rPPG 성능 변화를 비교하는 것입니다.

비교:

```text
EfficientPhys
      ↓
EfficientPhys + BiGRU
```

두 모델은 동일한 dataset split, window 설정, validation 조건에서 비교합니다.

