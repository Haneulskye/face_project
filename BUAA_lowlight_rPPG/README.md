# BUAA-MIHR Low-Light rPPG

## 1. Project Overview

This project investigates robust remote photoplethysmography (rPPG)
estimation under low-light conditions using the BUAA-MIHR dataset.

The main objective is to improve rPPG estimation when the facial
appearance and subtle skin-color variations become difficult to observe
because of insufficient illumination.

The current experiments focus on comparing:

- EfficientPhys
- EfficientPhys + GRU (planned ablation)
- EfficientPhys + BiGRU
- Quantization-Aware Training (QAT) variants
- Multi-ROI variants (planned ablation)

The primary hypothesis is that temporal context can help stabilize weak
or noisy frame-level physiological signals under low-light conditions.


---

## 2. Current Pipeline

The current experimental pipeline is:

```text
BUAA-MIHR RGB Video
        |
        v
Frame Extraction
        |
        v
Resize / Normalize
        |
        v
Temporal Window
(150 frames)
        |
        v
EfficientPhys
        |
        v
Temporal Modeling
(BiGRU)
        |
        v
Predicted rPPG / BVP Signal
        |
        v
Heart Rate Estimation
```

The current BUAA loader uses the full RGB frame.

Multi-ROI processing using forehead and cheek regions is planned as an
additional ablation experiment.


---

## 3. Dataset

### BUAA-MIHR

This project uses the BUAA-MIHR dataset to evaluate rPPG estimation
under different illumination conditions, with particular emphasis on
low-light environments.

The dataset is provided by the IR & MCT Lab, School of Automation Science
and Electrical Engineering, Beihang University (BUAA), for academic
research according to the BUAA-MIHR Database Release Agreement.


### Illumination Conditions

The illumination levels used in the current experiments include:

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

The primary low-light validation conditions are:

```text
1.0 / 1.6 / 2.5 / 4.0 lux
```


### Video Configuration

Example videos used in the current pipeline have the following
properties:

- Resolution: 640 × 480
- Frame rate: 30 FPS
- Duration: approximately 60 seconds
- Frames per video: approximately 1800


### Ground-Truth Physiological Signal

The provided PPG reference data contains:

- Sampling frequency (`fs`)
- PPG waveform (`data`)
- Detected pulse peaks (`peaks`)

The PPG reference signal is sampled at approximately 60 Hz in the
examined data.

The reference physiological signal is aligned with the RGB video for
training and evaluation.


### Example Dataset Structure

```text
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
```


### Dataset Availability

The BUAA-MIHR dataset itself is **NOT included in this repository**.

Users must obtain access to BUAA-MIHR through the official dataset
access procedure and comply with its applicable usage terms.

This repository contains only the code and configuration required for
the experimental pipeline.

Do NOT commit the original BUAA-MIHR videos or physiological data to
this repository.


---

## 4. Dataset Processing

The current dataset loader is:

```text
datasets/buaa_dataset_fast.py
```

The processing configuration is:

- Temporal window: 150 frames
- Stride: 75 frames
- Input resolution: 112 × 112
- Channels: RGB
- Pixel normalization: [0, 1]

At approximately 30 FPS:

```text
150 frames ≈ 5 seconds
```

The model input for one temporal window is:

```text
(T, C, H, W) = (150, 3, 112, 112)
```

The loader also calculates image-quality information including:

- Brightness
- Blur score
- Dark-pixel ratio
- Illumination level (lux)


---

## 5. Subject-Independent Evaluation

Subjects currently used in the experiments:

```text
01, 02, 03, 05, 06, 07, 08, 09, 10, 11, 12, 13
```

Subject-independent splits are used so that validation subjects are not
included in the corresponding training set.


### Split A

```text
Validation:
07, 09
```


### Split B

```text
Validation:
05, 11

Training:
01, 02, 03, 06, 07, 08, 09, 10, 12, 13
```


### Split C

```text
Validation:
03, 12

Training:
01, 02, 05, 06, 07, 08, 09, 10, 11, 13
```


