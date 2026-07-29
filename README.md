
# AI Virtual Steering Wheel 🚗

Control racing games using your hands through a webcam. This project uses **MediaPipe** for real-time hand tracking, **OpenCV** for computer vision, and **PyNput** to simulate keyboard inputs.

<img width="1200" height="675" alt="steering_linkedin_standalone" src="https://github.com/user-attachments/assets/f47b783c-88e7-4ab3-826d-eb0cbd67025b" />

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
Gaming-Steeringgggg/
├── app.py
├── canera.py
├── config.py
├── logger.py
├── steering_math.py
├── hand_landmarker.task
├── requirements.txt
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/VishalKumar-GitHub/Gaming-Steeringgggg.git
cd Gaming-Steeringgggg
```

### Windows Quick Start (Recommended)

One-click run:

- Double-click `AUTO_RUN_WINDOWS.bat`

or run from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_windows_fast.ps1
```

Manual commands:

Open PowerShell in the project folder, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.local.txt
python app.py
```

Press `Q` to quit.

### macOS / Linux Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### Linux System Packages (Required for OpenCV)

On Debian/Ubuntu, install these first:

```bash
sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0
```

### Install Dependencies

```bash
pip install -r requirements.local.txt
```

---

## Run

```bash
python app.py
```

Press `Q` to quit.

---

## Streamlit Cloud Deploy

Use `streamlit_app.py` as the main file in Streamlit Cloud.
The repo also includes `runtime.txt` to pin Python 3.11 for compatibility.

Dependency files:

- `requirements.txt` -> cloud deploy dependencies (Streamlit only)
- `requirements.local.txt` -> local controller dependencies (`app.py`)

This deploy target is a cloud-safe demo/status page. The real steering controller in `app.py` must be run locally on your Windows desktop because it needs:

- local webcam access
- local keyboard injection into your game window

Local run command (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File .\run_windows_fast.ps1
```

---

## Troubleshooting

### Error: `ImportError: libGL.so.1`

Install Linux OpenCV runtime libraries:

```bash
sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0
```

### Error: `Cannot open camera`

- Close other apps that may already be using your webcam.
- Linux: verify camera access and that `/dev/video0` exists.
- macOS: enable camera permission in System Settings > Privacy & Security > Camera.
- Windows: enable camera permission in Settings > Privacy > Camera.

### Windows PowerShell: script execution is disabled

If activation fails with a script policy error, run PowerShell as your user and use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Warning: `pynput keyboard backend unavailable`

This means keyboard key injection is disabled in the current environment (common in headless/remote sessions).
Hand tracking UI can still run, but steering/brake/accelerate key presses will not be sent to games until a desktop session is available.

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

## License

This project is licensed under the MIT License.

## About Me

**Vishal Kumar**
- [GitHub](https://github.com/VishalKumar-GitHub)

📫 **Follow me** on [Xing](https://www.xing.com/profile/Vishal_Kumar055381/web_profiles?expandNeffi=true) | [LinkedIn](https://www.linkedin.com/in/vishal-kumar-819585275/)
