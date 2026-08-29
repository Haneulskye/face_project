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

## Dataset

### BUAA-MIHR

This project uses the BUAA-MIHR dataset for evaluating rPPG estimation
under different illumination conditions, with a particular focus on
low-light environments.

The dataset was provided by the IR & MCT Lab, School of Automation Science
and Electrical Engineering, Beihang University (BUAA), for non-commercial
academic research.

### Dataset Characteristics

BUAA-MIHR contains facial videos recorded under multiple illumination
conditions.

In our experiments, the following illumination levels are available:

- 1.0 lux
- 1.6 lux
- 2.5 lux
- 4.0 lux
- 6.3 lux
- 10 lux
- 15.8 lux
- 25.1 lux
- 39.8 lux
- 63.1 lux
- 100 lux

This allows the model to be evaluated across very dark to relatively
well-illuminated environments.

Our primary low-light evaluation uses:

`1.0, 1.6, 2.5, and 4.0 lux`

### Video Configuration

Example BUAA-MIHR videos used in this project have the following properties:

- Resolution: 640 × 480
- Frame rate: 30 FPS
- Duration: approximately 60 seconds
- Frames per video: approximately 1800

The dataset also provides physiological reference signals that can be
aligned with the RGB video frames.

### Ground-Truth Physiological Signal

The provided PPG reference data contains:

- Sampling frequency (`fs`)
- PPG waveform (`data`)
- Detected pulse peaks (`peaks`)

For example, the PPG signal is sampled at approximately:

`60 Hz`

The PPG signal is temporally aligned with the video frames and used as
the ground-truth BVP target for model training and evaluation.

### Dataset Structure

A typical BUAA-MIHR directory has the following structure:

BUAA-MIHR/
├── Sub 01/
│   ├── Lux 1.0/
│   │   ├── lux1.0_APH.avi
│   │   ├── lux1.0_LXR.avi
│   │   ├── lux1.0_SPH.avi
│   │   ├── lux1.0.csv
│   │   ├── lux1.0_LXR.csv
│   │   ├── lux1.0_PPGData.mat
│   │   └── lux1.0_SPH.csv
│   ├── Lux 1.6/
│   ├── Lux 2.5/
│   └── ...
├── Sub 02/
└── ...

### Dataset Processing

The original videos are converted into temporal windows before being
provided to the rPPG model.

Current configuration:

- Window length: 150 frames
- Stride: 75 frames
- Input frame size: 112 × 112
- Input channels: RGB
- Pixel range: [0, 1]

At 30 FPS, a 150-frame window corresponds to approximately 5 seconds.

The processed model input has the shape:

`(T, C, H, W) = (150, 3, 112, 112)`

### Subject Split

The current experiments use subject-independent train/validation splits.

Subjects used in the experiments:

`01, 02, 03, 05, 06, 07, 08, 09, 10, 11, 12, 13`

Multiple validation subject splits are used to evaluate whether the
temporal model generalizes to unseen subjects.

Example splits:

| Split | Validation Subjects |
|------|---------------------|
| A | 07, 09 |
| B | 05, 11 |
| C | 03, 12 |

The remaining subjects are used for training.

### Low-Light Evaluation

Although the model can be trained using a broader range of illumination
conditions, validation is restricted to low-light samples using:

`--val_max_lux 4.0`

Therefore, the primary validation conditions are:

`1.0 / 1.6 / 2.5 / 4.0 lux`

This setup is intended to specifically measure rPPG robustness under
challenging low-light conditions.

### Dataset Availability

BUAA-MIHR is **not included in this GitHub repository**.

The dataset must be obtained through the official BUAA-MIHR access
procedure and used according to the terms of the BUAA-MIHR Database
Release Agreement.

This repository contains only the code required to process the dataset,
train the models, and reproduce the experimental pipeline.

After obtaining the dataset, configure its local path using:

python set_data_path.py --data_root /path/to/BUAA-MIHR