---

## 6. Low-Light Evaluation

The primary validation experiment restricts the illumination level using:

```bash
--val_max_lux 4.0
```

Therefore, the primary validation conditions are:

```text
1.0 lux
1.6 lux
2.5 lux
4.0 lux
```

This setting is designed to specifically evaluate rPPG robustness under
challenging low-light conditions.


---

## 7. Models

### EfficientPhys

EfficientPhys is used as the baseline rPPG model.


### EfficientPhys + BiGRU

A bidirectional GRU is added to investigate whether additional temporal
context improves rPPG estimation when frame-level physiological signals
become weak or noisy under low illumination.

The working hypothesis is:

```text
Low illumination
      |
      v
Weak / noisy visual physiological signal
      |
      v
Temporal context modeling
      |
      v
More stable rPPG estimation
```


### QAT

Quantization-Aware Training (QAT) variants have also been evaluated.

Current results suggest that QAT provides relatively small or
inconsistent gains compared with the improvement obtained from temporal
modeling.

Therefore, QAT is currently treated as a secondary experiment rather
than the primary contribution.


---

## 8. Current Experimental Configuration

Typical experimental settings:

```text
Window size       : 150
Stride            : 75
Frame depth       : 10
Batch size        : 2
Epochs            : 10
Max train windows : 120
Max val windows   : 80
Validation lux    : <= 4.0
Device            : CUDA
```

Example:

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


---

## 9. Evaluation Metric

The current training/evaluation loss is based on negative Pearson
correlation:

```text
Loss = 1 - Pearson correlation
```

Therefore:

```text
Pearson correlation = 1 - Loss
```

A higher Pearson correlation indicates stronger agreement between the
predicted rPPG waveform and the ground-truth physiological signal.


---

## 10. Experimental Results

### Subject Split Results

| Split | Validation Subjects | EfficientPhys | EfficientPhys + BiGRU | Improvement |
|------|---------------------|--------------:|----------------------:|------------:|
| A | 07, 09 | 0.1134 | 0.1304 | +0.0170 |
| B | 05, 11 | 0.0697 | 0.1376 | +0.0679 |
| C | 03, 12 | 0.0872 | 0.1485 | +0.0613 |


### Average Performance

```text
EfficientPhys mean        : 0.0901
EfficientPhys + BiGRU mean: 0.1388

Absolute improvement      : +0.0487
```

EfficientPhys + BiGRU outperformed the EfficientPhys baseline in all
three evaluated subject splits.


### Seed Experiments

Multiple random seeds were also evaluated on Split A.

Across the six tested seeds, EfficientPhys + BiGRU consistently
outperformed the EfficientPhys baseline.

Examples include:

| Seed | EfficientPhys | EfficientPhys + BiGRU |
|-----:|--------------:|----------------------:|
| 45 | 0.1663 | 0.1804 |
| 46 | 0.0923 | 0.0972 |
| 47 | 0.1692 | 0.1747 |

These results currently support further investigation of temporal
context modeling for low-light rPPG.

More extensive statistical evaluation is still required before making
strong conclusions.


---

## 11. Planned Ablation Experiments

The following experiments are planned to determine whether the observed
improvement is caused by bidirectional temporal context rather than only
additional model capacity.


### Temporal Model Ablation

```text
EfficientPhys
      vs.
EfficientPhys + GRU
      vs.
EfficientPhys + BiGRU
```

A result following:

```text
EfficientPhys < GRU < BiGRU
```

would provide stronger evidence for the benefit of bidirectional
temporal context.


### Temporal Window Ablation

Planned temporal window comparison:

```text
T = 30
T = 75
T = 150
T = 300
```


### ROI Ablation

Planned comparison:

```text
1. Full Face EfficientPhys

2. Full Face EfficientPhys + BiGRU

3. Multi-ROI EfficientPhys

4. Multi-ROI EfficientPhys + BiGRU
```

