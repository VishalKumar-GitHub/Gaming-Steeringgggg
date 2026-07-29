# AI Virtual Steering Wheel 🚗

Control racing games using your hands through a webcam. This project uses **MediaPipe** for real-time hand tracking, **OpenCV** for computer vision, and **PyNput** to simulate keyboard inputs.

---

## Demo

- 👊 Both Fists → Accelerate (↑ Arrow)
- ✋ Both Open Hands → Brake (↓ Arrow)
- ↖ Tilt Hands Left → Left Arrow
- ↗ Tilt Hands Right → Right Arrow

---

## Features

- Real-time hand tracking using MediaPipe
- Gesture-based vehicle controls
- Virtual steering wheel visualization
- Animated speedometer
- Steering angle detection
- Smooth steering interpolation
- HUD dashboard
- FPS counter
- Hand status detection
- Works with any keyboard-based racing game

---

## Tech Stack

- Python
- OpenCV
- MediaPipe
- NumPy
- PyNput

---

## Project Structure

```
AI-Virtual-Steering-Wheel/
│
├── app.py
├── requirements.txt
├── README.md
└── assets/
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/AI-Virtual-Steering-Wheel.git
cd AI-Virtual-Steering-Wheel
```

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Virtual Environment

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

or

```bash
pip install opencv-python mediapipe numpy pynput
```

---

## Run

```bash
python app.py
```

---

## Controls

| Hand Gesture | Action |
|--------------|--------|
| 👊 Both Fists | Accelerate |
| ✋ Both Open Hands | Brake |
| Tilt Left | Steer Left |
| Tilt Right | Steer Right |

---

## Steering Logic

The project detects both wrists using MediaPipe.

```
Left Wrist ●────────────● Right Wrist
```

The angle between the wrists is calculated using:

```
atan2(dy, dx)
```

Depending on the angle:

- Left Arrow
- Right Arrow
- Straight

---

## Open Hand Detection

MediaPipe detects 21 landmarks.

Finger tips:

```
8
12
16
20
```

Finger PIP joints:

```
6
10
14
18
```

If three or more fingers are extended, the hand is considered **Open**.

Otherwise, it is considered **Closed**.

---

## Dashboard

The interface displays:

- Virtual Steering Wheel
- Speedometer
- Steering Direction
- Steering Angle
- Acceleration Bar
- Brake Bar
- FPS
- Camera Status
- Hand Tracking Status

---

## Requirements

- Python 3.11+
- Webcam
- Windows / Linux / macOS

---

## Future Improvements

- Gear shifting using gestures
- AI cruise control
- Voice commands
- Real vehicle speed integration
- Force feedback support
- Custom gesture mapping
- Steering calibration
- Multiplayer mode

---

## Libraries Used

- OpenCV
- MediaPipe
- NumPy
- PyNput

---

## Author

**Sujal Shah**

B.Tech Computer Engineering (AI/ML)

GitHub: https://github.com/sujalshah593

---

## License

This project is licensed under the MIT License.
