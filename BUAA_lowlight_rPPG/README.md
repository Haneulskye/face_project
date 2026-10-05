# BUAA-MIHR Low-Light rPPG

Low-light remote photoplethysmography (rPPG) estimation using the
BUAA-MIHR dataset.

This project investigates whether recurrent temporal modeling can improve
rPPG estimation when low illumination weakens facial color variations.
EfficientPhys is used as the baseline, and GRU/BiGRU-based temporal
models are evaluated under subject-independent low-light conditions.

## 1. Method

```text
RGB Video (150 frames)
        ↓
Temporal Difference
        ↓
EfficientPhys Backbone
(TSM + Convolution + Spatial Attention)
        ↓
128-D Feature Sequence
        ↓
GRU / BiGRU
        ↓
Predicted BVP / rPPG Signal
        ↓
Heart Rate Estimation
```

EfficientPhys provides local temporal interaction through TSM.
GRU and BiGRU are added after the EfficientPhys backbone to model
sequence-level temporal dependencies.

### Models

- **EfficientPhys** — baseline
- **EfficientPhys + GRU** — unidirectional temporal model
- **EfficientPhys + BiGRU** — bidirectional temporal model
- **Parameter-Matched MLP** — model-capacity control

The main hypothesis is that recurrent temporal context can improve
rPPG estimation when frame-level physiological information becomes
weak or noisy under low illumination.

## 2. Dataset

Experiments use the **BUAA-MIHR** dataset.

Primary low-light validation conditions:

```text
1.0 / 1.6 / 2.5 / 4.0 lux
```

Typical video properties:

| Item | Value |
|---|---:|
| Resolution | 640 × 480 |
| Frame rate | 30 FPS |
| Duration | ~60 s |
| Frames | ~1800 |
| PPG sampling rate | ~60 Hz |

The original BUAA-MIHR dataset is **not included in this repository**.
It must be obtained through the official dataset access procedure and
used according to its release agreement.

## 3. Experimental Setup

| Setting | Value |
|---|---:|
| Input resolution | 36 × 36 |
| Window size | 150 frames |
| Stride | 75 frames |
| Frame depth | 10 |
| Batch size | 2 |
| Epochs | 10 |
| Optimizer | Adam |
| Learning rate | 1 × 10⁻⁴ |

A 150-frame window corresponds to approximately 5 seconds at 30 FPS.
EfficientPhys TSM processes each window using 10-frame temporal blocks.

### Subject-Independent Splits

| Split | Validation Subjects | Training Subjects |
|---|---|---|
| A | 07, 09 | 01, 02, 03, 05, 06, 08, 10, 11, 12, 13 |
| B | 05, 11 | 01, 02, 03, 06, 07, 08, 09, 10, 12, 13 |
| C | 03, 12 | 01, 02, 05, 06, 07, 08, 09, 10, 11, 13 |

Validation subjects are excluded from the corresponding training set.

Low-light validation is restricted with:

```bash
--val_max_lux 4.0
```

## 4. Evaluation

Training maximizes the Pearson correlation between predicted and
ground-truth BVP waveforms.

```text
Loss = 1 - Pearson correlation
```

The final evaluation uses six metrics:

- Pearson Correlation
- HR MAE
- HR RMSE
- HR MAPE
- ACC@5bpm
- SNR

Pearson and HR MAE are treated as the primary metrics.

The final repeated experiment uses:

```text
10 random seeds (42–51)
×
3 subject-independent splits (A/B/C)
=
30 paired conditions
```

## 5. Results

### Multi-Seed Evaluation

