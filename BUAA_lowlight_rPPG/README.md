BUAA-MIHR Low-Light rPPG
Overview
This project investigates robust remote photoplethysmography (rPPG)
estimation under low-light conditions using the BUAA-MIHR dataset.
The main objective is to improve rPPG estimation when insufficient
illumination makes subtle facial skin-color variations difficult to
observe. The current work focuses on whether temporal modeling can
stabilize weak or noisy physiological signals under challenging
low-light conditions.
Current model comparisons include:
- EfficientPhys
- EfficientPhys + BiGRU
- EfficientPhys + GRU (planned ablation)
- Quantization-Aware Training (QAT) variants
- Multi-ROI variants (planned ablation)
The primary hypothesis is that additional temporal context can improve
rPPG estimation under low illumination.
Pipeline
BUAA-MIHR RGB Video
        |
        v
Frame Extraction
        |
        v
Resize / Normalize
        |
        v
Temporal Window (150 frames)
        |
        v
EfficientPhys
        |
        v
Temporal Modeling (BiGRU)
        |
        v
Predicted rPPG / BVP Signal
        |
        v
Heart Rate Estimation
The current BUAA loader uses the full RGB frame. Multi-ROI processing
using forehead and cheek regions is planned as an ablation experiment.
Dataset
BUAA-MIHR
BUAA-MIHR is used to evaluate rPPG estimation under different
illumination conditions, with particular emphasis on low-light
environments.
The dataset is provided by the IR & MCT Lab, School of Automation
Science and Electrical Engineering, Beihang University (BUAA), for
academic research according to the BUAA-MIHR Database Release Agreement.
The primary low-light validation conditions used in this project are:
1.0 / 1.6 / 2.5 / 4.0 lux
Example videos used in the current pipeline have approximately:
- Resolution: 640 × 480
- Frame rate: 30 FPS
- Duration: 60 seconds
- Frames per video: 1800
The provided physiological reference data contains the PPG waveform,
sampling frequency, and detected pulse peaks. The examined PPG reference
signal is sampled at approximately 60 Hz and is aligned with the RGB
video for training and evaluation.
Dataset Availability
The original BUAA-MIHR dataset is not included in this repository.
Users must obtain access through the official BUAA-MIHR dataset access
procedure and comply with the applicable usage terms. This repository
contains only code and configuration for the experimental pipeline.
Do not commit the original BUAA-MIHR videos or physiological data to
this repository.
Data Processing
The current dataset loader is:
datasets/buaa_dataset_fast.py
Main preprocessing settings:
  Setting                      Value
  Temporal window         150 frames
  Stride                   75 frames
  Input resolution         112 × 112
  Channels                       RGB
  Pixel normalization       \(0, 1\)
At approximately 30 FPS, 150 frames correspond to about 5 seconds.
Model input for one temporal window:
(T, C, H, W) = (150, 3, 112, 112)
The loader also calculates image-quality information such as brightness,
blur score, dark-pixel ratio, and illumination level.
Evaluation Protocol
Subject-Independent Evaluation
Subject-independent splits are used so that validation subjects are not
included in the corresponding training set.
  Split   Validation Subjects
  A       07, 09
  B       05, 11
  C       03, 12
The primary low-light validation experiment uses:
--val_max_lux 4.0
Therefore, validation is restricted to 1.0, 1.6, 2.5, and 4.0 lux.
Models
EfficientPhys
EfficientPhys is used as the baseline rPPG model.
EfficientPhys + BiGRU
A bidirectional GRU is added after EfficientPhys to investigate whether
temporal context improves estimation when frame-level physiological
information becomes weak or noisy under low illumination.
Conceptually:
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
Quantization-Aware Training
QAT variants have also been evaluated. Current experiments show
relatively small or inconsistent gains compared with temporal modeling,
so QAT is treated as a secondary experiment rather than the primary
contribution.
Experimental Configuration
Typical settings:
Window size       : 150
Stride            : 75
Frame depth       : 10
Batch size        : 2
Epochs            : 10
Max train windows : 120
Max val windows   : 80
Validation lux    : <= 4.0
Device            : CUDA
Example training command:
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
Evaluation Metric
The current training/evaluation loss is based on negative Pearson
correlation:
Loss = 1 - Pearson correlation
A higher Pearson correlation indicates stronger agreement between the
predicted rPPG waveform and the ground-truth physiological signal.
Current Results
Subject Split Results
  Split       Validation     EfficientPhys   EfficientPhys +     Improvement
              Subjects                                 BiGRU 
  A           07, 09                0.1134            0.1304         +0.0170
  B           05, 11                0.0697            0.1376         +0.0679
  C           03, 12                0.0872            0.1485         +0.0613
Average Performance
EfficientPhys mean         : 0.0901
EfficientPhys + BiGRU mean : 0.1388
Absolute improvement       : +0.0487
EfficientPhys + BiGRU outperformed the EfficientPhys baseline in all
three evaluated subject splits.
Multiple random-seed experiments have also shown improvements with
EfficientPhys + BiGRU. More extensive statistical evaluation is still
required before making strong conclusions.
Planned Ablation Experiments
The following experiments are planned to determine whether the observed
improvement is specifically associated with temporal modeling and
bidirectional context.
Temporal Model
EfficientPhys
vs.
EfficientPhys + GRU
vs.
EfficientPhys + BiGRU
Temporal Window
T = 30
T = 75
T = 150
T = 300
ROI
Planned comparison:
1. Full-frame EfficientPhys
2. Full-frame EfficientPhys + BiGRU
3. Multi-ROI EfficientPhys
4. Multi-ROI EfficientPhys + BiGRU
The planned Multi-ROI configuration uses the forehead, left cheek, and
right cheek.
Additional evaluation will include multiple random seeds, multiple
subject splits, lux-specific evaluation, parameter-matched comparisons,
best-checkpoint evaluation, and statistical significance testing.
Parameter Analysis and Parameter-Matched Evaluation
Because adding GRU/BiGRU layers also increases model capacity, performance gains should not be attributed to temporal modeling alone without controlling for the number of trainable parameters.
Current trainable parameter counts are:
Model	Trainable Parameters
EfficientPhys	467,331
EfficientPhys + GRU	566,403
EfficientPhys + BiGRU	665,603


Compared with the EfficientPhys baseline, EfficientPhys + BiGRU contains approximately 42.4% more trainable parameters.
Therefore, an additional parameter-matched experiment is planned to distinguish improvements caused by increased model capacity from improvements associated with temporal and bidirectional temporal modeling. The comparison will use models with more closely matched parameter counts while keeping the low-light evaluation protocol consistent.
Environment
Current experimental environment:
Python      : 3.13.13
PyTorch     : 2.12.0+cu130
Torchvision : 0.27.0+cu130
CUDA        : 13.0
GPU         : NVIDIA RTX 5090
NumPy       : 2.4.6
Install dependencies with:
pip install -r requirements.txt
Dataset Path Setup
After obtaining BUAA-MIHR, configure the local dataset path:
python set_data_path.py \
    --data_root /path/to/BUAA-MIHR
Do not hard-code user-specific absolute paths into files committed to
GitHub.
Repository Structure
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
Future Work
The current repository focuses on low-light rPPG training and
evaluation. Future work will investigate:
- Real-time RGB camera inference
- Continuous heart-rate estimation using a sliding temporal window
- Image-quality monitoring under low illumination
- Multi-ROI processing
- Additional temporal-model ablations
The real-time application is a planned extension and is not part of the
current experimental implementation.