The planned Multi-ROI configuration uses:

- Forehead
- Left cheek
- Right cheek

ROI processing is treated as an ablation and is not assumed to improve
performance in advance.


### Additional Evaluation

Future evaluation should also include:

- Parameter-matched model comparisons
- Multiple random seeds
- Multiple subject splits
- Lux-specific evaluation
- Best-checkpoint evaluation
- Statistical significance testing


---

## 12. Environment

The current experimental environment includes:

```text
Python      : 3.13.13
PyTorch     : 2.12.0+cu130
Torchvision : 0.27.0+cu130
CUDA        : 13.0
GPU         : NVIDIA RTX 5090
NumPy       : 2.4.6
```

Install dependencies using:

```bash
pip install -r requirements.txt
```


---

## 13. Dataset Path Setup

After obtaining BUAA-MIHR, configure the local dataset path.

Example:

```bash
python set_data_path.py \
    --data_root /path/to/BUAA-MIHR
```

Do not hard-code user-specific absolute paths into files committed to
GitHub.


---

# Future Application / Real-Time Inference Design

## 14. Application Goal

The trained low-light rPPG model can potentially be extended into a
camera-based heart-rate measurement application.

The user-facing input would simply be an RGB camera stream.

Conceptual pipeline:

```text
Camera
  |
  v
RGB Video
  |
  v
Face Detection / Crop
  |
  v
Resize to 112 × 112
  |
  v
Temporal Buffer
  |
  v
EfficientPhys + BiGRU
  |
  v
Predicted rPPG / BVP
  |
  v
Heart Rate Estimation
  |
  v
BPM
```


---

## 15. Application Input

A potential real-time implementation would use:

```text
Input source     : Smartphone / webcam RGB camera
Frame rate       : approximately 30 FPS
Temporal window  : 150 frames
Window duration  : approximately 5 seconds
Resolution       : 112 × 112
Channels         : RGB
Normalization    : [0, 1]
```

Model input:

```text
(T, C, H, W) = (150, 3, 112, 112)
```

For real-world deployment, face detection and cropping should be applied
before the frames are passed to the model.


---

## 16. Application Output

The primary model output is a predicted rPPG/BVP waveform.

The predicted physiological signal can then be processed to estimate
heart rate.

Potential application outputs include:

```text
Predicted rPPG waveform
Estimated heart rate (BPM)
Illumination condition
Measurement quality
```


Example UI information:

```text
Heart Rate
72 BPM

Illumination
Low

Measurement Quality
Moderate
```


---

## 17. Low-Light Quality Monitoring

Because this project focuses on low-light rPPG, image-quality
information can also be calculated from incoming frames.

Potential quality indicators include:

- Mean brightness
- Dark-pixel ratio
- Blur score
- Estimated illumination condition

Conceptually:

```text
                 +--> EfficientPhys + BiGRU --> rPPG --> BPM
Camera RGB ------|
                 +--> Image Quality Analysis
                       |
                       +--> Brightness
                       +--> Dark ratio
                       +--> Blur
```


---

## 18. Real-Time Sliding Window

Instead of collecting a completely new 5-second video for every
measurement, a real-time application can use a sliding temporal window.

For example:

```text
0-5 s  -> inference
1-6 s  -> inference
2-7 s  -> inference
3-8 s  -> inference
...
```

After the initial buffer is filled, the estimated heart rate can
therefore be continuously updated.


---

## 19. Application Development Status

The real-time application described above is currently a **planned
extension** of the research pipeline.

The current repository focuses on:

```text
BUAA-MIHR
    |
    v
Low-Light rPPG Training
    |
    v
EfficientPhys / Temporal Model Comparison
    |
    v
Evaluation
```

Future work will extend the trained model toward:

```text
Real-Time Camera
      |
      v
Low-Light rPPG Inference
      |
      v
Continuous Heart Rate Estimation
```


---

## 20. Repository Structure

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

The original BUAA-MIHR dataset is intentionally excluded from the
repository.

