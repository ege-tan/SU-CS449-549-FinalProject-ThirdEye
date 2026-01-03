# SU-CS449-549-FinalProject-ThirdEye

> **Low-cost audio navigation for blind and visually impaired pedestrians using computer vision**

ThirdEye is an assistive navigation system that detects yellow road and sidewalk markings to provide real-time spoken guidance. Built on a Raspberry Pi 3 with a camera, it transforms existing visual infrastructure into an accessible wayfinding tool.

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-3-red.svg)](https://www.raspberrypi.org/)

## 🎯 Features

- **Real-time Path Detection**: Identifies yellow road markings using classical computer vision
- **Audio Guidance**: Provides clear spoken commands ("go straight", "stay left/right")
- **Intersection Detection**: Recognizes junction patterns using dot-density heuristics
- **Safety-First Design**: Conservative behavior with explicit "path lost" warnings
- **Low-Cost Hardware**: Runs on affordable Raspberry Pi 3 with basic camera
- **Offline Operation**: No internet required, ensuring privacy and reliability

## 🚀 Quick Start

### Hardware Requirements

- Raspberry Pi 3 (or newer)
- Pi Camera or USB webcam
- Speaker or earpiece for audio output
- Power supply

### Software Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/thirdeye.git
   cd thirdeye
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server**
   ```bash
   python server.py
   ```

4. **Run the client** (in a separate terminal)
   ```bash
   python client.py --server http://localhost:5000 --interval 1.0
   ```

## 📋 Requirements

```txt
flask>=2.0.0
opencv-python>=4.5.0
numpy>=1.19.0
requests>=2.25.0
pyttsx3>=2.90
picamera2  # For Pi Camera (optional)
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────┐
│     Physical Environment                │
│  (Yellow markings, junctions, paths)    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Raspberry Pi 3 (Client)              │
│  • Camera capture                       │
│  • HTTP POST to server                  │
│  • Text-to-speech output                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Analysis Server (Flask)              │
│  • HSV color segmentation               │
│  • Morphological processing             │
│  • Intersection detection               │
│  • Command generation                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    User                                 │
│  Receives audio cues and adjusts path   │
└─────────────────────────────────────────┘
```

## 🔧 Configuration

### Vision Parameters (server.py)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `YELLOW_LOWER` | `[20, 100, 100]` | HSV lower bound for yellow |
| `YELLOW_UPPER` | `[35, 255, 255]` | HSV upper bound for yellow |
| `FRAME_WIDTH` | `320` | Processing width (pixels) |
| `FRAME_HEIGHT` | `240` | Processing height (pixels) |
| Confidence threshold | `1.0%` | Minimum yellow pixels to detect path |
| Dot threshold | `15` | Minimum dots to trigger intersection |

### Client Settings (client.py)

```python
--server http://localhost:5000  # Server URL
--interval 1.0                  # Capture interval in seconds
```

## 🎮 Usage

### Command Vocabulary

- **"System ready. You can start walking."** - Initialization
- **"Go straight."** - Path aligned, continue forward
- **"Stay on left."** - Adjust toward left side
- **"Stay on right."** - Adjust toward right side
- **"Intersection detected."** - Junction or complex pattern ahead
- **"Path lost."** - No marking detected, stop and reorient

### Typical Workflow

1. Start the system in a location with visible yellow markings
2. Wait for "System ready" confirmation
3. Begin walking while following audio commands
4. System provides periodic guidance and warnings
5. Stop immediately when "path lost" is announced

## 🧪 Evaluation Results

Based on controlled testing with N=20 participants:

| Metric | Control | ThirdEye | Improvement |
|--------|---------|----------|-------------|
| Success Rate | 80% | 95% | +15% |
| Completion Time | 112.4s | 93.7s | -17% |
| Navigation Errors | 3.1 | 1.4 | -55% |
| SUS Score | 62.3 | 81.6 | +31% |
| NASA-TLX (workload) | 56.8 | 41.2 | -27% |

*All improvements statistically significant (p < 0.05)*

## 🔬 Technical Details

### Computer Vision Pipeline

1. **Capture**: RGB frame from camera
2. **Preprocessing**: Resize to 320×240, convert to HSV
3. **Segmentation**: Threshold yellow range with morphological operations
4. **Confidence Check**: Calculate yellow pixel ratio
5. **Pattern Analysis**: Detect dots (intersection) vs. lines (path)
6. **Position Estimation**: Compute centroid in lower half of frame
7. **Command Generation**: Map position to guidance command

### Intersection Detection

The system uses a texture-based heuristic to identify junctions:
- Apply edge detection (Canny) to yellow regions
- Find contours of small, roughly-square blobs
- Count "dots" (2-30 pixels, aspect ratio 0.5-2.0)
- Threshold: >15 dots triggers "intersection detected"

## 🛡️ Safety Considerations

- **Conservative Warnings**: System errs on the side of caution
- **Explicit Failure States**: "Path lost" triggers immediate stop
- **Controlled Testing**: Initial evaluation used spotters and safe areas
- **Not a Replacement**: Complements, not replaces, traditional mobility aids

## 🚧 Limitations

- **Environmental Sensitivity**: Performance degrades with shadows, glare, or worn paint
- **Controlled Conditions**: Tested in structured environments, not dynamic streets
- **Color-Based Detection**: May not work with all marking types or colors
- **Proxy Evaluation**: Blindfolded participants differ from actual blind users

## 🔮 Future Work

- [ ] Adaptive thresholding for varying lighting conditions
- [ ] Machine learning-based segmentation
- [ ] Temporal filtering to reduce command jitter
- [ ] Haptic feedback option to reduce audio load
- [ ] Evaluation with visually impaired users and O&M professionals
- [ ] Multi-color marking support
- [ ] GPS integration for route planning

## 📚 Research Background

This project was developed as part of CS 449/549 Human-Computer Interaction coursework, following the Four Pillars of Design:

1. **User Requirements**: Based on accessibility research and mobility needs
2. **Design Process**: Grounded in Norman's design principles and Nielsen heuristics
3. **Implementation**: Practical system using low-cost hardware
4. **Evaluation**: Quantitative testing with real user interaction

For full technical details, see the [Final Project Report](docs/CS449_Interaction_Final_Project_Report.pdf).

## 👥 Team

- **Mehmet Altunören** - User research, interaction design, evaluation
- **Ege Tan** - Computer vision, embedded implementation
- **Sait Kaçmaz** - Prototype/demo preparation, documentation
- **Eren Yıldız** - Backend/server, logging, analysis

## 📖 Citation

```bibtex
@techreport{thirdeye2025,
  title={ThirdEye: Low-Cost Audio Guidance from Yellow Road Markings Using a Raspberry Pi 3},
  author={Altunören, Mehmet and Tan, Ege and Kaçmaz, Sait and Yıldız, Eren},
  year={2025},
  institution={CS 449/549 Human-Computer Interaction}
}
```

## Demonstration Photos
![WhatsApp Image 2026-01-02 at 20 08 46](https://github.com/user-attachments/assets/501c2b8f-5343-4b1b-85e9-d65117e40928)

![WhatsApp Image 2026-01-02 at 20 08 56](https://github.com/user-attachments/assets/c1b43855-31ac-4529-8cf9-3fde70dd4ecd)

---

**Design Motto**: *Designing safer pedestrian guidance without expensive dedicated infrastructure or high-precision GPS.*
