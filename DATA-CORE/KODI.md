# K.O.D.I (Kinetic OS Device Interface) — Project Blueprint

Goal
- Deliver an offline, real-time hand-gesture interface using the front-facing camera as the core sensor.
- Primary target: Windows 11 (Media Foundation/DirectShow capture). Contingency target: Parrot OS 5.2 VM with USB camera passthrough.

Success criteria
- <100 ms camera-to-action latency on typical hardware; frame rate 30–60 FPS at 640x480 or better.
- Reliable recognition of the initial gesture set (static: open palm, fist, pinch, thumbs up/down; dynamic: swipe L/R/U/D, push, pinch-move drag, rotate for zoom/volume).
- On-device inference only; hotkey to pause/resume; visible feedback overlay; configurable gesture-to-action bindings.

Operating constraints
- No external network reliance; bundle models locally.
- Avoid privileged drivers or kernel hooks; use user-space input injection.
- Keep CPU fallback viable if GPU/accelerator is unavailable.

Phased roadmap (ordered, with contingencies)
1) Workspace & access (blocker)
   - Validate this folder is the project root (Desktop/K.O.D.I(Kinetic OS Device Interface)).
   - Camera access check: Windows -> OpenCV VideoCapture(0) with Media Foundation backend; confirm FPS/resolution. Contingency: if blocked/unavailable, pass the camera into Parrot VM (USB redirection); if hardware still inaccessible, use recorded sample videos for pipeline development until hardware is available.
   - GPU/acceleration check: detect CUDA/DirectML. Contingency: run CPU at reduced resolution/FPS; lock processing to ROI once hands are found.

2) Environment setup (blocker)
   - Create Python 3.11 venv in env/; install: opencv-python, mediapipe, numpy, pynput or keyboard, pywin32 (Windows), pyyaml/jsonschema, pytest.
   - Contingency: if mediapipe wheel fails on Windows, use mediapipe-models + TF Lite runtime with hand_landmarker.task or an ONNX hand pose model via onnxruntime. If OpenCV fails, try opencv-python-headless or DirectShow capture helpers. Parrot: apt install python3-opencv v4l-utils; pip install mediapipe or TF Lite runtime; fallback to ONNX/TF Lite models.

3) Capture pipeline
   - Build capture module with configurable resolution/FPS, frame queue, and frame skipping under load. Add ROI cropping after hand detection to cut latency.
   - Contingency: if latency is high, reduce resolution/FPS, drop frames, or switch backend; in VM, cap to 30 FPS to avoid USB bandwidth issues.

4) Hand landmarking
   - Integrate MediaPipe Hands; normalize 21 landmarks per hand; expose detection confidence.
   - Contingency: if MediaPipe performance/availability is inadequate, swap to TF Lite hand_landmarker.task, an ONNX hand pose model, or a lightweight palm detector + landmark head pair.

5) Gesture definition & classification
   - Static gestures: rule-based angles/distances between landmarks (open, fist, pinch, thumbs up/down).
   - Dynamic gestures: maintain a short temporal buffer (e.g., 10–15 frames) for trajectories (swipe directions, push, pinch-move drag, rotate).
   - Contingency: if accuracy is low, narrow the gesture set; collect a few-shot dataset and train a small classifier (KNN/SVM or simple temporal model). Add debouncing (N consecutive frames) and confidence thresholds.

6) Action mapping & integration
   - Map gestures to system actions via a config file (yaml/json). Windows: SendInput via pynput/pywin32; Parrot: xdotool/wmctrl or Wayland-friendly equivalents; optional local socket for app-specific bindings.
   - Contingency: if direct injection is blocked (UAC/policies), run a small helper with needed privileges or require user confirmation overlay; if Wayland blocks xdotool, use portals/dbus for focused apps.

7) UX feedback & controls
   - Overlay with hand boxes/landmarks and recognized gesture label; optional audio click.
   - Global hotkey (e.g., Ctrl+Alt+K) to pause/resume; CLI flag to start paused; optional tray icon on Windows.
   - Contingency: if overlay conflicts with full-screen apps, provide minimal HUD or console indicators and a reduced update rate.

8) Performance & robustness
   - Measure latency and per-stage timings; target <100 ms end-to-end. Tune exposure/white-balance normalization; add background suppression and ROI locking.
   - Contingency: degrade gracefully (lower FPS/resolution, restrict gestures to highest-signal set) while keeping responsiveness.

9) Packaging & delivery
   - Windows: bundle via PyInstaller or ship venv + launcher script; include configs, models, and a first-run calibration script. Contingency: if PyInstaller fails due to mediapipe binaries, ship zipped venv with a thin runner.
   - Parrot: provide shell launcher, systemd user service optional, and a .desktop entry if GUI is available.

Testing & validation
- Unit tests for gesture math and config parsing; integration tests with sample video clips; logging of confidences and timings.
- Manual test matrix: lighting (bright/dim/backlit), distance (arm-length vs near), single vs dual hand, occlusions, different backgrounds.

Planned project layout (root = this folder)
- PROJECT_BLUEPRINT.md (this document)
- src/kodi/ (capture.py, landmarks.py, gestures.py, actions.py, ui.py, config.py)
- models/ (hand_landmarker.task, alt ONNX/TF Lite models)
- config/ (gesture_bindings.yaml, runtime defaults)
- scripts/ (setup_env, camera_probe, run_kodi, package)
- tests/ (unit + sample video integration tests)
- docs/ (usage, API notes, calibration guide)
- assets/ (icons/overlays)
- data/ (recorded samples; keep private if sensitive)
- env/ (local venv if not packaging)

Immediate next steps after this blueprint
1) Create Python venv in env/ and install OpenCV + MediaPipe and support libs.
2) Write camera probe script to verify Windows access; if it fails, configure Parrot VM USB passthrough and retest with v4l2-ctl.
3) Scaffold src/kodi modules and default config; implement capture + MediaPipe + static gesture recognition.
4) Wire gesture-to-action bindings (keyboard/mouse) and add hotkey toggle.
5) Add overlay HUD and debouncing; tune thresholds with sample recordings.
6) Package (PyInstaller or zipped venv) and run the test matrix.