| Model | Pearson ↑ | HR MAE ↓ | HR RMSE ↓ | HR MAPE ↓ | ACC@5bpm ↑ | SNR ↑ |
|---|---:|---:|---:|---:|---:|---:|
| EfficientPhys | 0.083 ± 0.044 | 40.69 ± 9.49 | 59.69 ± 8.76 | 48.92 ± 10.09 | 32.9 ± 13.5 | -6.69 ± 1.09 |
| EfficientPhys + GRU | 0.096 ± 0.040 | 24.40 ± 6.51 | 34.88 ± 7.93 | 29.07 ± 6.95 | 32.6 ± 11.7 | -6.59 ± 1.00 |
| EfficientPhys + BiGRU | **0.112 ± 0.040** | **20.37 ± 6.09** | **30.54 ± 9.12** | **24.48 ± 7.51** | **40.0 ± 11.5** | **-6.02 ± 0.99** |

BiGRU achieved the best mean performance across all six metrics.

In paired comparisons:

- BiGRU vs. EfficientPhys: HR MAE improved in **30/30** conditions and Pearson in **29/30**.
- BiGRU vs. GRU: HR MAE improved in **24/30** conditions and Pearson in **23/30**.

These results show that the improvement is not limited to a particular
random seed or subject split.

## 6. Parameter-Matched Control

Adding recurrent modules also increases model capacity.

### Trainable Parameters

| Model | Trainable Parameters |
|---|---:|
| EfficientPhys | 467,331 |
| EfficientPhys + GRU | 566,403 |
| EfficientPhys + BiGRU | 665,603 |

BiGRU contains approximately **42.4% more trainable parameters** than
the EfficientPhys baseline.

To examine whether the performance improvement is explained only by
increased model capacity, a **Parameter-Matched MLP** was constructed
with the same number of trainable parameters as BiGRU but without
recurrent temporal modeling.

The control experiment was conducted under:

```text
Seed  = 42
Split = A
Validation subjects = 07, 09
```

| Model | Trainable Parameters | Pearson |
|---|---:|---:|
| EfficientPhys | 467,331 | 0.1134 |
| EfficientPhys + GRU | 566,403 | 0.1168 |
| Parameter-Matched MLP | 665,603 | 0.1119 |
| EfficientPhys + BiGRU | 665,603 | **0.1303** |

The Parameter-Matched MLP had the same number of parameters as BiGRU
but did not reproduce the BiGRU improvement. It also performed below
the EfficientPhys baseline in this control condition.

This result suggests that the observed improvement cannot be explained
by parameter count alone and supports the contribution of recurrent
temporal modeling.

> **Note:** This is a separate single-condition control experiment.
> Its Pearson values should not be directly compared with the
> 30-condition averages in Section 5.

## 7. Training

Example BiGRU training configuration:

```bash
python train.py \
  --model efficientphys_bigru \
  --window_size 150 \
  --stride 75 \
  --frame_depth 10 \
  --batch_size 2 \
  --epochs 10 \
  --max_train_windows 120 \
  --max_val_windows 80 \
  --val_max_lux 4.0 \
  --device cuda
```

## 8. Setup

Current experimental environment:

```text
Python      : 3.13.13
PyTorch     : 2.12.0+cu130
Torchvision : 0.27.0+cu130
CUDA        : 13.0
GPU         : NVIDIA RTX 5090
NumPy       : 2.4.6
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set the local BUAA-MIHR path:

```bash
python set_data_path.py --data_root /path/to/BUAA-MIHR
```

Do not commit the original dataset or user-specific absolute paths.

## 9. Repository Structure

```text
BUAA_lowlight_rPPG/
├── README.md
├── requirements.txt
├── train.py
├── set_data_path.py
├── datasets/
│   └── buaa_dataset_fast.py
└── buaa_experiment/
    ├── train_subjects.txt
    └── val_subjects.txt
```

## 10. Future Work

- Cross-dataset evaluation
- Additional low-light and subject conditions
- Multi-ROI experiments
- Lux-specific analysis
- Causal temporal modeling for real-time inference

The current BiGRU model uses both forward and backward temporal context
and is evaluated in an offline window-based setting. Real-time inference
will require a causal temporal model or a restricted past-context design.

