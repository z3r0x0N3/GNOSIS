#!/usr/bin/env python3
import faulthandler

# Enable diagnostics before any Qt import
faulthandler.enable()

import json
import csv
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import tempfile
import textwrap
import shutil as _shutil
from datetime import date, datetime, timedelta
from pathlib import Path
import math
import random
import struct
import wave

import uuid

import sys
import getpass
import platform
import secrets
import urllib.request
import urllib.error
import base64
import hashlib
import signal
import html
import stat
import time
import errno
from functools import partial
from collections import deque


def resolve_user_shell():
    import pwd

    shell = os.environ.get("SHELL")
    if shell and os.path.exists(shell):
        return shell
    try:
        return pwd.getpwuid(os.getuid()).pw_shell
    except Exception:
        return "/bin/bash"


def _global_qt_preflight():
    """Sanitize environment before importing any Qt modules to avoid XCB BadWindow crashes."""
    # Strip potentially unsafe overrides
    for var in [
        "QT_STYLE_OVERRIDE",
        "QT_QPA_PLATFORMTHEME",
        "QT_AUTO_SCREEN_SCALE_FACTOR",
        "QT_SCALE_FACTOR",
        "QT_SCREEN_SCALE_FACTORS",
        "QT_DEVICE_PIXEL_RATIO",
        "QT_PLUGIN_PATH",
        "QT_LINUX_ACCESSIBILITY_ALWAYS_ON",
    ]:
        os.environ.pop(var, None)
    # Remove library path contamination
    os.environ.pop("LD_LIBRARY_PATH", None)
    # Force stable XCB/software rendering
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    os.environ.setdefault("QT_XCB_GL_INTEGRATION", "none")
    os.environ.setdefault("QT_OPENGL", "software")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
    os.environ.setdefault("GCM_INTERACTIVE", "never")


_global_qt_preflight()

try:
    from PyQt5 import QtCore, QtGui, QtWidgets

    QT6 = False
except ImportError:  # pragma: no cover
    from PyQt6 import QtCore, QtGui, QtWidgets  # type: ignore

    QT6 = True
if not QT6:
    try:
        from PyQt5 import QtMultimedia
    except ImportError:
        QtMultimedia = None
else:  # pragma: no cover
    try:
        from PyQt6 import QtMultimedia
    except ImportError:
        QtMultimedia = None
SoundEffectClass = getattr(QtMultimedia, "QSoundEffect", None) if QtMultimedia is not None else None


PROJECT_ROOT = os.path.expanduser("~/PROJECTS")
USE_BIND_MOUNT = False  # operate directly from PROJECT_ROOT instead of bind-mounting into ~/active_project
ACTIVE_TARGET = os.path.expanduser("~/active_project")
STATUS_OPTIONS = ["In Progress (α)", "Redacted", "Completed", "Pending Review"]
GEMINI_CMD = os.environ.get("GEMINI_CLI", "gemini")
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
DATA_DIR = Path("~/.local/share/focus_manager").expanduser()
CONFIG_DIR = Path("~/.config/focus_manager").expanduser()
DB_PATH = DATA_DIR / "tasks.db"
SAFE_DIR_LOG = DATA_DIR / "git_safe_directory.log"
PROJECT_META_FILE = DATA_DIR / "projects_meta.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
CREDS_FILE = CONFIG_DIR / "credentials.enc"
SYSTEM_LISTS = ["My Day", "Planned", "Important", "Completed"]
AUTOGIT_LOG = Path("~/.autogit/auto_git.log").expanduser()
AUTOGIT_IGNORE = Path("~/.autogit/ignore_globs.txt").expanduser()
AUTOGIT_WATCH = Path("~/.autogit/dirs_main.txt").expanduser()
ACTIVE_PROJECT_PATH = os.path.expanduser("~/active_project")
FOCUS_MARKER = os.path.expanduser("~/.focused_project")
PROJECT_MANIFEST = ".project.json"
AUDIT_LOG = DATA_DIR / "audit.log"
TASKS_WATCH_FILE = DATA_DIR / ".tasks.json"
STABILITY_LOG = CONFIG_DIR / "stability.log"
STABILITY_STATE = CONFIG_DIR / "stability.json"
STABILITY_MARKER = CONFIG_DIR / ".stability_last_run"
DEFAULT_TASK_PROMPT = Path.home() / "PROJECTS" / "SINGULARITY-CONSOLE" / ".PROMPTS" / "ToDo.prompt"
DEFAULT_OVERVIEW_FILES = ("OVERVIEW.md", "overview.md", "README.md", "README.MD", "readme.md")
TASK_STATUS_VALUES = ["pending", "in_progress", "blocked", "review", "completed"]
TASK_ALLOWED_TRANSITIONS = {
    "pending": {"in_progress", "blocked"},
    "in_progress": {"completed", "blocked"},
    "blocked": {"pending"},
    "review": {"completed"},
    "completed": set(),  # terminal per spec
}
TASK_CAP = 5000
NORMAL_SCALE_MAX = 1.20
HIGH_SCALE_THRESHOLD = 1.40
EXTREME_SCALE_THRESHOLD = 1.60
INTERACTION_MIN_HEIGHT = 36
ACCENTS = {
    "cyan": {"primary": "#73f5ff", "glow": "#9ce4ff"},
    "purple": {"primary": "#8f4bff", "glow": "#b69aff"},
    "teal": {"primary": "#2bb8a6", "glow": "#5cd4c6"},
    "sunset": {"primary": "#FFB347", "glow": "#FFD18A"},  # sunset cream orange palette
}
BANNER_ACCENT = "#FF9F43"
GLYPH_MAP = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ",
    "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ",
    "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ",
    "s": "ꜱ", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "ˣ",
    "y": "ʏ", "z": "ᴢ",
    "A": "Λ", "B": "ß", "C": "ↈ", "D": "Đ", "E": "Ξ", "F": "Ғ",
    "G": "Ǥ", "H": "Ħ", "I": "Ⅰ", "J": "Ĵ", "K": "Ҡ", "L": "Ⅼ",
    "M": "⩑", "N": "Ŋ", "O": "Ø", "P": "Ᵽ", "Q": "Ǫ", "R": "ʁ",
    "S": "Ϟ", "T": "Ͳ", "U": "ϓ", "V": "Ѵ", "W": "Ŵ", "X": "✕",
    "Y": "Ұ", "Z": "Ƶ",
}
STATE_STYLES = {
    "Idle": {"color": "#2e9b8f", "label": "Idle"},
    "Loading": {"color": "#3b6aff", "label": "Loading"},
    "Executing": {"color": "#8f4bff", "label": "Executing"},
    "Awaiting User Input": {"color": "#d2a446", "label": "Awaiting User Input"},
    "Error": {"color": "#d14b4b", "label": "Error"},
}
# Lightweight audio orchestrator for PHØTØN feedback
class SoundEngine(QtCore.QObject):
    SOUND_LIBRARY = {
        "click": [
            {"freq": 520, "duration": 0.08, "volume": 0.7},
            {"freq": 560, "duration": 0.09, "volume": 0.65},
        ],
        "tab": [
            {"freq": 620, "duration": 0.12, "volume": 0.75},
            {"freq": 680, "duration": 0.14, "volume": 0.7},
        ],
        "focus": [
            {"freq": 760, "duration": 0.12, "volume": 0.65},
            {"freq": 820, "duration": 0.12, "volume": 0.7},
        ],
        "key": [
            {"freq": 380, "duration": 0.05, "volume": 0.35},
            {"freq": 420, "duration": 0.04, "volume": 0.3},
        ],
        "anim_start": [
            {"freq": 1120, "duration": 0.16, "volume": 0.75},
            {"freq": 1040, "duration": 0.18, "volume": 0.73},
        ],
        "anim_end": [
            {"freq": 900, "duration": 0.14, "volume": 0.72},
            {"freq": 860, "duration": 0.13, "volume": 0.68},
        ],
    }

    def __init__(self, enabled=True, accent_color=ACCENTS["cyan"]["glow"]):
        super().__init__()
        self.enabled = bool(enabled)
        self.accent_color = accent_color
        self.audio_dir = DATA_DIR / "photon_audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.sounds: dict[str, list] = {}
        self._load_library()

    def _load_library(self):
        if not SoundEffectClass:
            return
        for name, variants in self.SOUND_LIBRARY.items():
            prepared = []
            for idx, spec in enumerate(variants):
                file_path = self.audio_dir / f"{name}_{idx}.wav"
                if not file_path.exists():
                    self._generate_wave(file_path, spec)
                effect = SoundEffectClass()
                url = QtCore.QUrl.fromLocalFile(str(file_path))
                effect.setSource(url)
                effect.setLoopCount(1)
                effect.setVolume(min(1.0, spec.get("volume", 0.6)))
                prepared.append(effect)
            if prepared:
                self.sounds[name] = prepared

    def _generate_wave(self, path, spec):
        try:
            sample_rate = spec.get("sample_rate", 22050)
            frames = max(1, int(sample_rate * spec.get("duration", 0.1)))
            amplitude = int(32767 * min(1.0, spec.get("volume", 0.6)))
            with wave.open(str(path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                for i in range(frames):
                    t = i / sample_rate
                    envelope = math.sin(math.pi * (i / frames))
                    value = int(amplitude * envelope * math.sin(2 * math.pi * spec["freq"] * t))
                    wf.writeframes(struct.pack("<h", value))
        except Exception:
            if path.exists():
                try:
                    path.unlink()
                except Exception:
                    pass

    def update_accent(self, accent_color):
        self.accent_color = accent_color

    def play(self, name):
        if not self.enabled:
            return
        variants = self.sounds.get(name)
        if not variants:
            return
        try:
            effect = random.choice(variants)
            effect.stop()
            effect.play()
        except Exception:
            pass


class InteractionSoundFilter(QtCore.QObject):
    def __init__(self, sound_engine):
        super().__init__()
        self.sound_engine = sound_engine

    def eventFilter(self, obj, event):
        if not self.sound_engine or not self.sound_engine.enabled:
            return False
        if event.type() == QtCore.QEvent.MouseButtonRelease and isinstance(obj, QtWidgets.QAbstractButton):
            self.sound_engine.play("click")
        return False


class TerminalProcess(QtCore.QObject):
    output_ready = QtCore.pyqtSignal(bytes)
    terminated = QtCore.pyqtSignal(int)

    def __init__(self, shell=None, cwd=None, env=None, parent=None):
        super().__init__(parent)
        self.shell = shell or resolve_user_shell()
        self.cwd = cwd or os.getcwd()
        self.env = env or os.environ.copy()
        self.process: subprocess.Popen | None = None
        self.master_fd: int | None = None
        self._notifier: QtCore.QSocketNotifier | None = None
        self._poll_timer: QtCore.QTimer | None = None
        self._start_process()

    def _start_process(self):
        try:
            self.master_fd, slave_fd = os.openpty()
        except OSError:
            self.terminated.emit(-1)
            return
        kwargs = {
            "stdin": slave_fd,
            "stdout": slave_fd,
            "stderr": slave_fd,
            "env": self.env,
            "cwd": self.cwd,
            "close_fds": True,
        }
        if hasattr(os, "setsid"):
            kwargs["preexec_fn"] = os.setsid
        cmd = [self.shell, "-i"]
        try:
            self.process = subprocess.Popen(cmd, **kwargs)
        except Exception:
            try:
                os.close(slave_fd)
            except Exception:
                pass
            self.master_fd = None
            self.process = None
            self.terminated.emit(-1)
            return
        try:
            os.close(slave_fd)
        except Exception:
            pass
        if self.master_fd is not None:
            self._notifier = QtCore.QSocketNotifier(self.master_fd, QtCore.QSocketNotifier.Read, self)
            self._notifier.activated.connect(self._read_ready)
        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.setInterval(250)
        self._poll_timer.timeout.connect(self._check_process)
        self._poll_timer.start()

    def _read_ready(self):
        if self.master_fd is None:
            return
        try:
            chunk = os.read(self.master_fd, 4096)
        except OSError as exc:
            if exc.errno in {errno.EIO, errno.EBADF}:
                self._maybe_terminate()
            return
        if not chunk:
            self._maybe_terminate()
            return
        self.output_ready.emit(chunk)

    def _check_process(self):
        if not self.process:
            return
        rc = self.process.poll()
        if rc is not None:
            self._cleanup_resources()
            self.terminated.emit(rc)

    def _maybe_terminate(self):
        if self.process and self.process.poll() is None:
            return
        self._cleanup_resources()

    def _cleanup_resources(self):
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer.deleteLater()
            self._poll_timer = None
        if self._notifier:
            self._notifier.setEnabled(False)
            self._notifier.deleteLater()
            self._notifier = None
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except Exception:
                pass
            self.master_fd = None

    def write(self, data):
        if self.master_fd is None:
            return
        if isinstance(data, str):
            data = data.encode("utf-8")
        try:
            os.write(self.master_fd, data)
        except OSError:
            pass

    def send_signal(self, sig):
        if not self.process or not hasattr(self.process, "pid"):
            return
        try:
            pgid = os.getpgid(self.process.pid)
            os.killpg(pgid, sig)
        except Exception:
            try:
                self.process.send_signal(sig)
            except Exception:
                pass

    def restart(self):
        self.close()
        self._start_process()

    def close(self):
        if self.process:
            try:
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGTERM)
            except Exception:
                pass
            try:
                self.process.wait(timeout=1)
            except Exception:
                pass
            self.process = None
        self._cleanup_resources()


class PhotonTerminalDisplay(QtWidgets.QPlainTextEdit):
    KEY_MAP = {
        QtCore.Qt.Key_Left: "\x1b[D",
        QtCore.Qt.Key_Right: "\x1b[C",
        QtCore.Qt.Key_Up: "\x1b[A",
        QtCore.Qt.Key_Down: "\x1b[B",
        QtCore.Qt.Key_Home: "\x1b[H",
        QtCore.Qt.Key_End: "\x1b[F",
        QtCore.Qt.Key_PageUp: "\x1b[5~",
        QtCore.Qt.Key_PageDown: "\x1b[6~",
        QtCore.Qt.Key_Tab: "\t",
        QtCore.Qt.Key_Backtab: "\x1b[Z",
        QtCore.Qt.Key_Backspace: "\x7f",
        QtCore.Qt.Key_Return: "\r",
        QtCore.Qt.Key_Enter: "\r",
    }

    def __init__(self, on_input, sound_engine, parent=None):
        super().__init__(parent)
        self.on_input = on_input
        self.sound_engine = sound_engine
        self.setReadOnly(True)
        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        self.setUndoRedoEnabled(False)
        self.document().setMaximumBlockCount(8000)
        font = QtGui.QFont("JetBrains Mono")
        font.setStyleHint(QtGui.QFont.Monospace)
        self.setFont(font)
        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Paste):
            clipboard = QtWidgets.QApplication.clipboard()
            payload = clipboard.text()
            if payload:
                self.on_input(payload)
                self.sound_engine.play("key")
            event.accept()
            return
        sequence = self._map_key(event)
        if sequence:
            self.on_input(sequence)
            self.sound_engine.play("key")
            event.accept()
            return
        text = event.text()
        if text:
            self.on_input(text)
            self.sound_engine.play("key")
            event.accept()
            return
        super().keyPressEvent(event)

    def _map_key(self, event):
        if event.key() in self.KEY_MAP:
            return self.KEY_MAP[event.key()]
        return None


class TerminalDoorOverlay(QtWidgets.QWidget):
    def __init__(self, parent, accent_primary, accent_glow):
        super().__init__(parent)
        self.left_panel = QtWidgets.QFrame(self)
        self.right_panel = QtWidgets.QFrame(self)
        self.glitch_line = QtWidgets.QFrame(self)
        self.glitch_line.setFixedHeight(3)
        self.glitch_line.setFixedWidth(80)
        self.glitch_line.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.animation: QtCore.QParallelAnimationGroup | None = None
        self.glitch_metrics: dict[str, float] | None = None
        self.set_accent(accent_primary, accent_glow)
        self.hide()

    def set_accent(self, primary, glow):
        self.left_panel.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {glow});"
        )
        self.right_panel.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {glow}, stop:1 {primary});"
        )
        self.glitch_line.setStyleSheet(f"background-color: {glow};")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.left_panel.setGeometry(0, 0, self.width() // 2, self.height())
        self.right_panel.setGeometry(self.width() // 2, 0, self.width() - self.width() // 2, self.height())
        self.glitch_line.move(self.width() // 2 - self.glitch_line.width() // 2, self.height() // 2)

    def _chaos_noise(self, seed: float, scale: float = 1.0) -> float:
        """Generate bounded chaotic noise using a cosine seed folded through a logistic map."""
        x = math.cos(seed) * 0.5 + 0.5
        for _ in range(2):
            x = 4 * x * (1 - x)
        return (x - 0.5) * 2 * scale

    def _build_glitch_profile(self, width: int, height: int) -> dict[str, float]:
        """Compute glitch metrics (warp, curvature, noise) within safe thresholds."""
        t = time.time()
        seed = t * 0.77 + width * 0.013 + height * 0.021
        max_dev_px = max(8.0, min(28.0, width * 0.14))
        warp_intensity = 0.35 + abs(self._chaos_noise(seed, 0.45))
        warp_curvature = 0.12 + abs(self._chaos_noise(seed + 1.3, 0.33))
        noise_pct = min(0.35, 0.08 + abs(self._chaos_noise(seed + 2.1, 0.28)))
        jitter_px = 4 + abs(self._chaos_noise(seed + 3.7, 12.0))
        flicker_depth = 0.3 + abs(self._chaos_noise(seed + 4.2, 0.5))
        metrics = {
            "warp_intensity": warp_intensity,
            "warp_curvature": warp_curvature,
            "noise_pct": noise_pct,
            "max_deviation_px": max_dev_px,
            "jitter_px": jitter_px,
            "flicker_depth": min(0.8, flicker_depth),
        }
        self.glitch_metrics = metrics
        return metrics

    def start_animation(self, duration, on_finished=None):
        # Stop and dispose any previous animation to avoid dangling Qt objects.
        if self.animation:
            try:
                self.animation.stop()
            except Exception:
                pass
            try:
                self.animation.deleteLater()
            except Exception:
                pass
            self.animation = None
        profile = self._build_glitch_profile(self.width(), self.height())
        width = self.width()
        height = self.height()
        center = width // 2
        start_width = max(32, min(120, width // 6 + int(profile["warp_intensity"] * profile["max_deviation_px"])))
        left_start = QtCore.QRect(center - start_width, 0, start_width, height)
        right_start = QtCore.QRect(center, 0, start_width, height)
        left_end = QtCore.QRect(0, 0, center, height)
        right_end = QtCore.QRect(center, 0, width - center, height)
        self.left_panel.setGeometry(left_start)
        self.right_panel.setGeometry(right_start)
        glitch_start = QtCore.QPoint(
            center - self.glitch_line.width() // 2 + int(self._chaos_noise(time.time(), profile["jitter_px"])),
            height // 2,
        )
        curve_offset = int(profile["warp_curvature"] * profile["max_deviation_px"])
        glitch_end = QtCore.QPoint(
            width - self.glitch_line.width() - 12 + curve_offset,
            max(0, min(height, height // 2 + int(self._chaos_noise(time.time() + 1.1, profile["jitter_px"] / 1.5)))),
        )
        self.glitch_line.move(glitch_start)

        left_anim = QtCore.QPropertyAnimation(self.left_panel, b"geometry")
        left_anim.setDuration(duration)
        left_anim.setStartValue(left_start)
        left_anim.setEndValue(left_end)
        left_anim.setEasingCurve(QtCore.QEasingCurve.InOutCubic)

        right_anim = QtCore.QPropertyAnimation(self.right_panel, b"geometry")
        right_anim.setDuration(duration)
        right_anim.setStartValue(right_start)
        right_anim.setEndValue(right_end)
        right_anim.setEasingCurve(QtCore.QEasingCurve.InOutCubic)

        glitch_anim = QtCore.QPropertyAnimation(self.glitch_line, b"pos")
        glitch_anim.setDuration(duration)
        glitch_anim.setStartValue(glitch_start)
        glitch_anim.setEndValue(glitch_end)
        glitch_anim.setEasingCurve(QtCore.QEasingCurve.Linear)

        # Opacity flicker based on noise injection percentage.
        if not hasattr(self, "glitch_opacity"):
            self.glitch_opacity = QtWidgets.QGraphicsOpacityEffect(self.glitch_line)
            self.glitch_line.setGraphicsEffect(self.glitch_opacity)
        flicker = QtCore.QPropertyAnimation(self.glitch_opacity, b"opacity")
        flicker.setDuration(duration)
        flicker.setKeyValueAt(0.0, 1.0)
        flicker.setKeyValueAt(max(0.05, profile["noise_pct"] / 2), 1.0 - profile["flicker_depth"])
        flicker.setKeyValueAt(min(0.95, 1 - profile["noise_pct"] / 2), 1.0 - profile["flicker_depth"])
        flicker.setKeyValueAt(1.0, 1.0)

        self.animation = QtCore.QParallelAnimationGroup(self)
        self.animation.addAnimation(left_anim)
        self.animation.addAnimation(right_anim)
        self.animation.addAnimation(glitch_anim)
        self.animation.addAnimation(flicker)
        def cleanup():
            self.hide()
            if on_finished:
                try:
                    on_finished()
                except Exception:
                    pass
            if self.animation:
                try:
                    self.animation.deleteLater()
                except Exception:
                    pass
                self.animation = None

        self.animation.finished.connect(cleanup)
        self.show()
        self.raise_()
        self.animation.start()


class PhotonTerminalWidget(QtWidgets.QWidget):
    back_requested = QtCore.pyqtSignal()

    def __init__(self, sound_engine, accent_primary, accent_glow, parent=None, base_env=None):
        super().__init__(parent)
        self.sound_engine = sound_engine
        self.accent_primary = accent_primary
        self.accent_glow = accent_glow
        self.animation_enabled = True
        self.auto_scroll = True
        self.cwd_label = None
        self.base_env = base_env or os.environ.copy()
        self.shell_path = resolve_user_shell()
        self._build_ui()
        self._spawn_terminal()

    def _build_ui(self):
        layout = self._register_layout(QtWidgets.QVBoxLayout(self))
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        control_bar = QtWidgets.QWidget()
        control_layout = QtWidgets.QHBoxLayout(control_bar)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)
        self.singularity_btn = QtWidgets.QPushButton("≪ ⟬ SINGULARITY ⟭")
        self.singularity_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.singularity_btn.setToolTip("Return to the Singularity interface")
        self.singularity_btn.clicked.connect(self._request_return_to_interface)
        control_layout.addWidget(self.singularity_btn)
        control_layout.addStretch(1)
        right_controls = QtWidgets.QWidget()
        right_layout = QtWidgets.QHBoxLayout(right_controls)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.sigint_btn = QtWidgets.QPushButton("SIGINT")
        self.reset_btn = QtWidgets.QPushButton("Reset")
        for btn in (self.clear_btn, self.sigint_btn, self.reset_btn):
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.scroll_lock_checkbox = QtWidgets.QCheckBox("Scroll Lock")
        self.scroll_lock_checkbox.setStyleSheet("color:#9ce4ff;")
        self.scroll_lock_checkbox.setChecked(False)
        right_layout.addWidget(self.clear_btn)
        right_layout.addWidget(self.sigint_btn)
        right_layout.addWidget(self.reset_btn)
        right_layout.addWidget(self.scroll_lock_checkbox)
        control_layout.addWidget(right_controls)
        layout.addWidget(control_bar)
        self.cwd_label = QtWidgets.QLabel("Working directory: …")
        self.cwd_label.setStyleSheet("color:#9ce4ff; font-size:11px;")
        layout.addWidget(self.cwd_label)
        self.display = PhotonTerminalDisplay(self._send_input, sound_engine=self.sound_engine, parent=self)
        self.display.setStyleSheet("background-color:#050a13; border-radius:6px; padding:8px;")
        layout.addWidget(self.display)
        self.status_label = QtWidgets.QLabel("PHØTØN terminal ready")
        self.status_label.setStyleSheet("color:#b3f2ff; font-size:11px;")
        layout.addWidget(self.status_label)
        self.overlay = TerminalDoorOverlay(self, self.accent_primary, self.accent_glow)
        self.clear_btn.clicked.connect(self._clear_display)
        self.sigint_btn.clicked.connect(lambda: self._send_signal(signal.SIGINT))
        self.reset_btn.clicked.connect(self._reset_terminal)
        self.scroll_lock_checkbox.stateChanged.connect(self._on_scroll_lock_changed)

    def _register_layout(self, layout):
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        return layout

    def _spawn_terminal(self):
        env = self.base_env.copy()
        env.setdefault("TERM", "xterm-256color")
        env["SHELL"] = self.shell_path
        shell_name = os.path.basename(self.shell_path or "").lower()
        marker = 'printf "__PHOTON_CWD__%s__\\n" "$PWD"'
        if shell_name in {"bash", "sh"}:
            existing = env.get("PROMPT_COMMAND", "")
            env["PROMPT_COMMAND"] = f"{marker}; {existing}" if existing else marker
        self.terminal_process = TerminalProcess(shell=self.shell_path, cwd=os.getcwd(), env=env, parent=self)
        self.terminal_process.output_ready.connect(self._on_process_output)
        self.terminal_process.terminated.connect(self._on_process_terminated)
        # For non-bash shells we avoid prompt injection to keep shells clean.

    def focus_terminal(self):
        self.display.setFocus()

    def _request_return_to_interface(self):
        if self.back_requested:
            self.back_requested.emit()

    def tab_activated(self):
        if not self.animation_enabled:
            return
        self.status_label.setText("PHØTØN terminal engaging…")
        self.sound_engine.play("anim_start")
        self.overlay.resize(self.size())
        self.overlay.start_animation(
            duration=800,
            on_finished=lambda: (
                self.sound_engine.play("anim_end"),
                self.status_label.setText("PHØTØN terminal ready"),
            ),
        )

    def set_animation_enabled(self, enabled):
        self.animation_enabled = bool(enabled)

    def update_accent(self, primary, glow):
        self.accent_primary = primary
        self.accent_glow = glow
        self.overlay.set_accent(primary, glow)

    def _send_input(self, payload):
        if not payload:
            return
        if isinstance(payload, bytes):
            data = payload
        else:
            data = payload.encode("utf-8")
        self.terminal_process.write(data)

    def _on_scroll_lock_changed(self, state):
        self.auto_scroll = state != QtCore.Qt.Checked

    def _clear_display(self):
        self.display.clear()
        self.status_label.setText("Terminal buffer cleared")

    def _reset_terminal(self):
        self.status_label.setText("Resetting PHØTØN shell…")
        self.terminal_process.restart()

    def _send_signal(self, sig):
        self.terminal_process.send_signal(sig)

    def _on_process_output(self, chunk):
        text = chunk.decode("utf-8", errors="ignore")
        cleaned = self._strip_ansi(text)
        cleaned, cwd = self._extract_cwd(cleaned)
        if cwd:
            self.cwd_label.setText(f"Working directory: {cwd}")
        cursor = self.display.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(cleaned)
        if self.auto_scroll:
            self.display.ensureCursorVisible()

    def _extract_cwd(self, text):
        marker = "__PHOTON_CWD__"
        if marker not in text:
            return text, None
        pieces = text.split(marker)
        rebuilt = [pieces[0]]
        cwd = None
        for fragment in pieces[1:]:
            if "__" in fragment:
                candidate, rest = fragment.split("__", 1)
                cwd = candidate
                rebuilt.append(rest)
            else:
                rebuilt.append(marker + fragment)
        return "".join(rebuilt), cwd

    def _strip_ansi(self, text: str) -> str:
        ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        osc = re.compile(r"\x1B\].*?(?:\x07|\x1b\\)")
        text = ansi_escape.sub("", text)
        text = osc.sub("", text)
        text = text.replace("\r", "")
        return text

    def _on_process_terminated(self, code):
        self.status_label.setText(f"PHØTØN shell terminated (exit {code}).")

    def shutdown(self):
        if hasattr(self, "terminal_process"):
            self.terminal_process.close()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.sound_engine.play("focus")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.resize(self.size())
# UX state model: all operations drive this simple state set; UI listens for updates to keep feedback consistent.
# Runtime error conditions (audit):
# GUI: invalid input, missing paths, permission errors, focus/unfocus failure, import conflicts, blocking ops, selection missing.
# Backend: mount/umount failure, canonical path resolve failure, symlink escapes, non-empty mount target, missing deps (gemini/autogit/git), shell failure.
# Tasks: corrupt DB/schema mismatch, failed writes, concurrent access, invalid names.
# AutoGIT/Git: missing git/autogit, repo not initialized, git safety (dubious ownership), permission mismatch, operations outside root.


def qt_align_center():
    if QT6:
        return QtCore.Qt.AlignmentFlag.AlignCenter
    return QtCore.Qt.AlignCenter


def qt_no_edit(flags):
    if QT6:
        return flags & ~QtCore.Qt.ItemFlag.ItemIsEditable
    return flags & ~QtCore.Qt.ItemIsEditable


def qt_select_rows():
    if QT6:
        return QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
    return QtWidgets.QAbstractItemView.SelectRows


def qt_single_select():
    if QT6:
        return QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
    return QtWidgets.QAbstractItemView.SingleSelection


def today_str():
    return date.today().isoformat()


def now_str():
    return datetime.now().replace(microsecond=0).isoformat()


def glyph_transform(text: str) -> str:
    return " ".join(GLYPH_MAP.get(c, c) for c in text)


def normalize_lines(lines: list[str]) -> list[str]:
    max_width = max(len(line) for line in lines)
    return [
        (" " * ((max_width - len(line)) // 2)) +
        line +
        (" " * (max_width - len(line) - ((max_width - len(line)) // 2)))
        for line in lines
    ]


class StabilitySupervisor:
    """Lightweight self-healing supervisor to reduce segfault risks, governed by debug system."""

    def __init__(self, debug_level="normal", on_event=None, log_fn=None):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        STABILITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()
        self.state.setdefault("failures", [])
        self.state.setdefault("success", [])
        self.state.setdefault("corrections", [])
        self.debug_level = debug_level
        self.on_event = on_event
        self.log_fn = log_fn
        self.crashed_last_run = STABILITY_MARKER.exists()
        self._log("startup", {"status": "init", "crashed_last_run": self.crashed_last_run, "debug_level": self.debug_level})
        if self.crashed_last_run and not self.state.get("force_software_render"):
            # escalate to safe rendering after a detected crash
            self.state["force_software_render"] = True
            self.state["qt_safe_mode"] = True
            self.state["corrections"].append({"key": "force_software_render", "ts": now_str(), "reason": "previous_crash"})
            self._emit("correction", {"key": "force_software_render", "reason": "previous_crash", "mode": self.debug_level})
        self.env_base = self._sanitize_env()
        self._install_faulthandler()
        self._install_qt_message_handler()
        self._set_marker()
        self.qt_safe_mode = self.state.get("qt_safe_mode", False)
        self._save_state()

    def _load_state(self):
        if not STABILITY_STATE.exists():
            return {}
        try:
            return json.loads(STABILITY_STATE.read_text())
        except Exception:
            return {}

    def _save_state(self):
        try:
            STABILITY_STATE.write_text(json.dumps(self.state, indent=2))
        except Exception:
            pass

    def _log(self, scope, data):
        try:
            with open(STABILITY_LOG, "a", encoding="utf-8") as fh:
                fh.write(f"[{now_str()}] {scope}: {json.dumps(data)}\n")
        except Exception:
            pass
        self._emit(scope, data)

    def _emit(self, scope, data):
        if callable(self.on_event):
            try:
                self.on_event(scope, data)
            except Exception:
                pass
        if callable(self.log_fn):
            try:
                self.log_fn(scope, data)
            except Exception:
                pass

    def _set_marker(self):
        try:
            STABILITY_MARKER.write_text(now_str())
        except Exception:
            pass

    def clear_marker(self):
        try:
            if STABILITY_MARKER.exists():
                STABILITY_MARKER.unlink()
        except Exception:
            pass

    def _install_faulthandler(self):
        try:
            faulthandler.enable()
        except Exception:
            pass

    def _install_qt_message_handler(self):
        # Capture Qt warnings/errors to detect unstable plugin/GL states.
        self.qt_messages = deque(maxlen=100)

        def handler(mode, context, message):
            try:
                msg = str(message)
                ctx = getattr(context, "file", "") or ""
                line = getattr(context, "line", 0) or 0
                record = {"level": int(mode), "message": msg, "file": ctx, "line": line}
                self.qt_messages.append(record)
                self._log("qt", record)
                # escalate to safe render if repeated GL/plugin issues surface mid-run
                lowered = msg.lower()
                if any(tok in lowered for tok in ["xcb", "gl", "plugin", "xcbglintegrations"]):
                    self.state["qt_safe_mode"] = True
                    self.state["force_software_render"] = True
                    self.state["corrections"].append({"key": "force_software_render", "ts": now_str(), "reason": "qt_message"})
                    self.env_base = self._sanitize_env()
                    self._save_state()
                    self._emit("correction", {"key": "force_software_render", "reason": "qt_message", "mode": self.debug_level})
            except Exception:
                pass

        try:
            QtCore.qInstallMessageHandler(handler)
        except Exception:
            pass

    def _sanitize_env(self):
        env = os.environ.copy()
        # strip risky overrides
        for var in ["QT_STYLE_OVERRIDE", "LD_PRELOAD", "QT_PLUGIN_PATH"]:
            env.pop(var, None)
        env.setdefault("GIT_TERMINAL_PROMPT", "0")
        env.setdefault("GCM_INTERACTIVE", "never")
        if self.state.get("force_software_render", False):
            env.setdefault("QT_XCB_GL_INTEGRATION", "none")
            env.setdefault("QT_OPENGL", "software")
        if self.debug_level == "diagnostic":
            # capture snapshot for later inspection
            self.state["sanitized_env_snapshot"] = {k: v for k, v in env.items() if k.startswith("QT_") or k.startswith("GIT_")}
            self._save_state()
        return env

    def subprocess_env(self, extra=None):
        merged = self.env_base.copy()
        if extra:
            merged.update(extra)
        return merged

    def record_success(self, key):
        succ = self.state.get("success", [])
        if key not in succ:
            succ.append(key)
        self.state["success"] = succ
        self._save_state()
        self._emit("correction_success", {"key": key, "ts": now_str(), "mode": self.debug_level})

    def record_failure(self, key, data=None):
        self.state.setdefault("failures", [])
        self.state["failures"].append({"key": key, "data": data, "ts": now_str()})
        self._log("failure", {"key": key, "data": data})
        self._save_state()
        self._emit("correction_failure", {"key": key, "data": data, "ts": now_str(), "mode": self.debug_level})

    def monitor_tick(self):
        """Lightweight runtime monitor to demote risky states and promote safer env on the next launch."""
        try:
            if len(self.qt_messages) >= 10 and not self.state.get("qt_escalated"):
                self.state["qt_escalated"] = True
                self.state["force_software_render"] = True
                self.state["corrections"].append({"key": "force_software_render", "ts": now_str(), "reason": "qt_noise"})
                self.env_base = self._sanitize_env()
                self._save_state()
                self._emit("correction", {"key": "force_software_render", "reason": "qt_noise", "mode": self.debug_level})
        except Exception:
            pass


class WrapLayout(QtWidgets.QLayout):
    """Simple flow layout that can wrap child widgets when space is constrained."""

    def __init__(self, parent=None, margin=0, h_spacing=6, v_spacing=6):
        super().__init__(parent)
        self.item_list: list[QtWidgets.QLayoutItem] = []
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        self.wrap_enabled = True
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        while self.count():
            item = self.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.setParent(None)

    def addItem(self, item):
        self.item_list.append(item)

    def addWidget(self, widget, stretch=0):
        super().addWidget(widget)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.do_layout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        x = rect.x() + margins.left()
        y = rect.y() + margins.top()
        line_height = 0
        effective_rect = QtCore.QRect(
            rect.x() + margins.left(),
            rect.y() + margins.top(),
            rect.width() - (margins.left() + margins.right()),
            rect.height() - (margins.top() + margins.bottom()),
        )
        for item in self.item_list:
            widget = item.widget()
            if widget and not widget.isVisible():
                continue
            space_x = self.h_spacing
            space_y = self.v_spacing
            next_x = x + item.sizeHint().width() + space_x
            if self.wrap_enabled and next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height + margins.bottom() - rect.y()

    def set_wrap_enabled(self, enabled: bool):
        self.wrap_enabled = enabled

    def spacing(self):
        return self.h_spacing

    def setSpacing(self, spacing):
        self.h_spacing = spacing
        self.v_spacing = spacing


class CollapseToggle(QtWidgets.QToolButton):
    """Standardized toggle with rotating chevron semantics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setArrowType(QtCore.Qt.RightArrow)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFixedWidth(22)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setStyleSheet(
            "QToolButton { border: 1px solid #283b66; border-radius: 4px; padding: 4px; }"
            "QToolButton:hover { background-color: #1b2742; }"
            "QToolButton:pressed { background-color: #131c2f; }"
        )
        self.toggled.connect(self._update_icon)

    def _update_icon(self, expanded):
        self.setArrowType(QtCore.Qt.DownArrow if expanded else QtCore.Qt.RightArrow)


class CollapsiblePane(QtWidgets.QFrame):
    """Pane with animated collapse/expand and shared toggle UI."""

    def __init__(self, title, content_widget, collapsed=False, on_toggle=None, duration_ms=180, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet("QFrame { border: 1px solid #283b66; border-radius: 6px; }")
        self._on_toggle = on_toggle
        self.duration_ms = max(150, min(250, duration_ms))
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        header = QtWidgets.QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("color: #9ce4ff; font-weight: bold;")
        self.toggle = CollapseToggle()
        self.toggle.setChecked(not collapsed)
        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.toggle)
        layout.addLayout(header)
        self.content_widget = content_widget
        self.content_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.content_area = QtWidgets.QFrame()
        self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        content_layout = QtWidgets.QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.content_widget)
        layout.addWidget(self.content_area)
        self.content_area.setMaximumHeight(self.content_widget.sizeHint().height() if not collapsed else 0)
        self.anim = QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        self.anim.setDuration(self.duration_ms)
        self._expanded = not collapsed
        self.toggle.toggled.connect(self._toggle)
        self.anim.finished.connect(self._on_anim_finished)

    def _toggle(self, expanded):
        self.anim.stop()
        self._expanded = expanded
        target = self.content_widget.sizeHint().height() if expanded else 0
        # Allow the frame to expand fully when open and collapse to zero when closed without clipping children.
        self.content_area.setMaximumHeight(self.content_area.height())
        self.anim.setStartValue(self.content_area.maximumHeight())
        self.anim.setEndValue(target)
        self.anim.start()
        if self._on_toggle:
            self._on_toggle(not expanded)  # persist collapsed state

    def _on_anim_finished(self):
        if self._expanded:
            self.content_area.setMaximumHeight(QtWidgets.QWIDGETSIZE_MAX)
        else:
            self.content_area.setMaximumHeight(0)


class TooltipManager(QtCore.QObject):
    """Centralized tooltip handling with hover/focus delay and suppression support."""

    def __init__(self, parent=None, delay_ms=300):
        super().__init__(parent)
        self.delay_ms = max(100, delay_ms)
        self.registry: dict[QtWidgets.QWidget, str] = {}
        self.suppressed = False
        self._pending_widget: QtWidgets.QWidget | None = None
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._show_pending)

    def register(self, widget, primary, secondary=""):
        if widget is None:
            return
        text = primary if not secondary else f"{primary}\n{secondary}"
        self.registry[widget] = text
        widget.setToolTip(text)
        widget.installEventFilter(self)

    def has(self, widget):
        return widget in self.registry

    def suppress(self):
        self.suppressed = True
        self._timer.stop()
        QtWidgets.QToolTip.hideText()

    def resume(self):
        self.suppressed = False
        self._timer.stop()
        QtWidgets.QToolTip.hideText()

    def _show_pending(self):
        if self.suppressed or not self._pending_widget:
            return
        widget = self._pending_widget
        text = self.registry.get(widget)
        if not text:
            return
        pos = widget.mapToGlobal(widget.rect().center())
        QtWidgets.QToolTip.showText(pos, text, widget)

    def eventFilter(self, obj, event):
        if obj in self.registry:
            etype = event.type()
            if etype in (QtCore.QEvent.Enter, QtCore.QEvent.FocusIn):
                if not self.suppressed:
                    self._pending_widget = obj
                    self._timer.start(self.delay_ms)
            elif etype in (QtCore.QEvent.Leave, QtCore.QEvent.FocusOut, QtCore.QEvent.Hide, QtCore.QEvent.MouseButtonPress, QtCore.QEvent.ContextMenu):
                self._timer.stop()
                QtWidgets.QToolTip.hideText()
                self._pending_widget = None
        return super().eventFilter(obj, event)


class ContextMenuManager(QtCore.QObject):
    """Global context menu surface that renders supplied actions for any payload."""

    def __init__(self, parent=None, tooltip_manager: TooltipManager | None = None):
        super().__init__(parent)
        self.parent = parent
        self.tooltip_manager = tooltip_manager
        self.active_menu: QtWidgets.QMenu | None = None
        self.active_payload = None

    def close_menu(self):
        if self.active_menu:
            try:
                self.active_menu.close()
            except Exception:
                pass
            self.active_menu = None
        if self.tooltip_manager:
            self.tooltip_manager.resume()

    def _clamp_to_screen(self, pos: QtCore.QPoint, size_hint: QtCore.QSize):
        screen = QtWidgets.QApplication.primaryScreen()
        if not screen:
            return pos
        geo = screen.availableGeometry()
        x = min(max(pos.x(), geo.left()), geo.right() - size_hint.width())
        y = min(max(pos.y(), geo.top()), geo.bottom() - size_hint.height())
        return QtCore.QPoint(max(geo.left(), x), max(geo.top(), y))

    def _dispatch_action(self, callback, checked=False):
        try:
            if callback:
                try:
                    callback(checked)
                except TypeError:
                    callback()
        finally:
            self.close_menu()

    def _attach_tooltip_to_action(self, action: QtWidgets.QAction, tooltip: str):
        if not tooltip:
            return
        action.setToolTip(tooltip)

    def open_menu(self, payload, actions: list[dict], global_pos: QtCore.QPoint):
        if not actions:
            return
        self.close_menu()
        if self.tooltip_manager:
            self.tooltip_manager.suppress()
        menu = QtWidgets.QMenu(self.parent)
        for spec in actions:
            label = spec.get("label", "Action")
            action = QtWidgets.QAction(label, menu)
            if spec.get("type") == "toggle":
                action.setCheckable(True)
                action.setChecked(bool(spec.get("checked", False)))
            action.setEnabled(spec.get("enabled", True))
            tooltip = spec.get("tooltip", "")
            self._attach_tooltip_to_action(action, tooltip)
            callback = spec.get("action")
            action.triggered.connect(lambda checked=False, cb=callback: self._dispatch_action(cb, checked))
            menu.addAction(action)
        menu.aboutToHide.connect(self.close_menu)
        self.active_menu = menu
        self.active_payload = payload
        pos = self._clamp_to_screen(global_pos, menu.sizeHint())
        menu.popup(pos)


class ActionRegistry:
    """Shared action registry backing context menus and command palette."""

    def __init__(self):
        self.actions: dict[str, dict] = {}

    def register(self, action_id: str, label: str, handler, tooltip_primary="", tooltip_secondary="", context_filter=None, category="general", toggled=False):
        self.actions[action_id] = {
            "id": action_id,
            "label": label,
            "handler": handler,
            "tooltip_primary": tooltip_primary,
            "tooltip_secondary": tooltip_secondary,
            "context_filter": context_filter,
            "category": category,
            "toggled": toggled,
        }

    def actions_for_payload(self, payload: dict):
        results = []
        for spec in self.actions.values():
            filt = spec.get("context_filter")
            if filt and not filt(payload):
                continue
            results.append(spec)
        return results


class WatchManager:
    """Central watch list across tasks/projects/scopes."""

    def __init__(self):
        self.watched: dict[str, dict] = {}

    def toggle_watch(self, target_id: str, metadata=None):
        metadata = metadata or {}
        if target_id in self.watched:
            self.watched.pop(target_id, None)
            return False
        self.watched[target_id] = {"metadata": metadata, "ts": now_str()}
        return True

    def is_watched(self, target_id: str):
        return target_id in self.watched

    def items(self):
        return self.watched.copy()


class EventBus:
    """Simple in-process event bus with inspection."""

    def __init__(self, limit=500):
        self.limit = limit
        self.events: deque[dict] = deque(maxlen=limit)

    def emit(self, scope: str, payload: dict):
        entry = {"scope": scope, "payload": payload, "ts": now_str()}
        self.events.append(entry)
        return entry

    def list_events(self):
        return list(self.events)


class CommandPalette(QtWidgets.QDialog):
    """Global command palette with fuzzy matching over registered actions."""

    def __init__(self, action_registry: ActionRegistry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.action_registry = action_registry
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Type to search actions...")
        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.search)
        layout.addWidget(self.list_widget)
        self.search.textChanged.connect(self._refresh)
        self.list_widget.itemActivated.connect(self._activate)
        self.resize(520, 420)
        self.payload = None

    def open_for_payload(self, payload=None):
        self.payload = payload or {}
        self._refresh()
        self.search.setFocus()
        self.show()

    def _refresh(self):
        query = self.search.text().lower().strip()
        self.list_widget.clear()
        for spec in self.action_registry.actions_for_payload(self.payload):
            text = spec["label"]
            if query and query not in text.lower():
                continue
            item = QtWidgets.QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, spec)
            tooltip = spec.get("tooltip_primary", "")
            secondary = spec.get("tooltip_secondary", "")
            if tooltip or secondary:
                item.setToolTip(f"{tooltip}\n{secondary}".strip())
            self.list_widget.addItem(item)

    def _activate(self, item):
        spec = item.data(QtCore.Qt.UserRole)
        if not spec:
            return
        handler = spec.get("handler")
        if handler:
            try:
                handler(self.payload)
            except TypeError:
                handler()
        self.accept()


class RuntimeStateStrip(QtWidgets.QFrame):
    """Always-visible runtime state strip."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(12)
        self.project_lbl = QtWidgets.QLabel("Project: None")
        self.state_lbl = QtWidgets.QLabel("State: Idle")
        self.stability_lbl = QtWidgets.QLabel("Stability: Normal")
        self.alert_lbl = QtWidgets.QLabel("Warnings: 0")
        for lbl in (self.project_lbl, self.state_lbl, self.stability_lbl, self.alert_lbl):
            lbl.setStyleSheet("color: #9ce4ff; font-weight: bold;")
            layout.addWidget(lbl)
        layout.addStretch(1)
        self.setToolTip("Runtime heartbeat\nShows active project, state, stability, and warnings.")

    def update_state(self, project="None", state="Idle", stability="Normal", warnings=0):
        self.project_lbl.setText(f"Project: {project or 'None'}")
        self.state_lbl.setText(f"State: {state}")
        self.stability_lbl.setText(f"Stability: {stability}")
        self.alert_lbl.setText(f"Warnings: {warnings}")

class DebugWindow(QtWidgets.QMainWindow):
    """Structured, read-only debug inspector window."""

    new_entry = QtCore.pyqtSignal(str, object, str)
    closed = QtCore.pyqtSignal()

    def __init__(self, scopes):
        super().__init__()
        self.setWindowTitle("Debug Window")
        self.resize(900, 640)
        self.setMinimumSize(600, 400)
        self.scopes = scopes
        self.scope_filters = {scope: True for scope in scopes}
        self.history: list[tuple[str, object, str]] = []
        self.max_entries = 1500
        self.paused = False
        self.auto_scroll = True
        self._pending_refresh = False
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        controls = WrapLayout()
        self.pause_btn = QtWidgets.QPushButton("Pause")
        self.pause_btn.setCheckable(True)
        self.pause_btn.toggled.connect(self._toggle_pause)
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)
        self.autoscroll_box = QtWidgets.QCheckBox("Auto-scroll")
        self.autoscroll_box.setChecked(True)
        self.autoscroll_box.toggled.connect(self._on_autoscroll_toggled)
        controls.addWidget(self.pause_btn)
        controls.addWidget(self.clear_btn)
        controls.addWidget(self.autoscroll_box)
        layout.addLayout(controls)
        scope_row = WrapLayout()
        for scope in scopes:
            cb = QtWidgets.QCheckBox(scope)
            cb.setChecked(True)
            cb.stateChanged.connect(partial(self._on_scope_filter_changed, scope))
            scope_row.addWidget(cb)
        layout.addLayout(scope_row)
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        layout.addWidget(self.log_view)
        self.setCentralWidget(central)
        self.new_entry.connect(self._handle_entry)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    def _toggle_pause(self, paused):
        self.paused = paused
        self.pause_btn.setText("Resume" if paused else "Pause")
        if not paused and self._pending_refresh:
            self._refresh_view()
            self._pending_refresh = False

    def _on_autoscroll_toggled(self, value):
        self.auto_scroll = bool(value)

    def _set_scope_visible(self, scope, visible):
        self.scope_filters[scope] = visible
        self._refresh_view()

    def _on_scope_filter_changed(self, scope, state):
        if not self._ui_alive(self.log_view):
            return
        self._set_scope_visible(scope, bool(state))

    def append_entry(self, scope, data, timestamp):
        self.history.append((scope, data, timestamp))
        if len(self.history) > self.max_entries:
            self.history = self.history[-self.max_entries :]
        if self.paused:
            self._pending_refresh = True
            return
        self._refresh_view()

    def append_history(self, entries):
        for scope, data, ts in entries:
            self.history.append((scope, data, ts))
        if len(self.history) > self.max_entries:
            self.history = self.history[-self.max_entries :]
        self._refresh_view()

    def clear(self):
        self.history.clear()
        self.log_view.clear()

    def _handle_entry(self, scope, data, ts):
        self.append_entry(scope, data, ts)

    def _format_data(self, data, indent=2):
        prefix = " " * indent
        lines = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(self._format_data(value, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}-")
                    lines.extend(self._format_data(item, indent + 2))
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}message: {data}")
        return lines

    def _refresh_view(self):
        lines = []
        for scope, data, ts in self.history:
            if not self.scope_filters.get(scope, True):
                continue
            lines.append(scope.upper())
            lines.append(f"  timestamp: {ts}")
            lines.extend(self._format_data(data, indent=2))
            lines.append("")
        rendered = "\n".join(lines).rstrip()
        self.log_view.setPlainText(rendered)
        if self.auto_scroll:
            sb = self.log_view.verticalScrollBar()
            sb.setValue(sb.maximum())


class WorkspaceGraphView(QtWidgets.QGraphicsView):
    """Lightweight graph viewer that mirrors project structure and tasks."""

    node_selected = QtCore.pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)
        self.node_items: dict[str, QtWidgets.QGraphicsEllipseItem] = {}
        self.labels: dict[str, QtWidgets.QGraphicsSimpleTextItem] = {}
        self.meta: dict[str, dict] = {}

    def clear(self):
        self.scene.clear()
        self.node_items.clear()
        self.labels.clear()
        self.meta.clear()

    def wheelEvent(self, event):
        # Smooth zoom for graph exploration.
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def load_graph(self, nodes: list[dict], edges: list[tuple[str, str]]):
        self.clear()
        if not nodes:
            return
        radius = 28
        padding = 20
        cols = max(1, int(len(nodes) ** 0.5))
        for idx, node in enumerate(nodes):
            row = idx // cols
            col = idx % cols
            x = col * (radius * 3 + padding)
            y = row * (radius * 3 + padding)
            item = self._add_node(node, x, y, radius)
            self.node_items[node["id"]] = item
            self.meta[node["id"]] = node
        for src, dst in edges:
            if src in self.node_items and dst in self.node_items:
                s_item = self.node_items[src]
                d_item = self.node_items[dst]
                s_center = s_item.sceneBoundingRect().center()
                d_center = d_item.sceneBoundingRect().center()
                self.scene.addLine(QtCore.QLineF(s_center, d_center), QtGui.QPen(QtGui.QColor("#355a8a"), 1.4))
        self._auto_center()

    def _add_node(self, node, x, y, radius):
        color = "#2e9b8f" if node.get("type") == "folder" else "#3b6aff"
        if node.get("type") == "task":
            color = "#d2a446" if node.get("status") != "completed" else "#2e9b8f"
        pen = QtGui.QPen(QtGui.QColor(color))
        if node.get("status") != "completed" and node.get("type") == "task":
            pen.setStyle(QtCore.Qt.PenStyle.DotLine)
        pen.setWidth(2)
        ellipse = self.scene.addEllipse(x, y, radius * 2, radius * 2, pen, QtGui.QBrush(QtGui.QColor("#0f1626")))
        label = self.scene.addSimpleText(node.get("label", ""))
        label.setPos(x + 6, y + radius - 6)
        label.setBrush(QtGui.QBrush(QtGui.QColor("#d8f6ff")))
        self.labels[node["id"]] = label
        ellipse.setData(0, node["id"])
        return ellipse

    def _auto_center(self):
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-60, -60, 60, 60))
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def _reset_graph_item_scale(self, item, value=None):
        if item:
            item.setScale(1.0)

    def _on_graph_animation_scale(self, item, value):
        if item:
            item.setScale(value)

    def select_node(self, node_id: str):
        for nid, item in self.node_items.items():
            highlight = QtGui.QPen(QtGui.QColor("#8f4bff") if nid == node_id else QtGui.QColor("#355a8a"))
            highlight.setWidth(3 if nid == node_id else 1)
            item.setPen(highlight)

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        items = self.scene.items(pos)
        for item in items:
            node_id = item.data(0)
            if node_id and node_id in self.meta:
                self.select_node(node_id)
                self.node_selected.emit(node_id, self.meta[node_id])
                break
        super().mousePressEvent(event)


class NetworkGraphView(QtWidgets.QGraphicsView):
    """Flow-centric graph with latency labels along edges."""

    node_selected = QtCore.pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)
        self.node_items: dict[str, QtWidgets.QGraphicsEllipseItem] = {}
        self.edge_items: list[tuple[QtWidgets.QGraphicsLineItem, QtWidgets.QGraphicsSimpleTextItem, str]] = []
        self.meta: dict[str, dict] = {}

    def clear(self):
        self.scene.clear()
        self.node_items.clear()
        self.edge_items.clear()
        self.meta.clear()

    def wheelEvent(self, event):
        factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self.scale(factor, factor)

    def load_graph(self, nodes: list[dict], edges: list[dict]):
        self.clear()
        if not nodes:
            return
        radius = 24
        padding = 24
        cols = max(1, int(len(nodes) ** 0.5))
        for idx, node in enumerate(nodes):
            row = idx // cols
            col = idx % cols
            x = col * (radius * 3 + padding)
            y = row * (radius * 3 + padding)
            item = self._add_node(node, x, y, radius)
            self.node_items[node["id"]] = item
            self.meta[node["id"]] = node
        for edge in edges:
            self._add_edge(edge)
        self._auto_center()

    def _add_node(self, node, x, y, radius):
        color = "#2bb8a6" if node.get("scope") == "project" else "#8f4bff"
        if node.get("status") == "in_progress":
            color = "#FFB347"
        pen = QtGui.QPen(QtGui.QColor(color))
        pen.setWidth(2)
        ellipse = self.scene.addEllipse(x, y, radius * 2, radius * 2, pen, QtGui.QBrush(QtGui.QColor("#0c1526")))
        label = self.scene.addSimpleText(node.get("label", ""))
        label.setPos(x + 6, y + radius - 6)
        label.setBrush(QtGui.QBrush(QtGui.QColor("#d8f6ff")))
        ellipse.setData(0, node["id"])
        return ellipse

    def _add_edge(self, edge):
        src_id = edge.get("src")
        dst_id = edge.get("dst")
        if src_id not in self.node_items or dst_id not in self.node_items:
            return
        s_item = self.node_items[src_id]
        d_item = self.node_items[dst_id]
        s_center = s_item.sceneBoundingRect().center()
        d_center = d_item.sceneBoundingRect().center()
        throughput = edge.get("throughput", 1.0)
        pen = QtGui.QPen(QtGui.QColor(edge.get("color", "#3b6aff")))
        pen.setWidthF(max(1.2, min(6.0, throughput)))
        line = self.scene.addLine(QtCore.QLineF(s_center, d_center), pen)
        latency = edge.get("latency_ms", 0)
        label = self.scene.addSimpleText(f"{int(latency)} ms")
        label.setBrush(QtGui.QBrush(QtGui.QColor("#FFB347")))
        mid = (s_center + d_center) / 2
        label.setPos(mid.x(), mid.y())
        self.edge_items.append((line, label, edge.get("id", "")))

    def _auto_center(self):
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-80, -80, 80, 80))
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def select_node(self, node_id: str):
        for nid, item in self.node_items.items():
            highlight = QtGui.QPen(QtGui.QColor("#FFB347") if nid == node_id else QtGui.QColor("#355a8a"))
            highlight.setWidth(3 if nid == node_id else 1)
            item.setPen(highlight)

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        items = self.scene.items(pos)
        for item in items:
            node_id = item.data(0)
            if node_id and node_id in self.meta:
                self.select_node(node_id)
                self.node_selected.emit(node_id, self.meta[node_id])
                break
        super().mousePressEvent(event)

    def update_latency_label(self, edge_id, latency_ms):
        for line_item, text_item, eid in self.edge_items:
            if eid == edge_id:
                text_item.setText(f"{int(latency_ms)} ms")
                text_item.setScale(1.15)
                QtCore.QTimer.singleShot(200, partial(self._reset_graph_item_scale, text_item))
                break

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        for line_item, text_item, _ in self.edge_items:
            expanded = line_item.boundingRect().adjusted(-6, -6, 6, 6)
            if expanded.contains(pos):
                text_item.setScale(1.2)
                text_item.setBrush(QtGui.QBrush(QtGui.QColor("#FFD18A")))
            else:
                text_item.setScale(1.0)
                text_item.setBrush(QtGui.QBrush(QtGui.QColor("#FFB347")))
        super().mouseMoveEvent(event)

    def _reset_graph_item_scale(self, item, value=None):
        if item:
            item.setScale(1.0)


class TaskStore:
    def __init__(self, db_path=DB_PATH):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self._migrate_tasks_schema()
        self.system_ids = self._ensure_system_lists()
        self.default_list_id = self._ensure_default_list()

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                scope TEXT NOT NULL CHECK(scope IN ('global','project','system')),
                project TEXT,
                system_name TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE,
                source_id TEXT,
                list_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                notes TEXT,
                due_date TEXT,
                reminder TEXT,
                priority INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                project TEXT,
                order_index INTEGER DEFAULT 0,
                recurrence TEXT DEFAULT 'none',
                recurrence_interval INTEGER DEFAULT 0,
                my_day_date TEXT,
                phase_id TEXT,
                operation_id TEXT,
                function_id TEXT,
                job_id TEXT,
                atlas_task_id TEXT,
                source_atlas_file TEXT,
                source_section TEXT,
                dependency_task_ids TEXT,
                estimated_complexity TEXT,
                FOREIGN KEY(list_id) REFERENCES lists(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_list ON tasks(list_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed);")
        self.conn.commit()

    def _migrate_tasks_schema(self):
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(tasks);")
        cols = {row[1] for row in cur.fetchall()}
        if "uuid" not in cols:
            cur.execute("ALTER TABLE tasks ADD COLUMN uuid TEXT;")
        if "source_id" not in cols:
            cur.execute("ALTER TABLE tasks ADD COLUMN source_id TEXT;")
        if "status" not in cols:
            cur.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'pending';")
        # Atlas/phase metadata columns (added for expanded CSV compatibility)
        atlas_cols = {
            "phase_id": "TEXT",
            "operation_id": "TEXT",
            "function_id": "TEXT",
            "job_id": "TEXT",
            "atlas_task_id": "TEXT",
            "source_atlas_file": "TEXT",
            "source_section": "TEXT",
            "dependency_task_ids": "TEXT",
            "estimated_complexity": "TEXT",
        }
        for col, ctype in atlas_cols.items():
            if col not in cols:
                cur.execute(f"ALTER TABLE tasks ADD COLUMN {col} {ctype};")
        self.conn.commit()
        # backfill uuid and status based on completed flag
        cur.execute("SELECT id, uuid, completed, status, source_id FROM tasks;")
        rows = cur.fetchall()
        for row in rows:
            updates = {}
            if not row["uuid"]:
                updates["uuid"] = str(uuid.uuid4())
            if not row["status"]:
                updates["status"] = "completed" if row["completed"] else "pending"
            if not row["source_id"]:
                updates["source_id"] = str(row["id"])
            if updates:
                set_frag = ", ".join(f"{k}=?" for k in updates.keys())
                params = list(updates.values()) + [row["id"]]
                cur.execute(f"UPDATE tasks SET {set_frag} WHERE id=?", params)
        self.conn.commit()
        try:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_uuid ON tasks(uuid);")
            self.conn.commit()
        except Exception:
            pass

    def _ensure_system_lists(self):
        ids = {}
        for name in SYSTEM_LISTS:
            ids[name] = self._get_or_create_list(name, scope="system", system_name=name)
        return ids

    def _ensure_default_list(self):
        return self._get_or_create_list("General", scope="global")

    def _get_or_create_list(self, name, scope="global", project=None, system_name=None):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM lists WHERE name=? AND scope=? AND COALESCE(project,'')=COALESCE(?, '') AND COALESCE(system_name,'')=COALESCE(?, '')",
            (name, scope, project, system_name),
        )
        row = cur.fetchone()
        if row:
            return row["id"]
        now = now_str()
        cur.execute(
            "INSERT INTO lists (name, scope, project, system_name, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (name, scope, project, system_name, now, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def create_list(self, name, scope="global", project=None):
        return self._get_or_create_list(name, scope=scope, project=project)

    def rename_list(self, list_id, new_name):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE lists SET name=?, updated_at=? WHERE id=?",
            (new_name, now_str(), list_id),
        )
        self.conn.commit()

    def lists(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM lists ORDER BY scope DESC, sort_order ASC, name ASC")
        return cur.fetchall()

    def add_task(
        self,
        list_id,
        title,
        project=None,
        notes="",
        due_date=None,
        reminder=None,
        priority=False,
        recurrence="none",
        recurrence_interval=0,
    ):
        if self.count_tasks() >= TASK_CAP:
            raise ValueError(f"Task cap of {TASK_CAP} reached. No new tasks created.")
        cur = self.conn.cursor()
        cur.execute("SELECT COALESCE(MAX(order_index), 0) + 1 FROM tasks WHERE list_id=?", (list_id,))
        next_order = cur.fetchone()[0]
        now = now_str()
        task_uuid = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO tasks (list_id, uuid, title, notes, due_date, reminder, priority, completed, status, created_at, updated_at, project, order_index, recurrence, recurrence_interval)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                list_id,
                task_uuid,
                title,
                notes,
                due_date,
                reminder,
                1 if priority else 0,
                0,
                "pending",
                now,
                now,
                project,
                next_order,
                recurrence,
                recurrence_interval,
            ),
        )
        task_rowid = cur.lastrowid
        cur.execute("UPDATE tasks SET source_id=? WHERE id=?", (str(task_rowid), task_rowid))
        self.conn.commit()
        return task_uuid

    def update_task(self, task_uuid, **fields):
        if not fields:
            return
        task_id = self._task_pk(task_uuid)
        if task_id is None:
            raise ValueError("Task not found.")
        sets = []
        params = []
        for key, value in fields.items():
            sets.append(f"{key}=?")
            params.append(value)
        params.append(task_id)
        sets.append("updated_at=?")
        params.insert(-1, now_str())
        sql = f"UPDATE tasks SET {', '.join(sets)} WHERE id=?"
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()

    def delete_task(self, task_uuid):
        task_id = self._task_pk(task_uuid)
        if task_id is None:
            return
        cur = self.conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def set_complete(self, task_uuid, completed=True):
        task = self.get_task(task_uuid)
        if not task:
            raise ValueError("Task not found.")
        target_status = "completed" if completed else "pending"
        self.transition_status(task_uuid, target_status)

    def reorder(self, task_uuid, list_id, direction):
        task_id = self._task_pk(task_uuid)
        if task_id is None:
            return
        cur = self.conn.cursor()
        cur.execute("SELECT id, order_index FROM tasks WHERE list_id=? ORDER BY order_index", (list_id,))
        rows = cur.fetchall()
        order = [r["id"] for r in rows]
        if task_id not in order:
            return
        idx = order.index(task_id)
        if direction == "up" and idx > 0:
            order[idx - 1], order[idx] = order[idx], order[idx - 1]
        elif direction == "down" and idx < len(order) - 1:
            order[idx + 1], order[idx] = order[idx], order[idx + 1]
        for i, tid in enumerate(order):
            cur.execute("UPDATE tasks SET order_index=?, updated_at=? WHERE id=?", (i + 1, now_str(), tid))
        self.conn.commit()

    def tasks_for_list(self, list_ref):
        cur = self.conn.cursor()
        system = list_ref.get("system")
        today = today_str()
        base_query = "SELECT t.*, l.name AS list_name, l.scope AS list_scope, l.project AS list_project FROM tasks t JOIN lists l ON t.list_id=l.id"
        if system == "My Day":
            cur.execute(base_query + " WHERE t.my_day_date=? ORDER BY t.completed ASC, t.order_index ASC", (today,))
            return [self._with_derived(dict(r)) for r in cur.fetchall()]
        if system == "Planned":
            cur.execute(base_query + " WHERE t.due_date IS NOT NULL ORDER BY t.due_date ASC, t.completed ASC", ())
            return [self._with_derived(dict(r)) for r in cur.fetchall()]
        if system == "Important":
            cur.execute(base_query + " WHERE t.priority=1 ORDER BY t.completed ASC, t.order_index ASC", ())
            return [self._with_derived(dict(r)) for r in cur.fetchall()]
        if system == "Completed":
            cur.execute(base_query + " WHERE t.completed=1 ORDER BY t.completed_at DESC", ())
            return [self._with_derived(dict(r)) for r in cur.fetchall()]
        cur.execute(
            base_query + " WHERE t.list_id=? ORDER BY t.completed ASC, t.order_index ASC",
            (list_ref["id"],),
        )
        return [self._with_derived(dict(r)) for r in cur.fetchall()]

    def _with_derived(self, row):
        status = row.get("status") or ("completed" if row.get("completed") else "pending")
        due = row.get("due_date")
        is_overdue = False
        if due and status != "completed":
            try:
                is_overdue = datetime.strptime(due, "%Y-%m-%d").date() < date.today()
            except Exception:
                is_overdue = False
        derived = {
            "completion_percent": 1.0 if status == "completed" else (0.5 if status == "in_progress" else 0.0),
            "is_overdue": is_overdue,
            "has_blockers": status == "blocked",
        }
        row["derived"] = derived
        return row

    def _normalize_import_status(self, raw_status):
        status = (raw_status or "").strip().lower().replace(" ", "_")
        if status == "":
            return "pending"
        if status == "inprogress":
            status = "in_progress"
        if status not in TASK_STATUS_VALUES:
            return "pending"
        return status

    def _is_atlas_format(self, fieldnames):
        cols = set(fn.strip().lower() for fn in (fieldnames or []))
        required = {"task_name", "task_description"}
        return required.issubset(cols)

    def _task_pk(self, task_uuid):
        if task_uuid is None:
            return None
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM tasks WHERE uuid=?", (task_uuid,))
        row = cur.fetchone()
        return row["id"] if row else None

    def get_task(self, task_uuid):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT t.*, l.name AS list_name, l.scope AS list_scope, l.project AS list_project FROM tasks t JOIN lists l ON t.list_id=l.id WHERE t.uuid=?",
            (task_uuid,),
        )
        row = cur.fetchone()
        return self._with_derived(dict(row)) if row else None

    def add_to_my_day(self, task_uuid):
        self.update_task(task_uuid, my_day_date=today_str())

    def recurrence_next_due(self, row):
        rec = row["recurrence"]
        if not rec or rec == "none":
            return None
        base_date = row["due_date"] or today_str()
        try:
            dt = datetime.strptime(base_date, "%Y-%m-%d").date()
        except ValueError:
            dt = date.today()
        if rec == "daily":
            dt += timedelta(days=1)
        elif rec == "weekly":
            dt += timedelta(days=7)
        elif rec == "monthly":
            dt += timedelta(days=30)
        elif rec == "custom":
            interval = row["recurrence_interval"] or 0
            dt += timedelta(days=max(1, interval))
        return dt.isoformat()

    def spawn_recurrence(self, row):
        next_due = self.recurrence_next_due(row)
        if not next_due:
            return None
        return self.add_task(
            row["list_id"],
            row["title"],
            project=row["project"],
            notes=row["notes"],
            due_date=next_due,
            reminder=row["reminder"],
            priority=bool(row["priority"]),
            recurrence=row["recurrence"],
            recurrence_interval=row["recurrence_interval"],
        )

    def export_csv(self, path, atlas_format=False):
        # Export a richer task payload so import/export is symmetric and lossless for user-facing fields.
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                t.uuid,
                t.source_id,
                t.title,
                t.notes,
                t.due_date,
                t.reminder,
                t.priority,
                t.completed,
                t.status,
                t.created_at,
                t.updated_at,
                t.completed_at,
                t.project,
                t.order_index,
                t.recurrence,
                t.recurrence_interval,
                t.my_day_date,
                t.phase_id,
                t.operation_id,
                t.function_id,
                t.job_id,
                t.atlas_task_id,
                t.source_atlas_file,
                t.source_section,
                t.dependency_task_ids,
                t.estimated_complexity,
                l.name as list_name,
                l.scope as list_scope
            FROM tasks t
            JOIN lists l ON t.list_id=l.id
            WHERE l.scope != 'system'
            ORDER BY t.list_id, t.order_index ASC
            """
        )
        rows = [dict(r) for r in cur.fetchall()]
        if atlas_format:
            atlas_fields = [
                "phase_id",
                "operation_id",
                "function_id",
                "job_id",
                "task_id",
                "task_name",
                "task_description",
                "source_atlas_file",
                "source_section",
                "dependency_task_ids",
                "estimated_complexity",
                "status",
            ]
            with open(path, "w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=atlas_fields)
                writer.writeheader()
                for row in rows:
                    status_raw = row.get("status") or "pending"
                    writer.writerow(
                        {
                            "phase_id": row.get("phase_id") or "",
                            "operation_id": row.get("operation_id") or "",
                            "function_id": row.get("function_id") or "",
                            "job_id": row.get("job_id") or "",
                            "task_id": row.get("atlas_task_id") or row.get("source_id") or "",
                            "task_name": row.get("title") or "",
                            "task_description": row.get("notes") or "",
                            "source_atlas_file": row.get("source_atlas_file") or "",
                            "source_section": row.get("source_section") or "",
                            "dependency_task_ids": row.get("dependency_task_ids") or "",
                            "estimated_complexity": row.get("estimated_complexity") or "",
                            "status": status_raw.replace("_", " ").title(),
                        }
                    )
            return

        fieldnames = [
            "uuid",
            "source_id",
            "title",
            "notes",
            "due_date",
            "reminder",
            "priority",
            "completed",
            "status",
            "created_at",
            "updated_at",
            "completed_at",
            "project",
            "list_name",
            "list_scope",
            "order_index",
            "recurrence",
            "recurrence_interval",
            "my_day_date",
            "phase_id",
            "operation_id",
            "function_id",
            "job_id",
            "atlas_task_id",
            "source_atlas_file",
            "source_section",
            "dependency_task_ids",
            "estimated_complexity",
        ]
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "uuid": row.get("uuid") or "",
                        "source_id": row.get("source_id") or "",
                        "title": row.get("title") or "",
                        "notes": row.get("notes") or "",
                        "due_date": row.get("due_date") or "",
                        "reminder": row.get("reminder") or "",
                        "priority": int(bool(row.get("priority"))),
                        "completed": int(bool(row.get("completed"))),
                        "status": row.get("status") or "pending",
                        "created_at": row.get("created_at") or "",
                        "updated_at": row.get("updated_at") or "",
                        "completed_at": row.get("completed_at") or "",
                        "project": row.get("project") or "",
                        "list_name": row.get("list_name") or "",
                        "list_scope": row.get("list_scope") or "",
                        "order_index": row.get("order_index") if row.get("order_index") is not None else "",
                        "recurrence": row.get("recurrence") or "none",
                        "recurrence_interval": row.get("recurrence_interval") if row.get("recurrence_interval") is not None else 0,
                        "my_day_date": row.get("my_day_date") or "",
                        "phase_id": row.get("phase_id") or "",
                        "operation_id": row.get("operation_id") or "",
                        "function_id": row.get("function_id") or "",
                        "job_id": row.get("job_id") or "",
                        "atlas_task_id": row.get("atlas_task_id") or "",
                        "source_atlas_file": row.get("source_atlas_file") or "",
                        "source_section": row.get("source_section") or "",
                        "dependency_task_ids": row.get("dependency_task_ids") or "",
                        "estimated_complexity": row.get("estimated_complexity") or "",
                    }
                )

    def _validate_task_payload(self, task):
        status = task.get("status", "pending")
        if status not in TASK_STATUS_VALUES:
            raise ValueError(f"Invalid status '{status}' in task.")
        return status

    def import_csv(self, path, target_project=None, target_list_name=None):
        with open(path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        if len(rows) + self.count_tasks() > TASK_CAP:
            raise ValueError(f"Task import would exceed cap of {TASK_CAP}.")

        atlas_format = self._is_atlas_format(reader.fieldnames or [])
        cur = self.conn.cursor()
        cur.execute("BEGIN")

        def _parse_bool(value):
            if value is None:
                return False
            return str(value).strip().lower() in {"1", "true", "yes", "y"}

        def _parse_int(value, fallback=0):
            try:
                return int(value)
            except Exception:
                return fallback

        for raw in rows:
            task = {k: (v.strip() if isinstance(v, str) else v) for k, v in raw.items()}
            title = task.get("title")
            notes = task.get("notes") or ""
            project = target_project or task.get("project") or None
            list_name = target_list_name or task.get("list_name") or ("Imported" if not target_project else target_project)
            list_scope = task.get("list_scope", "").strip().lower()
            extra_fields = {
                "phase_id": task.get("phase_id"),
                "operation_id": task.get("operation_id"),
                "function_id": task.get("function_id"),
                "job_id": task.get("job_id"),
                "atlas_task_id": task.get("atlas_task_id"),
                "source_atlas_file": task.get("source_atlas_file"),
                "source_section": task.get("source_section"),
                "dependency_task_ids": task.get("dependency_task_ids"),
                "estimated_complexity": task.get("estimated_complexity"),
            }

            if atlas_format:
                # Map atlas CSV into internal schema
                title = task.get("task_name") or title or "Untitled"
                notes = task.get("task_description") or notes
                extra_fields.update(
                    {
                        "phase_id": task.get("phase_id"),
                        "operation_id": task.get("operation_id"),
                        "function_id": task.get("function_id"),
                        "job_id": task.get("job_id"),
                        "atlas_task_id": task.get("task_id"),
                        "source_atlas_file": task.get("source_atlas_file"),
                        "source_section": task.get("source_section"),
                        "dependency_task_ids": task.get("dependency_task_ids"),
                        "estimated_complexity": task.get("estimated_complexity"),
                    }
                )
                # Use atlas fields for grouping when list info missing
                list_name = target_list_name or task.get("source_section") or task.get("phase_id") or (target_project or "Imported (Atlas)")
                list_scope = "project" if target_project else "global"
                project = target_project or project or None

            status = self._normalize_import_status(task.get("status"))
            try:
                status = self._validate_task_payload({"status": status})
            except Exception:
                status = "pending"

            scope = "project" if target_project else (list_scope if list_scope in {"global", "project"} else ("project" if project else "global"))
            list_id = self._get_or_create_list(list_name, scope=scope, project=project)
            task_uuid = task.get("uuid") or str(uuid.uuid4())
            if self._task_pk(task_uuid):
                continue
            now = now_str()
            cur.execute("SELECT COALESCE(MAX(order_index), 0) + 1 FROM tasks WHERE list_id=?", (list_id,))
            default_order = cur.fetchone()[0]

            reminder = task.get("reminder") or None
            priority = 1 if _parse_bool(task.get("priority")) else 0
            completed_flag = 1 if _parse_bool(task.get("completed")) or status == "completed" else 0
            created_at = task.get("created_at") or now
            updated_at = task.get("updated_at") or now
            completed_at = task.get("completed_at") if completed_flag else None
            recurrence = (task.get("recurrence") or "none") or "none"
            recurrence_interval = _parse_int(task.get("recurrence_interval"), fallback=0)
            my_day_date = task.get("my_day_date") or None
            try_order = task.get("order_index")
            order_index = _parse_int(try_order, fallback=default_order) if try_order not in {None, ""} else default_order

            cur.execute(
                """
                INSERT OR IGNORE INTO tasks (
                    list_id,
                    uuid,
                    title,
                    notes,
                    due_date,
                    reminder,
                    priority,
                    completed,
                    status,
                    created_at,
                    updated_at,
                    completed_at,
                    project,
                    order_index,
                    recurrence,
                    recurrence_interval,
                    my_day_date,
                    phase_id,
                    operation_id,
                    function_id,
                    job_id,
                    atlas_task_id,
                    source_atlas_file,
                    source_section,
                    dependency_task_ids,
                    estimated_complexity
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    list_id,
                    task_uuid,
                    title or "Untitled",
                    notes,
                    task.get("due_date") or None,
                    reminder,
                    priority,
                    completed_flag,
                    status,
                    created_at,
                    updated_at,
                    completed_at,
                    project,
                    order_index,
                    recurrence,
                    recurrence_interval,
                    my_day_date,
                    extra_fields.get("phase_id") or None,
                    extra_fields.get("operation_id") or None,
                    extra_fields.get("function_id") or None,
                    extra_fields.get("job_id") or None,
                    extra_fields.get("atlas_task_id") or (task.get("task_id") if atlas_format else None) or None,
                    extra_fields.get("source_atlas_file") or None,
                    extra_fields.get("source_section") or None,
                    extra_fields.get("dependency_task_ids") or None,
                    extra_fields.get("estimated_complexity") or None,
                ),
            )
        self.conn.commit()

    def transition_status(self, task_uuid, new_status):
        if new_status not in TASK_STATUS_VALUES:
            raise ValueError(f"Invalid status: {new_status}")
        task = self.get_task(task_uuid)
        if not task:
            raise ValueError("Task not found.")
        current = task.get("status") or "pending"
        if new_status == current:
            return
        allowed = TASK_ALLOWED_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise ValueError(f"Invalid transition {current} -> {new_status}")
        completed_flag = 1 if new_status == "completed" else 0
        completed_at = now_str() if new_status == "completed" else None
        self.update_task(task_uuid, status=new_status, completed=completed_flag, completed_at=completed_at)

    def count_tasks(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tasks;")
        row = cur.fetchone()
        return row[0] if row else 0

    def project_incomplete_count(self, project_name):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM tasks WHERE project=? AND completed=0",
            (project_name,),
        )
        row = cur.fetchone()
        return row[0] if row else 0


class Backend:
    def run(self, command, sudo_password=None):
        sudo_fn = ""
        if sudo_password:
            # override sudo to read from stdin via piped password
            sudo_fn = f"SUDO_PASSWORD={shlex.quote(sudo_password)}; sudo() {{ echo \"$SUDO_PASSWORD\" | command sudo -S \"$@\"; }}; "
        full_cmd = f"{sudo_fn}source ~/.focus_unfocus.sh >/dev/null 2>&1; {command}"
        return subprocess.run(
            ["bash", "-lc", full_cmd],
            capture_output=True,
            text=True,
        )

    def detect_active(self):
        if not USE_BIND_MOUNT:
            return None
        script = textwrap.dedent(
            """
            source ~/.focus_unfocus.sh >/dev/null 2>&1
            if mountpoint -q "$HOME/active_project"; then
              findmnt -n -o SOURCE "$HOME/active_project"
            fi
            """
        )
        result = subprocess.run(
            ["bash", "-lc", script],
            capture_output=True,
            text=True,
        )
        source_path = result.stdout.strip()
        if source_path and source_path.startswith(PROJECT_ROOT + "/"):
            return os.path.basename(source_path)
        return None

    def list_projects(self):
        projects = []
        with os.scandir(PROJECT_ROOT) as entries:
            for entry in entries:
                if entry.is_dir():
                    projects.append((entry.name, entry.stat().st_mtime))
        projects.sort(key=lambda x: x[1], reverse=True)
        return projects

    def focus(self, project):
        if not USE_BIND_MOUNT:
            path = os.path.join(PROJECT_ROOT, project)
            if not os.path.isdir(path):
                return subprocess.CompletedProcess([], 1, "", f"Project '{project}' is missing at {path}.")
            return subprocess.CompletedProcess([], 0, f"Focused on project '{project}' (direct access at {path}).", "")
        return self.run(f"set -o pipefail; _focus_project {shlex.quote(project)}", sudo_password=getattr(self, "sudo_password", None))

    def unfocus(self):
        if not USE_BIND_MOUNT:
            # Only unmount if a stale mount exists; otherwise succeed silently.
            if os.path.ismount(ACTIVE_PROJECT_PATH):
                return subprocess.run(
                    ["sudo", "-n", "umount", ACTIVE_PROJECT_PATH],
                    capture_output=True,
                    text=True,
                )
            return subprocess.CompletedProcess([], 0, "Unfocused (direct mode).", "")
        return self.run("set -o pipefail; _unfocus_project", sudo_password=getattr(self, "sudo_password", None))

    def write_focus_marker(self, project_name):
        source_path = os.path.realpath(os.path.join(PROJECT_ROOT, project_name))
        marker = f"{source_path}\n"
        try:
            with open(FOCUS_MARKER, "w", encoding="utf-8") as fh:
                fh.write(marker)
            os.chmod(FOCUS_MARKER, 0o600)
        except Exception:
            return False
        return True

    def remove_focus_marker(self):
        try:
            if os.path.exists(FOCUS_MARKER):
                os.remove(FOCUS_MARKER)
        except Exception:
            return False
        return True


class AutoGITIntegration:
    def __init__(self):
        self.autogit_bin = self._find_autogit_bin()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _merge_env(self, env=None):
        merged = (env or os.environ).copy()
        merged.setdefault("GIT_DISCOVERY_ACROSS_FILESYSTEM", "1")
        return merged

    def _git_identity(self, env):
        name = env.get("GIT_AUTHOR_NAME") or env.get("GIT_COMMITTER_NAME") or getpass.getuser() or "autogit"
        email = env.get("GIT_AUTHOR_EMAIL") or env.get("GIT_COMMITTER_EMAIL") or f"{name}@local"
        return name, email

    def _ensure_identity(self, project_path, env):
        name, email = self._git_identity(env)
        subprocess.run(["git", "-C", project_path, "config", "user.name", name], capture_output=True, text=True, env=env)
        subprocess.run(["git", "-C", project_path, "config", "user.email", email], capture_output=True, text=True, env=env)

    def _find_autogit_bin(self):
        candidates = [
            os.environ.get("AUTO_GIT_BIN"),
            shutil.which("autogit.sh"),
            os.path.expanduser("~/bin/autogit.sh"),
            os.path.expanduser("~/bin/autogit_dirwatch.sh"),
        ]
        for cand in candidates:
            if cand and os.path.exists(cand) and os.access(cand, os.X_OK):
                return cand
        return None

    def available(self):
        return self.autogit_bin is not None

    def _run_autogit_once(self, project_path, env=None):
        if not self.available():
            return subprocess.CompletedProcess([], 127, "", "AutoGIT not found.")
        tmpdir = tempfile.mkdtemp(prefix="autogit_focus_")
        watch_file = os.path.join(tmpdir, "watch.txt")
        clone_file = os.path.join(tmpdir, "clone.txt")
        pid_file = os.path.join(tmpdir, "autogit.pid")
        with open(watch_file, "w", encoding="utf-8") as fh:
            fh.write(f"{project_path}\n")
        env = self._merge_env(env)
        env.update(
            {
                "WATCH_FILE": watch_file,
                "CLONE_FILE": clone_file,
                "PID_FILE": pid_file,
                "IGNORE_FILE": str(AUTOGIT_IGNORE),
                "LOG_FILE": str(AUTOGIT_LOG),
            }
        )
        result = subprocess.run(
            [self.autogit_bin, "run-once"],
            capture_output=True,
            text=True,
            env=env,
        )
        return self._wrap_autogit_result(result, project_path, env)

    def _wrap_autogit_result(self, result, project_path, env):
        if result.returncode == 0:
            return result
        env = self._merge_env(env)
        status = subprocess.run(
            ["git", "-C", project_path, "status", "--short"],
            capture_output=True,
            text=True,
            env=env,
        )
        if status.returncode == 0 and self.is_git_repo(project_path, env=env):
            note = (
                f"AutoGIT exited with {result.returncode} but git is initialized. "
                f"Review {AUTOGIT_LOG} for details; treating init as succeeded."
            )
            stdout_parts = [getattr(result, "stdout", "") or ""]
            stdout_parts.append(note)
            return subprocess.CompletedProcess(
                getattr(result, "args", []),
                0,
                "\n".join([part for part in stdout_parts if part.strip()]),
                getattr(result, "stderr", ""),
            )
        return result

    def init_project(self, project_path, env=None):
        return self._run_autogit_once(project_path, env=env)

    def commit_project(self, project_path, env=None):
        return self._run_autogit_once(project_path, env=env)

    def git_status(self, project_path, env=None):
        env = self._merge_env(env)
        return subprocess.run(
            ["git", "-C", project_path, "status", "--short"],
            capture_output=True,
            text=True,
            env=env,
        )

    def is_git_repo(self, project_path, env=None):
        env = self._merge_env(env)
        result = subprocess.run(
            ["git", "-C", project_path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            env=env,
        )
        return result.returncode == 0

    def ensure_git_repo(self, project_path, env=None):
        env = self._merge_env(env)
        if os.path.exists(project_path) and not os.path.isdir(project_path):
            return subprocess.CompletedProcess([], 1, "", f"{project_path} exists and is not a directory")
        os.makedirs(project_path, exist_ok=True)
        if self.is_git_repo(project_path, env=env):
            self._ensure_identity(project_path, env)
            # ensure we are on a usable branch
            self.ensure_branch(project_path, env=env)
            return subprocess.CompletedProcess([], 0, "", "")
        result = subprocess.run(
            ["git", "-C", project_path, "init", "-b", "main"],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode == 0:
            self._ensure_identity(project_path, env)
            self.ensure_branch(project_path, env=env)
        return result

    def ensure_branch(self, project_path, branch="main", env=None):
        env = self._merge_env(env)
        # Determine current branch
        head = subprocess.run(
            ["git", "-C", project_path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            env=env,
        )
        current = head.stdout.strip() if head.returncode == 0 else ""
        if current and current != "HEAD":
            return head
        # list branches
        branches = subprocess.run(
            ["git", "-C", project_path, "branch", "--list"],
            capture_output=True,
            text=True,
            env=env,
        )
        existing = [b.strip().lstrip("* ").strip() for b in branches.stdout.splitlines() if b.strip()]
        if branch in existing:
            return subprocess.run(["git", "-C", project_path, "checkout", branch], capture_output=True, text=True, env=env)
        if existing:
            # pick first existing branch
            return subprocess.run(["git", "-C", project_path, "checkout", existing[0]], capture_output=True, text=True, env=env)
        # no branches: create main
        return subprocess.run(["git", "-C", project_path, "checkout", "-b", branch], capture_output=True, text=True, env=env)

    def is_dubious_error(self, result):
        msg = (getattr(result, "stderr", "") or "") + (getattr(result, "stdout", "") or "")
        return "dubious ownership" in msg.lower()

    def config_has_safe_directory(self, project_path, env=None):
        env = self._merge_env(env)
        res = subprocess.run(
            ["git", "config", "--global", "--get-all", "safe.directory"],
            capture_output=True,
            text=True,
            env=env,
        )
        if res.returncode != 0:
            return False
        current = res.stdout.splitlines()
        return project_path in current

    def add_safe_directory(self, project_path, reason="", env=None):
        if not os.path.realpath(project_path).startswith(os.path.realpath(PROJECT_ROOT)):
            return False
        env = self._merge_env(env)
        if self.config_has_safe_directory(project_path, env=env):
            return True
        res = subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", project_path],
            capture_output=True,
            text=True,
            env=env,
        )
        if res.returncode == 0:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(SAFE_DIR_LOG, "a", encoding="utf-8") as fh:
                fh.write(f"{ts} added {project_path} reason={reason}\n")
            return True
        return False


class ProjectImporter:
    def __init__(self, autogit: AutoGITIntegration):
        self.autogit = autogit

    def validate_source(self, source_path):
        if not source_path or not os.path.isdir(source_path):
            return "Source must be an existing directory."
        real_source = os.path.realpath(source_path)
        canonical_root = os.path.realpath(PROJECT_ROOT)
        if real_source.startswith(canonical_root):
            return "Cannot import from the canonical project storage."
        if os.path.realpath(source_path) == os.path.realpath(ACTIVE_PROJECT_PATH):
            return "Cannot import from the active project mount."
        if os.path.ismount(source_path):
            return "Cannot import from a mount point."
        if real_source.startswith("/media/sf_STEF"):
            return "Cannot import from /media/sf_STEF."
        return None

    def copy_tree_safely(self, src, dst):
        skipped = []
        for root, dirs, files in os.walk(src):
            rel_root = os.path.relpath(root, src)
            target_root = os.path.join(dst, rel_root) if rel_root != "." else dst
            os.makedirs(target_root, exist_ok=True)
            # ensure dirs created
            for fname in files:
                src_path = os.path.join(root, fname)
                if os.path.islink(src_path):
                    target = os.path.realpath(src_path)
                    if not target.startswith(os.path.realpath(src)):
                        skipped.append(src_path)
                        continue
                    if os.path.isdir(target):
                        continue  # skip directory symlinks to avoid recursion
                    shutil.copy2(target, os.path.join(target_root, fname))
                    continue
                shutil.copy2(src_path, os.path.join(target_root, fname))
        return skipped

    def move_contents(self, src, dst):
        skipped = []
        for entry in os.listdir(src):
            src_path = os.path.join(src, entry)
            if os.path.islink(src_path):
                target = os.path.realpath(src_path)
                if not target.startswith(os.path.realpath(src)):
                    skipped.append(src_path)
                    continue
            shutil.move(src_path, os.path.join(dst, entry))
        return skipped


class WorkerSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)


class Worker(QtCore.QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(str(exc))
        else:
            self.signals.result.emit(res)


class CreateProjectDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Project")
        layout = QtWidgets.QVBoxLayout(self)
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("project-name")
        self.readme_checkbox = QtWidgets.QCheckBox("Create README.md")
        self.autogit_checkbox = QtWidgets.QCheckBox("Initialize Git with AutoGIT")
        layout.addWidget(QtWidgets.QLabel("Project name:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(self.readme_checkbox)
        layout.addWidget(self.autogit_checkbox)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return self.name_edit.text().strip(), self.readme_checkbox.isChecked(), self.autogit_checkbox.isChecked()


class ImportOptionsDialog(QtWidgets.QDialog):
    def __init__(self, source_path, default_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Existing Folder")
        layout = QtWidgets.QVBoxLayout(self)
        self.source_path = source_path
        self.name_edit = QtWidgets.QLineEdit(default_name)
        self.copy_checkbox = QtWidgets.QCheckBox("Copy contents")
        self.copy_checkbox.setChecked(True)
        self.move_checkbox = QtWidgets.QCheckBox("Move contents instead of copying")
        self.autogit_checkbox = QtWidgets.QCheckBox("Initialize with AutoGIT")
        self.readme_checkbox = QtWidgets.QCheckBox("Create README.md if missing")
        self.copy_checkbox.stateChanged.connect(self._sync_move_copy)
        self.move_checkbox.stateChanged.connect(self._sync_move_copy)
        layout.addWidget(QtWidgets.QLabel(f"Source: {source_path}"))
        layout.addWidget(QtWidgets.QLabel("Project name:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(self.copy_checkbox)
        layout.addWidget(self.move_checkbox)
        layout.addWidget(self.autogit_checkbox)
        layout.addWidget(self.readme_checkbox)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _sync_move_copy(self):
        if self.sender() == self.move_checkbox and self.move_checkbox.isChecked():
            self.copy_checkbox.setChecked(False)
        elif self.sender() == self.copy_checkbox and self.copy_checkbox.isChecked():
            self.move_checkbox.setChecked(False)

    def get_values(self):
        return {
            "name": self.name_edit.text().strip(),
            "copy": self.copy_checkbox.isChecked(),
            "move": self.move_checkbox.isChecked(),
            "autogit": self.autogit_checkbox.isChecked(),
            "readme": self.readme_checkbox.isChecked(),
        }


class FocusManager(QtWidgets.QMainWindow):
    def __init__(self, supervisor=None, settings=None, debug_level=None):
        super().__init__()
        # Debug control plane levels: normal | debug | diagnostic
        self.settings = settings or self.load_settings()
        self.debug_level = debug_level or self.settings.get("debug_level", "normal")
        self.supervisor = supervisor or StabilitySupervisor(debug_level=self.debug_level, on_event=self._stability_event, log_fn=None)
        # ensure supervisor routes events to this debug system
        self.supervisor.on_event = self._stability_event
        self.teardown_active = False
        self._state_transition_active = False
        self._ui_ready = False
        self._ui_tearing_down = False
        self._ui_mutation_active = False
        self._ui_mutation_queue: deque[tuple[str, callable, tuple, dict]] = deque()
        self._auto_commit_toggle_active = False
        self.backend = Backend()
        self.store = TaskStore()
        self.autogit = AutoGITIntegration()
        self.importer = ProjectImporter(self.autogit)
        self.tooltip_manager = TooltipManager(self)
        self.context_menu_manager = ContextMenuManager(self, self.tooltip_manager)
        self.action_registry = ActionRegistry()
        self.watch_manager = WatchManager()
        self.event_bus = EventBus()
        self.command_palette = CommandPalette(self.action_registry, self)
        self._register_global_actions()
        self.setObjectName("singularityMainWindow")
        self.status_map = {}
        self.active_project = None
        self.view_mode = "canonical"
        self.current_list_ref = None
        self.current_task_id = None
        self.current_state = "Idle"
        self.threadpool = QtCore.QThreadPool.globalInstance()
        self.project_meta = self.load_project_meta()
        self.column_visibility: dict[str, dict[str, bool]] = self.settings.get("column_visibility", {})
        self.table_registry: dict[str, QtWidgets.QTableWidget] = {}
        # localsync folder mapping per project
        self.localsync_paths: dict[str, str] = {}
        self.warning_count = 0
        self.redaction_state: dict[str, bool] = {}
        self.selected_project = None
        self.focus_path = None
        self.ui_state = {
            "selected_project": None,
            "focused_project": None,
            "mount_active": False,
            "view_mode": "canonical",
        }
        self.workspace_view_mode = "list"
        self.workspace_selected_meta: dict | None = None
        self.workspace_fs_model = None
        self.workspace_root_path = None
        self.workspace_status: dict[str, str] = {}
        self.localsync_paths.update({k: v.get("localsync_path") for k, v in self.project_meta.items() if isinstance(v, dict) and v.get("localsync_path")})
        self.workspace_sel_connected = False
        self.network_view_mode = "graph"
        self.network_capture_enabled = True
        self.network_capture_paused = False
        self.network_latency_mode = "aggregate"
        self.network_events: deque[dict] = deque(maxlen=500)
        self.network_endpoints: dict[str, dict] = {}
        self.startup_cleanup_ok = True
        # Auto-commit monitoring
        self.autogit_watchers: dict[str, QtCore.QFileSystemWatcher] = {}
        self.autogit_timers: dict[str, QtCore.QTimer] = {}
        # Enforce non-interactive git behavior globally.
        os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
        os.environ.setdefault("GCM_INTERACTIVE", "never")
        self.base_font_size = QtWidgets.QApplication.font().pointSizeF() or 11
        loaded_scale = self.settings.get("interface", {}).get("ui_scale", 100)
        # If a previously saved scale is excessively large, bring it back to a sane default so the window remains usable.
        if loaded_scale > 160:
            loaded_scale = 160
            self.settings.setdefault("interface", {})["ui_scale"] = loaded_scale
            self.save_settings()
        self.ui_scale = loaded_scale
        self.scale_factor = max(0.6, min(4.0, self.ui_scale / 100))
        self._animated_scale = self.scale_factor
        self._scale_anim = None
        self.scalable_layouts = []
        self.layout_margins = {}
        self.wrap_layouts = []
        self.wrap_mode = False
        self.wrap_spill_direction = self.settings.get("interface", {}).get("spill_direction", "horizontal")
        self.accent_primary = ACCENTS["cyan"]["primary"]
        self.accent_glow = ACCENTS["cyan"]["glow"]
        audio_pref = self.settings.get("interface", {}).get("audio_feedback", True)
        self._tab_change_pending_idx = None
        self._tab_change_flush_scheduled = False
        self._last_active_tab = 0
        self.sound_engine = SoundEngine(enabled=audio_pref, accent_color=self.accent_glow)
        self.interaction_sound_filter = InteractionSoundFilter(self.sound_engine)
        self.installEventFilter(self.interaction_sound_filter)
        app = QtWidgets.QApplication.instance()
        if app:
            app.installEventFilter(self.interaction_sound_filter)
        self.responsive_layouts: list[QtWidgets.QBoxLayout] = []
        self.responsive_base_dir: dict[QtWidgets.QBoxLayout, QtWidgets.QBoxLayout.Direction] = {}
        self.operation_ctx = {"state": "idle", "name": None, "target": None, "dry_run": False}
        self.debug_scopes = [
            "APPLICATION",
            "PROJECTS",
            "TASKS",
            "VERSIONING",
            "FOCUS_STATE",
            "UI_STATE",
            "SETTINGS",
            "LLM_EXECUTION",
            "FILESYSTEM",
            "ERRORS",
            "PERFORMANCE",
            "STABILITY",
        ]
        self.debug_history: list[tuple[str, object, str]] = []
        self.debug_window: DebugWindow | None = None
        self.github_reachable = None
        self.repo_cache: list[dict] | None = None
        self.repo_cache_time: datetime | None = None
        self.repo_fetching = False
        self.startup_stability_warning = self.supervisor.crashed_last_run
        if self.supervisor.crashed_last_run:
            self.log_debug("APPLICATION", {"stability": "previous_crash_detected", "safe_mode": self.supervisor.state.get("force_software_render", False)})
        # Session flag for monitors/cleanup
        self.session_active = True
        if USE_BIND_MOUNT:
            # Ensure mountpoint directory exists and is safe
            try:
                if not os.path.exists(ACTIVE_PROJECT_PATH):
                    os.makedirs(ACTIVE_PROJECT_PATH, exist_ok=True)
                if os.path.islink(ACTIVE_PROJECT_PATH):
                    os.unlink(ACTIVE_PROJECT_PATH)
                    os.makedirs(ACTIVE_PROJECT_PATH, exist_ok=True)
            except Exception:
                pass
        self.ensure_shell_auto_cd_snippet()
        self.keybinds = self.settings.get(
            "controls",
            {
                "new_task": "Ctrl+N",
                "complete_task": "Ctrl+D",
                "focus_project": "Ctrl+Shift+F",
                "commit": "Ctrl+Shift+C",
                "tab_prev": "Ctrl+Left",
                "tab_next": "Ctrl+Right",
            },
        )
        self.credentials_store = self.load_credentials()
        self.selected_cred_label = self.credentials_store.get("selected")
        # active credential set
        self.active_credentials = self.credentials_store.get("sets", {}).get(self.selected_cred_label or "", {}) if self.selected_cred_label else {}
        self.api_tokens = list(self.active_credentials.get("tokens", []))
        self.credentials_verified = bool(self.active_credentials.get("verified", False))
        self.verified_user = self.active_credentials.get("username", "") if self.credentials_verified else ""
        self._load_gemini_settings()
        self.setWindowTitle("SINGULARITY CONSOLE")
        self.resize(1400, 900)
        # Keep a small, fixed minimum size so scaling does not inflate minimum geometry.
        self.setMinimumSize(600, 400)
        self._apply_app_font(self.scale_factor)
        # Cleanup any stale mounts before building UI
        self._force_cleanup_on_start()
        self._build_ui()
        self._apply_background_image()
        self._bulk_register_tooltips()
        if self.startup_stability_warning and hasattr(self, "error_banner"):
            self.show_error_banner("Previous session ended unexpectedly; safe rendering enabled.")
        QtCore.QTimer.singleShot(0, self._mark_ui_ready)
        self.apply_loaded_settings()
        self.apply_ui_scale(initial=True)
        self.apply_credentials_to_ui()
        self._ensure_ai_toggle_ui()
        self._apply_git_auth_env()
        self._setup_shortcuts()
        QtCore.QTimer.singleShot(400, self._show_usage_note)
        self.refresh_projects()
        self.populate_lists()
        self.refresh_health_panel()
        self.check_github_connectivity()
        self._start_consistency_monitor()
        self.update_identity_banner()
        self._init_task_watcher()
        self.log_debug(
            "APPLICATION",
            {
                "status": "ready",
                "gemini_cmd": GEMINI_CMD,
                "data_dir": str(DATA_DIR),
            },
        )
        self.log_debug(
            "PERFORMANCE",
            {
                "threadpool_max": self.threadpool.maxThreadCount(),
                "ui_scale": self.scale_factor,
            },
        )
        if not self.startup_cleanup_ok and hasattr(self, "error_banner"):
            self.show_error_banner("Startup cleanup incomplete: active_project may still be mounted. Unfocus manually.")
        # Ensure cleanup on quit signals
        app = QtWidgets.QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.cleanup_session)
        signal.signal(signal.SIGINT, self._handle_termination_signal)
        signal.signal(signal.SIGTERM, self._handle_termination_signal)

    def load_project_meta(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not PROJECT_META_FILE.exists():
            return {}
        try:
            with open(PROJECT_META_FILE, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            normalized = {}
            for k, v in raw.items():
                if isinstance(v, dict):
                    origin = v.get("origin", "Local")
                    auto_commit = bool(v.get("auto_commit", False))
                    localsync = bool(v.get("localsync", False))
                    localsync_path = v.get("localsync_path")
                    import_method = v.get("import_method")
                    origin_path = v.get("origin_path")
                    last_sync = v.get("last_sync")
                else:
                    origin = v
                    auto_commit = False
                    localsync = False
                    localsync_path = None
                    import_method = None
                    origin_path = None
                    last_sync = None
                normalized[k] = {
                    "origin": origin,
                    "auto_commit": auto_commit,
                    "localsync": localsync,
                    "localsync_path": localsync_path,
                    "import_method": import_method,
                    "origin_path": origin_path,
                    "last_sync": last_sync,
                }
            return normalized
        except Exception:
            return {}

    def save_project_meta(self):
        try:
            with open(PROJECT_META_FILE, "w", encoding="utf-8") as fh:
                json.dump(self.project_meta, fh, indent=2)
        except Exception:
            pass

    def _build_ui(self):
        central = QtWidgets.QWidget()
        central.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        central.setObjectName("centralwidget")
        central.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        central.setAutoFillBackground(True)
        self.setCentralWidget(central)
        main_layout = self._register_layout(QtWidgets.QVBoxLayout(central))

        # Global status bar showing state and focus info.
        status_bar = self._register_layout(WrapLayout())
        self.state_dot = QtWidgets.QFrame()
        self.state_dot.setFixedSize(14, 14)
        self.state_dot.setStyleSheet("background-color: #2e9b8f; border-radius: 7px;")
        self.state_text_label = QtWidgets.QLabel("Idle")
        self.state_msg_label = QtWidgets.QLabel("")
        self.state_msg_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.state_msg_label.setStyleSheet("color: #8ad0ff;")
        self.focus_state_label = QtWidgets.QLabel("Unfocused")
        self.focus_state_label.setStyleSheet("color: #d2a446;")
        self.auto_cd_label = QtWidgets.QLabel("Terminal Auto-Focus: DISABLED")
        self.auto_cd_label.setStyleSheet("color: #d2a446;")
        status_bar.addWidget(self.state_dot)
        status_bar.addWidget(self.state_text_label)
        status_bar.addWidget(self.state_msg_label)
        status_bar.addWidget(self.focus_state_label)
        self.global_project_label = QtWidgets.QLabel("Selected: No Project Selected | Focused: None")
        self.global_project_label.setStyleSheet("color: #9ce4ff; font-weight: bold;")
        status_bar.addWidget(self.global_project_label)
        status_bar.addWidget(self.auto_cd_label)
        self.dry_run_checkbox = QtWidgets.QCheckBox("Dry Run")
        self.dry_run_checkbox.setToolTip("Simulate destructive operations without applying changes.")
        status_bar.addWidget(self.dry_run_checkbox)
        self.auto_commit_global_btn = QtWidgets.QPushButton("Auto Commit")
        self.auto_commit_global_btn.setCheckable(True)
        self.auto_commit_global_btn.setEnabled(False)
        status_bar.addWidget(self.auto_commit_global_btn)
        self.debug_window_btn = QtWidgets.QPushButton("Debug Window")
        self.debug_window_btn.setCheckable(True)
        self.ensure_interactable(self.debug_window_btn)
        status_bar.addWidget(self.debug_window_btn)
        main_layout.addLayout(status_bar)

        # Error banner (hidden until needed)
        self.error_banner = QtWidgets.QFrame()
        self.error_banner.setStyleSheet("background-color: #4a1f1f; border: 1px solid #d14b4b; border-radius: 6px;")
        error_layout = QtWidgets.QHBoxLayout(self.error_banner)
        self.error_label = QtWidgets.QLabel("")
        self.error_close = QtWidgets.QPushButton("Dismiss")
        self.error_close.setMinimumWidth(80)
        self.error_close.clicked.connect(self.clear_error_banner)
        error_layout.addWidget(self.error_label, 1)
        error_layout.addWidget(self.error_close)
        self.error_banner.setVisible(False)
        main_layout.addWidget(self.error_banner)

        health_content = QtWidgets.QWidget()
        health_layout = QtWidgets.QVBoxLayout(health_content)
        self.health_focus_label = QtWidgets.QLabel("Focus: Unknown")
        self.health_active_label = QtWidgets.QLabel("Active: Unknown")
        self.health_mount_label = QtWidgets.QLabel("Mount: Unknown")
        self.health_cred_label = QtWidgets.QLabel("Credentials: Unknown")
        self.health_autogit_label = QtWidgets.QLabel("AutoGIT: Unknown")
        self.health_github_label = QtWidgets.QLabel("GitHub: Unknown")
        self.health_auto_cd_label = QtWidgets.QLabel("Terminal Auto-Focus: Unknown")
        for lbl in [
            self.health_focus_label,
            self.health_active_label,
            self.health_mount_label,
            self.health_cred_label,
            self.health_autogit_label,
            self.health_github_label,
            self.health_auto_cd_label,
        ]:
            health_layout.addWidget(lbl)
        self.health_box = CollapsiblePane(
            "System Health",
            health_content,
            collapsed=self.get_collapsible_state("system-health", False),
            on_toggle=partial(self._on_collapsible_toggle, "system-health"),
        )
        self.register_pane_context(self.health_box, "system-health")
        main_layout.addWidget(self.health_box)

        header = QtWidgets.QLabel("SINGULARITY CONSOLE")
        header.setAlignment(qt_align_center())
        header.setStyleSheet("color: #73f5ff; font-size: 22px; letter-spacing: 3px;")
        main_layout.addWidget(header)
        # Identity banner (monospaced, centered)
        self.identity_banner = QtWidgets.QLabel()
        self.identity_banner.setAlignment(qt_align_center())
        self.identity_banner.setWordWrap(False)
        self.identity_banner.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.identity_banner.setStyleSheet("white-space: pre;")
        main_layout.addWidget(self.identity_banner)
        self.runtime_strip = RuntimeStateStrip(self)
        self.runtime_strip.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.runtime_strip.customContextMenuRequested.connect(
            lambda pos: self.context_menu_manager.open_menu(
                {
                    "type": "runtime-strip",
                    "targetId": "runtime",
                    "metadata": {"state": getattr(self, "current_state", "Idle"), "warnings": self.warning_count},
                    "capabilities": ["inspect", "watch"],
                },
                self._build_context_actions(
                    {
                        "type": "runtime-strip",
                        "targetId": "runtime",
                        "metadata": {"state": getattr(self, "current_state", "Idle"), "warnings": self.warning_count},
                        "capabilities": ["inspect", "watch"],
                    }
                ),
                self.runtime_strip.mapToGlobal(pos),
            )
        )
        main_layout.addWidget(self.runtime_strip)
        self._update_runtime_strip()

        self.operation_panel = QtWidgets.QFrame()
        self.operation_panel.setStyleSheet("background-color: #111b2d; border: 1px solid #3b6aff; border-radius: 6px;")
        op_layout = self._register_layout(QtWidgets.QHBoxLayout(self.operation_panel))
        self.operation_label = QtWidgets.QLabel("Idle")
        self.operation_progress = QtWidgets.QProgressBar()
        self.operation_progress.setRange(0, 0)
        op_layout.addWidget(self.operation_label)
        op_layout.addWidget(self.operation_progress)
        self.operation_panel.setVisible(False)
        main_layout.addWidget(self.operation_panel)
        body_layout = QtWidgets.QHBoxLayout()
        self.body_layout = body_layout
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)
        tabs = QtWidgets.QTabWidget()
        body_layout.addWidget(tabs, 1)
        photon_panel = self._build_photon_side_panel(tabs)
        self.photon_panel = photon_panel
        self.photon_panel_attached = False  # only insert when active to reclaim space when inactive
        main_layout.addLayout(body_layout)
        self.tab_widget = tabs

        # ----- Projects tab -----
        projects_scroll = QtWidgets.QScrollArea()
        projects_scroll.setWidgetResizable(True)
        projects_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        projects_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        projects_tab = QtWidgets.QWidget()
        projects_layout = self._register_layout(QtWidgets.QVBoxLayout(projects_tab))
        self.projects_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical if not QT6 else QtCore.Qt.Orientation.Vertical)
        self.projects_splitter.setHandleWidth(8)
        self.projects_splitter.setChildrenCollapsible(False)

        projects_pane = QtWidgets.QWidget()
        projects_pane.setMinimumHeight(120)
        projects_pane_layout = self._register_layout(QtWidgets.QVBoxLayout(projects_pane))
        self.active_label = QtWidgets.QLabel("Active: unknown")
        self.active_label.setAlignment(qt_align_center())
        self.active_label.setStyleSheet("color: #c8b5ff; font-size: 16px; padding: 8px; border: 1px solid #5b36b8; border-radius: 8px;")
        projects_pane_layout.addWidget(self.active_label)

        proj_btn_row = self._register_layout(WrapLayout(margin=0, h_spacing=8, v_spacing=0))
        self.focus_btn = QtWidgets.QPushButton("Focus Selected")
        self.focus_btn.setToolTip("Focus the selected project directly from canonical storage.")
        self.unfocus_btn = QtWidgets.QPushButton("Unfocus")
        self.unfocus_btn.setToolTip("Clear the focused project (and unmount if any stale mount exists).")
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.setToolTip("Reload project list and focus state.")
        self.create_btn = QtWidgets.QPushButton("New Project")
        self.create_btn.setToolTip("Create a new empty project in canonical storage.")
        self.import_project_btn = QtWidgets.QPushButton("Import Existing Folder")
        self.import_project_btn.setToolTip("Import a local folder as a project into canonical storage.")
        self.rename_btn = QtWidgets.QPushButton("Rename Project")
        self.rename_btn.setToolTip("Rename the selected project.")
        self.generate_todo_btn = QtWidgets.QPushButton("Generate To-Do List")
        self.generate_todo_btn.setToolTip("Generate a task list from the project overview using the saved prompt.")
        self.summarize_btn = QtWidgets.QPushButton("Summarize")
        self.summarize_btn.setToolTip("Generate a Gemini summary of the selected or focused project.")
        self.project_tasks_btn = QtWidgets.QPushButton("+Tasks")
        self.project_tasks_btn.setToolTip("Create a task list for the selected project named after the project.")
        self.delete_project_btn = QtWidgets.QPushButton("Delete Project")
        self.delete_project_btn.setToolTip("Permanently delete the selected project from canonical storage.")
        for btn in [
            self.focus_btn,
            self.unfocus_btn,
            self.refresh_btn,
            self.create_btn,
            self.import_project_btn,
            self.rename_btn,
            self.generate_todo_btn,
            self.summarize_btn,
            self.project_tasks_btn,
            self.delete_project_btn,
        ]:
            self.ensure_interactable(btn)
            proj_btn_row.addWidget(btn)
        self.delete_project_btn.setEnabled(False)
        projects_pane_layout.addLayout(proj_btn_row)

        self.project_context_label = QtWidgets.QLabel("Selected: No Project Selected | Focused: None")
        self.project_context_label.setStyleSheet("color: #9ce4ff; font-weight: bold;")
        projects_pane_layout.addWidget(self.project_context_label)

        project_box = QtWidgets.QGroupBox("Projects")
        project_layout = self._register_layout(QtWidgets.QVBoxLayout(project_box))
        self.project_table = QtWidgets.QTableWidget(0, 6)
        self.project_table.setHorizontalHeaderLabels(["Project", "Last Modified", "Status", "Origin", "LocalSync", "Local Path"])
        self.project_table.horizontalHeader().setStretchLastSection(True)
        try:
            self.project_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        except Exception:
            pass
        self.project_table.setSelectionBehavior(qt_select_rows())
        self.project_table.setSelectionMode(qt_single_select())
        self._enable_vertical_scroll(self.project_table)
        self.register_table_row_context(self.project_table, "projectsTable", self._project_payload_for_row)
        self.register_table_for_context(self.project_table, "projectsTable")
        project_layout.addWidget(self.project_table)
        self.fs_view = None
        self.fs_model = None

        summary_panel = QtWidgets.QWidget()
        summary_layout = self._register_layout(QtWidgets.QVBoxLayout(summary_panel))
        self.summary_view = QtWidgets.QTextEdit()
        self.summary_view.setReadOnly(True)
        self.summary_view.setPlaceholderText("Summaries will appear here.")
        self.summary_view.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self._enable_vertical_scroll(self.summary_view)
        summary_layout.addWidget(self.summary_view)

        proj_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal if not QT6 else QtCore.Qt.Orientation.Horizontal)
        proj_splitter.addWidget(project_box)
        proj_splitter.addWidget(summary_panel)
        proj_splitter.setSizes([600, 400])

        self.projects_splitter.addWidget(projects_pane)
        self.projects_splitter.addWidget(proj_splitter)
        saved_sizes = self.load_splitter_state("projects_fs")
        if saved_sizes:
            try:
                self.projects_splitter.setSizes([int(s) for s in saved_sizes])
            except Exception:
                self.projects_splitter.setSizes([500, 500])
        else:
            self.projects_splitter.setSizes([500, 500])
        self.projects_splitter.splitterMoved.connect(partial(self._on_splitter_moved, "projects_fs", self.projects_splitter))
        projects_layout.addWidget(self.projects_splitter)

        projects_scroll.setWidget(projects_tab)
        tabs.addTab(projects_scroll, "Projects")

        # ----- Workspaces tab -----
        workspaces_scroll = QtWidgets.QScrollArea()
        workspaces_scroll.setWidgetResizable(True)
        workspaces_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        workspaces_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        workspaces_tab = QtWidgets.QWidget()
        workspaces_layout = self._register_layout(QtWidgets.QVBoxLayout(workspaces_tab))
        self.workspace_vsplit = QtWidgets.QSplitter(QtCore.Qt.Vertical if not QT6 else QtCore.Qt.Orientation.Vertical)
        self.workspace_vsplit.setHandleWidth(8)
        self.workspace_vsplit.setChildrenCollapsible(False)

        top_panel = QtWidgets.QFrame()
        top_panel.setStyleSheet("background-color: #0f1626; border: 1px solid #3b6aff; border-radius: 6px;")
        top_layout = self._register_layout(WrapLayout(parent=top_panel, margin=4, h_spacing=8, v_spacing=0))
        top_layout.setContentsMargins(8, 8, 8, 8)

        self.workspace_add_btn = QtWidgets.QToolButton()
        self.workspace_add_btn.setText("Add")
        self.workspace_add_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.workspace_add_menu = QtWidgets.QMenu(self.workspace_add_btn)
        file_menu = self.workspace_add_menu.addMenu("File")
        for label, ext in [("Source Code", ".py"), ("Data", ".json"), ("Configuration", ".yml"), ("Metadata", ".md")]:
            action = file_menu.addAction(label)
            action.triggered.connect(partial(self._on_workspace_add_file, ext))
        folder_menu = self.workspace_add_menu.addMenu("Folder")
        for label in ["General", "Data", "Config", "Docs"]:
            action = folder_menu.addAction(label)
            action.triggered.connect(partial(self._on_workspace_add_folder, label))
        db_menu = self.workspace_add_menu.addMenu("Database")
        for label in ["SQLite"]:
            action = db_menu.addAction(label)
            action.triggered.connect(partial(self._on_workspace_add_database, label))
        self.workspace_add_btn.setMenu(self.workspace_add_menu)
        top_layout.addWidget(self.workspace_add_btn)

        self.workspace_import_btn = QtWidgets.QToolButton()
        self.workspace_import_btn.setText("Import")
        self.workspace_import_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.workspace_import_menu = QtWidgets.QMenu(self.workspace_import_btn)
        import_file_action = self.workspace_import_menu.addAction("File")
        import_folder_action = self.workspace_import_menu.addAction("Folder")
        import_archive_action = self.workspace_import_menu.addAction("Archive")
        import_file_action.triggered.connect(self._workspace_import_file)
        import_folder_action.triggered.connect(self._workspace_import_folder)
        import_archive_action.triggered.connect(self._workspace_import_archive)
        self.workspace_import_btn.setMenu(self.workspace_import_menu)
        top_layout.addWidget(self.workspace_import_btn)

        self.workspace_remove_btn = QtWidgets.QToolButton()
        self.workspace_remove_btn.setText("Remove")
        self.workspace_remove_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.workspace_remove_menu = QtWidgets.QMenu(self.workspace_remove_btn)
        for label, kind in [("File", "file"), ("Folder", "folder"), ("Database", "database")]:
            action = self.workspace_remove_menu.addAction(label)
            action.triggered.connect(partial(self._on_workspace_remove_entity, kind))
        self.workspace_remove_btn.setMenu(self.workspace_remove_menu)
        top_layout.addWidget(self.workspace_remove_btn)

        self.workspace_mod_btn = QtWidgets.QToolButton()
        self.workspace_mod_btn.setText("Mod")
        self.workspace_mod_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.workspace_mod_menu = QtWidgets.QMenu(self.workspace_mod_btn)
        mod_actions = [
            ("Toggle Hidden", "hidden"),
            ("Set Read-Only", "readonly"),
            ("Set Executable", "exec"),
            ("Mark In Progress", "in_progress"),
            ("Mark Complete", "complete"),
            ("Mark Incomplete", "incomplete"),
        ]
        for label, action_key in mod_actions:
            action = self.workspace_mod_menu.addAction(label)
            action.triggered.connect(partial(self._on_workspace_mod_entity, action_key))
        self.workspace_mod_btn.setMenu(self.workspace_mod_menu)
        top_layout.addWidget(self.workspace_mod_btn)

        toggle_row = self._register_layout(QtWidgets.QHBoxLayout())
        toggle_row.setSpacing(6)
        toggle_row.setContentsMargins(0, 0, 0, 0)
        self.workspace_graph_toggle = QtWidgets.QToolButton()
        self.workspace_graph_toggle.setText("Graph View")
        self.workspace_graph_toggle.setCheckable(True)
        self.workspace_list_toggle = QtWidgets.QToolButton()
        self.workspace_list_toggle.setText("List View")
        self.workspace_list_toggle.setCheckable(True)
        self.workspace_list_toggle.setChecked(True)
        self.workspace_toggle_group = QtWidgets.QButtonGroup(self)
        self.workspace_toggle_group.setExclusive(True)
        self.workspace_toggle_group.addButton(self.workspace_graph_toggle)
        self.workspace_toggle_group.addButton(self.workspace_list_toggle)
        self.workspace_graph_toggle.toggled.connect(self._on_workspace_graph_toggled)
        self.workspace_list_toggle.toggled.connect(self._on_workspace_list_toggled)
        toggle_row.addWidget(QtWidgets.QLabel("View Toggle:"))
        toggle_row.addWidget(self.workspace_graph_toggle)
        toggle_row.addWidget(self.workspace_list_toggle)
        toggle_row.addStretch(1)
        top_layout.addItem(toggle_row)
        top_layout.addWidget(QtWidgets.QLabel("Tags:"))
        self.workspace_tags_edit = QtWidgets.QLineEdit()
        self.workspace_tags_edit.setPlaceholderText("Project tags (comma-separated)")
        self.workspace_tags_edit.setEnabled(False)
        self.workspace_tags_edit.editingFinished.connect(self._on_workspace_tags_changed)
        top_layout.addWidget(self.workspace_tags_edit)
        self.workspace_redacted_tag = QtWidgets.QCheckBox("Redacted")
        self.workspace_redacted_tag.setEnabled(False)
        self.workspace_redacted_tag.toggled.connect(self._on_workspace_redacted_tag_toggled)
        top_layout.addWidget(self.workspace_redacted_tag)

        self.workspace_vsplit.addWidget(top_panel)

        workspace_body_split = QtWidgets.QSplitter(QtCore.Qt.Horizontal if not QT6 else QtCore.Qt.Orientation.Horizontal)
        workspace_body_split.setHandleWidth(8)
        workspace_body_split.setChildrenCollapsible(False)

        inspector_panel = QtWidgets.QGroupBox("Attribute Inspector")
        inspector_layout = self._register_layout(QtWidgets.QVBoxLayout(inspector_panel))
        inspector_layout.setContentsMargins(8, 8, 8, 8)
        self.workspace_attr_scroll = QtWidgets.QScrollArea()
        self.workspace_attr_scroll.setWidgetResizable(True)
        self.workspace_attr_widget = QtWidgets.QWidget()
        self.workspace_attr_form = QtWidgets.QFormLayout(self.workspace_attr_widget)
        self.workspace_attr_form.setLabelAlignment(QtCore.Qt.AlignLeft)
        self.workspace_attr_scroll.setWidget(self.workspace_attr_widget)
        inspector_layout.addWidget(self.workspace_attr_scroll)
        workspace_body_split.addWidget(inspector_panel)

        self.workspace_stack = QtWidgets.QStackedWidget()
        self.workspace_graph = WorkspaceGraphView()
        self.workspace_graph.node_selected.connect(self._on_workspace_graph_selected)
        self.workspace_list_view = QtWidgets.QTreeView()
        self.workspace_list_view.setHeaderHidden(False)
        self.workspace_list_view.setSelectionMode(qt_single_select())
        self._enable_vertical_scroll(self.workspace_list_view)
        self.workspace_list_view.setExpandsOnDoubleClick(True)
        self.workspace_list_view.clicked.connect(self._on_workspace_fs_selected)
        self.workspace_stack.addWidget(self.workspace_graph)
        self.workspace_stack.addWidget(self.workspace_list_view)
        workspace_body_split.addWidget(self.workspace_stack)

        self.workspace_vsplit.addWidget(workspace_body_split)
        default_top = 140
        default_left = default_top * 3
        saved_v = self.load_splitter_state("workspace_vsplit")
        saved_h = self.load_splitter_state("workspace_hsplit")
        if saved_v:
            try:
                self.workspace_vsplit.setSizes([int(s) for s in saved_v])
            except Exception:
                self.workspace_vsplit.setSizes([default_top, 700])
        else:
            self.workspace_vsplit.setSizes([default_top, 700])
        if saved_h:
            try:
                workspace_body_split.setSizes([int(s) for s in saved_h])
            except Exception:
                workspace_body_split.setSizes([default_left, 900])
        else:
            workspace_body_split.setSizes([default_left, 900])
        self.workspace_vsplit.splitterMoved.connect(partial(self._on_splitter_moved, "workspace_vsplit", self.workspace_vsplit))
        workspace_body_split.splitterMoved.connect(partial(self._on_splitter_moved, "workspace_hsplit", workspace_body_split))

        workspaces_layout.addWidget(self.workspace_vsplit)
        workspaces_scroll.setWidget(workspaces_tab)
        tabs.addTab(workspaces_scroll, "WORKSPACES")

        # ----- Network tab -----
        network_scroll = QtWidgets.QScrollArea()
        network_scroll.setWidgetResizable(True)
        network_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        network_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        network_tab = QtWidgets.QWidget()
        network_layout = self._register_layout(QtWidgets.QVBoxLayout(network_tab))
        self.network_vsplit = QtWidgets.QSplitter(QtCore.Qt.Vertical if not QT6 else QtCore.Qt.Orientation.Vertical)
        self.network_vsplit.setHandleWidth(8)
        self.network_vsplit.setChildrenCollapsible(False)

        net_top_panel = QtWidgets.QFrame()
        net_top_panel.setStyleSheet("background-color: #0f1626; border: 1px solid #2bb8a6; border-radius: 6px;")
        net_top_layout = self._register_layout(WrapLayout(parent=net_top_panel, margin=4, h_spacing=8, v_spacing=0))
        net_top_layout.setContentsMargins(8, 8, 8, 8)

        self.net_capture_btn = QtWidgets.QToolButton()
        self.net_capture_btn.setText("Capture")
        self.net_capture_btn.setCheckable(True)
        self.net_capture_btn.setChecked(True)
        self.net_capture_btn.toggled.connect(self._on_net_capture_toggled)
        net_top_layout.addWidget(self.net_capture_btn)

        self.net_pause_btn = QtWidgets.QToolButton()
        self.net_pause_btn.setText("Pause")
        self.net_pause_btn.setCheckable(True)
        self.net_pause_btn.toggled.connect(self._on_net_pause_toggled)
        net_top_layout.addWidget(self.net_pause_btn)

        self.net_stop_btn = QtWidgets.QToolButton()
        self.net_stop_btn.setText("Stop")
        self.net_stop_btn.clicked.connect(self._network_stop_capture)
        net_top_layout.addWidget(self.net_stop_btn)

        self.net_capture_scope = QtWidgets.QComboBox()
        self.net_capture_scope.addItems(["Global", "Active Project"])
        net_top_layout.addWidget(self.net_capture_scope)

        self.net_protocol_filter = QtWidgets.QComboBox()
        self.net_protocol_filter.addItems(["Any", "file", "task", "api", "db"])
        self.net_endpoint_filter = QtWidgets.QLineEdit()
        self.net_endpoint_filter.setPlaceholderText("Endpoint")
        self.net_project_filter = QtWidgets.QLineEdit()
        self.net_project_filter.setPlaceholderText("Project")
        self.net_event_filter = QtWidgets.QComboBox()
        self.net_event_filter.addItems(["Any", "state", "mutation", "sync", "error"])
        self.net_time_filter = QtWidgets.QComboBox()
        self.net_time_filter.addItems(["Any", "Last 1m", "Last 5m", "Last 15m"])
        self.net_latency_mode_toggle = QtWidgets.QComboBox()
        self.net_latency_mode_toggle.addItems(["Aggregate", "Point-to-point"])
        self.net_latency_mode_toggle.currentTextChanged.connect(self._network_latency_mode_changed)
        for label, widget in [
            ("Protocol", self.net_protocol_filter),
            ("Endpoint", self.net_endpoint_filter),
            ("Project", self.net_project_filter),
            ("Event", self.net_event_filter),
            ("Time", self.net_time_filter),
            ("Latency", self.net_latency_mode_toggle),
        ]:
            net_top_layout.addWidget(QtWidgets.QLabel(label))
            net_top_layout.addWidget(widget)

        self.net_inject_btn = QtWidgets.QPushButton("Inject Event")
        self.net_inject_btn.clicked.connect(self._network_inject_event)
        net_top_layout.addWidget(self.net_inject_btn)

        self.net_view_group = QtWidgets.QButtonGroup(self)
        self.net_view_graph = QtWidgets.QToolButton()
        self.net_view_graph.setText("Graph")
        self.net_view_graph.setCheckable(True)
        self.net_view_graph.setChecked(True)
        self.net_view_timeline = QtWidgets.QToolButton()
        self.net_view_timeline.setText("Timeline")
        self.net_view_timeline.setCheckable(True)
        self.net_view_table = QtWidgets.QToolButton()
        self.net_view_table.setText("Table")
        self.net_view_table.setCheckable(True)
        for btn in [self.net_view_graph, self.net_view_timeline, self.net_view_table]:
            self.net_view_group.addButton(btn)
            net_top_layout.addWidget(btn)
        self.net_view_graph.toggled.connect(self._on_net_view_graph_toggled)
        self.net_view_timeline.toggled.connect(self._on_net_view_timeline_toggled)
        self.net_view_table.toggled.connect(self._on_net_view_table_toggled)

        self.network_vsplit.addWidget(net_top_panel)

        network_body_split = QtWidgets.QSplitter(QtCore.Qt.Horizontal if not QT6 else QtCore.Qt.Orientation.Horizontal)
        network_body_split.setHandleWidth(8)
        network_body_split.setChildrenCollapsible(False)

        endpoint_panel = QtWidgets.QGroupBox("Endpoints / Channels")
        endpoint_layout = self._register_layout(QtWidgets.QVBoxLayout(endpoint_panel))
        endpoint_layout.setContentsMargins(8, 8, 8, 8)
        self.net_endpoint_list = QtWidgets.QTreeWidget()
        self.net_endpoint_list.setHeaderLabels(["Endpoint", "Status", "Latency", "Throughput", "Errors", "Project"])
        self.net_endpoint_list.setSelectionMode(qt_single_select())
        self._enable_vertical_scroll(self.net_endpoint_list)
        self.net_endpoint_list.itemSelectionChanged.connect(self._on_net_endpoint_selected)
        endpoint_layout.addWidget(self.net_endpoint_list)
        network_body_split.addWidget(endpoint_panel)

        self.net_stack = QtWidgets.QStackedWidget()
        self.net_graph_view = NetworkGraphView()
        self.net_graph_view.node_selected.connect(self._on_net_graph_selected)
        self.net_timeline = QtWidgets.QListWidget()
        self._enable_vertical_scroll(self.net_timeline)
        self.net_table = QtWidgets.QTableWidget(0, 7)
        self.net_table.setHorizontalHeaderLabels(["Time", "Type", "Source", "Dest", "Latency (ms)", "Throughput", "Project"])
        try:
            self.net_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        except Exception:
            pass
        self._enable_vertical_scroll(self.net_table)
        self.register_table_row_context(self.net_table, "networkTable", self._net_payload_for_row)
        self.register_table_for_context(self.net_table, "networkTable")
        self.net_stack.addWidget(self.net_graph_view)
        self.net_stack.addWidget(self.net_timeline)
        self.net_stack.addWidget(self.net_table)
        network_body_split.addWidget(self.net_stack)

        self.network_vsplit.addWidget(network_body_split)
        net_saved_v = self.load_splitter_state("network_vsplit")
        net_saved_h = self.load_splitter_state("network_hsplit")
        if net_saved_v:
            try:
                self.network_vsplit.setSizes([int(s) for s in net_saved_v])
            except Exception:
                self.network_vsplit.setSizes([160, 700])
        else:
            self.network_vsplit.setSizes([160, 700])
        if net_saved_h:
            try:
                network_body_split.setSizes([int(s) for s in net_saved_h])
            except Exception:
                network_body_split.setSizes([340, 900])
        else:
            network_body_split.setSizes([340, 900])
        self.network_vsplit.splitterMoved.connect(partial(self._on_splitter_moved, "network_vsplit", self.network_vsplit))
        network_body_split.splitterMoved.connect(partial(self._on_splitter_moved, "network_hsplit", network_body_split))

        network_layout.addWidget(self.network_vsplit)
        network_scroll.setWidget(network_tab)
        tabs.addTab(network_scroll, "NETWORK")

        # ----- Tasks tab -----
        tasks_scroll = QtWidgets.QScrollArea()
        tasks_scroll.setWidgetResizable(True)
        tasks_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        tasks_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        tasks_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        tasks_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        tasks_tab = QtWidgets.QWidget()
        tasks_layout = self._register_layout(QtWidgets.QVBoxLayout(tasks_tab))
        task_controls = self._register_layout(WrapLayout(margin=0, h_spacing=8, v_spacing=0))
        self.new_task_btn = QtWidgets.QPushButton("New Task")
        self.new_task_btn.setToolTip("Add a new task to the current list.")
        self.save_task_btn = QtWidgets.QPushButton("Save Task")
        self.save_task_btn.setToolTip("Save edits to the selected task.")
        self.complete_task_btn = QtWidgets.QPushButton("Complete/Restore")
        self.complete_task_btn.setToolTip("Toggle completion state of the selected task.")
        self.my_day_btn = QtWidgets.QPushButton("Add to My Day")
        self.my_day_btn.setToolTip("Add the selected task to My Day.")
        self.priority_btn = QtWidgets.QPushButton("Toggle Important")
        self.priority_btn.setToolTip("Toggle the important flag for the selected task.")
        self.delete_task_btn = QtWidgets.QPushButton("Delete Task")
        self.delete_task_btn.setToolTip("Delete the selected task.")
        self.move_up_btn = QtWidgets.QPushButton("Move Up")
        self.move_up_btn.setToolTip("Move the selected task up in the list.")
        self.move_down_btn = QtWidgets.QPushButton("Move Down")
        self.move_down_btn.setToolTip("Move the selected task down in the list.")
        self.tasks_import_btn = QtWidgets.QPushButton("Import JSON")
        self.tasks_import_btn.setText("Import CSV")
        self.tasks_import_btn.setToolTip("Import tasks from a CSV export.")
        self.tasks_export_btn = QtWidgets.QPushButton("Export CSV")
        self.tasks_export_btn.setToolTip("Export tasks to a CSV file.")
        self.import_mode_combo = QtWidgets.QComboBox()
        self.import_mode_combo.addItems(["Strict", "Audit", "Lenient"])
        self.import_mode_combo.setCurrentText("Strict")
        self.import_mode_combo.setToolTip("Choose import validation mode.")
        self.ensure_interactable(self.import_mode_combo)
        for btn in [
            self.new_task_btn,
            self.save_task_btn,
            self.complete_task_btn,
            self.my_day_btn,
            self.priority_btn,
            self.delete_task_btn,
            self.move_up_btn,
            self.move_down_btn,
            self.tasks_import_btn,
            self.tasks_export_btn,
        ]:
            self.ensure_interactable(btn)
            task_controls.addWidget(btn)
        task_controls.addWidget(QtWidgets.QLabel("Import Mode"))
        task_controls.addWidget(self.import_mode_combo)
        tasks_layout.addLayout(task_controls)
        self.tasks_context_label = QtWidgets.QLabel("Selected: No Project Selected | Focused: None")
        self.tasks_context_label.setStyleSheet("color: #9ce4ff; font-weight: bold;")
        tasks_layout.addWidget(self.tasks_context_label)

        task_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal if not QT6 else QtCore.Qt.Orientation.Horizontal)

        list_panel = QtWidgets.QWidget()
        list_layout = self._register_layout(QtWidgets.QVBoxLayout(list_panel))
        list_box = QtWidgets.QGroupBox("Task Lists")
        list_inner_layout = self._register_layout(QtWidgets.QVBoxLayout(list_box))
        self.list_tree = QtWidgets.QTreeWidget()
        self.list_tree.setHeaderLabels(["List", "Scope"])
        self.list_tree.setSelectionMode(qt_single_select())
        self._enable_vertical_scroll(self.list_tree)
        list_inner_layout.addWidget(self.list_tree)
        list_btns = self._register_layout(WrapLayout())
        self.new_list_btn = QtWidgets.QPushButton("New List")
        self.rename_list_btn = QtWidgets.QPushButton("Rename List")
        list_btns.addWidget(self.new_list_btn)
        list_btns.addWidget(self.rename_list_btn)
        list_inner_layout.addLayout(list_btns)
        list_layout.addWidget(list_box)
        task_splitter.addWidget(list_panel)

        task_table_panel = QtWidgets.QWidget()
        task_table_layout = self._register_layout(QtWidgets.QVBoxLayout(task_table_panel))
        self.task_table = QtWidgets.QTableWidget(0, 6)
        self.task_table.setHorizontalHeaderLabels(["Title", "Due", "Priority", "State", "List", "Project"])
        self.task_table.horizontalHeader().setStretchLastSection(True)
        try:
            header = self.task_table.horizontalHeader()
            header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            header.setMinimumSectionSize(90)
            header.setDefaultSectionSize(140)
        except Exception:
            pass
        try:
            vheader = self.task_table.verticalHeader()
            vheader.setDefaultSectionSize(28)
            vheader.setMinimumSectionSize(80)
            vheader.setDefaultAlignment(QtCore.Qt.AlignCenter)
            vheader.setVisible(True)
        except Exception:
            pass
        self.task_table.setAlternatingRowColors(False)
        self.task_table.setStyleSheet(
            "QTableWidget{background-color:#0f1626;alternate-background-color:#0f1626;}"
            "QTableWidget::item{padding:6px 8px;background-color:#0f1626;color:#d8f6ff;}"
            "QTableWidget::item:selected{background-color:#1f2d4a;color:#73f5ff;}"
        )
        self.task_table.setSelectionBehavior(qt_select_rows())
        self.task_table.setSelectionMode(qt_single_select())
        self._enable_vertical_scroll(self.task_table)
        self._normalize_task_table_columns()
        self.register_table_row_context(self.task_table, "tasksTable", self._task_payload_for_row)
        self.register_table_for_context(self.task_table, "tasksTable")
        task_table_layout.addWidget(self.task_table)
        task_splitter.addWidget(task_table_panel)

        detail_panel = QtWidgets.QWidget()
        detail_layout = self._register_layout(QtWidgets.QVBoxLayout(detail_panel))
        detail_box = QtWidgets.QGroupBox("Task Details")
        form = QtWidgets.QFormLayout(detail_box)
        self.title_edit = QtWidgets.QLineEdit()
        self.notes_edit = QtWidgets.QTextEdit()
        self.due_checkbox = QtWidgets.QCheckBox("Enable")
        due_row = QtWidgets.QHBoxLayout()
        self.due_date_edit = QtWidgets.QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(date.today())
        due_row.addWidget(self.due_date_edit)
        due_row.addWidget(self.due_checkbox)
        self.reminder_checkbox = QtWidgets.QCheckBox("Enable")
        reminder_row = QtWidgets.QHBoxLayout()
        self.reminder_edit = QtWidgets.QDateTimeEdit()
        self.reminder_edit.setCalendarPopup(True)
        self.reminder_edit.setDateTime(datetime.now())
        reminder_row.addWidget(self.reminder_edit)
        reminder_row.addWidget(self.reminder_checkbox)
        self.priority_checkbox = QtWidgets.QCheckBox("Important")
        self.recurrence_combo = QtWidgets.QComboBox()
        self.recurrence_combo.addItems(["none", "daily", "weekly", "monthly", "custom"])
        self.recur_interval_spin = QtWidgets.QSpinBox()
        self.recur_interval_spin.setRange(1, 365)
        recur_row = QtWidgets.QHBoxLayout()
        recur_row.addWidget(self.recurrence_combo)
        recur_row.addWidget(QtWidgets.QLabel("Interval days"))
        recur_row.addWidget(self.recur_interval_spin)
        form.addRow("Title", self.title_edit)
        form.addRow("Notes", self.notes_edit)
        form.addRow("Due Date", due_row)
        form.addRow("Reminder", reminder_row)
        form.addRow("Priority", self.priority_checkbox)
        form.addRow("Recurrence", recur_row)
        detail_layout.addWidget(detail_box)
        task_splitter.addWidget(detail_panel)

        task_splitter.setSizes([280, 520, 500])
        tasks_layout.addWidget(task_splitter)
        tasks_scroll.setWidget(tasks_tab)
        tabs.addTab(tasks_scroll, "Tasks")

        # ----- Versioning tab -----
        version_scroll = QtWidgets.QScrollArea()
        version_scroll.setWidgetResizable(True)
        version_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        version_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        version_tab = QtWidgets.QWidget()
        version_layout = self._register_layout(QtWidgets.QVBoxLayout(version_tab))
        repo_content = QtWidgets.QWidget()
        repo_layout = self._register_layout(QtWidgets.QVBoxLayout(repo_content))
        self.repo_status_label = QtWidgets.QLabel("Repository overview collapsed – expand to load.")
        self.repo_status_label.setStyleSheet("color: #8ad0ff;")
        repo_layout.addWidget(self.repo_status_label)
        self.repo_table = QtWidgets.QTableWidget(0, 5)
        self.repo_table.setHorizontalHeaderLabels(["Repository Name", "Available Branches", "Active Branch", "Last Updated", "Visibility"])
        try:
            self.repo_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        except Exception:
            pass
        self.repo_table.setSelectionMode(qt_single_select())
        self.repo_table.setSelectionBehavior(qt_select_rows())
        self.repo_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.repo_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.repo_table.setAlternatingRowColors(False)
        self.repo_table.setStyleSheet(
            "QTableWidget { background: #0f1626; color: #d8f6ff; } "
            "QTableWidget::item { background: #0f1626; color: #d8f6ff; } "
            "QTableWidget::item:selected { background: rgba(146,158,255,0.25); }"
        )
        self._enable_vertical_scroll(self.repo_table)
        self.register_table_row_context(self.repo_table, "repoTable", self._repo_payload_for_row)
        self.register_table_for_context(self.repo_table, "repoTable")
        repo_layout.addWidget(self.repo_table)
        self.repo_pane = CollapsiblePane(
            "Repository Overview",
            repo_content,
            collapsed=self.get_collapsible_state("repo-overview", True),
            on_toggle=self._on_repo_overview_toggled,
        )
        self.register_pane_context(self.repo_pane, "repo-overview")
        version_layout.addWidget(self.repo_pane)
        self.version_context_label = QtWidgets.QLabel("Selected: No Project Selected | Focused: None")
        self.version_context_label.setStyleSheet("color: #9ce4ff; font-weight: bold;")
        version_layout.addWidget(self.version_context_label)
        vcs_box = QtWidgets.QGroupBox("Version Control (AutoGIT)")
        vcs_layout = self._register_layout(QtWidgets.QVBoxLayout(vcs_box))
        self.autogit_path_label = QtWidgets.QLabel("Target: (focus or select a project)")
        self.autogit_status_label = QtWidgets.QLabel("Git: Unknown")
        self.autogit_status_label.setStyleSheet("color: #8ad0ff;")
        self.autogit_status_btn = QtWidgets.QPushButton("Git Status")
        self.autogit_status_btn.setToolTip("Check git status for the selected project.")
        self.autogit_init_btn = QtWidgets.QPushButton("Init with AutoGIT")
        self.autogit_init_btn.setToolTip("Initialize AutoGIT/git for the selected project.")
        self.autogit_commit_btn = QtWidgets.QPushButton("AutoGIT Commit")
        self.autogit_commit_btn.setToolTip("Run an AutoGIT commit for the selected project.")
        self.auto_commit_toggle = QtWidgets.QPushButton("Auto Commit")
        self.auto_commit_toggle.setCheckable(True)
        self.auto_commit_toggle.setEnabled(False)
        self.auto_commit_toggle.setToolTip("Enable or disable AutoGIT auto-commit for the selected project.")
        vcs_btn_row = self._register_layout(WrapLayout())
        vcs_btn_row.addWidget(self.autogit_status_btn)
        vcs_btn_row.addWidget(self.autogit_init_btn)
        vcs_btn_row.addWidget(self.autogit_commit_btn)
        vcs_btn_row.addWidget(self.auto_commit_toggle)
        for btn in [self.autogit_status_btn, self.autogit_init_btn, self.autogit_commit_btn, self.auto_commit_toggle]:
            self.ensure_interactable(btn)
        self.vcs_output = QtWidgets.QPlainTextEdit()
        self.vcs_output.setReadOnly(True)
        self.vcs_output.setPlaceholderText("AutoGIT output will appear here.")
        vcs_layout.addWidget(self.autogit_path_label)
        vcs_layout.addWidget(self.autogit_status_label)
        vcs_layout.addLayout(vcs_btn_row)
        vcs_layout.addWidget(self.vcs_output)
        # Version history section
        history_content = QtWidgets.QWidget()
        history_layout = self._register_layout(QtWidgets.QVBoxLayout(history_content))
        hist_btn_row = self._register_layout(WrapLayout(margin=0, h_spacing=8, v_spacing=0))
        self.fetch_versions_btn = QtWidgets.QPushButton("Fetch Versions")
        self.fetch_versions_btn.setEnabled(False)
        self.fetch_versions_btn.setToolTip("Fetch commit history from GitHub for the selected project.")
        self.revert_version_btn = QtWidgets.QPushButton("Revert to Selected Version")
        self.revert_version_btn.setEnabled(False)
        self.revert_version_btn.setToolTip("Reset the selected project to the chosen commit (requires confirmation).")
        for btn in [self.fetch_versions_btn, self.revert_version_btn]:
            self.ensure_interactable(btn)
        hist_btn_row.addWidget(self.fetch_versions_btn)
        hist_btn_row.addWidget(self.revert_version_btn)
        history_layout.addLayout(hist_btn_row)
        self.version_list = QtWidgets.QListWidget()
        self.version_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._enable_vertical_scroll(self.version_list)
        history_layout.addWidget(self.version_list)
        self.history_box = CollapsiblePane(
            "Version History",
            history_content,
            collapsed=self.get_collapsible_state("version-history", False),
            on_toggle=partial(self._on_collapsible_toggle, "version-history"),
        )
        self.register_pane_context(self.history_box, "version-history")
        version_layout.addWidget(self.history_box)
        version_layout.addWidget(vcs_box)
        redaction_row = self._register_layout(WrapLayout(margin=0, h_spacing=8, v_spacing=0))
        redaction_row.addWidget(QtWidgets.QLabel("Redaction:"))
        self.redaction_badge = QtWidgets.QLabel("UNREDACTED")
        self.redaction_badge.setAlignment(QtCore.Qt.AlignCenter)
        self.redaction_badge.setStyleSheet("color: #9ce4ff; border: 1px solid #9ce4ff; border-radius: 6px; padding: 6px 10px;")
        redaction_row.addWidget(self.redaction_badge)
        self.redact_btn = QtWidgets.QPushButton("Redact")
        self.unredact_btn = QtWidgets.QPushButton("Unredact")
        for btn in (self.redact_btn, self.unredact_btn):
            self.ensure_interactable(btn)
        redaction_row.addWidget(self.redact_btn)
        redaction_row.addWidget(self.unredact_btn)
        redaction_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        version_layout.addLayout(redaction_row)
        version_scroll.setWidget(version_tab)
        tabs.addTab(version_scroll, "Versioning")

        # ----- Settings tab (intentionally empty) -----
        settings_tab = QtWidgets.QWidget()
        settings_layout = self._register_layout(QtWidgets.QVBoxLayout(settings_tab))
        self.settings_context_label = QtWidgets.QLabel("Selected: No Project Selected | Focused: None")
        self.settings_context_label.setStyleSheet("color: #9ce4ff; font-weight: bold;")
        settings_layout.addWidget(self.settings_context_label)

        # Collapsible sections
        settings_layout.addWidget(self._build_settings_section("User", self._build_user_section()))
        settings_layout.addWidget(self._build_settings_section("Accessibility", self._build_accessibility_section()))
        settings_layout.addWidget(self._build_settings_section("Interface", self._build_interface_section()))
        settings_layout.addWidget(self._build_settings_section("Controls", self._build_controls_section()))
        settings_layout.addStretch(1)
        settings_scroll = QtWidgets.QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        settings_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        settings_scroll.setWidget(settings_tab)
        tabs.addTab(settings_scroll, "Settings")
        self.tab_scrolls = [projects_scroll, workspaces_scroll, network_scroll, tasks_scroll, version_scroll, settings_scroll]
        tabs.currentChanged.connect(self._on_tab_changed)

        self._apply_theme(scale_factor=self.scale_factor)
        self._wire_events()
        self._refresh_network_views()

    def _build_stylesheet(self, scale_factor=1.0, density="normal", theme="dark", accent_primary=None, accent_glow=None):
        font_size = max(9, int(12 * scale_factor))
        btn_v = max(2, int(8 * scale_factor))
        btn_h = max(4, int(12 * scale_factor))
        header_pad = max(3, int(6 * scale_factor))
        text_pad = max(3, int(8 * scale_factor))
        line_pad = max(3, int(6 * scale_factor))
        group_margin = max(4, int(10 * scale_factor))
        title_v = max(2, int(4 * scale_factor))
        title_h = max(4, int(8 * scale_factor))
        if density == "compact":
            btn_v = max(2, int(6 * scale_factor))
            btn_h = max(4, int(10 * scale_factor))
        elif density == "spacious":
            btn_v = max(4, int(10 * scale_factor))
            btn_h = max(8, int(14 * scale_factor))
        if theme == "darker":
            bg_window = "#070a12"
            bg_panel = "#0b1020"
            header_bg = "#11182a"
        elif theme == "contrast":
            bg_window = "#0a0a0a"
            bg_panel = "#0c1628"
            header_bg = "#111b2d"
        else:
            bg_window = "#0b0f1a"
            bg_panel = "#0f1626"
            header_bg = "#131c2f"
        accent_primary = accent_primary or ACCENTS["cyan"]["primary"]
        accent_glow = accent_glow or ACCENTS["cyan"]["glow"]
        try:
            rgb = tuple(int(accent_primary.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        except Exception:
            rgb = (255, 179, 71)
        selected_bg = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.35)"
        return f"""
            QWidget {{ background-color: {bg_window}; color: #d8f6ff; font-family: 'JetBrains Mono', 'Roboto Mono', monospace; font-size: {font_size}px; }}
            QPushButton {{ background-color: #1f2d4a; border: 1px solid #3b6aff; padding: {btn_v}px {btn_h}px; border-radius: 6px; color: #9ce4ff; }}
            QPushButton:hover {{ background-color: #25355a; border-color: {accent_glow}; }}
            QPushButton:pressed {{ background-color: #1a2642; }}
            QTableWidget {{ gridline-color: #1f2d4a; }}
            QHeaderView::section {{ background-color: {header_bg}; color: #8ad0ff; padding: {header_pad}px; border: 0px; }}
            QTreeView {{ alternate-background-color: {bg_panel}; }}
            QTextEdit {{ border: 1px solid #3b6aff; border-radius: 6px; padding: {text_pad}px; background: {bg_panel}; }}
            QLineEdit {{ border: 1px solid #3b6aff; border-radius: 4px; padding: {line_pad}px; background: #101827; }}
            QCheckBox {{ color: #b7d9ff; }}
            QGroupBox {{ border: 1px solid #283b66; border-radius: 8px; margin-top: {group_margin}px; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: {title_v}px {title_h}px; color: #9ce4ff; }}
            QTabBar::tab:selected {{ color: {accent_primary}; border-bottom: 2px solid {accent_primary}; }}
            QTabBar::tab:hover {{ color: {accent_glow}; }}
            QTableView::item:selected {{ background-color: {selected_bg}; color: #f8f9fb; }}
            QProgressBar::chunk {{ background-color: {accent_primary}; }}
            QProgressBar {{ border: 1px solid {accent_glow}; border-radius: 4px; text-align: center; }}
            """

    def _apply_app_font(self, scale_factor):
        base_size = self.base_font_size or QtWidgets.QApplication.font().pointSizeF() or 11
        font = QtGui.QFont(QtWidgets.QApplication.font())
        font.setPointSizeF(base_size * scale_factor)
        QtWidgets.QApplication.instance().setFont(font)

    def _apply_spacing_scale(self):
        spacing = max(4, int(8 * self.scale_factor))
        for layout in self.scalable_layouts:
            try:
                layout.setSpacing(spacing)
                margins = self.layout_margins.get(layout, (0, 0, 0, 0))
                layout.setContentsMargins(
                    int(margins[0] * self.scale_factor),
                    int(margins[1] * self.scale_factor),
                    int(margins[2] * self.scale_factor),
                    int(margins[3] * self.scale_factor),
                )
            except Exception:
                continue

    def update_accent_usage(self):
        accent = getattr(self, "accent_primary", ACCENTS["sunset"]["primary"])
        glow = getattr(self, "accent_glow", ACCENTS["sunset"]["glow"])
        if hasattr(self, "sound_engine"):
            self.sound_engine.update_accent(glow)
        if hasattr(self, "photon_terminal_widget"):
            self.photon_terminal_widget.update_accent(accent, glow)
        # Active/focused cues
        self.update_active_label()
        # Auto-commit buttons use accent when enabled
        style_on = f"background-color: #1f2d4a; border: 1px solid {accent}; color: {accent};"
        style_off = ""
        if hasattr(self, "auto_commit_toggle"):
            self.auto_commit_toggle.setStyleSheet(style_on if self.auto_commit_toggle.isChecked() else style_off)
        if hasattr(self, "auto_commit_global_btn"):
            self.auto_commit_global_btn.setStyleSheet(style_on if self.auto_commit_global_btn.isChecked() else style_off)
        # Progress bar adopts accent
        if hasattr(self, "operation_progress"):
            self.operation_progress.setStyleSheet(
                f"QProgressBar::chunk{{background-color:{accent};}} QProgressBar{{border:1px solid {glow}; border-radius:4px; text-align:center;}}"
            )
        # Ensure table selection uses accent via stylesheet refresh (applied in _apply_theme). Repaint to pick up style.
        if hasattr(self, "project_table"):
            self.project_table.viewport().update()
        self.reflow_layouts()
        self._geometry_guard()
        self._update_photon_entry_button_style()

    def _update_photon_entry_button_style(self):
        btn = getattr(self, "photon_entry_btn", None)
        if not btn:
            return
        accent = getattr(self, "accent_primary", ACCENTS["cyan"]["primary"])
        glow = getattr(self, "accent_glow", ACCENTS["cyan"]["glow"])
        btn.setStyleSheet(
            f"border-radius: 26px; background-color: {accent}; color: #050a13; border: 2px solid {glow};"
        )
        effect = getattr(self, "_photon_entry_effect", None)
        if effect:
            effect.setColor(QtGui.QColor(glow))

    # ---- Session safety helpers ----
    def _force_cleanup_on_start(self):
        """Ensure no stale mount or focus metadata survives between sessions."""
        try:
            os.chdir(Path.home())
        except Exception:
            pass
        if USE_BIND_MOUNT and os.path.ismount(ACTIVE_PROJECT_PATH):
            # Attempt non-interactive unmount to avoid prompts
            self.detach_fs_view()
            ok = self._unmount_active_mount(no_prompt=True)
            if not ok:
                self.startup_cleanup_ok = False
        self.active_project = self.get_marker_project()
        self.ui_state["focused_project"] = self.active_project
        self.ui_state["mount_active"] = False

    def _unmount_active_mount(self, allow_prompt=False, no_prompt=False):
        """Shared unmount helper; avoids prompts when no_prompt is True."""
        try:
            os.chdir(Path.home())
        except Exception:
            pass
        self.detach_fs_view()
        if not os.path.ismount(ACTIVE_PROJECT_PATH):
            self.backend.remove_focus_marker()
            return True
        if no_prompt:
            # Try sudo -n first, then plain umount; keep it quick/non-blocking.
            for cmd in (["sudo", "-n", "umount", ACTIVE_PROJECT_PATH], ["umount", ACTIVE_PROJECT_PATH]):
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
                    if res.returncode == 0:
                        self.backend.remove_focus_marker()
                        return True
                except Exception:
                    continue
            return False
        # prompt-based path (uses backend/unfocus which may ask for sudo password)
        result = self.backend.unfocus()
        if result.returncode == 0:
            self.backend.remove_focus_marker()
            return True
        return False

    def _start_consistency_monitor(self):
        self.consistency_timer = QtCore.QTimer(self)
        self.consistency_timer.setInterval(5000)
        self.consistency_timer.timeout.connect(self._check_consistency_state)
        self.consistency_timer.start()
        self.log_debug("STABILITY", {"monitor": "started", "interval_ms": 5000, "debug_level": getattr(self, "debug_level", "normal")})

    def _check_consistency_state(self):
        if not self.session_active:
            return
        if not self._ui_alive(self):
            self.log_debug("STABILITY", {"monitor_tick": "skipped", "reason": "teardown"})
            return
        mount_project = self.backend.detect_active() if USE_BIND_MOUNT else None
        marker_project = self.get_marker_project()
        ui_project = self.active_project
        manifest_project = None
        if mount_project:
            manifest = self.load_manifest(mount_project)
            manifest_project = manifest.get("project_name") if isinstance(manifest, dict) else None
        mismatch = False
        names = [p for p in ((mount_project if USE_BIND_MOUNT else None), marker_project, ui_project, manifest_project) if p]
        if names and len(set(names)) > 1:
            mismatch = True
        if USE_BIND_MOUNT:
            if mount_project and not ui_project:
                mismatch = True
            if not mount_project and ui_project:
                mismatch = True
        else:
            if marker_project and not ui_project:
                mismatch = True
            if ui_project and not marker_project:
                mismatch = False  # allowed when marker just removed
        if mismatch:
            self._handle_desync(mount_project, marker_project, ui_project, manifest_project)
        if hasattr(self, "supervisor"):
            self.supervisor.monitor_tick()
            if self.debug_level != "normal":
                self.log_debug("STABILITY", {"monitor_tick": True, "qt_messages": len(getattr(self.supervisor, "qt_messages", []))})

    def _handle_desync(self, mount_project, marker_project, ui_project, manifest_project):
        if not self._ui_alive(self):
            return
        self.set_state("Error", "Active project desynchronized")
        self.show_error_banner("Active project desynchronized. Resyncing...")
        self._resync_focus(mount_project, marker_project, ui_project, manifest_project)

    def _resync_focus(self, mount_project, marker_project, ui_project, manifest_project):
        if not self._ui_alive(self):
            return
        self.detach_fs_view()
        self._unmount_active_mount(no_prompt=True)
        self.backend.remove_focus_marker()
        if hasattr(self, "photon_terminal_widget"):
            self.photon_terminal_widget.shutdown()
        self.active_project = None
        self.update_active_label()
        self.refresh_health_panel()
        target = None
        for candidate in (ui_project, marker_project, manifest_project):
            if candidate and os.path.isdir(os.path.join(PROJECT_ROOT, candidate)):
                target = candidate
                break
        if target:
            result = self.backend.focus(target)
            if result.returncode == 0:
                self.backend.write_focus_marker(target)
                self.active_project = target
                self.update_active_label()
                self.update_context_labels()
                self.refresh_health_panel()
                self.show_error_banner("Resync complete.")
                self.set_state("Idle", "Resynced")
                return
        self.update_active_label()
        self.update_context_labels()
        self.refresh_health_panel()
        self.show_error_banner("Resync failed. Unfocused for safety.")
        self.set_state("Error", "Resync failed")

    def _apply_theme(self, theme=None, density=None, scale_factor=None):
        if theme is None and hasattr(self, "theme_combo"):
            theme = self.theme_combo.currentText()
        theme = theme or "dark"
        if density is None and hasattr(self, "density_combo"):
            density = self.density_combo.currentText()
        density = density or "normal"
        sf = scale_factor or getattr(self, "scale_factor", 1.0)
        accent_key = self.accent_combo.currentText() if hasattr(self, "accent_combo") else "cyan"
        accent = ACCENTS.get(accent_key, ACCENTS["cyan"])
        self.accent_primary = accent["primary"]
        self.accent_glow = accent["glow"]
        palette = self.palette()
        if theme == "darker":
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#070a12"))
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#0b1020"))
        elif theme == "contrast":
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0a0a0a"))
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#0c1628"))
        else:
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0b0f1a"))
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#0f1626"))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#d8f6ff"))
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#d8f6ff"))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#152137"))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#9ce4ff"))
        self.setPalette(palette)
        self.setStyleSheet(self._build_stylesheet(scale_factor=sf, density=density, theme=theme, accent_primary=self.accent_primary, accent_glow=self.accent_glow))
        dot_size = max(10, int(14 * sf))
        self.state_dot.setFixedSize(dot_size, dot_size)
        dot_color_match = re.search(r"background-color:\s*([^;]+);", self.state_dot.styleSheet())
        dot_color = dot_color_match.group(1).strip() if dot_color_match else "#2e9b8f"
        self.state_dot.setStyleSheet(f"background-color: {dot_color}; border-radius: {max(5, dot_size//2)}px;")
        self._apply_spacing_scale()
        self.update_accent_usage()

    def apply_ui_scale(self, initial=False, animate=False):
        # Preserve current window geometry so scaling never alters window size/position.
        current_geom = self.geometry()
        current_min = self.minimumSize()
        density = self.density_combo.currentText() if hasattr(self, "density_combo") else "normal"
        if hasattr(self, "ui_scale_slider"):
            self.ui_scale = self.ui_scale_slider.value()
            if hasattr(self, "ui_scale_value"):
                self.ui_scale_value.setText(f"{self.ui_scale}%")
        target_factor = max(0.6, min(4.0, (self.ui_scale or 100) / 100))
        target_wrap = target_factor > 1.0
        if animate and not initial:
            if hasattr(self, "_scale_anim") and self._scale_anim and self._scale_anim.state() == QtCore.QAbstractAnimation.Running:
                self._scale_anim.stop()
            self._scale_anim = QtCore.QPropertyAnimation(self, b"animatedScale")
            self._scale_anim.setDuration(150)
            self._scale_anim.setStartValue(getattr(self, "_animated_scale", self.scale_factor))
            self._scale_anim.setEndValue(target_factor)
            self._scale_anim.start()
        else:
            self._apply_app_font(target_factor)
            self._apply_theme(scale_factor=target_factor)
            self.update_wrap_mode(active=target_wrap)
        self.scale_factor = target_factor
        self.wrap_mode = target_wrap
        self._animated_scale = target_factor
        # Restore geometry and minimum size to avoid any implicit resize from layout changes.
        self.setMinimumSize(current_min)
        self.setGeometry(current_geom)
        if not initial:
            self.settings.setdefault("interface", {})
            self.settings["interface"]["ui_scale"] = int(self.ui_scale)
            self.settings["interface"]["wrap_mode"] = bool(self.wrap_mode)
            self.settings["interface"]["spill_direction"] = self.wrap_spill_direction
            self.save_settings()
        self.update_identity_banner()
        self.reflow_layouts()
        self._geometry_guard()
        self.log_debug(
            "UI_STATE",
            {
                "scale_factor": round(self.scale_factor, 2),
                "wrap_mode": self.wrap_mode,
                "density": density,
            },
        )

    def on_ui_scale_changed(self, value):
        self.ui_scale = value
        self.apply_ui_scale(animate=True)

    def update_wrap_mode(self, active=None):
        wrap_active = bool(self.scale_factor > 1.0) if active is None else bool(active)
        self.wrap_mode = wrap_active if self.scale_factor > 1.0 else False
        for layout in getattr(self, "wrap_layouts", []):
            try:
                layout.set_wrap_enabled(self.wrap_mode)
            except Exception:
                continue

    def _get_animated_scale(self):
        return getattr(self, "_animated_scale", self.scale_factor)

    def _set_animated_scale(self, value):
        self._animated_scale = value
        self._apply_app_font(value)
        self._apply_theme(scale_factor=value)
        self.update_wrap_mode(active=value > 1.0)
        self.update_identity_banner()

    animatedScale = QtCore.pyqtProperty(float, fget=_get_animated_scale, fset=_set_animated_scale)

    # ---- Responsive layout helpers ----
    def ensure_interactable(self, widget):
        if isinstance(widget, (QtWidgets.QPushButton, QtWidgets.QLineEdit, QtWidgets.QComboBox, QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox, QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit)):
            widget.setMinimumHeight(INTERACTION_MIN_HEIGHT)
            widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def _apply_background_image(self):
        try:
            bg_path = os.path.join(os.path.dirname(__file__), "background.png")
            if not os.path.exists(bg_path):
                return
            url_path = bg_path.replace("\\", "/")
            sheet = (
                f"#singularityMainWindow {{ background-image: url('{url_path}'); background-position: center center; background-repeat: no-repeat; background-attachment: fixed; }}"
                f"#centralwidget {{ background-image: url('{url_path}'); background-position: center center; background-repeat: no-repeat; background-attachment: fixed; }}"
            )
            self.setStyleSheet(sheet)
        except Exception:
            pass

    # ---- Tooltip and context menu primitives ----
    def _bulk_register_tooltips(self):
        if not hasattr(self, "tooltip_manager") or self.tooltip_manager is None:
            return
        interactive_types = (
            QtWidgets.QPushButton,
            QtWidgets.QToolButton,
            QtWidgets.QCheckBox,
            QtWidgets.QRadioButton,
            QtWidgets.QComboBox,
            QtWidgets.QSpinBox,
            QtWidgets.QDoubleSpinBox,
            QtWidgets.QLineEdit,
            QtWidgets.QAbstractSlider,
            QtWidgets.QTabBar,
        )
        for widget in self.findChildren(QtWidgets.QWidget):
            if isinstance(widget, interactive_types) and not self.tooltip_manager.has(widget):
                existing = widget.toolTip()
                if existing:
                    self.tooltip_manager.register(widget, existing)
                    continue
                label = ""
                if hasattr(widget, "text"):
                    try:
                        label = widget.text()
                    except Exception:
                        label = ""
                label = label or widget.objectName() or widget.__class__.__name__
                self.tooltip_manager.register(widget, label, "Affects system state or selection.")

    def _normalize_column_id(self, label: str):
        cleaned = re.sub(r"[^A-Za-z0-9]+", "_", label or "").strip("_").lower()
        return cleaned or "col"

    def _get_column_visibility(self, table_id: str, column_id: str, default=True):
        return self.column_visibility.get(table_id, {}).get(column_id, default)

    def _set_column_visibility(self, table_id: str, column_id: str, visible: bool):
        self.column_visibility.setdefault(table_id, {})[column_id] = bool(visible)
        self.settings["column_visibility"] = self.column_visibility
        self.save_settings()

    def _apply_column_visibility(self, table_id: str, table_widget: QtWidgets.QTableWidget):
        header = table_widget.horizontalHeader()
        for logical in range(table_widget.columnCount()):
            label = header.model().headerData(logical, QtCore.Qt.Horizontal) or f"col_{logical}"
            column_id = self._normalize_column_id(str(label))
            visible = self._get_column_visibility(table_id, column_id, default=True)
            table_widget.setColumnHidden(logical, not visible)

    def toggle_column_visibility(self, table_id: str, column_id: str, logical_index: int, visible: bool):
        table = self.table_registry.get(table_id)
        if not table:
            return
        table.setColumnHidden(logical_index, not visible)
        self._set_column_visibility(table_id, column_id, visible)

    def register_table_for_context(self, table_widget: QtWidgets.QTableWidget, table_id: str):
        if not table_widget:
            return
        self.table_registry[table_id] = table_widget
        table_widget.setObjectName(table_id)
        header = table_widget.horizontalHeader()
        header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(partial(self._on_table_header_context, table_id, table_widget))
        self._apply_column_visibility(table_id, table_widget)
        if hasattr(self, "tooltip_manager") and self.tooltip_manager:
            self.tooltip_manager.register(header, "Column Controls", "Right-click any column header for quick settings.")

    def register_table_row_context(self, table_widget: QtWidgets.QTableWidget, table_id: str, payload_builder=None):
        if not table_widget:
            return
        table_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table_widget.customContextMenuRequested.connect(partial(self._on_table_row_context, table_id, table_widget, payload_builder))
        if hasattr(self, "tooltip_manager") and self.tooltip_manager:
            self.tooltip_manager.register(table_widget, f"{table_id} rows", "Right-click any row for quick actions.")

    def _on_table_header_context(self, table_id: str, table_widget: QtWidgets.QTableWidget, pos: QtCore.QPoint):
        header = table_widget.horizontalHeader()
        logical = header.logicalIndexAt(pos)
        if logical < 0:
            return
        label = header.model().headerData(logical, QtCore.Qt.Horizontal) or f"col_{logical}"
        column_id = self._normalize_column_id(str(label))
        is_visible = not table_widget.isColumnHidden(logical)
        payload = {
            "type": "table-column",
            "targetId": f"{table_id}:{column_id}",
            "metadata": {
                "tableId": table_id,
                "columnId": column_id,
                "columnLabel": str(label),
                "isVisible": is_visible,
                "logicalIndex": logical,
            },
            "capabilities": ["visibility"],
        }
        actions = self._build_context_actions(payload)
        global_pos = header.mapToGlobal(pos)
        self.context_menu_manager.open_menu(payload, actions, global_pos)

    def _on_table_row_context(self, table_id: str, table_widget: QtWidgets.QTableWidget, payload_builder, pos: QtCore.QPoint):
        index = table_widget.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        if payload_builder:
            payload = payload_builder(row)
        else:
            payload = {
                "type": "table-row",
                "targetId": f"{table_id}:{row}",
                "metadata": {"tableId": table_id, "row": row},
                "capabilities": [],
            }
        if not payload:
            return
        actions = self._build_context_actions(payload)
        global_pos = table_widget.viewport().mapToGlobal(pos)
        self.context_menu_manager.open_menu(payload, actions, global_pos)

    def _task_payload_for_row(self, row: int):
        uuid_item = self.task_table.item(row, 0)
        task_id = uuid_item.text() if uuid_item else ""
        if not task_id:
            header_item = self.task_table.verticalHeaderItem(row)
            task_id = header_item.text() if header_item else ""
        task = self.store.get_task(task_id) if task_id else None
        return {
            "type": "task",
            "targetId": task_id or f"tasksTable:{row}",
            "metadata": {
                "tableId": "tasksTable",
                "row": row,
                "task": task or {},
                "project": task.get("project") if task else None,
                "origin_path": os.path.join(PROJECT_ROOT, task.get("project")) if task and task.get("project") else None,
            },
            "capabilities": ["visibility", "watch"],
        }

    def _project_payload_for_row(self, row: int):
        item = self.project_table.item(row, 0)
        name = item.text() if item else f"project_{row}"
        path = os.path.join(PROJECT_ROOT, name)
        return {
            "type": "project",
            "targetId": name,
            "metadata": {"tableId": "projectsTable", "row": row, "origin_path": path},
            "capabilities": ["watch"],
        }

    def _repo_payload_for_row(self, row: int):
        item = self.repo_table.item(row, 0)
        name = item.text() if item else f"repo_{row}"
        return {
            "type": "repository",
            "targetId": name,
            "metadata": {"tableId": "repoTable", "row": row},
            "capabilities": ["watch"],
        }

    def _net_payload_for_row(self, row: int):
        values = []
        for col in range(self.net_table.columnCount()):
            cell = self.net_table.item(row, col)
            values.append(cell.text() if cell else "")
        target_id = f"net_event_{row}"
        return {
            "type": "network-event",
            "targetId": target_id,
            "metadata": {"tableId": "networkTable", "row": row, "values": values},
            "capabilities": ["watch"],
        }

    def register_pane_context(self, pane: CollapsiblePane, pane_id: str):
        if not pane or not hasattr(pane, "title_label"):
            return
        pane.title_label.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        pane.title_label.customContextMenuRequested.connect(partial(self._on_pane_context, pane_id, pane))
        if hasattr(self, "tooltip_manager") and self.tooltip_manager:
            self.tooltip_manager.register(pane.title_label, f"{pane_id} controls", "Right-click for quick panel settings.")

    def _on_pane_context(self, pane_id: str, pane: CollapsiblePane, pos: QtCore.QPoint):
        is_collapsed = not bool(pane.toggle.isChecked())
        payload = {
            "type": "panel",
            "targetId": pane_id,
            "metadata": {
                "paneId": pane_id,
                "isCollapsed": is_collapsed,
                "paneRef": pane,
            },
            "capabilities": ["collapse"],
        }
        actions = self._build_context_actions(payload)
        global_pos = pane.title_label.mapToGlobal(pos)
        self.context_menu_manager.open_menu(payload, actions, global_pos)

    def _build_context_actions(self, payload: dict) -> list[dict]:
        actions: list[dict] = []
        ptype = payload.get("type")
        meta = payload.get("metadata") or {}
        caps = set(payload.get("capabilities") or [])
        # Global action registry first
        for spec in self.action_registry.actions_for_payload(payload):
            tooltip = spec.get("tooltip_primary", "")
            secondary = spec.get("tooltip_secondary", "")
            combined = f"{tooltip}\n{secondary}".strip()
            checked = False
            atype = "toggle" if spec.get("toggled") else "action"
            if spec.get("id") == "watch":
                checked = self.watch_manager.is_watched(payload.get("targetId", ""))
                atype = "toggle"
            actions.append(
                {
                    "label": spec.get("label", "Action"),
                    "type": atype,
                    "checked": checked,
                    "tooltip": combined,
                    "action": lambda checked=False, handler=spec.get("handler"): handler(payload),
                }
            )
        if ptype == "table-column":
            if "visibility" in caps:
                table_id = meta.get("tableId")
                col_id = meta.get("columnId")
                logical = meta.get("logicalIndex")
                if table_id and col_id is not None and logical is not None:
                    col_label = meta.get("columnLabel", col_id)
                    visible = bool(meta.get("isVisible", True))
                    actions.append(
                        {
                            "label": "Toggle Visibility",
                            "type": "toggle",
                            "checked": visible,
                            "tooltip": (
                                f"{'Hide' if visible else 'Show'} column '{col_label}'.\n"
                                "Visibility is persisted for this table."
                            ),
                            "action": partial(self.toggle_column_visibility, table_id, col_id, logical),
                        }
                    )
        elif ptype == "panel":
            if "collapse" in caps:
                collapsed = bool(meta.get("isCollapsed", False))
                pane_id = meta.get("paneId")
                pane_ref: CollapsiblePane | None = meta.get("paneRef")
                actions.append(
                    {
                        "label": "Expanded",
                        "type": "toggle",
                        "checked": not collapsed,
                        "tooltip": ("Collapse this panel" if not collapsed else "Expand this panel"),
                        "action": lambda checked, pid=pane_id, pref=pane_ref: self._toggle_panel_state(pid, pref, checked),
                    }
                )
        return actions

    def _toggle_panel_state(self, pane_id: str, pane: CollapsiblePane, expanded: bool):
        if pane and hasattr(pane, "toggle"):
            pane.toggle.setChecked(expanded)
        self.set_collapsible_state(pane_id, collapsed=not expanded)

    def _current_context_payload(self):
        return {
            "type": "application",
            "targetId": self.active_project or "console",
            "metadata": {"active_project": self.active_project, "state": getattr(self, "current_state", "Idle")},
            "capabilities": ["inspect", "watch"],
        }

    def _register_global_actions(self):
        self.action_registry.register(
            "inspect",
            "Inspect",
            self._context_inspect,
            tooltip_primary="Inspect the selected object",
            tooltip_secondary="Opens an inline inspector with identity and metadata.",
            context_filter=lambda p: bool(p.get("targetId")),
        )
        self.action_registry.register(
            "copy_id",
            "Copy ID / Reference",
            self._context_copy_id,
            tooltip_primary="Copy the object's identifier",
            tooltip_secondary="Use in logs, watch list, or command palette filters.",
            context_filter=lambda p: bool(p.get("targetId")),
        )
        self.action_registry.register(
            "jump_origin",
            "Jump to Origin",
            self._context_jump_origin,
            tooltip_primary="Navigate to the object's source",
            tooltip_secondary="Focuses list/table/source view if available.",
            context_filter=lambda p: bool(p.get("metadata", {}).get("origin_path") or p.get("metadata", {}).get("row")),
        )
        self.action_registry.register(
            "toggle_scope",
            "Toggle Visibility/Scope",
            self._context_toggle_scope,
            tooltip_primary="Include or hide this object in the current scope",
            tooltip_secondary="Persists where supported (columns, watched sets).",
            context_filter=lambda p: "isVisible" in (p.get("metadata") or {}),
            toggled=True,
        )
        self.action_registry.register(
            "watch",
            "Watch / Unwatch",
            self._context_watch_toggle,
            tooltip_primary="Monitor this object for events",
            tooltip_secondary="Adds to global watch list and event bus surfacing.",
            context_filter=lambda p: bool(p.get("targetId")),
            toggled=True,
        )
        self.action_registry.register(
            "pin",
            "Pin / Unpin",
            self._context_pin_toggle,
            tooltip_primary="Keep this object prioritized",
            tooltip_secondary="Pins in lists where supported; otherwise tracked globally.",
            context_filter=lambda p: bool(p.get("targetId")),
            toggled=True,
        )
        self.action_registry.register(
            "mute",
            "Mute",
            self._context_mute_toggle,
            tooltip_primary="Silence non-critical notifications for this object",
            tooltip_secondary="Muted objects remain active but less noisy.",
            context_filter=lambda p: bool(p.get("targetId")),
            toggled=True,
        )
        self.action_registry.register(
            "watch_center",
            "Open Watch Center",
            lambda payload: self._open_watch_center(),
            tooltip_primary="Manage watched objects globally",
            tooltip_secondary="Inspect and unwatch items from one place.",
            context_filter=lambda _p: True,
        )
        self.action_registry.register(
            "event_viewer",
            "Open Event Bus",
            lambda payload: self._open_event_viewer(),
            tooltip_primary="Inspect recent events",
            tooltip_secondary="Filter and replay context from the unified event bus.",
            context_filter=lambda _p: True,
        )

    def _context_inspect(self, payload):
        meta = payload.get("metadata", {})
        target = payload.get("targetId", "Unknown")
        text = json.dumps({"targetId": target, "type": payload.get("type"), "metadata": meta}, indent=2)
        QtWidgets.QMessageBox.information(self, "Inspect", text)

    def _context_copy_id(self, payload):
        target = payload.get("targetId", "")
        if not target:
            return
        QtWidgets.QApplication.clipboard().setText(str(target))
        self.set_state("Idle", f"Copied {target}")

    def _context_jump_origin(self, payload):
        meta = payload.get("metadata", {})
        path = meta.get("origin_path") or meta.get("source_atlas_file")
        if path and os.path.exists(path):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
            return
        row = meta.get("row")
        if payload.get("type") == "table-row" and row is not None:
            table_id = meta.get("tableId")
            table = self.table_registry.get(table_id) if table_id else None
            if table:
                try:
                    table.selectRow(int(row))
                except Exception:
                    pass

    def _context_toggle_scope(self, payload):
        meta = payload.get("metadata", {})
        if payload.get("type") == "table-column" and "logicalIndex" in meta:
            table_id = meta.get("tableId")
            col_id = meta.get("columnId")
            logical = meta.get("logicalIndex")
            current = bool(meta.get("isVisible", True))
            self.toggle_column_visibility(table_id, col_id, logical, not current)
            return

    def _context_watch_toggle(self, payload):
        target = payload.get("targetId")
        added = self.watch_manager.toggle_watch(target, payload)
        self.set_state("Idle", "Watching" if added else "Unwatched")
        self.event_bus.emit("watch", {"target": target, "added": added})

    def _context_pin_toggle(self, payload):
        # Track pinned items in settings for persistence.
        target = payload.get("targetId")
        pins = set(self.settings.get("pinned", []))
        if target in pins:
            pins.remove(target)
            pinned = False
        else:
            pins.add(target)
            pinned = True
        self.settings["pinned"] = sorted(pins)
        self.save_settings()
        self.event_bus.emit("pin", {"target": target, "pinned": pinned})

    def _context_mute_toggle(self, payload):
        target = payload.get("targetId")
        muted = set(self.settings.get("muted", []))
        if target in muted:
            muted.remove(target)
            now_muted = False
        else:
            muted.add(target)
            now_muted = True
        self.settings["muted"] = sorted(muted)
        self.save_settings()
        self.event_bus.emit("mute", {"target": target, "muted": now_muted})

    def _open_watch_center(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Watch Center")
        layout = QtWidgets.QVBoxLayout(dlg)
        list_widget = QtWidgets.QListWidget()
        for target, data in self.watch_manager.items().items():
            item = QtWidgets.QListWidgetItem(f"{target} @ {data.get('ts')}")
            item.setToolTip(json.dumps(data.get("metadata", {}), indent=2))
            item.setData(QtCore.Qt.UserRole, target)
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        btn = QtWidgets.QPushButton("Unwatch Selected")
        layout.addWidget(btn)

        def unwatch():
            for it in list_widget.selectedItems():
                tid = it.data(QtCore.Qt.UserRole)
                self.watch_manager.toggle_watch(tid)
            dlg.accept()

        btn.clicked.connect(unwatch)
        dlg.resize(420, 360)
        dlg.exec_()

    def _open_event_viewer(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Event Bus")
        layout = QtWidgets.QVBoxLayout(dlg)
        search = QtWidgets.QLineEdit()
        search.setPlaceholderText("Filter by scope or payload...")
        list_widget = QtWidgets.QListWidget()
        layout.addWidget(search)
        layout.addWidget(list_widget)

        def refresh():
            query = search.text().lower().strip()
            list_widget.clear()
            for ev in reversed(self.event_bus.list_events()):
                scope = ev.get("scope", "")
                payload = ev.get("payload", {})
                txt = f"[{ev.get('ts')}] {scope}"
                if query and query not in txt.lower() and query not in json.dumps(payload).lower():
                    continue
                item = QtWidgets.QListWidgetItem(txt)
                item.setToolTip(json.dumps(payload, indent=2))
                list_widget.addItem(item)

        search.textChanged.connect(refresh)
        refresh()
        dlg.resize(520, 420)
        dlg.exec_()

    def reflow_layouts(self):
        if not hasattr(self, "responsive_layouts"):
            return
        for layout in list(self.responsive_layouts):
            try:
                base_dir = self.responsive_base_dir.get(layout, QtWidgets.QBoxLayout.LeftToRight)
                spacing = max(4, int(8 * self.scale_factor))
                if self.scale_factor > HIGH_SCALE_THRESHOLD:
                    layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
                    layout.setSpacing(spacing + 4)
                elif self.scale_factor > NORMAL_SCALE_MAX and layout.count() > 1:
                    layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
                    layout.setSpacing(spacing + 2)
                else:
                    layout.setDirection(base_dir)
                    layout.setSpacing(spacing)
            except Exception:
                continue
        for wrap in getattr(self, "wrap_layouts", []):
            try:
                wrap.setSpacing(max(4, int(8 * self.scale_factor)))
            except Exception:
                continue

    def _geometry_guard(self):
        # Detect simple clipping/overlap after scale changes and request relayout.
        widgets = self.findChildren(QtWidgets.QWidget)
        for w in widgets:
            if not w.isVisible():
                continue
            parent = w.parentWidget()
            if not parent:
                continue
            geom = w.geometry()
            if geom.bottom() > parent.height() or geom.right() > parent.width() or w.height() < w.minimumHeight():
                    parent.updateGeometry()
                try:
                    parent.layout().activate()
                except Exception:
                    pass

    # ---- Date/time formatting helpers (12-hour, human-readable) ----
    @staticmethod
    def _format_ui_datetime(value):
        try:
            if isinstance(value, (int, float)):
                dt = datetime.fromtimestamp(value)
            elif isinstance(value, datetime):
                dt = value
            else:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return dt.strftime("%b %d, %Y %I:%M %p")
        except Exception:
            return str(value)

    @staticmethod
    def _format_ui_time(value):
        try:
            if isinstance(value, (int, float)):
                dt = datetime.fromtimestamp(value)
            elif isinstance(value, datetime):
                dt = value
            else:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return dt.strftime("%I:%M:%S %p")
        except Exception:
            return str(value)

    def _reset_tab_scroll(self, idx):
        if not hasattr(self, "tab_scrolls"):
            return
        if 0 <= idx < len(self.tab_scrolls):
            area = self.tab_scrolls[idx]
            if area is None:
                return
            try:
                area.verticalScrollBar().setValue(0)
            except Exception:
                pass

    def _on_tab_changed(self, idx):
        self._tab_change_pending_idx = idx
        if not self._tab_change_flush_scheduled:
            self._tab_change_flush_scheduled = True
            QtCore.QTimer.singleShot(0, self._flush_tab_change)

    # ---- PHOTON layout attachment helpers ----
    def _attach_photon_panel(self):
        panel = getattr(self, "photon_panel", None)
        layout = getattr(self, "body_layout", None)
        if not panel or not layout or getattr(self, "photon_panel_attached", False):
            return
        panel.setParent(self)
        panel.setVisible(True)
        layout.addWidget(panel)
        self.photon_panel_attached = True

    def _detach_photon_panel(self):
        panel = getattr(self, "photon_panel", None)
        layout = getattr(self, "body_layout", None)
        if not panel or not layout or not getattr(self, "photon_panel_attached", False):
            return
        layout.removeWidget(panel)
        panel.setVisible(False)
        panel.hide()
        panel.setParent(None)
        self.photon_panel_attached = False

    # ---- UX/state helpers ----
    def _log_state_violation(self, reason, state, message):
        self.log_debug("STABILITY", {"state_violation": reason, "requested_state": state, "message": message})

    def _flush_tab_change(self):
        idx = self._tab_change_pending_idx
        self._tab_change_pending_idx = None
        self._tab_change_flush_scheduled = False
        if idx is None:
            return
        self._reset_tab_scroll(idx)
        self._last_active_tab = idx
        if hasattr(self, "sound_engine"):
            self.sound_engine.play("tab")
        if getattr(self, "photon_panel_container", None) and self.photon_panel_container.isVisible():
            self.photon_terminal_widget.tab_activated()

    def _enter_photon_interface(self):
        if not hasattr(self, "photon_panel_container"):
            return
        if self.photon_panel_container.isVisible():
            if hasattr(self, "photon_entry_btn"):
                self.photon_entry_btn.setChecked(True)
            return
        self._attach_photon_panel()
        tabs = getattr(self, "tab_widget", None)
        if tabs:
            self._last_active_tab = tabs.currentIndex()
        self.photon_panel_container.setVisible(True)
        try:
            height = max(300, self.height() // 2)
            self.photon_panel_container.setMinimumHeight(height)
            self.photon_panel_container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        except Exception:
            pass
        if hasattr(self, "photon_entry_btn"):
            self.photon_entry_btn.setChecked(True)
        if hasattr(self, "photon_terminal_widget"):
            self.photon_terminal_widget.tab_activated()
            self.photon_terminal_widget.focus_terminal()

    def _return_to_singularity_interface(self):
        if not hasattr(self, "photon_panel_container"):
            return
        if not self.photon_panel_container.isVisible():
            return
        self.photon_panel_container.setVisible(False)
        self._detach_photon_panel()
        if hasattr(self, "photon_entry_btn"):
            self.photon_entry_btn.setChecked(False)
        tabs = getattr(self, "tab_widget", None)
        if not tabs or tabs.count() == 0:
            return
        target = getattr(self, "_last_active_tab", 0)
        target = max(0, min(target, tabs.count() - 1))
        tabs.setCurrentIndex(target)

    def set_state(self, state, message=""):
        if not self._ui_alive(self):
            return
        self.request_ui_mutation("set_state", self._perform_state_transition, state, message)

    def _perform_state_transition(self, state, message):
        if getattr(self, "_state_transition_active", False):
            return
        self._state_transition_active = True
        try:
            style = STATE_STYLES.get(state, STATE_STYLES["Idle"])
            self.current_state = state
            dot_size = max(10, int(14 * getattr(self, "scale_factor", 1.0)))
            self.state_dot.setFixedSize(dot_size, dot_size)
            # keep state colors but respect rounded size; accent reserved for active cues elsewhere
            self.state_dot.setStyleSheet(f"background-color: {style['color']}; border-radius: {max(5, dot_size//2)}px;")
            self.state_text_label.setText(style["label"])
            self.state_msg_label.setText(message)
            if state == "Error":
                self.refresh_health_panel("Unknown")
            self.log_debug("UI_STATE", {"state": state, "message": message})
            self._update_runtime_strip(state=state)
        finally:
            self._state_transition_active = False
            if getattr(self, "_state_queue", deque()):
                try:
                    self._state_queue.popleft()
                except Exception:
                    self._state_queue = deque()

    def _update_runtime_strip(self, state=None):
        if not hasattr(self, "runtime_strip"):
            return
        project = self.active_project or "None"
        stability = "Safe" if getattr(self.supervisor, "state", {}).get("force_software_render") else getattr(self.supervisor, "debug_level", "normal").title()
        state_val = state or getattr(self, "current_state", "Idle")
        self.runtime_strip.update_state(project=project, state=state_val, stability=stability, warnings=self.warning_count)

    def _safe_show_operation(self, message, state):
        if not self._ui_alive(self):
            return
        self.operation_label.setText(message)
        self.operation_progress.setRange(0, 0)
        self.operation_panel.setVisible(True)
        self.set_state(state, message)

    def show_operation(self, message, state="Loading"):
        self.request_ui_mutation("show_operation", self._safe_show_operation, message, state)

    def finish_operation(self, message=""):
        def _finish():
            if not self._ui_alive(self):
                return
            self.operation_panel.setVisible(False)
            self.operation_progress.setRange(0, 1)
            if self.current_state != "Error":
                self.set_state("Idle", message)
        self.request_ui_mutation("finish_operation", _finish)

    def show_error_banner(self, message):
        self.error_label.setText(message)
        self.error_banner.setVisible(True)
        self.set_state("Error", message)
        self.log_debug("ERRORS", {"message": message})
        self.warning_count += 1
        self._update_runtime_strip()

    def clear_error_banner(self):
        self.error_label.setText("")
        self.error_banner.setVisible(False)
        if self.current_state == "Error":
            self.set_state("Idle", "")

    # ---- Task file watcher ----
    def _init_task_watcher(self):
        try:
            TASKS_WATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
            if not TASKS_WATCH_FILE.exists():
                TASKS_WATCH_FILE.touch()
            self.tasks_watcher = QtCore.QFileSystemWatcher([str(TASKS_WATCH_FILE)])
            self.tasks_watcher.fileChanged.connect(self._handle_tasks_file_change)
        except Exception:
            self.tasks_watcher = None

    def _handle_tasks_file_change(self):
        list_ref = getattr(self, "current_list_ref", None)
        selected_task = self.current_task_id
        try:
            self.store.import_json(str(TASKS_WATCH_FILE), mode=self._current_import_mode())
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Tasks Reload Failed", f"{exc}")
            self.show_error_banner(str(exc))
            return
        if self.tasks_watcher and TASKS_WATCH_FILE.exists():
            if str(TASKS_WATCH_FILE) not in self.tasks_watcher.files():
                self.tasks_watcher.addPath(str(TASKS_WATCH_FILE))
        self.populate_lists()
        if list_ref:
            self._restore_list_selection(list_ref)
        self.load_tasks()
        if selected_task:
            self._auto_select_task(selected_task)

    def _restore_list_selection(self, list_ref):
        target_id = list_ref.get("id")
        target_scope = list_ref.get("scope")
        def match_item(item):
            data = item.data(0, QtCore.Qt.UserRole)
            return data and data.get("id") == target_id and data.get("scope") == target_scope
        def walk(item):
            if match_item(item):
                self.list_tree.setCurrentItem(item)
                return True
            for i in range(item.childCount()):
                if walk(item.child(i)):
                    return True
            return False
        for i in range(self.list_tree.topLevelItemCount()):
            if walk(self.list_tree.topLevelItem(i)):
                self.on_list_selection()
                return

    def _focus_on_text_input(self):
        fw = QtWidgets.QApplication.focusWidget()
        return isinstance(
            fw,
            (
                QtWidgets.QLineEdit,
                QtWidgets.QTextEdit,
                QtWidgets.QPlainTextEdit,
                QtWidgets.QSpinBox,
                QtWidgets.QDoubleSpinBox,
                QtWidgets.QComboBox,
                QtWidgets.QTextBrowser,
            ),
        )

    def _handle_scale_shortcuts(self, event):
        if not (event.modifiers() & QtCore.Qt.ControlModifier):
            return False
        if self._focus_on_text_input():
            return False
        key = event.key()
        if key in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
            self._step_ui_scale(10)
            return True
        if key == QtCore.Qt.Key_Minus:
            self._step_ui_scale(-10)
            return True
        if key == QtCore.Qt.Key_0:
            self._reset_ui_scale()
            return True
        return False

    def keyPressEvent(self, event):
        if self._handle_scale_shortcuts(event):
            return
        super().keyPressEvent(event)

    def _step_ui_scale(self, delta):
        target = int(self.ui_scale or 100) + delta
        target = max(60, min(400, target))
        if hasattr(self, "ui_scale_slider"):
            self.ui_scale_slider.setValue(target)
        else:
            self.ui_scale = target
            self.apply_ui_scale(animate=True)

    def _reset_ui_scale(self):
        if hasattr(self, "ui_scale_slider"):
            self.ui_scale_slider.setValue(100)
        else:
            self.ui_scale = 100
            self.apply_ui_scale(animate=True)

    def _current_import_mode(self):
        if hasattr(self, "import_mode_combo"):
            return self.import_mode_combo.currentText().lower()
        return "strict"

    def ensure_shell_auto_cd_snippet(self):
        snippet = textwrap.dedent(
            """
            # Auto-cd to focused project if present
            case $- in
              *i*) ;;
              *) return ;;
            esac
            if [ -f "$HOME/.focused_project" ]; then
                TARGET="$(cat "$HOME/.focused_project")"
                if [ -d "$TARGET" ]; then
                    cd "$TARGET" 2>/dev/null || cd "$HOME"
                else
                    rm -f "$HOME/.focused_project"
                fi
            fi
            """
        ).strip("\n")
        for rc in [Path.home() / ".bashrc", Path.home() / ".zshrc"]:
            try:
                if rc.exists():
                    with open(rc, "r", encoding="utf-8") as fh:
                        content = fh.read()
                else:
                    content = ""
                marker = "# Auto-cd to focused project if present"
                if marker in content:
                    continue
                with open(rc, "a", encoding="utf-8") as fh:
                    fh.write("\n\n" + snippet + "\n")
            except Exception:
                continue

    # ---- Git safety helpers ----
    def git_with_safe_retry(self, func, project_path, label, env=None):
        result = func()
        if self.autogit.is_dubious_error(result):
            if project_path.startswith(PROJECT_ROOT) and not os.path.islink(project_path):
                added = self.autogit.add_safe_directory(project_path, reason=label, env=env)
                if added:
                    result = func()
        return result

    def autogit_with_safe_retry(self, func, project_path, label, env=None):
        result = func()
        if self.autogit.is_dubious_error(result):
            if project_path.startswith(PROJECT_ROOT) and not os.path.islink(project_path):
                added = self.autogit.add_safe_directory(project_path, reason=label, env=env)
                if added:
                    result = func()
        return result

    def _ui_alive(self, widget=None):
        if getattr(self, "teardown_active", False):
            return False
        app = QtWidgets.QApplication.instance()
        if app is None or getattr(app, "closingDown", lambda: False)():
            return False
        if widget is not None:
            try:
                if hasattr(widget, "isVisible") and not widget.isVisible():
                    return False
                if hasattr(widget, "isWindow") and widget.isWindow() and hasattr(widget, "isHidden") and widget.isHidden():
                    return False
            except Exception:
                return False
        return True

    def run_in_background(self, fn, on_result, on_error=None):
        worker = Worker(fn)

        def safe_result(res):
            if not self._ui_alive():
                self.log_debug("STABILITY", {"dropped_result": getattr(fn, "__name__", "worker"), "reason": "teardown"})
                return
            self.request_ui_mutation("worker_result", on_result, res)

        def safe_error(err):
            if not self._ui_alive():
                self.log_debug("STABILITY", {"dropped_error": getattr(fn, "__name__", "worker"), "reason": "teardown", "error": err})
                return
            if on_error:
                self.request_ui_mutation("worker_error", on_error, err)

        worker.signals.result.connect(safe_result, QtCore.Qt.QueuedConnection)
        if on_error:
            worker.signals.error.connect(safe_error, QtCore.Qt.QueuedConnection)
        self.threadpool.start(worker)

    def processes_using_active_mount(self):
        if not USE_BIND_MOUNT:
            return []
        try:
            proc = subprocess.run(
                ["lsof", "+D", ACTIVE_PROJECT_PATH],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0 and proc.stdout:
                return proc.stdout.strip().splitlines()
        except FileNotFoundError:
            return []
        return []

    def ensure_fs_model(self, root_path):
        if self.fs_view is None:
            return
        if self.fs_model is None:
            self.fs_model = QtWidgets.QFileSystemModel()
            # hide hidden files to keep manifests invisible in UI browsing
            self.fs_model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)
        self.fs_model.setRootPath(root_path)
        self.fs_view.setModel(self.fs_model)
        self.fs_view.setRootIndex(self.fs_model.index(root_path))

    def detach_fs_view(self):
        if hasattr(self, "fs_view") and self.fs_view:
            self.fs_view.setModel(None)
        self.fs_model = None

    def _enable_vertical_scroll(self, widget):
        # Improve wheel navigation across scrollable widgets.
        if hasattr(widget, "setVerticalScrollMode"):
            try:
                widget.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            except Exception:
                pass
        if hasattr(widget, "setHorizontalScrollMode"):
            try:
                widget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerItem)
            except Exception:
                pass
        if hasattr(widget, "setVerticalScrollBarPolicy"):
            widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        if hasattr(widget, "setHorizontalScrollBarPolicy"):
            widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        if hasattr(widget, "viewport"):
            widget.viewport().setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)

    # ---- UI mutation scheduler ----
    def _mark_ui_ready(self):
        self._ui_ready = True
        self.log_debug("STABILITY", {"ui_ready": True})

    def request_ui_mutation(self, reason, func, *args, **kwargs):
        if self._ui_tearing_down or self.teardown_active:
            self.log_debug("STABILITY", {"mutation_dropped": reason, "teardown": True})
            return
        self._ui_mutation_queue.append((reason, func, args, kwargs))
        if not self._ui_mutation_active:
            QtCore.QTimer.singleShot(0, self._process_mutations)

    def _process_mutations(self):
        if self._ui_mutation_active or self._ui_tearing_down:
            return
        if not self._ui_mutation_queue:
            return
        if QtCore.QThread.currentThread() != self.thread():
            QtCore.QTimer.singleShot(0, self._process_mutations)
            return
        if not self._ui_ready:
            QtCore.QTimer.singleShot(0, self._process_mutations)
            return
        reason, func, args, kwargs = self._ui_mutation_queue.popleft()
        self._ui_mutation_active = True
        try:
            func(*args, **kwargs)
            self.log_debug("STABILITY", {"mutation_executed": reason})
        except Exception as exc:  # noqa: BLE001
            self.log_debug("STABILITY", {"mutation_failed": reason, "error": str(exc)})
        finally:
            self._ui_mutation_active = False
            if self._ui_mutation_queue:
                QtCore.QTimer.singleShot(0, self._process_mutations)

    # ---- Safe UI mutation helpers ----
    def _set_checked_safely(self, widget, value):
        if not widget or not self._ui_alive(widget):
            return
        try:
            blocker = QtCore.QSignalBlocker(widget)
            widget.setChecked(bool(value))
            del blocker
            if self.debug_level == "diagnostic":
                self.log_debug("STABILITY", {"signal_block": widget.objectName() or repr(widget), "checked": bool(value)})
        except Exception:
            pass

    def _set_enabled_safely(self, widget, value):
        if not widget or not self._ui_alive(widget):
            return
        try:
            blocker = QtCore.QSignalBlocker(widget)
            widget.setEnabled(bool(value))
            del blocker
            if self.debug_level == "diagnostic":
                self.log_debug("STABILITY", {"signal_block": widget.objectName() or repr(widget), "enabled": bool(value)})
        except Exception:
            pass

    def _set_text_safely(self, widget, text):
        if not widget or not self._ui_alive(widget):
            return
        try:
            blocker = QtCore.QSignalBlocker(widget)
            widget.setText(text)
            del blocker
            if self.debug_level == "diagnostic":
                self.log_debug("STABILITY", {"signal_block": widget.objectName() or repr(widget), "text": text})
        except Exception:
            pass
    def _on_splitter_moved(self, key, splitter, *args):
        if not self._ui_alive(splitter):
            self.log_debug("STABILITY", {"dropped_splitter": key})
            return
        try:
            self.save_splitter_state(key, splitter.sizes())
        except Exception:
            pass

    def _normalize_task_table_columns(self):
        try:
            header = self.task_table.horizontalHeader()
            widths = [320, 140, 90, 120, 180, 180]
            for idx, w in enumerate(widths):
                header.resizeSection(idx, w)
        except Exception:
            pass

    # ---- Debug window helpers ----
    def log_debug(self, scope, data):
        scope = scope.upper()
        timestamp = now_str()
        self.debug_history.append((scope, data, timestamp))
        if len(self.debug_history) > 1500:
            self.debug_history = self.debug_history[-1500:]
        if self.debug_window:
            self.debug_window.append_entry(scope, data, timestamp)
        # route stability/self-healing into same pipeline for single-source-of-truth
        if scope == "STABILITY" and self.debug_level == "diagnostic":
            try:
                # Persist a diagnostic snapshot for later inspection
                diag_log = DATA_DIR / "stability_diagnostic.log"
                diag_log.parent.mkdir(parents=True, exist_ok=True)
                with open(diag_log, "a", encoding="utf-8") as fh:
                    fh.write(f"[{timestamp}] {json.dumps(data)}\n")
            except Exception:
                pass
        try:
            self.event_bus.emit(scope, {"data": data, "ts": timestamp})
        except Exception:
            pass

    def _stability_event(self, scope, data):
        # Route stability/self-healing events through the unified debug system.
        if self.debug_level == "normal" and scope not in {"failure", "correction_failure"}:
            # keep normal mode quiet unless something failed
            return
        payload = {"scope": scope, **(data if isinstance(data, dict) else {"data": data})}
        self.log_debug("STABILITY", payload)
        # persist a bounded history for later inspection
        self.settings.setdefault("stability_history", [])
        hist = self.settings["stability_history"]
        hist.append({"ts": now_str(), **payload})
        self.settings["stability_history"] = hist[-200:]
        self.save_settings()

    def _on_collapsible_toggle(self, key, collapsed):
        if not self._ui_alive(self):
            return
        self.set_collapsible_state(key, collapsed)

    def toggle_debug_window(self):
        if self.debug_window and self.debug_window.isVisible():
            self.debug_window.close()
            self.debug_window = None
            self.debug_window_btn.setChecked(False)
            return
        self.debug_window = DebugWindow(self.debug_scopes)
        self.debug_window.closed.connect(self._on_debug_window_closed)
        self.debug_window.append_history(self.debug_history)
        self.debug_window.show()
        self.debug_window.raise_()
        self.debug_window.activateWindow()
        self.debug_window_btn.setChecked(True)
        self.log_debug("APPLICATION", {"debug_window": "opened"})

    def create_project_task_list(self):
        proj = self.get_selected_project()
        if not proj:
            QtWidgets.QMessageBox.warning(self, "No Project", "Select a project to create a task list for.")
            return
        self.request_ui_mutation("create_project_task_list", self._create_project_task_list_safe, proj)

    def _create_project_task_list_safe(self, proj):
        if not self._ui_alive(self.list_tree):
            return
        name = proj
        existing = self.store.lists(scope="project", project=proj)
        for lst in existing:
            if lst.get("name") == name:
                QtWidgets.QMessageBox.information(self, "Exists", f"Task list '{name}' already exists for project {proj}.")
                return
        self.store._get_or_create_list(name, scope="project", project=proj)
        self.populate_lists()
        root = self.list_tree.topLevelItem(2)  # project root
        if root:
            root.setExpanded(True)
            for i in range(root.childCount()):
                proj_node = root.child(i)
                if proj_node.text(0) == proj:
                    proj_node.setExpanded(True)
                    for j in range(proj_node.childCount()):
                        child = proj_node.child(j)
                        if child.text(0) == name:
                            self.list_tree.setCurrentItem(child)
                            self.on_list_selection()
                            break
        self.set_state("Idle", f"Created task list '{name}' for project {proj}")

    def _on_debug_window_closed(self):
        self.debug_window = None
        if hasattr(self, "debug_window_btn"):
            self.debug_window_btn.setChecked(False)

    # ---- Operation lifecycle and audit ----
    def start_operation(self, name, target=None, dry_run=False):
        self.operation_ctx = {"state": "preparing", "name": name, "target": target, "dry_run": dry_run}
        self.set_state("Loading", f"{name} preparing...")
        self.log_audit(name, target, "start", dry_run=dry_run)
        self.log_debug("APPLICATION", {"operation": name, "target": target, "state": "start", "dry_run": dry_run})

    def set_operation_state(self, state):
        if not self.operation_ctx:
            return
        self.operation_ctx["state"] = state
        if state == "executing":
            self.operation_progress.setStyleSheet(
                f"QProgressBar::chunk{{background-color:{getattr(self,'accent_primary',ACCENTS['sunset']['primary'])};}}"
                f"QProgressBar{{border:1px solid {getattr(self,'accent_glow',ACCENTS['sunset']['glow'])}; border-radius:4px; text-align:center;}}"
            )

    def finalize_operation(self, outcome):
        # outcome: committed / rolled_back / failed
        if not self.operation_ctx:
            return
        self.operation_ctx["state"] = outcome
        self.log_audit(self.operation_ctx.get("name"), self.operation_ctx.get("target"), outcome, dry_run=self.operation_ctx.get("dry_run"))
        self.operation_ctx = {"state": "idle", "name": None, "target": None, "dry_run": False}
        self.log_debug("APPLICATION", {"operation": "finalize", "outcome": outcome})

    def log_audit(self, op_type, target, outcome, dry_run=False):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            stamp = now_str()
            tgt = target or "-"
            suffix = " dry-run" if dry_run else ""
            with open(AUDIT_LOG, "a", encoding="utf-8") as fh:
                fh.write(f"[{stamp}] {op_type} project={tgt} {outcome}{suffix}\n")
        except Exception:
            pass

    # ---- Manifest helpers ----
    def manifest_path(self, project):
        return os.path.join(PROJECT_ROOT, project, PROJECT_MANIFEST)

    def load_manifest(self, project):
        path = self.manifest_path(project)
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
        except Exception:
            return {}
        return {}

    def write_manifest(self, project, data):
        path = self.manifest_path(project)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            os.chmod(path, 0o600)
        except Exception:
            pass

    def ensure_manifest(self, project, origin="Local", origin_path=None):
        existing = self.load_manifest(project)
        manifest = existing if isinstance(existing, dict) else {}
        if "project_id" not in manifest:
            manifest["project_id"] = str(uuid.uuid4())
        manifest.setdefault("project_name", project)
        manifest["origin"] = origin
        manifest["origin_path"] = origin_path
        manifest.setdefault("creation_timestamp", now_str())
        manifest.setdefault("preferred_credentials", self.selected_cred_label)
        meta_entry = self.project_meta.get(project, {})
        manifest["auto_commit_enabled"] = bool(meta_entry.get("auto_commit", False))
        manifest["localsync_enabled"] = bool(meta_entry.get("localsync", False))
        manifest["localsync_path"] = meta_entry.get("localsync_path")
        manifest.setdefault("redacted", False)
        manifest.setdefault("tags", [])
        self.write_manifest(project, manifest)

    def update_manifest_fields(self, project, **fields):
        manifest = self.load_manifest(project)
        if not isinstance(manifest, dict):
            manifest = {}
        manifest.setdefault("project_id", str(uuid.uuid4()))
        manifest.setdefault("project_name", project)
        manifest.update(fields)
        self.write_manifest(project, manifest)

    # ---- System health ----
    def refresh_health_panel(self, github_status=None):
        focus_state = "Unknown"
        active = "Unknown"
        if self.active_project:
            focus_state = "Focused"
            active = self.active_project
        elif self.get_marker_project():
            focus_state = "Marker only"
            active = self.get_marker_project()
        else:
            focus_state = "Unfocused"
            active = "None"
        if USE_BIND_MOUNT:
            mount_state = "mounted" if os.path.ismount(ACTIVE_PROJECT_PATH) else "unmounted"
        else:
            mount_state = "direct" if self.active_project else "inactive"
        cred_state = "Unknown"
        if self.credentials_verified:
            cred_state = f"Verified ({self.verified_user or 'user'})"
        elif self.credentials_store.get("sets"):
            cred_state = "Loaded, unverified"
        else:
            cred_state = "Missing"
        autogit_state = "Unavailable"
        if self.autogit.available():
            autogit_state = "Idle"
            if self.active_project:
                meta = self.project_meta.get(self.active_project, {})
                if meta.get("auto_commit"):
                    autogit_state = "Watching"
        github_state = github_status if github_status else ("Reachable" if self.github_reachable else ("Unknown" if self.github_reachable is None else "Unreachable"))
        if hasattr(self, "health_focus_label"):
            self.health_focus_label.setText(f"Focus: {focus_state}")
        if hasattr(self, "health_active_label"):
            self.health_active_label.setText(f"Active: {active}")
        if hasattr(self, "health_mount_label"):
            self.health_mount_label.setText(f"Mount: {mount_state}")
        if hasattr(self, "health_auto_cd_label"):
            self.health_auto_cd_label.setText("Terminal Auto-Focus: ENABLED" if os.path.exists(FOCUS_MARKER) else "Terminal Auto-Focus: DISABLED")
        if hasattr(self, "health_cred_label"):
            self.health_cred_label.setText(f"Credentials: {cred_state}")
        if hasattr(self, "health_autogit_label"):
            self.health_autogit_label.setText(f"AutoGIT: {autogit_state}")
        if hasattr(self, "health_github_label"):
            self.health_github_label.setText(f"GitHub: {github_state}")

    def check_github_connectivity(self):
        def work():
            try:
                req = urllib.request.Request("https://api.github.com", method="HEAD")
                urllib.request.urlopen(req, timeout=5)
                return True
            except Exception:
                return False

        def on_result(ok):
            self.github_reachable = ok
            self.refresh_health_panel("Reachable" if ok else "Unreachable")

        self.run_in_background(work, on_result)

    def last_commit_hash(self, path):
        try:
            env = self.git_env()
            res = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True, env=env)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            return None
        return None
    def _register_layout(self, layout):
        # Track layouts so we can rescale spacing/margins when UI scale changes.
        self.scalable_layouts.append(layout)
        if not hasattr(self, "wrap_layouts"):
            self.wrap_layouts = []
        if isinstance(layout, WrapLayout):
            self.wrap_layouts.append(layout)
        if isinstance(layout, QtWidgets.QBoxLayout) and not isinstance(layout, WrapLayout):
            self.responsive_layouts.append(layout)
            self.responsive_base_dir[layout] = layout.direction()
        try:
            margins = layout.getContentsMargins()
            self.layout_margins[layout] = margins
        except Exception:
            self.layout_margins[layout] = (0, 0, 0, 0)
        return layout

    # ---- Settings builders ----
    def _build_settings_section(self, title, content_widget):
        if content_widget is None:
            content_widget = QtWidgets.QWidget()
        default_expanded = not self.get_collapsible_state(f"settings.{title.lower()}", False)
        pane = CollapsiblePane(
            title,
            content_widget,
            collapsed=not default_expanded,
            on_toggle=partial(self._on_collapsible_toggle, f"settings.{title.lower()}"),
        )
        self.register_pane_context(pane, f"settings.{title.lower()}")
        return pane

    def _build_photon_side_panel(self, tabs=None):
        panel = QtWidgets.QFrame()
        panel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        panel_layout = self._register_layout(QtWidgets.QVBoxLayout(panel))
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)
        entry_btn = QtWidgets.QPushButton("⦿")
        entry_btn.setCheckable(True)
        entry_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        entry_btn.setToolTip("Enter the PHØTØN terminal")
        entry_btn.clicked.connect(self._enter_photon_interface)
        # Tuck the PHØTØN toggle into the tab bar corner to avoid vertical whitespace.
        corner_box = QtWidgets.QFrame()
        corner_box.setObjectName("photonCornerBox")
        corner_box.setStyleSheet(
            "#photonCornerBox {"
            "border: 1px solid #2b3854; border-radius: 8px; background-color: #0a1322; padding: 2px;"
            "}"
        )
        corner_layout = QtWidgets.QHBoxLayout(corner_box)
        corner_layout.setContentsMargins(4, 4, 4, 4)
        corner_layout.setSpacing(4)
        entry_btn.setFixedSize(36, 36)
        icon_font = QtGui.QFont("JetBrains Mono")
        icon_font.setPointSize(14)
        entry_btn.setFont(icon_font)
        corner_layout.addWidget(entry_btn)
        if tabs is not None:
            tabs.setCornerWidget(corner_box, QtCore.Qt.TopRightCorner)
        else:
            panel_layout.addWidget(corner_box, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.photon_entry_btn = entry_btn
        entry_effect = QtWidgets.QGraphicsDropShadowEffect()
        entry_effect.setOffset(0, 0)
        entry_effect.setColor(QtGui.QColor(self.accent_glow))
        entry_effect.setBlurRadius(18)
        entry_btn.setGraphicsEffect(entry_effect)
        self._photon_entry_effect = entry_effect
        pulse_anim = QtCore.QPropertyAnimation(entry_effect, b"blurRadius")
        pulse_anim.setStartValue(14)
        pulse_anim.setEndValue(28)
        pulse_anim.setDuration(1400)
        pulse_anim.setLoopCount(-1)
        pulse_anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        pulse_anim.start()
        self._photon_entry_pulse = pulse_anim
        container = QtWidgets.QFrame()
        container.setFrameShape(QtWidgets.QFrame.NoFrame)
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        container_layout = self._register_layout(QtWidgets.QVBoxLayout(container))
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        terminal = PhotonTerminalWidget(
            self.sound_engine,
            self.accent_primary,
            self.accent_glow,
            parent=container,
            base_env=self.supervisor.subprocess_env(),
        )
        terminal.back_requested.connect(self._return_to_singularity_interface)
        container_layout.addWidget(terminal)
        container.setVisible(False)
        panel_layout.addWidget(container)
        panel_layout.addStretch(1)
        self.photon_panel_container = container
        self.photon_terminal_widget = terminal
        return panel

    def log_vcs(self, msg):
        # Non-sensitive logging to versioning output pane
        if hasattr(self, "vcs_output"):
            self.vcs_output.appendPlainText(msg)

    def _build_user_section(self):
        import pwd, grp
        user_info = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(user_info)
        try:
            pw = pwd.getpwuid(os.getuid())
            username = pw.pw_name
            home = pw.pw_dir
            shell = pw.pw_shell
            gid = pw.pw_gid
        except Exception:
            username = getpass.getuser()
            home = str(Path.home())
            shell = os.environ.get("SHELL", "")
            gid = os.getgid()
        uid = os.getuid()
        groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem] if 'grp' in locals() else []
        primary_group = grp.getgrgid(gid).gr_name if 'grp' in locals() else str(gid)
        if primary_group not in groups:
            groups.append(primary_group)
        level = "admin" if ("sudo" in groups or uid == 0) else "standard"
        layout.addRow("Username", QtWidgets.QLabel(username))
        layout.addRow("UID / GID", QtWidgets.QLabel(f"{uid} / {gid}"))
        layout.addRow("Home", QtWidgets.QLabel(home))
        layout.addRow("Shell", QtWidgets.QLabel(shell))
        layout.addRow("Groups", QtWidgets.QLabel(", ".join(sorted(groups))))
        layout.addRow("Access Level", QtWidgets.QLabel(level))
        return user_info

    def _build_accessibility_section(self):
        container = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(container)
        version_box = QtWidgets.QGroupBox("Versioning")
        version_layout = QtWidgets.QVBoxLayout(version_box)
        creds_box = QtWidgets.QGroupBox("Credentials")
        creds_layout = QtWidgets.QFormLayout(creds_box)
        self.cred_label = QtWidgets.QLineEdit()
        self.cred_label.setPlaceholderText("Credential label (e.g., username or alias)")
        self.cred_username = QtWidgets.QLineEdit()
        self.cred_password = QtWidgets.QLineEdit()
        self.cred_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.token_input = QtWidgets.QLineEdit()
        self.token_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.token_list = QtWidgets.QListWidget()
        self.token_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        add_token_btn = QtWidgets.QPushButton("+")
        self.token_show_btn = QtWidgets.QPushButton("👁")
        self.token_show_btn.setCheckable(True)
        def add_token():
            token = self.token_input.text().strip()
            if token:
                # store tokens only in memory, not persisted, to avoid plaintext storage
                item = QtWidgets.QListWidgetItem("•••••• (token)")
                item.setData(QtCore.Qt.UserRole, False)
                self.token_list.addItem(item)
                if not hasattr(self, "api_tokens"):
                    self.api_tokens = []
                self.api_tokens.append(token)
                self.active_credentials["tokens"] = self.api_tokens
                self.token_input.clear()
                if self.selected_cred_label:
                    self.credentials_store.setdefault("sets", {})
                    self.credentials_store["sets"].setdefault(self.selected_cred_label, {})
                    self.credentials_store["sets"][self.selected_cred_label]["tokens"] = self.api_tokens
                self.save_credentials()
        add_token_btn.clicked.connect(add_token)
        def toggle_token_visibility():
            if self.token_show_btn.isChecked():
                self.token_input.setEchoMode(QtWidgets.QLineEdit.Normal)
                self.token_show_btn.setText("🙈")
                self.token_input.setStyleSheet("color: #d2a446;")
            else:
                self.token_input.setEchoMode(QtWidgets.QLineEdit.Password)
                self.token_show_btn.setText("👁")
                self.token_input.setStyleSheet("")
        self.token_show_btn.clicked.connect(toggle_token_visibility)
        token_row = QtWidgets.QHBoxLayout()
        token_row.addWidget(self.token_input)
        token_row.addWidget(add_token_btn)
        token_row.addWidget(self.token_show_btn)
        self.save_creds_btn = QtWidgets.QPushButton("Save Credentials")
        self.save_creds_btn.setToolTip("Persist the current credential set securely.")
        self.save_creds_btn.clicked.connect(self.save_current_credentials)
        self.cred_set_combo = QtWidgets.QComboBox()
        self.cred_set_combo.currentTextChanged.connect(self.switch_credential_set)
        creds_layout.addRow("GitHub Username", self.cred_username)
        creds_layout.addRow("GitHub Password", self.cred_password)
        creds_layout.addRow("API Access Token", token_row)
        token_list_row = QtWidgets.QHBoxLayout()
        self.toggle_selected_token_btn = QtWidgets.QPushButton("Show/Hide Selected Token")
        self.toggle_selected_token_btn.clicked.connect(self.toggle_selected_token_visibility)
        self.toggle_selected_token_btn.setToolTip("Toggle visibility for the selected saved token (session only).")
        token_list_row.addWidget(self.token_list)
        token_list_row.addWidget(self.toggle_selected_token_btn)
        creds_layout.addRow("Credential Label", self.cred_label)
        creds_layout.addRow("Select Credential Set", self.cred_set_combo)
        creds_layout.addRow("Tokens", token_list_row)
        self.verify_creds_btn = QtWidgets.QPushButton("Verify Credentials")
        self.verify_status_label = QtWidgets.QLabel("")
        creds_layout.addRow(self.verify_creds_btn, self.verify_status_label)
        version_layout.addWidget(creds_box)
        version_layout.addWidget(self.save_creds_btn)
        creds_display_box = QtWidgets.QGroupBox("Saved Credentials")
        creds_display_layout = QtWidgets.QVBoxLayout(creds_display_box)
        self.active_cred_label = QtWidgets.QLabel("Active: None")
        self.saved_creds_list = QtWidgets.QListWidget()
        self.saved_creds_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        creds_display_layout.addWidget(self.active_cred_label)
        creds_display_layout.addWidget(self.saved_creds_list)
        version_layout.addWidget(creds_display_box)
        self.verify_creds_btn.clicked.connect(self.verify_credentials)
        v.addWidget(version_box)
        v.addStretch(1)
        # Initialize credential status visibility
        if self.credentials_verified:
            user = self.verified_user or self.active_credentials.get("username", "")
            self.verify_status_label.setText(f"Using stored credentials{(' as ' + user) if user else ''}")
            self.verify_status_label.setStyleSheet("color: #2e9b8f;")
        elif self.credentials_store.get("sets"):
            self.verify_status_label.setText("Credentials loaded, not verified")
            self.verify_status_label.setStyleSheet("color: #d2a446;")
        else:
            self.verify_status_label.setText("Credentials missing – versioning disabled")
            self.verify_status_label.setStyleSheet("color: #d14b4b;")
        return container

    def _build_interface_section(self):
        container = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(container)
        theme_box = QtWidgets.QGroupBox("Theme")
        theme_layout = QtWidgets.QFormLayout(theme_box)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["dark", "darker", "contrast"])
        self.accent_combo = QtWidgets.QComboBox()
        self.accent_combo.addItems(["cyan", "purple", "teal", "sunset"])
        self.anim_checkbox = QtWidgets.QCheckBox("Enable animations")
        self.anim_checkbox.setChecked(self.settings.get("interface", {}).get("animations", True))
        self.verbosity_checkbox = QtWidgets.QCheckBox("Verbose status")
        self.verbosity_checkbox.setChecked(self.settings.get("interface", {}).get("verbosity", True))
        self.audio_checkbox = QtWidgets.QCheckBox("Audio Feedback (PHØTØN)")
        self.audio_checkbox.setChecked(self.settings.get("interface", {}).get("audio_feedback", True))
        self.density_combo = QtWidgets.QComboBox()
        self.density_combo.addItems(["compact", "normal", "spacious"])
        self.ui_scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.ui_scale_slider.setMinimum(60)
        self.ui_scale_slider.setMaximum(400)
        self.ui_scale_slider.setSingleStep(10)
        self.ui_scale_slider.setTickInterval(20)
        self.ui_scale_slider.setValue(int(self.ui_scale))
        self.ui_scale_value = QtWidgets.QLabel(f"{int(self.ui_scale)}%")
        ui_scale_row = QtWidgets.QHBoxLayout()
        ui_scale_row.addWidget(self.ui_scale_slider)
        ui_scale_row.addWidget(self.ui_scale_value)
        ui_scale_helper = QtWidgets.QLabel("UI Element Scale (window size unaffected)")
        ui_scale_helper.setToolTip("Scales interface fonts, padding, icons, and spacing only. The window size/geometry is not changed.")
        theme_layout.addRow("Theme", self.theme_combo)
        theme_layout.addRow("Accent", self.accent_combo)
        theme_layout.addRow("Animations", self.anim_checkbox)
        theme_layout.addRow("Audio FX", self.audio_checkbox)
        theme_layout.addRow("Status Verbosity", self.verbosity_checkbox)
        theme_layout.addRow("Pane Density", self.density_combo)
        theme_layout.addRow(ui_scale_helper, ui_scale_row)
        v.addWidget(theme_box)
        v.addStretch(1)
        self.theme_combo.currentTextChanged.connect(self.apply_interface_settings)
        self.accent_combo.currentTextChanged.connect(self.apply_interface_settings)
        self.anim_checkbox.stateChanged.connect(self.apply_interface_settings)
        self.audio_checkbox.stateChanged.connect(self.apply_interface_settings)
        self.verbosity_checkbox.stateChanged.connect(self.apply_interface_settings)
        self.density_combo.currentTextChanged.connect(self.apply_interface_settings)
        self.ui_scale_slider.valueChanged.connect(self.on_ui_scale_changed)
        return container

    def _build_controls_section(self):
        container = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(container)
        form = QtWidgets.QFormLayout()
        self.key_edit_focus = QtWidgets.QKeySequenceEdit(QtGui.QKeySequence(self.keybinds["focus_project"]))
        self.key_edit_new_task = QtWidgets.QKeySequenceEdit(QtGui.QKeySequence(self.keybinds["new_task"]))
        self.key_edit_complete = QtWidgets.QKeySequenceEdit(QtGui.QKeySequence(self.keybinds["complete_task"]))
        self.key_edit_commit = QtWidgets.QKeySequenceEdit(QtGui.QKeySequence(self.keybinds["commit"]))
        self.key_edit_tab_prev = QtWidgets.QKeySequenceEdit(QtGui.QKeySequence(self.keybinds.get("tab_prev", "Ctrl+Left")))
        self.key_edit_tab_next = QtWidgets.QKeySequenceEdit(QtGui.QKeySequence(self.keybinds.get("tab_next", "Ctrl+Right")))
        self.key_warning = QtWidgets.QLabel("")
        self.key_warning.setStyleSheet("color: #d14b4b;")
        form.addRow("Focus/Unfocus", self.key_edit_focus)
        form.addRow("New Task", self.key_edit_new_task)
        form.addRow("Complete Task", self.key_edit_complete)
        form.addRow("Commit", self.key_edit_commit)
        form.addRow("Previous Tab", self.key_edit_tab_prev)
        form.addRow("Next Tab", self.key_edit_tab_next)
        # AI toggle and Gemini key
        ai_group = QtWidgets.QGroupBox("AI / Gemini")
        ai_form = QtWidgets.QFormLayout(ai_group)
        self.ai_toggle = QtWidgets.QCheckBox("Enable AI Functionality")
        self.ai_toggle.setChecked(bool(self.ai_enabled))
        self.ai_toggle.stateChanged.connect(self._on_ai_toggle_changed)
        self.gemini_api_key_edit = QtWidgets.QLineEdit()
        self.gemini_api_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.gemini_api_key_edit.setText(self.gemini_api_key)
        self.gemini_email_edit = QtWidgets.QLineEdit()
        self.gemini_email_edit.setPlaceholderText("email@example.com")
        self.gemini_email_edit.setText(self.gemini_email)
        self.gemini_password_edit = QtWidgets.QLineEdit()
        self.gemini_password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.gemini_password_edit.setText(self.gemini_password)
        self.verify_gemini_btn = QtWidgets.QPushButton("Verify Gemini")
        self.verify_gemini_btn.clicked.connect(self.verify_gemini_credentials_ui)
        ai_form.addRow(self.ai_toggle)
        ai_form.addRow("Gemini API Key", self.gemini_api_key_edit)
        ai_form.addRow("Gemini Email", self.gemini_email_edit)
        ai_form.addRow("Gemini Password", self.gemini_password_edit)
        ai_form.addRow(self.verify_gemini_btn)
        v.addWidget(ai_group)
        v.addLayout(form)
        v.addWidget(self.key_warning)
        # apply on change
        self.key_edit_focus.editingFinished.connect(self.apply_keybinds)
        self.key_edit_new_task.editingFinished.connect(self.apply_keybinds)
        self.key_edit_complete.editingFinished.connect(self.apply_keybinds)
        self.key_edit_commit.editingFinished.connect(self.apply_keybinds)
        self.key_edit_tab_prev.editingFinished.connect(self.apply_keybinds)
        self.key_edit_tab_next.editingFinished.connect(self.apply_keybinds)
        self.gemini_api_key_edit.editingFinished.connect(self._on_gemini_key_changed)
        self.gemini_email_edit.editingFinished.connect(self._on_gemini_email_changed)
        self.gemini_password_edit.editingFinished.connect(self._on_gemini_password_changed)
        v.addStretch(1)
        return container

    def _wire_events(self):
        self.focus_btn.clicked.connect(self.focus_selected)
        self.unfocus_btn.clicked.connect(self.unfocus_current)
        self.refresh_btn.clicked.connect(self.refresh_projects)
        self.create_btn.clicked.connect(self.create_project)
        self.rename_btn.clicked.connect(self.rename_project)
        self.generate_todo_btn.clicked.connect(self.generate_todo_from_prompt)
        self.summarize_btn.clicked.connect(self.summarize_project)
        self.project_tasks_btn.clicked.connect(self.create_project_task_list)
        self.import_project_btn.clicked.connect(self.import_existing_folder)
        self.delete_project_btn.clicked.connect(self.delete_project)
        self.project_table.itemSelectionChanged.connect(self._on_project_selection)
        self.list_tree.itemSelectionChanged.connect(self.on_list_selection)
        self.task_table.itemSelectionChanged.connect(self.on_task_selection)
        self.new_list_btn.clicked.connect(self.create_list)
        self.rename_list_btn.clicked.connect(self.rename_list)
        self.new_task_btn.clicked.connect(self.add_task_dialog)
        self.save_task_btn.clicked.connect(self.save_task_details)
        self.complete_task_btn.clicked.connect(self.toggle_complete_selected)
        self.my_day_btn.clicked.connect(self.add_selected_to_my_day)
        self.priority_btn.clicked.connect(self.toggle_priority_selected)
        self.delete_task_btn.clicked.connect(self.delete_selected_task)
        self.move_up_btn.clicked.connect(self._on_move_task_up)
        self.move_down_btn.clicked.connect(self._on_move_task_down)
        self.tasks_import_btn.clicked.connect(self.import_tasks)
        self.tasks_export_btn.clicked.connect(self.export_tasks)
        self.autogit_status_btn.clicked.connect(self.autogit_status)
        self.autogit_init_btn.clicked.connect(self.autogit_init)
        self.autogit_commit_btn.clicked.connect(self.autogit_commit)
        self.auto_commit_toggle.clicked.connect(self.toggle_auto_commit)
        self.auto_commit_global_btn.clicked.connect(self.toggle_auto_commit)
        self.fetch_versions_btn.clicked.connect(self.fetch_versions)
        self.revert_version_btn.clicked.connect(self.revert_version)
        self.version_list.itemSelectionChanged.connect(self._on_version_selection_changed)
        self.redact_btn.clicked.connect(lambda: self._on_redaction_toggle(True))
        self.unredact_btn.clicked.connect(lambda: self._on_redaction_toggle(False))
        self.debug_window_btn.clicked.connect(self.toggle_debug_window)

    def _setup_shortcuts(self):
        # build shortcuts from configurable keybinds
        self.shortcuts = {
            "new_task": QtWidgets.QShortcut(QtGui.QKeySequence(self.keybinds["new_task"]), self, activated=self.add_task_dialog),
            "complete_task": QtWidgets.QShortcut(QtGui.QKeySequence(self.keybinds["complete_task"]), self, activated=self.toggle_complete_selected),
            "focus_project": QtWidgets.QShortcut(QtGui.QKeySequence(self.keybinds["focus_project"]), self, activated=self.focus_selected),
            "commit": QtWidgets.QShortcut(QtGui.QKeySequence(self.keybinds["commit"]), self, activated=self.autogit_commit),
            "tab_prev": QtWidgets.QShortcut(QtGui.QKeySequence(self.keybinds.get("tab_prev", "Ctrl+Left")), self, activated=self._switch_tab_prev),
            "tab_next": QtWidgets.QShortcut(QtGui.QKeySequence(self.keybinds.get("tab_next", "Ctrl+Right")), self, activated=self._switch_tab_next),
            "command_palette": QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+K"), self, activated=lambda: self.command_palette.open_for_payload(self._current_context_payload())),
        }
        # arrow keys within Tasks pane to move focus across the three panes
        self.shortcuts["tasks_left"] = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Left), self, activated=self._focus_tasks_left, context=QtCore.Qt.ApplicationShortcut)
        self.shortcuts["tasks_right"] = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Right), self, activated=self._focus_tasks_right, context=QtCore.Qt.ApplicationShortcut)
        self.shortcuts["tasks_up"] = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Up), self, activated=self._focus_tasks_up, context=QtCore.Qt.WidgetWithChildrenShortcut)
        self.shortcuts["tasks_down"] = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Down), self, activated=self._focus_tasks_down, context=QtCore.Qt.WidgetWithChildrenShortcut)

    def _switch_tab_prev(self):
        tabs = getattr(self, "tab_widget", None) or self.centralWidget().findChild(QtWidgets.QTabWidget)
        if not tabs:
            return
        current = tabs.currentIndex()
        count = tabs.count()
        tabs.setCurrentIndex((current - 1) % count)

    def _switch_tab_next(self):
        tabs = getattr(self, "tab_widget", None) or self.centralWidget().findChild(QtWidgets.QTabWidget)
        if not tabs:
            return
        current = tabs.currentIndex()
        count = tabs.count()
        tabs.setCurrentIndex((current + 1) % count)

    def _focus_tasks_left(self):
        if self.task_table.hasFocus() or self.title_edit.hasFocus():
            self.list_tree.setFocus(QtCore.Qt.TabFocusReason)
        elif self.list_tree.hasFocus():
            self.task_table.setFocus(QtCore.Qt.TabFocusReason)
            self._ensure_task_selected()
        else:
            self.list_tree.setFocus(QtCore.Qt.TabFocusReason)

    def _focus_tasks_right(self):
        if self.list_tree.hasFocus():
            self.task_table.setFocus(QtCore.Qt.TabFocusReason)
            self._ensure_task_selected()
        elif self.task_table.hasFocus():
            self.title_edit.setFocus(QtCore.Qt.TabFocusReason)
        else:
            self.task_table.setFocus(QtCore.Qt.TabFocusReason)
            self._ensure_task_selected()

    def _focus_tasks_up(self):
        if self.task_table.hasFocus():
            self._move_task_selection(-1)

    def _focus_tasks_down(self):
        if self.task_table.hasFocus():
            self._move_task_selection(1)

    def _move_task_selection(self, delta):
        model = self.task_table.model()
        if not model:
            return
        sel = self.task_table.selectionModel()
        if not sel or not sel.hasSelection():
            if self.task_table.rowCount() > 0:
                self.task_table.selectRow(0)
            return
        index = sel.selectedRows()[0]
        row = index.row() + delta
        row = max(0, min(self.task_table.rowCount() - 1, row))
        self.task_table.selectRow(row)
        self._ensure_task_selected()

    def _ensure_task_selected(self):
        sel = self.task_table.selectionModel()
        if not sel or not sel.hasSelection():
            if self.task_table.rowCount() > 0:
                self.task_table.selectRow(0)

    def _show_usage_note(self):
        QtWidgets.QMessageBox.information(
            self,
            "Usage",
            "Select a project and click Focus Selected to work on it directly.\n"
            "Use lists to manage tasks (My Day, Planned, Important, Completed, global/project lists).\n"
            "Shortcuts: Ctrl+N new task, Ctrl+D complete/restore, Ctrl+Shift+F focus project.",
        )

    def refresh_projects(self):
        self.set_state("Loading", "Loading projects...")
        try:
            projects = self.backend.list_projects()
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(self, "Error", f"Project root not found: {PROJECT_ROOT}")
            self.show_error_banner(f"Project root not found: {PROJECT_ROOT}")
            return

        self.active_project = self.get_marker_project()
        names = [p[0] for p in projects]
        self.redaction_state = {k: v for k, v in self.redaction_state.items() if k in names}
        if self.selected_project and self.selected_project not in names:
            self.selected_project = None
        self.project_table.setRowCount(len(projects))
        for row, (name, mtime) in enumerate(projects):
            # ensure manifest exists and capture redaction state
            meta_entry = self.project_meta.get(name, {"origin": "Local", "auto_commit": False, "localsync": False})
            origin_val = meta_entry.get("origin", "Local")
            self.ensure_manifest(name, origin=origin_val, origin_path=meta_entry.get("origin_path"))
            manifest = self.load_manifest(name) or {}
            redacted = bool(manifest.get("redacted", False))
            self.redaction_state[name] = redacted
            display_name = f"{name} [REDACTED]" if redacted else name
            name_item = QtWidgets.QTableWidgetItem(display_name)
            name_item.setData(QtCore.Qt.UserRole, name)
            time_str = self._format_ui_datetime(datetime.fromtimestamp(mtime))
            time_item = QtWidgets.QTableWidgetItem(time_str)
            origin_item = QtWidgets.QTableWidgetItem(origin_val)
            name_item.setFlags(qt_no_edit(name_item.flags()))
            time_item.setFlags(qt_no_edit(time_item.flags()))
            origin_item.setFlags(qt_no_edit(origin_item.flags()))
            if redacted:
                name_item.setForeground(QtGui.QColor("#d14b4b"))
            self.project_table.setItem(row, 0, name_item)
            self.project_table.setItem(row, 1, time_item)

            status_value = self.status_map.get(name, "Pending Review")
            combo = QtWidgets.QComboBox()
            combo.addItems(STATUS_OPTIONS)
            if status_value in STATUS_OPTIONS:
                combo.setCurrentText(status_value)
            combo.currentTextChanged.connect(partial(self._on_status_changed, name))
            self.project_table.setCellWidget(row, 2, combo)
            self.project_table.setItem(row, 3, origin_item)
            localsync_cb = QtWidgets.QCheckBox("LocalSync")
            localsync_cb.setToolTip('syncs Remote project location with data from local system prioritizing the most up to date version')
            localsync_cb.setChecked(bool(meta_entry.get("localsync", False)))
            localsync_cb.stateChanged.connect(partial(self._on_localsync_changed, name, localsync_cb))
            self.ensure_interactable(localsync_cb)
            self.project_table.setCellWidget(row, 4, localsync_cb)
            # show selected localsync path (truncated)
            path_preview = meta_entry.get("localsync_path") or ""
            path_item = QtWidgets.QTableWidgetItem(path_preview if len(path_preview) < 48 else "…" + path_preview[-46:])
            path_item.setFlags(qt_no_edit(path_item.flags()))
            self.project_table.setItem(row, 5, path_item)

            if self.active_project and name == self.active_project:
                name_item.setBackground(QtGui.QColor("#1b2742"))
                time_item.setBackground(QtGui.QColor("#1b2742"))
                origin_item.setBackground(QtGui.QColor("#1b2742"))

        self.update_active_label()
        self.populate_lists()
        self.update_task_controls_enabled()
        self.update_autogit_path_label()
        self.glitch(self.active_label)
        self.set_state("Idle", "")
        sel = self.get_selected_project()
        self.delete_project_btn.setEnabled(bool(sel) and sel != self.active_project)
        self.update_context_labels()
        self.log_debug(
            "FILESYSTEM",
            {
                "project_root": PROJECT_ROOT,
                "projects": len(projects),
            },
        )

    def _set_status(self, project, value):
        self.status_map[project] = value
        self.project_meta.setdefault(project, {})["localsync"] = self.project_meta.get(project, {}).get("localsync", False)
        self.save_project_meta()

    def _run_localsync(self, project):
        project_path = os.path.join(PROJECT_ROOT, project)
        local_path = self.localsync_paths.get(project)
        if not local_path or not os.path.isdir(project_path) or not os.path.isdir(local_path):
            self.log_debug("PROJECTS", {"localsync": "skipped", "project": project, "reason": "path-missing"})
            return
        start = time.monotonic()
        synced_files = 0

        def newer(src, dst):
            return os.path.getmtime(src) > os.path.getmtime(dst)

        for root, dirs, files in os.walk(project_path):
            rel = os.path.relpath(root, project_path)
            target_root = os.path.join(local_path, rel) if rel != "." else local_path
            os.makedirs(target_root, exist_ok=True)
            for fname in files:
                src = os.path.join(root, fname)
                dst = os.path.join(target_root, fname)
                try:
                    if not os.path.exists(dst) or newer(src, dst):
                        shutil.copy2(src, dst)
                        synced_files += 1
                except Exception:
                    continue
        for root, dirs, files in os.walk(local_path):
            rel = os.path.relpath(root, local_path)
            target_root = os.path.join(project_path, rel) if rel != "." else project_path
            os.makedirs(target_root, exist_ok=True)
            for fname in files:
                src = os.path.join(root, fname)
                dst = os.path.join(target_root, fname)
                try:
                    if not os.path.exists(dst) or newer(src, dst):
                        shutil.copy2(src, dst)
                        synced_files += 1
                except Exception:
                    continue
        latency_ms = int((time.monotonic() - start) * 1000)
        self.log_debug("PROJECTS", {"localsync": "completed", "project": project, "files": synced_files, "latency_ms": latency_ms})

    def _on_status_changed(self, project, value):
        if not self._ui_alive(self.project_table):
            return
        self._set_status(project, value)

    def _toggle_localsync(self, project, state, checkbox=None):
        enabled = bool(state)
        # selecting ON requires explicit folder pick
        if enabled:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Local Folder for LocalSync")
            if not path:
                if checkbox:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
                return
            self.localsync_paths[project] = path
        elif project in self.localsync_paths:
            # keep stored path but mark disabled
            pass
        meta = self.project_meta.setdefault(project, {})
        meta["localsync"] = enabled
        if enabled:
            meta["localsync_path"] = self.localsync_paths.get(project)
        self.save_project_meta()
        self.update_manifest_fields(project, localsync_enabled=enabled, localsync_path=self.localsync_paths.get(project))
        if enabled:
            self._run_localsync(project)
        self._record_network_event(
            {
                "protocol": "sync",
                "event": "state",
                "source": project,
                "dest": self.localsync_paths.get(project) if enabled else "localsync-disabled",
                "project": project,
                "latency_ms": 0,
                "throughput": 0.5,
            }
        )
        self.refresh_workspace_views(force=True)
        self.log_debug(
            "PROJECTS",
            {"project": project, "localsync": enabled},
        )
        self.refresh_projects()

    def _on_localsync_changed(self, project, checkbox, state):
        if not self._ui_alive(self.project_table):
            return
        FocusManager._toggle_localsync(self, project, state, checkbox)

    def _on_project_selection(self):
        self.update_autogit_path_label()
        sel = self.get_selected_project()
        self.delete_project_btn.setEnabled(bool(sel) and sel != self.active_project)
        # update focus state visuals based on current marker/backend
        self.active_project = self.get_marker_project()
        self.selected_project = self.get_selected_project()
        self.update_active_label()
        self.update_context_labels()

    def get_selected_project(self):
        selected = self.project_table.selectionModel().selectedRows()
        if not selected:
            return None
        item = self.project_table.item(selected[0].row(), 0)
        if not item:
            return None
        return item.data(QtCore.Qt.UserRole) or item.text()

    def _normalized_tags(self, tags):
        normalized = []
        seen = set()
        for tag in tags or []:
            if not isinstance(tag, str):
                continue
            clean = tag.strip()
            if not clean:
                continue
            key = clean.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(clean)
        return normalized

    def get_project_redaction(self, project):
        if not project:
            return False
        if project in self.redaction_state:
            return self.redaction_state[project]
        manifest = self.load_manifest(project)
        redacted = bool(manifest.get("redacted", False)) if isinstance(manifest, dict) else False
        self.redaction_state[project] = redacted
        return redacted

    def _update_project_row_redaction(self, project, redacted):
        if not hasattr(self, "project_table") or not project:
            return
        for row in range(self.project_table.rowCount()):
            item = self.project_table.item(row, 0)
            if not item:
                continue
            name = item.data(QtCore.Qt.UserRole) or item.text()
            if name == project or item.text().startswith(f"{project} "):
                display_name = f"{project} [REDACTED]" if redacted else project
                item.setText(display_name)
                item.setData(QtCore.Qt.UserRole, project)
                item.setForeground(QtGui.QColor("#d14b4b") if redacted else QtGui.QColor("#d8f6ff"))
                break

    def _update_redaction_badge(self, project, redacted):
        if not hasattr(self, "redaction_badge"):
            return
        if not project:
            self.redaction_badge.setText("No project selected")
            self.redaction_badge.setStyleSheet("color: #d2a446; border: 1px solid #d2a446; border-radius: 6px; padding: 6px 10px;")
            if hasattr(self, "redact_btn"):
                self.redact_btn.setEnabled(False)
                self.unredact_btn.setEnabled(False)
            return
        color = "#d14b4b" if redacted else "#9ce4ff"
        border = color
        bg = "rgba(209,75,75,0.18)" if redacted else "#1f2d4a"
        label = "REDACTED" if redacted else "UNREDACTED"
        self.redaction_badge.setText(f"{label} · {project}")
        self.redaction_badge.setStyleSheet(f"color: {color}; border: 1px solid {border}; border-radius: 6px; padding: 6px 10px; background-color: {bg}; font-weight: bold;")
        if hasattr(self, "redact_btn"):
            enabled = bool(self.selected_project or self.active_project)
            self.redact_btn.setEnabled(enabled)
            self.unredact_btn.setEnabled(enabled)

    def _update_workspace_tag_controls(self, project=None, redacted=None, tags=None):
        if not hasattr(self, "workspace_tags_edit"):
            return
        if not project:
            self.workspace_tags_edit.blockSignals(True)
            self.workspace_tags_edit.setText("")
            self.workspace_tags_edit.setEnabled(False)
            self.workspace_tags_edit.blockSignals(False)
            self.workspace_redacted_tag.blockSignals(True)
            self.workspace_redacted_tag.setChecked(False)
            self.workspace_redacted_tag.setEnabled(False)
            self.workspace_redacted_tag.blockSignals(False)
            return
        manifest = self.load_manifest(project) or {}
        tag_list = tags if tags is not None else manifest.get("tags", [])
        normalized_tags = self._normalized_tags(tag_list)
        if redacted is None:
            redacted = bool(manifest.get("redacted", False))
        self.workspace_tags_edit.blockSignals(True)
        self.workspace_tags_edit.setText(", ".join(normalized_tags))
        self.workspace_tags_edit.setEnabled(True)
        self.workspace_tags_edit.blockSignals(False)
        self.workspace_redacted_tag.blockSignals(True)
        self.workspace_redacted_tag.setChecked(bool(redacted))
        self.workspace_redacted_tag.setEnabled(True)
        self.workspace_redacted_tag.blockSignals(False)

    def set_project_redaction(self, project, redacted, *, tags=None, source="ui"):
        if not project:
            return
        manifest = self.load_manifest(project) or {}
        tag_list = tags if tags is not None else manifest.get("tags", [])
        normalized_tags = self._normalized_tags(tag_list)
        if redacted and all(t.lower() != "redacted" for t in normalized_tags):
            normalized_tags.append("Redacted")
        elif not redacted:
            normalized_tags = [t for t in normalized_tags if t.lower() != "redacted"]
        self.update_manifest_fields(project, tags=normalized_tags, redacted=bool(redacted))
        self.redaction_state[project] = bool(redacted)
        self._update_project_row_redaction(project, bool(redacted))
        self._update_redaction_badge(project, bool(redacted))
        self._update_workspace_tag_controls(project, bool(redacted), normalized_tags)
        if hasattr(self, "project_table"):
            self.project_table.viewport().update()
        self.refresh_health_panel()
        self._sync_repo_visibility(project, bool(redacted))
        self.log_debug(
            "PROJECTS",
            {"project": project, "redacted": bool(redacted), "tags": normalized_tags, "source": source},
        )

    def refresh_redaction_ui(self):
        project = self.selected_project or self.active_project
        redacted = self.get_project_redaction(project) if project else False
        self._update_redaction_badge(project, redacted)
        self._update_workspace_tag_controls(project, redacted)
        self._update_project_row_redaction(project, redacted)

    def _on_redaction_toggle(self, redacted, *args):
        project = self.selected_project or self.active_project
        if not project:
            QtWidgets.QMessageBox.warning(self, "Select Project", "Select a project to change redaction state.")
            return
        self.set_project_redaction(project, redacted, source="version-tab")

    def get_marker_project(self):
        # prefer marker for authoritative focused project path
        if os.path.exists(FOCUS_MARKER):
            try:
                with open(FOCUS_MARKER, "r", encoding="utf-8") as fh:
                    path = fh.readline().strip()
                if path and os.path.isdir(path):
                    self.focus_path = path
                    return os.path.basename(path)
                # stale marker; clean up
                os.remove(FOCUS_MARKER)
            except Exception:
                return None
        self.focus_path = None
        return None

    def update_context_labels(self):
        selected = self.selected_project or "No Project Selected"
        focused = self.active_project or "None"
        self.ui_state["selected_project"] = self.selected_project
        self.ui_state["focused_project"] = self.active_project
        self.ui_state["mount_active"] = os.path.ismount(ACTIVE_PROJECT_PATH) if USE_BIND_MOUNT else bool(self.active_project)
        txt = f"Selected: {selected} | Focused: {focused}"
        accent = getattr(self, "accent_primary", ACCENTS["sunset"]["primary"])
        glow = getattr(self, "accent_glow", ACCENTS["sunset"]["glow"])
        styled_txt = txt.replace(selected, f"<span style='color:{accent};font-weight:bold'>{selected}</span>") if self.selected_project else txt
        styled_txt = styled_txt.replace(focused, f"<span style='color:{accent};font-weight:bold'>{focused}</span>") if self.active_project else styled_txt
        self.global_project_label.setText(styled_txt)
        self.global_project_label.setTextFormat(QtCore.Qt.RichText)
        self.project_context_label.setText(styled_txt)
        self.project_context_label.setTextFormat(QtCore.Qt.RichText)
        self.tasks_context_label.setText(styled_txt)
        self.tasks_context_label.setTextFormat(QtCore.Qt.RichText)
        self.version_context_label.setText(styled_txt)
        self.version_context_label.setTextFormat(QtCore.Qt.RichText)
        self.autogit_path_label.setText(f"Target: {selected}")
        self.settings_context_label.setText(txt)
        self.update_auto_commit_toggle_state()
        self.fetch_versions_btn.setEnabled(bool(self.selected_project))
        self.revert_version_btn.setEnabled(bool(self.selected_project) and self.version_list.currentItem() is not None)
        self.refresh_redaction_ui()
        self.refresh_workspace_views()
        self.refresh_health_panel()
        self.log_debug(
            "PROJECTS",
            {
                "selected_project": self.selected_project,
                "focused_project": self.active_project,
                "origin": self.project_meta.get(self.selected_project, {}).get("origin") if self.selected_project else None,
            },
        )
        self.log_debug(
            "FOCUS_STATE",
            {
                "focused": bool(self.active_project),
                "focus_file": FOCUS_MARKER,
                "resolved_path": self.focus_path,
            },
        )
        self._update_runtime_strip()

    def resolve_project_path(self, require_focus_or_selection=True, prefer_canonical=False):
        proj = self.active_project or self.get_selected_project()
        if proj:
            return os.path.join(PROJECT_ROOT, proj), proj
        if require_focus_or_selection:
            QtWidgets.QMessageBox.warning(
                self,
                "Select Project",
                "Focus a project or select one to use AutoGIT.",
            )
        return None, None

    # ---- Workspaces ----
    def refresh_workspace_views(self, force=False):
        if not hasattr(self, "workspace_stack"):
            return
        path, proj = self.resolve_project_path(require_focus_or_selection=False, prefer_canonical=True)
        if not path or not os.path.isdir(path):
            self.workspace_root_path = None
            if self.workspace_list_view:
                self.workspace_list_view.setModel(None)
            if self.workspace_graph:
                self.workspace_graph.clear()
            self.workspace_selected_meta = None
            self._update_workspace_inspector(None)
            self._update_workspace_tag_controls(None)
            return
        root_changed = force or path != self.workspace_root_path or self.workspace_fs_model is None
        self.workspace_root_path = path
        if self.workspace_fs_model is None:
            self.workspace_fs_model = QtWidgets.QFileSystemModel()
            self.workspace_fs_model.setReadOnly(False)
            try:
                self.workspace_fs_model.setFilter(QtCore.QDir.AllEntries | QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Hidden)
            except Exception:
                pass
        if root_changed:
            root_index = self.workspace_fs_model.setRootPath(path)
            self.workspace_list_view.setModel(self.workspace_fs_model)
            self.workspace_list_view.setRootIndex(root_index)
            try:
                self.workspace_list_view.setColumnWidth(0, 260)
            except Exception:
                pass
            if not self.workspace_sel_connected:
                sel_model = self.workspace_list_view.selectionModel()
                if sel_model:
                    sel_model.selectionChanged.connect(partial(self._on_workspace_fs_selection_changed, sel_model))
                    self.workspace_sel_connected = True
        nodes, edges = self._build_workspace_graph_data(path, proj)
        self.workspace_graph.load_graph(nodes, edges)
        self._set_workspace_view_mode(self.workspace_view_mode, force=True)
        if self.workspace_selected_meta:
            meta = self.workspace_selected_meta
            if meta.get("type") in {"file", "folder", "database"} and meta.get("path") and os.path.exists(meta["path"]):
                self._select_workspace_list_path(meta["path"])
                meta = self._workspace_meta_for_path(meta["path"])
                self.workspace_selected_meta = meta
            self._update_workspace_inspector(self.workspace_selected_meta)
        else:
            self._update_workspace_inspector(None)
        self._update_workspace_tag_controls(proj, self.get_project_redaction(proj) if proj else False)

    def _set_workspace_view_mode(self, mode, force=False):
        if mode not in {"graph", "list"}:
            return
        if not force and mode == self.workspace_view_mode:
            return
        self.workspace_view_mode = mode
        if mode == "graph":
            self.workspace_stack.setCurrentWidget(self.workspace_graph)
            if hasattr(self, "workspace_graph_toggle") and not self.workspace_graph_toggle.isChecked():
                self.workspace_graph_toggle.setChecked(True)
        else:
            self.workspace_stack.setCurrentWidget(self.workspace_list_view)
            if hasattr(self, "workspace_list_toggle") and not self.workspace_list_toggle.isChecked():
                self.workspace_list_toggle.setChecked(True)

    def _on_workspace_graph_toggled(self, checked):
        if not self._ui_alive(self.workspace_stack):
            return
        if checked:
            self._set_workspace_view_mode("graph")

    def _on_workspace_list_toggled(self, checked):
        if not self._ui_alive(self.workspace_stack):
            return
        if checked:
            self._set_workspace_view_mode("list")

    def _on_workspace_add_file(self, ext, *args):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_add_file(ext)

    def _on_workspace_add_folder(self, name, *args):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_add_folder(name)

    def _on_workspace_add_database(self, kind, *args):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_add_database(kind)

    def _on_workspace_remove_entity(self, kind, *args):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_remove_entity(kind)

    def _on_workspace_mod_entity(self, action_key, *args):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_mod_entity(action_key)

    def _workspace_meta_for_path(self, path):
        if not path:
            return None
        try:
            st = os.stat(path)
        except Exception:
            return None
        kind = "folder" if os.path.isdir(path) else "file"
        if path.lower().endswith(".db"):
            kind = "database"
        rel = os.path.relpath(path, self.workspace_root_path) if self.workspace_root_path else os.path.basename(path)
        return {
            "id": f"fs:{rel}",
            "type": kind,
            "path": path,
            "label": os.path.basename(path),
            "size": st.st_size,
            "perms": stat.S_IMODE(st.st_mode),
            "hidden": os.path.basename(path).startswith("."),
            "modified": self._format_ui_datetime(datetime.fromtimestamp(st.st_mtime)),
            "project": self.active_project or self.selected_project,
            "status": self.workspace_status.get(path),
        }

    def _on_workspace_fs_selected(self, index):
        if not self.workspace_fs_model:
            return
        path = self.workspace_fs_model.filePath(index)
        meta = self._workspace_meta_for_path(path)
        self.workspace_selected_meta = meta
        self._update_workspace_inspector(meta)
        if meta and meta.get("type") in {"file", "folder", "database"}:
            self._select_workspace_graph_for_path(meta["path"])

    def _on_workspace_fs_selection_changed(self, sel_model, *args):
        if not self._ui_alive(self.workspace_list_view):
            return
        self._on_workspace_fs_selected(sel_model.currentIndex())

    def _on_workspace_graph_selected(self, node_id, meta):
        self.workspace_selected_meta = meta
        if meta.get("type") in {"file", "folder", "database"} and meta.get("path"):
            self._select_workspace_list_path(meta["path"])
        self._update_workspace_inspector(meta)

    def _select_workspace_list_path(self, path):
        if not self.workspace_fs_model or not path:
            return
        idx = self.workspace_fs_model.index(path)
        if idx.isValid():
            sel = self.workspace_list_view.selectionModel()
            if sel:
                sel.select(idx, QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows)
                self.workspace_list_view.scrollTo(idx)

    def _select_workspace_graph_for_path(self, path):
        if not path or not self.workspace_root_path:
            return
        rel = os.path.relpath(path, self.workspace_root_path)
        node_id = f"fs:{rel}"
        self.workspace_graph.select_node(node_id)

    def _clear_form_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _update_workspace_inspector(self, meta):
        self._clear_form_layout(self.workspace_attr_form)
        if not meta:
            self.workspace_attr_form.addRow(QtWidgets.QLabel("Select an item to view attributes"))
            return
        def add_row(label, widget):
            self.workspace_attr_form.addRow(QtWidgets.QLabel(label), widget)
        add_row("Type", QtWidgets.QLabel(meta.get("type", "-")))
        if meta.get("type") in {"file", "folder", "database"}:
            path_edit = QtWidgets.QLineEdit(meta.get("path", ""))
            path_edit.setReadOnly(True)
            add_row("Path", path_edit)
            name_edit = QtWidgets.QLineEdit(meta.get("label", ""))
            name_edit.editingFinished.connect(partial(self._on_workspace_rename, meta, name_edit))
            add_row("Name", name_edit)
            size_lbl = QtWidgets.QLabel(f"{meta.get('size', 0)} bytes")
            add_row("Size", size_lbl)
            perms_edit = QtWidgets.QLineEdit(oct(meta.get("perms", 0o644)))
            perms_edit.editingFinished.connect(partial(self._on_workspace_apply_permission, meta, perms_edit))
            add_row("Permissions (octal)", perms_edit)
            hidden_cb = QtWidgets.QCheckBox("Hidden")
            hidden_cb.setChecked(bool(meta.get("hidden")))
            hidden_cb.toggled.connect(partial(self._on_workspace_toggle_hidden, meta))
            add_row("Visibility", hidden_cb)
            modified_lbl = QtWidgets.QLabel(meta.get("modified", ""))
            add_row("Modified", modified_lbl)
            if meta.get("status"):
                add_row("Status", QtWidgets.QLabel(meta.get("status")))
        elif meta.get("type") == "task":
            add_row("Title", QtWidgets.QLabel(meta.get("label", "")))
            status_combo = QtWidgets.QComboBox()
            status_combo.addItems(TASK_STATUS_VALUES)
            if meta.get("status") in TASK_STATUS_VALUES:
                status_combo.setCurrentText(meta.get("status"))
            status_combo.currentTextChanged.connect(partial(self._on_workspace_task_status_changed, meta))
            add_row("Status", status_combo)
            priority_cb = QtWidgets.QCheckBox("Important")
            priority_cb.setChecked(bool(meta.get("priority")))
            priority_cb.toggled.connect(partial(self._on_workspace_task_priority_toggled, meta))
            add_row("Priority", priority_cb)

    def _workspace_apply_permission(self, meta, text):
        path = meta.get("path")
        if not path:
            return
        start = time.monotonic()
        try:
            mode = int(text, 8)
            os.chmod(path, mode)
            self.workspace_selected_meta = self._workspace_meta_for_path(path)
            self.refresh_workspace_views(force=True)
            self._record_network_event(
                {
                    "protocol": "file",
                    "event": "state",
                    "source": path,
                    "dest": path,
                    "project": meta.get("project") or self.active_project,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                    "throughput": 0.5,
                }
            )
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Permission Error", f"Could not apply permissions: {exc}")

    def _workspace_toggle_hidden(self, meta, hidden):
        path = meta.get("path")
        if not path:
            return
        start = time.monotonic()
        parent = os.path.dirname(path)
        name = os.path.basename(path)
        target_name = name.lstrip(".")
        if hidden and not name.startswith("."):
            target_name = "." + name
        elif not hidden:
            target_name = name.lstrip(".")
        target_path = os.path.join(parent, target_name)
        if target_path == path:
            return
        try:
            os.rename(path, target_path)
            self.workspace_selected_meta = self._workspace_meta_for_path(target_path)
            self.refresh_workspace_views(force=True)
            self._record_network_event(
                {
                    "protocol": "file",
                    "event": "state",
                    "source": path,
                    "dest": target_path,
                    "project": meta.get("project") or self.active_project,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                    "throughput": 0.5,
                }
            )
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Visibility Error", f"Could not toggle visibility: {exc}")

    def _workspace_rename(self, meta, new_name):
        path = meta.get("path")
        if not path or not new_name:
            return
        start = time.monotonic()
        parent = os.path.dirname(path)
        target = os.path.join(parent, new_name)
        if target == path:
            return
        try:
            os.rename(path, target)
            self.workspace_selected_meta = self._workspace_meta_for_path(target)
            self.refresh_workspace_views(force=True)
            self._record_network_event(
                {
                    "protocol": "file",
                    "event": "mutation",
                    "source": path,
                    "dest": target,
                    "project": meta.get("project") or self.active_project,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                    "throughput": 0.5,
                }
            )
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Rename Error", f"Could not rename: {exc}")

    def _workspace_add_file(self, ext):
        path, proj = self.resolve_project_path(require_focus_or_selection=True, prefer_canonical=True)
        if not path:
            return
        start = time.monotonic()
        name, ok = QtWidgets.QInputDialog.getText(self, "New File", "Enter file name:", text=f"new{ext}")
        if not ok or not name.strip():
            return
        filename = name.strip()
        if not filename.endswith(ext):
            filename += ext
        target = os.path.join(path, filename)
        if os.path.exists(target):
            QtWidgets.QMessageBox.warning(self, "Exists", f"{target} already exists.")
            return
        try:
            with open(target, "w", encoding="utf-8") as fh:
                fh.write("")
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Create Error", f"Could not create file: {exc}")
            return
        latency = int((time.monotonic() - start) * 1000)
        self._record_network_event(
            {
                "protocol": "file",
                "event": "mutation",
                "source": proj or "global",
                "dest": target,
                "project": proj,
                "latency_ms": latency,
                "throughput": max(1.0, os.path.getsize(target) if os.path.exists(target) else 1.0),
            }
        )
        self.workspace_selected_meta = self._workspace_meta_for_path(target)
        self.refresh_workspace_views(force=True)

    def _workspace_add_folder(self, label):
        path, proj = self.resolve_project_path(require_focus_or_selection=True, prefer_canonical=True)
        if not path:
            return
        start = time.monotonic()
        name, ok = QtWidgets.QInputDialog.getText(self, "New Folder", "Folder name:", text=label.lower())
        if not ok or not name.strip():
            return
        target = os.path.join(path, name.strip())
        try:
            os.makedirs(target, exist_ok=False)
        except FileExistsError:
            QtWidgets.QMessageBox.warning(self, "Exists", f"{target} already exists.")
            return
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Create Error", f"Could not create folder: {exc}")
            return
        latency = int((time.monotonic() - start) * 1000)
        self._record_network_event(
            {
                "protocol": "file",
                "event": "mutation",
                "source": proj or "global",
                "dest": target,
                "project": proj,
                "latency_ms": latency,
                "throughput": 1.0,
            }
        )
        self.workspace_selected_meta = self._workspace_meta_for_path(target)
        self.refresh_workspace_views(force=True)

    def _workspace_add_database(self, kind):
        path, proj = self.resolve_project_path(require_focus_or_selection=True, prefer_canonical=True)
        if not path:
            return
        start = time.monotonic()
        name, ok = QtWidgets.QInputDialog.getText(self, "New Database", "Database file name:", text="database.db")
        if not ok or not name.strip():
            return
        filename = name.strip()
        if not filename.lower().endswith(".db"):
            filename += ".db"
        target = os.path.join(path, filename)
        if os.path.exists(target):
            QtWidgets.QMessageBox.warning(self, "Exists", f"{target} already exists.")
            return
        try:
            sqlite3.connect(target).close()
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Create Error", f"Could not create database: {exc}")
            return
        latency = int((time.monotonic() - start) * 1000)
        self._record_network_event(
            {
                "protocol": "db",
                "event": "mutation",
                "source": proj or "global",
                "dest": target,
                "project": proj,
                "latency_ms": latency,
                "throughput": 1.0,
            }
        )
        self.workspace_selected_meta = self._workspace_meta_for_path(target)
        self.refresh_workspace_views(force=True)

    def _workspace_remove_entity(self, kind):
        meta = self.workspace_selected_meta
        if not meta or meta.get("type") not in {"file", "folder", "database"}:
            QtWidgets.QMessageBox.warning(self, "Select Item", "Select a file, folder, or database to remove.")
            return
        if kind == "database" and meta.get("type") != "database":
            QtWidgets.QMessageBox.warning(self, "Mismatch", "Select a database to remove.")
            return
        path = meta.get("path")
        if not path or not os.path.exists(path):
            return
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete '{path}' from the active project?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Delete Error", f"Could not delete: {exc}")
            return
        self._record_network_event(
            {
                "protocol": "file" if meta.get("type") != "database" else "db",
                "event": "mutation",
                "source": meta.get("path"),
                "dest": "deleted",
                "project": meta.get("project") or self.active_project,
                "latency_ms": 0,
                "throughput": 0,
            }
        )
        self.workspace_selected_meta = None
        self.refresh_workspace_views(force=True)

    def _workspace_mod_entity(self, action_key):
        meta = self.workspace_selected_meta
        if not meta:
            QtWidgets.QMessageBox.warning(self, "Select Item", "Select an item to modify.")
            return
        if action_key in {"complete", "incomplete", "in_progress"}:
            if meta.get("type") != "task":
                if meta.get("type") in {"file", "folder", "database"}:
                    if action_key == "in_progress":
                        path = meta.get("path")
                        if path:
                            self.workspace_status[path] = "in_progress"
                            self.refresh_workspace_views(force=True)
                            self._record_network_event(
                                {
                                    "protocol": "file",
                                    "event": "state",
                                    "source": path,
                                    "dest": path,
                                    "project": meta.get("project") or self.active_project,
                                    "latency_ms": 0,
                                    "throughput": 0.5,
                                }
                            )
                    return
                QtWidgets.QMessageBox.warning(self, "Task Required", "Select a task node to modify status.")
                return
            target_status = "completed" if action_key == "complete" else ("pending" if action_key == "incomplete" else "in_progress")
            self._workspace_update_task_status(meta, target_status)
            return
        if meta.get("type") not in {"file", "folder", "database"}:
            QtWidgets.QMessageBox.warning(self, "File/Folder Required", "Select a file or folder to modify.")
            return
        if action_key == "hidden":
            self._workspace_toggle_hidden(meta, not meta.get("hidden"))
        elif action_key == "readonly":
            path = meta.get("path")
            if path:
                start = time.monotonic()
                try:
                    st = os.stat(path)
                    mode = stat.S_IMODE(st.st_mode)
                    os.chmod(path, mode & ~0o222)
                    self.workspace_selected_meta = self._workspace_meta_for_path(path)
                    self.refresh_workspace_views(force=True)
                    self._record_network_event(
                        {
                            "protocol": "file",
                            "event": "state",
                            "source": path,
                            "dest": path,
                            "project": meta.get("project") or self.active_project,
                            "latency_ms": int((time.monotonic() - start) * 1000),
                            "throughput": 0.5,
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    QtWidgets.QMessageBox.critical(self, "Permission Error", f"Could not set read-only: {exc}")
        elif action_key == "exec":
            path = meta.get("path")
            if path:
                start = time.monotonic()
                try:
                    st = os.stat(path)
                    mode = stat.S_IMODE(st.st_mode)
                    os.chmod(path, mode | 0o111)
                    self.workspace_selected_meta = self._workspace_meta_for_path(path)
                    self.refresh_workspace_views(force=True)
                    self._record_network_event(
                        {
                            "protocol": "file",
                            "event": "state",
                            "source": path,
                            "dest": path,
                            "project": meta.get("project") or self.active_project,
                            "latency_ms": int((time.monotonic() - start) * 1000),
                            "throughput": 0.5,
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    QtWidgets.QMessageBox.critical(self, "Permission Error", f"Could not set executable: {exc}")

    def _workspace_import_file(self):
        project_path, proj = self.resolve_project_path(require_focus_or_selection=True, prefer_canonical=True)
        if not project_path:
            return
        src, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import File")
        if not src:
            return
        default_target = os.path.join(project_path, os.path.basename(src))
        dest, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Destination", default_target)
        if not dest:
            return
        try:
            start = time.monotonic()
            shutil.copy2(src, dest)
            latency = int((time.monotonic() - start) * 1000)
            self._record_network_event(
                {
                    "protocol": "file",
                    "event": "copy",
                    "source": src,
                    "dest": dest,
                    "project": proj,
                    "latency_ms": latency,
                    "throughput": max(1.0, os.path.getsize(dest) if os.path.exists(dest) else 1.0),
                }
            )
            self.workspace_selected_meta = self._workspace_meta_for_path(dest)
            self.refresh_workspace_views(force=True)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Import Failed", f"Could not import file: {exc}")

    def _workspace_import_folder(self):
        project_path, proj = self.resolve_project_path(require_focus_or_selection=True, prefer_canonical=True)
        if not project_path:
            return
        src = QtWidgets.QFileDialog.getExistingDirectory(self, "Import Folder")
        if not src:
            return
        target_name, ok = QtWidgets.QInputDialog.getText(self, "Destination Folder Name", "Folder name:", text=os.path.basename(src))
        if not ok or not target_name.strip():
            return
        dest = os.path.join(project_path, target_name.strip())
        if os.path.exists(dest):
            QtWidgets.QMessageBox.warning(self, "Exists", f"{dest} already exists.")
            return
        try:
            start = time.monotonic()
            shutil.copytree(src, dest)
            latency = int((time.monotonic() - start) * 1000)
            self._record_network_event(
                {
                    "protocol": "file",
                    "event": "copy",
                    "source": src,
                    "dest": dest,
                    "project": proj,
                    "latency_ms": latency,
                    "throughput": 1.0,
                }
            )
            self.workspace_selected_meta = self._workspace_meta_for_path(dest)
            self.refresh_workspace_views(force=True)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Import Failed", f"Could not import folder: {exc}")

    def _workspace_import_archive(self):
        project_path, proj = self.resolve_project_path(require_focus_or_selection=True, prefer_canonical=True)
        if not project_path:
            return
        src, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Archive")
        if not src:
            return
        dest = os.path.join(project_path, os.path.basename(src))
        try:
            start = time.monotonic()
            shutil.copy2(src, dest)
            latency = int((time.monotonic() - start) * 1000)
            self._record_network_event(
                {
                    "protocol": "file",
                    "event": "copy",
                    "source": src,
                    "dest": dest,
                    "project": proj,
                    "latency_ms": latency,
                    "throughput": max(1.0, os.path.getsize(dest) if os.path.exists(dest) else 1.0),
                }
            )
            self.workspace_selected_meta = self._workspace_meta_for_path(dest)
            self.refresh_workspace_views(force=True)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Import Failed", f"Could not import archive: {exc}")

    def _workspace_update_task_status(self, meta, status):
        task_id = meta.get("uuid")
        if not task_id:
            return
        try:
            self.store.transition_status(task_id, status)
            self.update_task_controls_enabled()
            self.update_project_status_from_tasks(meta.get("project"))
            self.populate_lists()
            self.load_tasks()
            self.refresh_workspace_views(force=True)
            self._record_network_event(
                {
                    "protocol": "task",
                    "event": "mutation",
                    "source": meta.get("project") or "tasks",
                    "dest": task_id,
                    "project": meta.get("project"),
                    "latency_ms": 0,
                    "throughput": 1.0,
                }
            )
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Task Update Failed", f"{exc}")

    def _workspace_update_task_priority(self, meta, important):
        task_id = meta.get("uuid")
        if not task_id:
            return
        try:
            self.store.update_task(task_id, priority=1 if important else 0)
            self.load_tasks()
            self.refresh_workspace_views(force=True)
            self._record_network_event(
                {
                    "protocol": "task",
                    "event": "state",
                    "source": meta.get("project") or "tasks",
                    "dest": task_id,
                    "project": meta.get("project"),
                    "latency_ms": 0,
                    "throughput": 0.5,
                }
            )
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Task Update Failed", f"{exc}")

    def _on_workspace_rename(self, meta, widget):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_rename(meta, widget.text())

    def _on_workspace_apply_permission(self, meta, widget):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_apply_permission(meta, widget.text())

    def _on_workspace_toggle_hidden(self, meta, checked):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_toggle_hidden(meta, checked)

    def _on_workspace_task_status_changed(self, meta, val):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_update_task_status(meta, val)

    def _on_workspace_task_priority_toggled(self, meta, val):
        if not self._ui_alive(self.workspace_stack):
            return
        self._workspace_update_task_priority(meta, val)

    def _on_workspace_tags_changed(self):
        if not self._ui_alive(self.workspace_stack):
            return
        project = self.selected_project or self.active_project
        if not project:
            return
        raw = self.workspace_tags_edit.text() if hasattr(self, "workspace_tags_edit") else ""
        tags = self._normalized_tags(raw.split(","))
        redacted = any(t.lower() == "redacted" for t in tags)
        self.set_project_redaction(project, redacted, tags=tags, source="workspace-tags")

    def _on_workspace_redacted_tag_toggled(self, checked):
        if not self._ui_alive(self.workspace_stack):
            return
        project = self.selected_project or self.active_project
        if not project:
            return
        raw = self.workspace_tags_edit.text() if hasattr(self, "workspace_tags_edit") else ""
        tags = self._normalized_tags(raw.split(","))
        self.set_project_redaction(project, bool(checked), tags=tags, source="workspace-tag-toggle")

    def _sync_repo_visibility(self, project, make_private):
        headers, _ = self.build_github_headers()
        if not headers:
            self.log_vcs(f"[redaction] Skipped GitHub visibility update for {project}: missing credentials")
            return
        owner = self.verified_user or self.active_credentials.get("username") or (self.get_credentials()[0] if hasattr(self, "get_credentials") else "")
        if not owner or not project:
            self.log_vcs(f"[redaction] Skipped GitHub visibility update: missing owner or project")
            return
        url = f"https://api.github.com/repos/{owner}/{project}"
        payload = json.dumps({"private": bool(make_private)}).encode("utf-8")
        headers = headers.copy()
        headers["Content-Type"] = "application/json"

        def work():
            req = urllib.request.Request(url, data=payload, headers=headers, method="PATCH")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    code = resp.getcode()
                    data = json.load(resp)
                    return True, code, data, None
            except urllib.error.HTTPError as e:
                try:
                    err_body = e.read().decode("utf-8")
                except Exception:
                    err_body = str(e)
                return False, e.code, None, err_body
            except Exception as exc:  # noqa: BLE001
                return False, None, None, str(exc)

        def on_result(result):
            ok, code, data, err = result
            if not ok:
                self.log_vcs(f"[redaction] GitHub visibility update failed ({code}): {err}")
                return
            label = "private" if make_private else "public"
            self.log_vcs(f"[redaction] Set repo '{project}' {label} (HTTP {code})")

        def on_error(err):
            self.log_vcs(f"[redaction] Visibility update error: {err}")

        self.run_in_background(work, on_result, on_error)

    def _build_workspace_graph_data(self, path, proj):
        nodes = []
        edges = []
        root_id = "root"
        nodes.append({"id": root_id, "label": proj or os.path.basename(path), "type": "folder", "path": path})
        max_nodes = 140
        count = 1
        for root, dirs, files in os.walk(path):
            dirs.sort()
            files.sort()
            rel_root = os.path.relpath(root, path)
            parent_id = root_id if rel_root == "." else f"fs:{rel_root}"
            if rel_root != ".":
                nodes.append({"id": parent_id, "label": os.path.basename(root), "type": "folder", "path": root})
                parent_parent = os.path.dirname(rel_root)
                edges.append((root_id if parent_parent == "" or parent_parent == "." else f"fs:{parent_parent}", parent_id))
                count += 1
            for d in dirs:
                if count >= max_nodes:
                    break
                d_path = os.path.join(root, d)
                rel = os.path.relpath(d_path, path)
                nid = f"fs:{rel}"
                nodes.append({"id": nid, "label": d, "type": "folder", "path": d_path})
                edges.append((parent_id, nid))
                count += 1
            for f in files:
                if count >= max_nodes:
                    break
                f_path = os.path.join(root, f)
                rel = os.path.relpath(f_path, path)
                nid = f"fs:{rel}"
                nodes.append({"id": nid, "label": f, "type": "file", "path": f_path})
                edges.append((parent_id, nid))
                count += 1
            if count >= max_nodes:
                break
        try:
            cur = self.store.conn.cursor()
            cur.execute("SELECT uuid, title, status, priority FROM tasks WHERE project=?", (proj,))
            for row in cur.fetchall():
                tid = row["uuid"]
                label = (row["title"] or tid)[:28]
                nid = f"task:{tid}"
                nodes.append(
                    {
                        "id": nid,
                        "label": label,
                        "type": "task",
                        "status": row["status"] or "pending",
                        "uuid": tid,
                        "project": proj,
                        "priority": row["priority"],
                    }
                )
                edges.append((root_id, nid))
        except Exception:
            pass
        return nodes, edges

    # ---- Network ----
    def _network_set_capture(self, enabled):
        self.network_capture_enabled = bool(enabled)
        if not enabled:
            self.network_capture_paused = True
        else:
            self.network_capture_paused = False

    def _network_stop_capture(self):
        self.network_capture_enabled = False
        self.network_capture_paused = True
        self.net_capture_btn.setChecked(False)

    def _network_latency_mode_changed(self, val):
        self.network_latency_mode = "point" if "point" in val.lower() else "aggregate"
        self._refresh_network_views()

    def _set_network_view(self, mode):
        if mode not in {"graph", "timeline", "table"}:
            return
        self.network_view_mode = mode
        if mode == "graph":
            self.net_stack.setCurrentWidget(self.net_graph_view)
        elif mode == "timeline":
            self.net_stack.setCurrentWidget(self.net_timeline)
        else:
            self.net_stack.setCurrentWidget(self.net_table)

    def _network_inject_event(self):
        path, proj = self.resolve_project_path(require_focus_or_selection=False, prefer_canonical=True)
        now = datetime.now()
        payload = {
            "type": "inject",
            "source": "injector",
            "dest": proj or "global",
            "project": proj,
            "latency_ms": 5,
            "throughput": 1.0,
            "timestamp": now.timestamp(),
            "protocol": "inject",
            "event": "mutation",
        }
        self._record_network_event(payload)

    def _record_network_event(self, event: dict):
        if not self.network_capture_enabled or self.network_capture_paused:
            return
        scope = self.net_capture_scope.currentText() if hasattr(self, "net_capture_scope") else "Global"
        proj = self.active_project or self.selected_project
        if scope == "Active Project" and proj and event.get("project") and event.get("project") != proj:
            return
        event.setdefault("timestamp", time.time())
        event.setdefault("latency_ms", 0)
        event.setdefault("throughput", 1.0)
        self.network_events.append(event)
        self._update_network_endpoints(event)
        self._refresh_network_views()

    def _update_network_endpoints(self, event):
        for role in ["source", "dest"]:
            ep = event.get(role)
            if not ep:
                continue
            entry = self.network_endpoints.setdefault(ep, {"id": ep, "latency": event.get("latency_ms", 0), "throughput": event.get("throughput", 0), "errors": 0, "project": event.get("project"), "status": "active"})
            entry["latency"] = event.get("latency_ms", entry.get("latency", 0))
            entry["throughput"] = max(entry.get("throughput", 0), event.get("throughput", 0))
            entry["project"] = event.get("project") or entry.get("project")
            if event.get("event") == "error":
                entry["errors"] = entry.get("errors", 0) + 1

    def _passes_net_filters(self, event):
        proto = self.net_protocol_filter.currentText() if hasattr(self, "net_protocol_filter") else "Any"
        evtype = self.net_event_filter.currentText() if hasattr(self, "net_event_filter") else "Any"
        projf = self.net_project_filter.text().strip() if hasattr(self, "net_project_filter") else ""
        epf = self.net_endpoint_filter.text().strip()
        tf = self.net_time_filter.currentText() if hasattr(self, "net_time_filter") else "Any"
        if proto != "Any" and event.get("protocol") != proto:
            return False
        if evtype != "Any" and event.get("event") != evtype:
            return False
        if projf and (event.get("project") or "").lower().find(projf.lower()) == -1:
            return False
        if epf and epf.lower() not in (event.get("source", "") + event.get("dest", "")).lower():
            return False
        if tf != "Any":
            delta = {"Last 1m": 60, "Last 5m": 300, "Last 15m": 900}.get(tf, None)
            if delta and time.time() - event.get("timestamp", time.time()) > delta:
                return False
        return True

    def _refresh_network_views(self):
        if not hasattr(self, "net_stack"):
            return
        filtered = [e for e in list(self.network_events) if self._passes_net_filters(e)]
        graph_nodes, graph_edges = self._build_network_graph_data(filtered)
        self.net_graph_view.load_graph(graph_nodes, graph_edges)
        self._populate_net_endpoints(filtered)
        self._populate_net_timeline(filtered)
        self._populate_net_table(filtered)

    def _build_network_graph_data(self, events):
        nodes = []
        edges = []
        seen = set()
        for ep_id, meta in self.network_endpoints.items():
            nodes.append(
                {
                    "id": ep_id,
                    "label": ep_id,
                    "scope": "project" if meta.get("project") == (self.active_project or self.selected_project) else "global",
                }
            )
        for idx, ev in enumerate(events[-120:]):
            eid = f"edge-{idx}"
            src = ev.get("source")
            dst = ev.get("dest")
            if not src or not dst:
                continue
            key = (src, dst)
            if key in seen and self.network_latency_mode != "point":
                continue
            seen.add(key)
            color = "#2e9b8f" if ev.get("event") in ("sync", "state") else "#d14b4b" if ev.get("event") == "error" else "#3b6aff"
            edges.append(
                {
                    "id": eid,
                    "src": src,
                    "dst": dst,
                    "latency_ms": ev.get("latency_ms", 0),
                    "throughput": ev.get("throughput", 1.0),
                    "color": color,
                }
            )
        return nodes, edges

    def _populate_net_endpoints(self, events):
        self.net_endpoint_list.clear()
        for ep_id, meta in self.network_endpoints.items():
            item = QtWidgets.QTreeWidgetItem(
                [
                    ep_id,
                    meta.get("status", "active"),
                    f"{int(meta.get('latency', 0))} ms",
                    f"{meta.get('throughput', 0):.2f}",
                    str(meta.get("errors", 0)),
                    meta.get("project") or "-",
                ]
            )
            item.setData(0, QtCore.Qt.UserRole, meta)
            self.net_endpoint_list.addTopLevelItem(item)

    def _populate_net_timeline(self, events):
        self.net_timeline.clear()
        for ev in events[-200:]:
            ts = self._format_ui_time(ev.get("timestamp", time.time()))
            text = f"[{ts}] {ev.get('event','')} {ev.get('source','?')} -> {ev.get('dest','?')} ({int(ev.get('latency_ms',0))} ms)"
            self.net_timeline.addItem(text)

    def _populate_net_table(self, events):
        self.net_table.setRowCount(len(events))
        for row, ev in enumerate(events):
            ts = self._format_ui_time(ev.get("timestamp", time.time()))
            vals = [
                ts,
                ev.get("event", ""),
                ev.get("source", ""),
                ev.get("dest", ""),
                str(int(ev.get("latency_ms", 0))),
                f"{ev.get('throughput', 0):.2f}",
                ev.get("project") or "",
            ]
            for col, val in enumerate(vals):
                self.net_table.setItem(row, col, QtWidgets.QTableWidgetItem(val))

    def _on_net_endpoint_selected(self):
        items = self.net_endpoint_list.selectedItems()
        if not items:
            return
        meta = items[0].data(0, QtCore.Qt.UserRole) or {}
        self.net_graph_view.select_node(meta.get("id"))

    def _on_net_graph_selected(self, node_id, meta):
        # align selection with endpoint list
        matches = self.net_endpoint_list.findItems(node_id, QtCore.Qt.MatchExactly, 0)
        if matches:
            self.net_endpoint_list.setCurrentItem(matches[0])

    def _on_net_capture_toggled(self, val):
        if not self._ui_alive(self.net_stack):
            return
        self._network_set_capture(val)

    def _on_net_pause_toggled(self, val):
        if not self._ui_alive(self.net_stack):
            return
        self.network_capture_paused = bool(val)

    def _on_net_view_graph_toggled(self, checked):
        if checked and self._ui_alive(self.net_stack):
            self._set_network_view("graph")

    def _on_net_view_timeline_toggled(self, checked):
        if checked and self._ui_alive(self.net_stack):
            self._set_network_view("timeline")

    def _on_net_view_table_toggled(self, checked):
        if checked and self._ui_alive(self.net_stack):
            self._set_network_view("table")


    def ensure_remote_repo(self, project, dry_run=False):
        username, password, tokens = self.get_credentials()
        if not username or not (password or tokens):
            return False, "Missing GitHub credentials."
        repo = project
        headers, _ = self.build_github_headers()
        if not headers:
            return False, "Missing GitHub credentials."
        def request(method, url, data=None):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            return urllib.request.urlopen(req, timeout=15)
        # check existence
        try:
            request("GET", f"https://api.github.com/repos/{username}/{repo}")
            exists = True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                exists = False
            else:
                return False, f"GitHub check failed: {e}"
        except Exception as exc:  # noqa: BLE001
            return False, f"GitHub check failed: {exc}"
        if not exists:
            if dry_run:
                return True, f"[Dry run] Would create repo {username}/{repo}"
            payload = json.dumps({"name": repo, "private": True}).encode("utf-8")
            try:
                request("POST", "https://api.github.com/user/repos", data=payload)
            except Exception as exc:  # noqa: BLE001
                return False, f"GitHub repo create failed: {exc}"
        # set remote if missing
        path = os.path.join(PROJECT_ROOT, project)
        env = self.git_env()
        remote_url = f"https://github.com/{username}/{repo}.git"
        if not dry_run:
            subprocess.run(["git", "-C", path, "remote", "remove", "origin"], capture_output=True, text=True, env=env)
            res = subprocess.run(["git", "-C", path, "remote", "add", "origin", remote_url], capture_output=True, text=True, env=env)
            if res.returncode != 0:
                # maybe already exists; set-url
                subprocess.run(["git", "-C", path, "remote", "set-url", "origin", remote_url], capture_output=True, text=True, env=env)
        return True, "Remote ensured"

    def update_autogit_path_label(self):
        path, proj = self.resolve_project_path(require_focus_or_selection=False, prefer_canonical=True)
        if path and proj:
            self.autogit_path_label.setText(f"Target: {proj} ({path})")
            if self.autogit.available():
                self.update_git_status_label(path)
            else:
                self.autogit_status_label.setText("AutoGIT not found")
                self.autogit_status_label.setStyleSheet("color: #d14b4b;")
        else:
            self.autogit_path_label.setText("Target: (focus or select a project)")
            self.autogit_status_label.setText("Git: Unknown")
            self.autogit_status_label.setStyleSheet("color: #8ad0ff;")

    def update_auto_commit_toggle_state(self):
        proj = self.selected_project
        if not proj:
            self._set_enabled_safely(self.auto_commit_toggle, False)
            self._set_enabled_safely(self.auto_commit_global_btn, False)
            self._set_checked_safely(self.auto_commit_toggle, False)
            self._set_checked_safely(self.auto_commit_global_btn, False)
            self._set_enabled_safely(self.revert_version_btn, False)
            return
        path = os.path.join(PROJECT_ROOT, proj)
        env = self.git_env()
        initialized = self.autogit.is_git_repo(path, env=env) if os.path.isdir(path) else False
        meta_entry = self.project_meta.get(proj, {"origin": "Local", "auto_commit": False})
        state = bool(meta_entry.get("auto_commit", False))
        enabled = initialized and self.autogit.available()
        self._set_enabled_safely(self.auto_commit_toggle, enabled)
        self._set_enabled_safely(self.auto_commit_global_btn, enabled)
        self._set_checked_safely(self.auto_commit_toggle, state if enabled else False)
        self._set_checked_safely(self.auto_commit_global_btn, state if enabled else False)
        self._set_enabled_safely(self.revert_version_btn, enabled and self.version_list.currentItem() is not None)
        self.update_accent_usage()

    def update_autogit_watch(self, project, enable):
        AUTOGIT_WATCH.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        if AUTOGIT_WATCH.exists():
            with open(AUTOGIT_WATCH, "r", encoding="utf-8") as fh:
                lines = [ln.strip() for ln in fh if ln.strip() and not ln.strip().startswith("#")]
        proj_path = os.path.join(PROJECT_ROOT, project)
        if enable:
            if proj_path not in lines:
                lines.append(proj_path)
            self._enable_auto_commit_watcher(project, proj_path)
        else:
            lines = [ln for ln in lines if ln != proj_path]
            self._disable_auto_commit_watcher(project)
        header = "# AutoGIT watch list (managed by Focus Manager)\n"
        with open(AUTOGIT_WATCH, "w", encoding="utf-8") as fh:
            fh.write(header + "\n".join(lines) + ("\n" if lines else ""))

    def _enable_auto_commit_watcher(self, project, path):
        if project in self.autogit_watchers:
            return
        watcher = QtCore.QFileSystemWatcher(self)
        try:
            watcher.addPath(path)
        except Exception:
            return
        watcher.directoryChanged.connect(partial(self._on_project_fs_changed, project))
        watcher.fileChanged.connect(partial(self._on_project_fs_changed, project))
        self.autogit_watchers[project] = watcher

    def _disable_auto_commit_watcher(self, project):
        timer = self.autogit_timers.pop(project, None)
        if timer:
            try:
                timer.stop()
            except Exception:
                pass
        watcher = self.autogit_watchers.pop(project, None)
        if watcher:
            try:
                watcher.deleteLater()
            except Exception:
                pass

    def _on_project_fs_changed(self, project, *_args):
        if not self._ui_alive(self):
            return
        meta_entry = self.project_meta.get(project, {})
        if not meta_entry.get("auto_commit"):
            return
        path = os.path.join(PROJECT_ROOT, project)
        if not os.path.isdir(path):
            return
        timer = self.autogit_timers.get(project)
        if not timer:
            timer = QtCore.QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(partial(self._auto_commit_project, project, path, None, False))
            self.autogit_timers[project] = timer
        timer.start(1200)

    def toggle_auto_commit(self):
        proj = self.selected_project
        if not proj:
            return
        if getattr(self, "_auto_commit_toggle_active", False):
            self.log_debug("STABILITY", {"signal_recursion": "auto_commit_toggle"})
            return
        self._auto_commit_toggle_active = True

        def release_toggle_flag():
            self._auto_commit_toggle_active = False

        self.start_operation("auto_commit_toggle", target=proj, dry_run=self.dry_run_checkbox.isChecked())
        path = os.path.join(PROJECT_ROOT, proj)
        env = self.git_env()
        if not self.autogit.is_git_repo(path, env=env):
            QtWidgets.QMessageBox.warning(self, "Git Required", "Initialize git/AutoGIT before enabling auto commit.")
            self._set_checked_safely(self.auto_commit_toggle, False)
            self._set_checked_safely(self.auto_commit_global_btn, False)
            self.finalize_operation("failed")
            release_toggle_flag()
            return
        meta_entry = self.project_meta.get(proj, {"origin": "Local", "auto_commit": False})
        new_state = not bool(meta_entry.get("auto_commit", False))

        def proceed_toggle():
            meta_entry["origin"] = meta_entry.get("origin", "Local")
            meta_entry["auto_commit"] = new_state
            self.project_meta[proj] = meta_entry
            self.save_project_meta()
            self._set_checked_safely(self.auto_commit_toggle, new_state)
            self._set_checked_safely(self.auto_commit_global_btn, new_state)
            self.update_autogit_watch(proj, new_state)
            self.update_manifest_fields(proj, auto_commit_enabled=new_state)
            state_txt = "enabled" if new_state else "disabled"
            self.set_state("Idle", f"Auto commit {state_txt} for {proj}")
            self.finalize_operation("committed")
            self.refresh_health_panel()
            self.update_accent_usage()
            if new_state:
                # perform an immediate sync/commit to bring remote up to date
                self._auto_commit_project(proj, path, env=self.git_env(), manual=False)
            release_toggle_flag()

        if new_state:
            if self.dry_run_checkbox.isChecked():
                QtWidgets.QMessageBox.information(self, "Dry Run", f"[Dry run] Would enable auto-commit for {proj}")
                self._set_checked_safely(self.auto_commit_toggle, False)
                self._set_checked_safely(self.auto_commit_global_btn, False)
                self.finalize_operation("rolled_back")
                release_toggle_flag()
                return
            # ensure repo exists remotely, async
            self.show_operation("Ensuring remote repository...", state="Executing")
            self.set_operation_state("executing")

            def work():
                ok, msg = self.ensure_remote_repo(proj, dry_run=self.dry_run_checkbox.isChecked())
                return ok, msg

            def on_result(res):
                ok, msg = res
                if not ok:
                    QtWidgets.QMessageBox.critical(self, "Auto Commit", msg)
                    self._set_checked_safely(self.auto_commit_toggle, False)
                    self._set_checked_safely(self.auto_commit_global_btn, False)
                    self.finish_operation("Auto commit disabled")
                    self.finalize_operation("failed")
                    release_toggle_flag()
                    return
                proceed_toggle()
                self.finish_operation("Auto commit ready")
                release_toggle_flag()

            def on_error(err):
                QtWidgets.QMessageBox.critical(self, "Auto Commit", err)
                self._set_checked_safely(self.auto_commit_toggle, False)
                self._set_checked_safely(self.auto_commit_global_btn, False)
                self.finish_operation("Auto commit disabled")
                self.finalize_operation("failed")
                release_toggle_flag()

            self.run_in_background(work, on_result, on_error)
        else:
            if self.dry_run_checkbox.isChecked():
                QtWidgets.QMessageBox.information(self, "Dry Run", f"[Dry run] Would disable auto-commit for {proj}")
                self._set_checked_safely(self.auto_commit_toggle, True)
                self._set_checked_safely(self.auto_commit_global_btn, True)
                self.finalize_operation("rolled_back")
                release_toggle_flag()
                return
            proceed_toggle()

    def focus_selected(self):
        project = self.get_selected_project()
        if not project:
            QtWidgets.QMessageBox.warning(self, "Select Project", "Select a project to focus.")
            return
        target_path = os.path.join(PROJECT_ROOT, project)
        if not os.path.isdir(target_path):
            QtWidgets.QMessageBox.critical(self, "Missing Project", f"{target_path} does not exist.")
            return
        self.start_operation("focus", target=project, dry_run=False)
        self.ui_state["focused_project"] = None
        self.ui_state["mount_active"] = False
        if USE_BIND_MOUNT and not getattr(self.backend, "sudo_password", None):
            pwd, ok = QtWidgets.QInputDialog.getText(self, "Sudo Password", "Enter sudo password:", QtWidgets.QLineEdit.Password)
            if not ok:
                self.finalize_operation("rolled_back")
                return
            self.backend.sudo_password = pwd
        self.show_operation("Focusing project...", state="Executing")
        self.set_operation_state("executing")
        result = self.backend.focus(project)
        if result.returncode != 0:
            msg = result.stderr.strip() or result.stdout.strip() or "Focus failed."
            QtWidgets.QMessageBox.critical(self, "Focus Error", msg)
            self.show_error_banner(msg)
            self.finish_operation("Focus failed")
            self.finalize_operation("failed")
            return
        QtWidgets.QMessageBox.information(self, "Focused", result.stdout.strip() or f"Focused {project}.")
        self.finish_operation("Focus complete")
        self.backend.write_focus_marker(project)
        self.active_project = self.get_marker_project() or project
        self.ui_state["focused_project"] = self.active_project
        self.ui_state["mount_active"] = os.path.ismount(ACTIVE_PROJECT_PATH) if USE_BIND_MOUNT else bool(self.active_project)
        self.update_manifest_fields(project, last_focused_timestamp=now_str(), preferred_credentials=self.selected_cred_label)
        self.update_active_label()
        self.update_autogit_path_label()
        self.update_context_labels()
        self.refresh_projects()
        self.refresh_health_panel()
        self.finalize_operation("committed")

    def unfocus_current(self):
        self.start_operation("unfocus", target=self.active_project, dry_run=False)
        self.ui_state["view_mode"] = "canonical"
        # ensure cwd not inside mount
        try:
            os.chdir(Path.home())
        except Exception:
            pass
        # detach file views to release handles before unmount
        self.detach_fs_view()
        QtWidgets.QApplication.processEvents()
        # Check for busy processes only when a bind mount is in use.
        if USE_BIND_MOUNT:
            busy = self.processes_using_active_mount()
            if busy:
                msg = "The following processes are using the mount:\n" + "\n".join(busy[:10])
                msg += "\nAttempt lazy unmount?"
                reply = QtWidgets.QMessageBox.question(self, "Mount Busy", msg, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if reply != QtWidgets.QMessageBox.Yes:
                    self.finish_operation("Unfocus aborted")
                    self.finalize_operation("failed")
                    return
            if not getattr(self.backend, "sudo_password", None):
                pwd, ok = QtWidgets.QInputDialog.getText(self, "Sudo Password", "Enter sudo password:", QtWidgets.QLineEdit.Password)
                if not ok:
                    self.finalize_operation("rolled_back")
                    return
                self.backend.sudo_password = pwd
        self.show_operation("Unfocusing project...", state="Executing")
        self.set_operation_state("executing")
        result = self.backend.unfocus()
        success_msg = result.stdout.strip() or "Unfocused."
        if result.returncode != 0:
            msg = result.stderr.strip() or result.stdout.strip() or "Unfocus failed."
            if USE_BIND_MOUNT:
                # Attempt lazy unmount as safe fallback if confirmed already
                lazy = subprocess.run(["sudo", "-n", "umount", "-l", ACTIVE_PROJECT_PATH], capture_output=True, text=True)
                if lazy.returncode != 0:
                    QtWidgets.QMessageBox.critical(self, "Unfocus Error", msg)
                    self.show_error_banner(msg)
                    self.finish_operation("Unfocus failed")
                    self.finalize_operation("failed")
                    return
                else:
                    success_msg = "Lazy unmount applied due to busy mount."
            else:
                QtWidgets.QMessageBox.critical(self, "Unfocus Error", msg)
                self.show_error_banner(msg)
                self.finish_operation("Unfocus failed")
                self.finalize_operation("failed")
                return
        QtWidgets.QMessageBox.information(self, "Unfocused", success_msg)
        self.finish_operation("Unfocus complete")
        self.backend.remove_focus_marker()
        self.active_project = self.get_marker_project()
        self.ui_state["focused_project"] = None
        self.ui_state["mount_active"] = os.path.ismount(ACTIVE_PROJECT_PATH) if USE_BIND_MOUNT else False
        self.update_active_label()
        self.update_autogit_path_label()
        self.refresh_projects()
        # reattach filesystem model in canonical view after successful unmount
        self.ensure_fs_model(PROJECT_ROOT)
        self.refresh_health_panel()
        self.finalize_operation("committed")

    def create_project(self):
        self.set_state("Awaiting User Input", "Create project")
        dialog = CreateProjectDialog(self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            self.set_state("Idle", "")
            return
        name, with_readme, with_autogit = dialog.get_values()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Invalid Name", "Project name cannot be empty.")
            self.set_state("Idle", "")
            return
        if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
            QtWidgets.QMessageBox.warning(self, "Invalid Name", "Use letters, numbers, dots, underscores, or hyphens.")
            self.set_state("Idle", "")
            return
        path = os.path.join(PROJECT_ROOT, name)
        if os.path.exists(path):
            QtWidgets.QMessageBox.critical(self, "Exists", f"{path} already exists.")
            self.set_state("Idle", "")
            return
        self.start_operation("create", target=name, dry_run=self.dry_run_checkbox.isChecked())
        if self.dry_run_checkbox.isChecked():
            QtWidgets.QMessageBox.information(self, "Dry Run", f"[Dry run] Would create project at {path}")
            self.finalize_operation("rolled_back")
            self.set_state("Idle", "Dry-run complete")
            return
        self.set_operation_state("executing")
        try:
            os.makedirs(path, exist_ok=False)
            if with_readme:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                content = f"# {name}\n\nCreated: {ts}\n\nDescribe the project here.\n"
                with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create project: {exc}")
            self.show_error_banner(str(exc))
            self.set_state("Idle", "")
            self.finalize_operation("failed")
            return
        self.project_meta[name] = {"origin": "New", "auto_commit": False}
        self.project_meta[name].update({"import_method": "create", "origin_path": path, "last_sync": None, "localsync": False, "localsync_path": None})
        self.save_project_meta()
        self.ensure_manifest(name, origin="New", origin_path=path)
        self.update_manifest_fields(name, preferred_credentials=self.selected_cred_label, auto_commit_enabled=False, localsync_enabled=False)
        if with_autogit:
            self.run_autogit_init_for_path(path)
        QtWidgets.QMessageBox.information(self, "Created", f"Project {name} created.")
        self.refresh_projects()
        self.set_state("Idle", "")
        self.refresh_health_panel()
        self.finalize_operation("committed")

    def rename_project(self):
        project = self.get_selected_project()
        if not project:
            QtWidgets.QMessageBox.warning(self, "Select Project", "Select a project to rename.")
            return
        if self.active_project == project:
            QtWidgets.QMessageBox.critical(self, "Blocked", "Cannot rename the active project.")
            return
        self.set_state("Awaiting User Input", "Enter new project name")
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Rename Project", "New name:", text=project)
        if not ok:
            self.set_state("Idle", "")
            return
        new_name = new_name.strip()
        if not new_name:
            QtWidgets.QMessageBox.warning(self, "Invalid Name", "Project name cannot be empty.")
            self.set_state("Idle", "")
            return
        if not re.fullmatch(r"[A-Za-z0-9._-]+", new_name):
            QtWidgets.QMessageBox.warning(self, "Invalid Name", "Use letters, numbers, dots, underscores, or hyphens.")
            self.set_state("Idle", "")
            return
        if new_name == project:
            self.set_state("Idle", "")
            return
        src = os.path.join(PROJECT_ROOT, project)
        dst = os.path.join(PROJECT_ROOT, new_name)
        if os.path.exists(dst):
            QtWidgets.QMessageBox.critical(self, "Conflict", f"{dst} already exists.")
            self.set_state("Idle", "")
            return
        try:
            os.rename(src, dst)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Error", f"Rename failed: {exc}")
            self.set_state("Idle", "")
            return
        if project in self.status_map:
            self.status_map[new_name] = self.status_map.pop(project)
        QtWidgets.QMessageBox.information(self, "Renamed", f"{project} → {new_name}")
        self.refresh_projects()
        self.set_state("Idle", "")

    def toggle_view(self):
        return

    def delete_project(self):
        project = self.get_selected_project()
        if not project:
            return
        if self.active_project == project:
            QtWidgets.QMessageBox.warning(self, "Locked", "Cannot delete the focused project. Unfocus first.")
            return
        self.start_operation("delete", target=project, dry_run=self.dry_run_checkbox.isChecked())
        # ensure GUI cwd not inside mount
        try:
            os.chdir(Path.home())
        except Exception:
            pass
        proj_path = os.path.join(PROJECT_ROOT, project)
        real_proj = os.path.realpath(proj_path)
        if not real_proj.startswith(os.path.realpath(PROJECT_ROOT)):
            QtWidgets.QMessageBox.critical(self, "Unsafe Path", "Refusing to delete outside canonical root.")
            self.finalize_operation("failed")
            return
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete project '{project}' permanently?\nPath: {proj_path}",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if reply != QtWidgets.QMessageBox.Yes:
            self.finalize_operation("rolled_back")
            return
        if self.dry_run_checkbox.isChecked():
            QtWidgets.QMessageBox.information(self, "Dry Run", f"[Dry run] Would delete {proj_path}")
            self.set_state("Idle", "Dry-run complete")
            self.finalize_operation("rolled_back")
            return
        self.set_operation_state("executing")
        try:
            shutil.rmtree(real_proj)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Delete Failed", f"Could not delete project: {exc}")
            self.finalize_operation("failed")
            return
        self.project_meta.pop(project, None)
        self.save_project_meta()
        self.active_project = self.get_marker_project()
        self.refresh_projects()
        self.project_table.clearSelection()
        self.update_active_label()
        self.set_state("Idle", "Project deleted")
        self.selected_project = None
        self.update_context_labels()
        self.refresh_health_panel()
        self.finalize_operation("committed")

    def summarize_project(self):
        target = self.active_project or self.get_selected_project()
        if not target:
            QtWidgets.QMessageBox.warning(self, "No Project", "Focus a project or select one to summarize.")
            return
        path = os.path.join(PROJECT_ROOT, target)
        if not os.path.isdir(path):
            QtWidgets.QMessageBox.critical(self, "Missing Path", f"{path} does not exist.")
            return
        self.show_operation("Analyzing project...", state="Executing")
        prompt = self.build_summary_prompt(target, path)

        gemini_bin = self._resolve_gemini_cmd()
        if not gemini_bin:
            QtWidgets.QMessageBox.critical(self, "Gemini Error", "Gemini CLI not found or not executable.")
            self.finish_operation("Summarize failed")
            return
        if not self._gemini_authenticated():
            QtWidgets.QMessageBox.critical(self, "Gemini Error", "Gemini is not authenticated. Interactive login is disabled in GUI mode.")
            self.finish_operation("Summarize failed")
            return

        def work():
            return subprocess.run(
                [gemini_bin],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=40,
                env=self.supervisor.subprocess_env(),
            )

        def on_result(result):
            if result.returncode != 0:
                QtWidgets.QMessageBox.critical(self, "Gemini Error", result.stderr.strip() or result.stdout.strip() or "Gemini CLI error.")
                self.show_error_banner("Gemini error")
                self.finish_operation("Summarize failed")
                return
            text_out = result.stdout.strip() or "No summary returned."
            self.summary_view.setPlainText(text_out)
            self.glitch(self.summary_view)
            self.finish_operation("Summary complete")

        def on_error(errmsg):
            QtWidgets.QMessageBox.critical(self, "Gemini Error", errmsg)
            self.show_error_banner(errmsg)
            self.finish_operation("Summarize failed")

        self.run_in_background(work, on_result, on_error)

    def build_summary_prompt(self, name, path):
        structure_lines = []
        content_lines = []
        total_chars = 0
        max_chars = 20000
        max_file_size = 512 * 1024
        for root, dirs, files in os.walk(path):
            rel_root = os.path.relpath(root, path)
            rel_root = "." if rel_root == "." else rel_root
            structure_lines.append(rel_root + "/")
            dirs.sort()
            files.sort()
            for fname in files:
                if fname == PROJECT_MANIFEST:
                    continue
                structure_lines.append(f"  {fname}")
                fpath = os.path.join(root, fname)
                try:
                    size = os.path.getsize(fpath)
                    if size > max_file_size:
                        continue
                    with open(fpath, "rb") as fh:
                        head = fh.read(2048)
                        if b"\0" in head:
                            continue
                        rest = head + fh.read(max_file_size - len(head))
                    text = rest.decode("utf-8", errors="ignore")
                except Exception:
                    continue
                if total_chars + len(text) > max_chars:
                    continue
                total_chars += len(text)
                rel_path = os.path.relpath(fpath, path)
                content_lines.append(f"\n[{rel_path}]\n{text}")
        structure = "\n".join(structure_lines)
        contents = "".join(content_lines)
        prompt = (
            f"Summarize this project in one paragraph. Explain what it is, what it appears to do, and its state.\n"
            f"Project: {name}\n"
            f"Directory structure:\n{structure}\n"
            f"File contents (text-only, truncated):\n{contents}\n"
        )
        return prompt

    def _task_prompt_path(self):
        custom = self.settings.get("llm", {}).get("task_prompt_path") if hasattr(self, "settings") else None
        if custom:
            try:
                return Path(custom).expanduser()
            except Exception:
                return DEFAULT_TASK_PROMPT
        return DEFAULT_TASK_PROMPT

    def _resolve_overview_path(self, project_path):
        configured = self.settings.get("projects", {}).get("overview_file") if hasattr(self, "settings") else None
        candidates = []
        if configured:
            candidates.append(configured)
        candidates.extend(DEFAULT_OVERVIEW_FILES)
        for fname in candidates:
            if not fname:
                continue
            candidate = os.path.join(project_path, fname)
            if os.path.isfile(candidate):
                return candidate
        return None

    def _extract_json_block(self, text):
        try:
            return json.loads(text)
        except Exception:
            pass
        try:
            start = text.index("{")
            end = text.rindex("}")
            if start < end:
                snippet = text[start : end + 1]
                return json.loads(snippet)
        except Exception:
            pass
        raise ValueError("Response was not valid JSON.")

    def _validate_decomposition_schema(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("LLM response is not a JSON object.")
        phases = payload.get("phases")
        if not phases or not isinstance(phases, list):
            raise ValueError("Missing 'phases' array in LLM response.")
        task_count = 0
        for phase in phases:
            if not isinstance(phase, dict):
                raise ValueError("Invalid phase entry.")
            if "operations" not in phase or not isinstance(phase["operations"], list):
                raise ValueError(f"Phase {phase.get('id','?')} missing operations.")
            for op in phase["operations"]:
                if not isinstance(op, dict):
                    raise ValueError("Invalid operation entry.")
                if "functions" not in op or not isinstance(op["functions"], list):
                    raise ValueError(f"Operation {op.get('id','?')} missing functions.")
                for func in op["functions"]:
                    if not isinstance(func, dict):
                        raise ValueError("Invalid function entry.")
                    if "jobs" not in func or not isinstance(func["jobs"], list):
                        raise ValueError(f"Function {func.get('id','?')} missing jobs.")
                    for job in func["jobs"]:
                        if not isinstance(job, dict):
                            raise ValueError("Invalid job entry.")
                        tasks = job.get("tasks")
                        if not tasks or not isinstance(tasks, list):
                            raise ValueError(f"Job {job.get('id','?')} missing tasks.")
                        for task in tasks:
                            if not isinstance(task, dict):
                                raise ValueError("Invalid task entry.")
                            desc = task.get("description")
                            if not desc or not isinstance(desc, str):
                                raise ValueError(f"Task {task.get('id','?')} missing description.")
                            task_count += 1
        if task_count == 0:
            raise ValueError("LLM response contained no tasks.")
        return task_count

    def _decomposition_to_tasks_payload(self, payload, project_name):
        lists = []
        tasks = []
        phase_map = {}
        for idx, phase in enumerate(payload.get("phases", []), start=1):
            phase_id = str(phase.get("id") or f"PHASE-{idx}")
            list_entry = {
                "id": phase_id,
                "name": f"{phase_id} {phase.get('name','')}".strip(),
                "scope": "project",
                "project": project_name,
            }
            lists.append(list_entry)
            phase_map[phase_id] = list_entry
            for op in phase.get("operations", []):
                op_name = op.get("name") or op.get("id")
                for func in op.get("functions", []):
                    func_name = func.get("name") or func.get("id")
                    for job in func.get("jobs", []):
                        job_name = job.get("name") or job.get("id")
                        for task in job.get("tasks", []):
                            task_id = str(task.get("id") or f"TASK-T{len(tasks)+1}")
                            desc = task.get("description", "").strip()
                            title = f"{task_id} {desc}" if desc else task_id
                            deps = task.get("dependencies") or []
                            inputs = task.get("inputs") or []
                            outputs = task.get("outputs") or []
                            failures = task.get("failure_modes") or []
                            notes_parts = []
                            if op_name:
                                notes_parts.append(f"Operation: {op_name}")
                            if func_name:
                                notes_parts.append(f"Function: {func_name}")
                            if job_name:
                                notes_parts.append(f"Job: {job_name}")
                            if deps:
                                notes_parts.append(f"Dependencies: {', '.join(map(str, deps))}")
                            if inputs:
                                notes_parts.append(f"Inputs: {', '.join(map(str, inputs))}")
                            if outputs:
                                notes_parts.append(f"Outputs: {', '.join(map(str, outputs))}")
                            if failures:
                                notes_parts.append(f"Failure Modes: {', '.join(map(str, failures))}")
                            tasks.append(
                                {
                                    "id": task_id,
                                    "list_id": phase_id,
                                    "title": title,
                                    "notes": "\n".join(notes_parts),
                                    "project": project_name,
                                    "status": "pending",
                                    "priority": 1 if task.get("priority") else 0,
                                }
                            )
        return {"lists": lists, "tasks": tasks}

    def generate_todo_from_prompt(self):
        project_path, project = self.resolve_project_path(require_focus_or_selection=True, prefer_canonical=True)
        if not project_path or not project:
            return
        if not os.path.isdir(project_path):
            QtWidgets.QMessageBox.critical(self, "Missing Path", f"{project_path} does not exist.")
            self.show_error_banner("Project path missing")
            self.log_debug("ERRORS", {"source": "FILESYSTEM", "message": f"Missing project path {project_path}"})
            return
        overview_path = self._resolve_overview_path(project_path)
        if not overview_path:
            QtWidgets.QMessageBox.critical(
                self,
                "Overview Missing",
                f"No project overview found. Expected one of {', '.join(DEFAULT_OVERVIEW_FILES)} in {project_path}",
            )
            self.show_error_banner("Project overview not found")
            return
        try:
            overview_text = Path(overview_path).read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Read Error", f"Could not read overview: {exc}")
            self.show_error_banner("Failed to read overview")
            return
        if not overview_text.strip():
            QtWidgets.QMessageBox.critical(self, "Empty Overview", "The project overview file is empty.")
            self.show_error_banner("Empty overview")
            return
        prompt_path = self._task_prompt_path()
        if not prompt_path.exists():
            QtWidgets.QMessageBox.critical(
                self,
                "Prompt Missing",
                f"Prompt file not found at {prompt_path}. Configure a valid .prompt file.",
            )
            self.show_error_banner("Prompt file missing")
            return
        try:
            prompt_text = prompt_path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Prompt Error", f"Could not read prompt file: {exc}")
            self.show_error_banner("Prompt read failure")
            return
        if not prompt_text.strip():
            QtWidgets.QMessageBox.critical(self, "Prompt Error", "Prompt file is empty.")
            self.show_error_banner("Prompt missing content")
            return
        self.log_debug(
            "LLM_EXECUTION",
            {"prompt_file": str(prompt_path), "overview_path": overview_path, "project": project, "status": "queued"},
        )
        self.generate_todo_btn.setEnabled(False)
        self.show_operation("Generating To-Do list...", state="Executing")

        gemini_bin = self._resolve_gemini_cmd()
        if not gemini_bin:
            QtWidgets.QMessageBox.critical(self, "Gemini Error", "Gemini CLI not found or not executable.")
            self.finish_operation("To-Do generation failed")
            return
        if not self._gemini_authenticated():
            QtWidgets.QMessageBox.critical(self, "Gemini Error", "Gemini is not authenticated. Interactive login is disabled in GUI mode.")
            self.finish_operation("To-Do generation failed")
            return

        payload = (
            prompt_text.strip()
            + "\n\nPROJECT_NAME: "
            + project
            + "\nPROJECT OVERVIEW (Markdown):\n"
            + overview_text.strip()
        )

        def work():
            return subprocess.run(
                [gemini_bin],
                input=payload,
                capture_output=True,
                text=True,
                timeout=90,
                env=self.supervisor.subprocess_env(),
            )

        def on_result(result):
            self.generate_todo_btn.setEnabled(True)
            if result.returncode != 0:
                errmsg = result.stderr.strip() or result.stdout.strip() or "LLM command failed."
                QtWidgets.QMessageBox.critical(self, "LLM Error", errmsg)
                self.show_error_banner(errmsg)
                self.log_debug("LLM_EXECUTION", {"status": "error", "stderr": errmsg, "returncode": result.returncode})
                self.log_debug("ERRORS", {"source": "LLM", "message": errmsg})
                self.finish_operation("To-Do generation failed")
                return
            raw = result.stdout.strip()
            try:
                decomposition = self._extract_json_block(raw)
                task_count = self._validate_decomposition_schema(decomposition)
            except Exception as exc:  # noqa: BLE001
                QtWidgets.QMessageBox.critical(self, "Response Error", str(exc))
                self.show_error_banner(str(exc))
                self.log_debug("LLM_EXECUTION", {"status": "error", "message": str(exc), "response_preview": raw[:200]})
                self.log_debug("ERRORS", {"source": "LLM", "message": str(exc)})
                self.finish_operation("Invalid JSON response")
                return
            self.log_debug(
                "LLM_EXECUTION",
                {
                    "prompt_file": str(prompt_path),
                    "overview_path": overview_path,
                    "status": "parsed",
                    "response_valid_json": True,
                    "tasks_detected": task_count,
                },
            )
            try:
                payload = self._decomposition_to_tasks_payload(decomposition, project)
                if not payload["tasks"]:
                    raise ValueError("No tasks found after conversion.")
                fd, tmp_path = tempfile.mkstemp(suffix=".json")
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2)
                try:
                    self.store.import_json(tmp_path, mode="audit")
                finally:
                    pass
                target_path = os.path.join(project_path, ".tasks.json")
                shutil.move(tmp_path, target_path)
                self.store.import_json(target_path, mode="strict")
            except Exception as exc:  # noqa: BLE001
                QtWidgets.QMessageBox.critical(self, "Import Error", str(exc))
                self.show_error_banner(str(exc))
                try:
                    if "tmp_path" in locals() and os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    if "target_path" in locals() and os.path.exists(target_path):
                        os.remove(target_path)
                except Exception:
                    pass
                self.log_debug("ERRORS", {"source": "TASK_IMPORT", "message": str(exc)})
                self.finish_operation("To-Do generation failed")
                return
            self.log_debug(
                "TASKS",
                {
                    "tasks_detected": len(payload["tasks"]),
                    "lists_detected": len(payload["lists"]),
                    "import_path": target_path,
                    "project": project,
                },
            )
            self.log_debug(
                "FILESYSTEM",
                {
                    "prompt_file": str(prompt_path),
                    "overview_path": overview_path,
                    "tasks_json": target_path,
                },
            )
            self.populate_lists()
            self.load_tasks()
            self.update_project_status_from_tasks(project)
            QtWidgets.QMessageBox.information(
                self,
                "To-Do Generated",
                f"Imported {len(payload['tasks'])} tasks from LLM output into {project}/.tasks.json",
            )
            self.finish_operation("To-Do list created")

        def on_error(errmsg):
            self.generate_todo_btn.setEnabled(True)
            QtWidgets.QMessageBox.critical(self, "LLM Error", errmsg)
            self.show_error_banner(errmsg)
            self.log_debug("LLM_EXECUTION", {"status": "error", "message": errmsg})
            self.log_debug("ERRORS", {"source": "LLM", "message": errmsg})
            self.finish_operation("To-Do generation failed")

        self.log_debug(
            "LLM_EXECUTION",
            {
                "status": "running",
                "prompt_file": str(prompt_path),
                "overview_path": overview_path,
                "tokens_sent_est": len(payload.split()),
            },
        )
        self.run_in_background(work, on_result, on_error)

    # ---- AutoGIT ----
    def run_autogit_init_for_path(self, path):
        if not self.autogit.available():
            QtWidgets.QMessageBox.warning(self, "AutoGIT Missing", "AutoGIT executable not found. Set AUTO_GIT_BIN or install AutoGIT.")
            return
        self.show_operation("Initializing version control...", state="Executing")
        env = self.git_env()
        pre = self.autogit.ensure_git_repo(path, env=env)
        if pre.returncode != 0 and self.autogit.is_dubious_error(pre):
            if self.autogit.add_safe_directory(path, reason="Autogit init ensure repo", env=env):
                pre = self.autogit.ensure_git_repo(path, env=env)
        if pre.returncode != 0:
            self.display_autogit_result("Init git", pre)
            self.show_error_banner("git init failed")
            self.finish_operation("VCS init failed")
            return
        result = self.autogit_with_safe_retry(lambda: self.autogit.init_project(path, env=env), path, "Autogit init", env=env)
        self.display_autogit_result("Init", result)
        self.update_git_status_label(path)
        self.finish_operation("VCS init complete")
        try:
            proj_name = os.path.basename(path.rstrip("/"))
            self.log_audit("autogit_init", proj_name, "success" if result.returncode == 0 else "failed")
        except Exception:
            pass

    def autogit_init(self):
        path, proj = self.resolve_project_path(prefer_canonical=True)
        if not path:
            return
        self.run_autogit_init_for_path(path)

    def _auto_commit_project(self, proj, path, env=None, manual=False):
        if not proj or not path or not os.path.isdir(path):
            return
        if not self._ui_alive(self):
            return
        env = env or self.git_env()

        def work():
            pre = self.autogit.ensure_git_repo(path, env=env)
            if pre.returncode != 0 and self.autogit.is_dubious_error(pre):
                if self.autogit.add_safe_directory(path, reason="autocommit ensure repo", env=env):
                    pre = self.autogit.ensure_git_repo(path, env=env)
            if pre.returncode != 0:
                return False, "git init failed", pre.stderr
            divergence = self.git_divergence(path, env=env)
            if divergence and divergence.get("behind", 0) > 0:
                return False, "remote ahead", f"Remote has {divergence['behind']} commits ahead of local; pull/rebase first."
            status = subprocess.run(["git", "-C", path, "status", "--porcelain"], capture_output=True, text=True, env=env)
            if status.returncode != 0:
                return False, "git status failed", status.stderr
            if not status.stdout.strip():
                return True, "clean", ""
            add = subprocess.run(["git", "-C", path, "add", "-A"], capture_output=True, text=True, env=env)
            if add.returncode != 0:
                return False, "git add failed", add.stderr
            msg = f"{'Manual' if manual else 'Auto'} commit {now_str()}"
            commit = subprocess.run(["git", "-C", path, "commit", "-m", msg], capture_output=True, text=True, env=env)
            if commit.returncode != 0:
                return False, "git commit failed", commit.stderr
            ok, msg_remote = self.ensure_remote_repo(proj, dry_run=False)
            if not ok:
                return False, msg_remote, ""
            push = subprocess.run(["git", "-C", path, "push", "-u", "origin", "main"], capture_output=True, text=True, env=env)
            if push.returncode != 0:
                return False, "git push failed", push.stderr or push.stdout
            return True, "pushed", ""

        def on_result(res):
            ok, msg, stderr = res
            if not ok:
                if manual:
                    QtWidgets.QMessageBox.critical(self, "Auto Commit", msg)
                self.log_debug("VERSIONING", {"autocommit": "failed", "project": proj, "message": msg, "stderr": stderr})
                self.finish_operation("Auto commit failed" if manual else "Auto commit idle")
                return
            if msg == "clean":
                if manual:
                    QtWidgets.QMessageBox.information(self, "Auto Commit", "No changes to commit.")
                self.finish_operation("Auto commit complete")
                return
            self.update_manifest_fields(proj, last_known_commit=self.last_commit_hash(path))
            self.refresh_health_panel()
            self.log_audit("autogit_commit", proj, "success")
            if manual:
                self.finish_operation("Commit complete")
            self.log_debug("VERSIONING", {"autocommit": "success", "project": proj})

        def on_error(err):
            if manual:
                QtWidgets.QMessageBox.critical(self, "Auto Commit", str(err))
            self.log_debug("VERSIONING", {"autocommit": "error", "project": proj, "error": str(err)})
            if manual:
                self.finish_operation("Auto commit failed")

        if manual:
            self.show_operation("Running commit...", state="Executing")
        self.run_in_background(work, on_result, on_error)

    def autogit_commit(self):
        path, proj = self.resolve_project_path(prefer_canonical=True)
        if not path:
            return
        # defer to event loop to avoid re-entrant state transitions from direct signal handlers
        self.request_ui_mutation("autogit_commit", self._autogit_commit_safe, proj, path)

    def _autogit_commit_safe(self, proj, path):
        if not self._ui_alive() or self._state_transition_active:
            self.log_debug("STABILITY", {"mutation_deferred": "autogit_commit", "reason": "busy"})
            self.request_ui_mutation("autogit_commit_retry", self._autogit_commit_safe, proj, path)
            return
        env = self.git_env()
        self._auto_commit_project(proj, path, env=env, manual=True)

    def _on_version_selection_changed(self):
        if not self._ui_alive(self.version_list):
            return
        enabled = self.version_list.currentItem() is not None and self.auto_commit_toggle.isEnabled()
        self._set_enabled_safely(self.revert_version_btn, enabled)

    def _on_repo_overview_toggled(self, collapsed):
        self.set_collapsible_state("repo-overview", collapsed)
        if not collapsed:
            self.load_repository_overview()

    def _format_repo_timestamp(self, value):
        if not value:
            return "-"
        try:
            if value.endswith("Z"):
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(value)
            local_dt = dt.astimezone()
            return local_dt.strftime("%b %d %I:%M %p")
        except Exception:
            return value

    def _set_repo_status(self, message, *, error=False, loading=False, cached=False):
        if not hasattr(self, "repo_status_label"):
            return
        color = "#2e9b8f"
        if error:
            color = "#d14b4b"
        elif loading:
            color = "#8ad0ff"
        self.repo_status_label.setText(f"{message}{' (cached)' if cached else ''}")
        self.repo_status_label.setStyleSheet(f"color: {color};")

    def _populate_repo_table(self, entries: list[dict], cached=False):
        if not hasattr(self, "repo_table"):
            return
        self.repo_table.setRowCount(len(entries))
        base_bg = QtGui.QColor("#0f1626")
        for row, entry in enumerate(entries):
            name_item = QtWidgets.QTableWidgetItem(entry.get("name", ""))
            branches = ", ".join(entry.get("branches") or [])
            branch_item = QtWidgets.QTableWidgetItem(branches or "-")
            active_item = QtWidgets.QTableWidgetItem(entry.get("default", ""))
            updated_item = QtWidgets.QTableWidgetItem(self._format_repo_timestamp(entry.get("updated")))
            visibility = "PRIVATE" if entry.get("private") else "PUBLIC"
            vis_item = QtWidgets.QTableWidgetItem(visibility)
            vis_color = QtGui.QColor("#2e9b8f") if entry.get("private") else QtGui.QColor("#d14b4b")
            vis_item.setForeground(vis_color)
            for itm in (name_item, branch_item, active_item, updated_item, vis_item):
                itm.setFlags(qt_no_edit(itm.flags()))
                itm.setBackground(base_bg)
            self.repo_table.setItem(row, 0, name_item)
            self.repo_table.setItem(row, 1, branch_item)
            self.repo_table.setItem(row, 2, active_item)
            self.repo_table.setItem(row, 3, updated_item)
            self.repo_table.setItem(row, 4, vis_item)
        status_msg = "No repositories found." if not entries else f"Loaded {len(entries)} repositories."
        self._set_repo_status(status_msg, cached=cached)

    def load_repository_overview(self, force=False):
        if self.repo_fetching:
            return
        if self.repo_cache is not None and not force:
            self._populate_repo_table(self.repo_cache, cached=True)
            return
        headers, method_used = self.build_github_headers()
        if not headers:
            self._set_repo_status("GitHub credentials missing; add and verify in Settings.", error=True)
            return
        self.repo_fetching = True
        self._set_repo_status("Loading repositories...", loading=True)

        def work():
            repos_url = "https://api.github.com/user/repos?per_page=100"
            req = urllib.request.Request(repos_url, headers=headers, method="GET")
            entries = []
            with urllib.request.urlopen(req, timeout=20) as resp:
                repos = json.load(resp)
            for repo in repos:
                name = repo.get("name") or ""
                owner = (repo.get("owner") or {}).get("login") or ""
                private = bool(repo.get("private"))
                default_branch = repo.get("default_branch") or ""
                updated = repo.get("updated_at") or repo.get("pushed_at") or ""
                branches = []
                branch_url_template = repo.get("branches_url") or ""
                if branch_url_template and "{" in branch_url_template:
                    branch_url = branch_url_template.split("{", 1)[0]
                else:
                    branch_url = branch_url_template or f"https://api.github.com/repos/{owner}/{name}/branches"
                branch_url = f"{branch_url}?per_page=100" if "?" not in branch_url else branch_url
                try:
                    breq = urllib.request.Request(branch_url, headers=headers, method="GET")
                    with urllib.request.urlopen(breq, timeout=15) as bresp:
                        branch_data = json.load(bresp)
                        if isinstance(branch_data, list):
                            branches = [b.get("name", "") for b in branch_data if isinstance(b, dict) and b.get("name")]
                except Exception:
                    branches = branches or []
                entries.append(
                    {
                        "name": name,
                        "owner": owner,
                        "branches": branches,
                        "default": default_branch,
                        "updated": updated,
                        "private": private,
                    }
                )
            return entries

        def on_result(entries):
            self.repo_fetching = False
            self.repo_cache = entries or []
            self.repo_cache_time = datetime.now()
            self._populate_repo_table(self.repo_cache)

        def on_error(err):
            self.repo_fetching = False
            self.repo_cache = None
            self._set_repo_status(f"Failed to load repositories: {err}", error=True)

        self.run_in_background(work, on_result, on_error)

    def autogit_status(self):
        path, proj = self.resolve_project_path(prefer_canonical=True)
        if not path:
            return
        self.show_operation("Checking git status...", state="Executing")
        env = self.git_env()
        pre = self.autogit.ensure_git_repo(path, env=env)
        if pre.returncode != 0 and self.autogit.is_dubious_error(pre):
            if self.autogit.add_safe_directory(path, reason="Git status ensure repo", env=env):
                pre = self.autogit.ensure_git_repo(path, env=env)
        if pre.returncode != 0:
            self.display_autogit_result("Init git", pre)
            self.show_error_banner("git init failed")
            self.finish_operation("Git status failed")
            return
        result = self.git_with_safe_retry(lambda: self.autogit.git_status(path, env=env), path, "Git status", env=env)
        if result.returncode != 0:
            self.display_autogit_result("Status", result)
            QtWidgets.QMessageBox.warning(self, "Git Status", result.stderr or "Git status failed.")
            self.finish_operation("Git status failed")
            return
        status = result.stdout.strip() or "Clean working tree."
        self.vcs_output.setPlainText(status)
        self.update_git_status_label(path, status)
        self.finish_operation("Git status complete")
        self.glitch(self.vcs_output)
        self.log_debug(
            "VERSIONING",
            {
                "project": proj,
                "git_status": status[:200],
                "returncode": result.returncode,
            },
        )

    def display_autogit_result(self, label, result):
        stdout = result.stdout.strip() if hasattr(result, "stdout") else ""
        stderr = result.stderr.strip() if hasattr(result, "stderr") else ""
        text = f"[{label}] exit={result.returncode}\n"
        if stdout:
            text += f"STDOUT:\n{stdout}\n"
        if stderr:
            text += f"STDERR:\n{stderr}\n"
        self.vcs_output.setPlainText(text)
        self.glitch(self.vcs_output)
        if result.returncode != 0:
            self.show_error_banner(f"{label} failed")

    def prompt_autogit_for_task(self, task):
        if not self.autogit.available():
            return
        project = task.get("project") or self.active_project
        if not project:
            return
        # ensure focused project is the one we operate on
        if self.active_project and self.active_project != project:
            return
        path, _ = self.resolve_project_path(require_focus_or_selection=False, prefer_canonical=True)
        reply = QtWidgets.QMessageBox.question(
            self,
            "AutoGIT Commit?",
            f"Task '{task['title']}' completed.\nRun an AutoGIT commit for project '{project}'?",
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return
        env = self.git_env()
        if not self.autogit.is_git_repo(path, env=env):
            pre = self.autogit.ensure_git_repo(path, env=env)
            if pre.returncode != 0 and self.autogit.is_dubious_error(pre):
                if self.autogit.add_safe_directory(path, reason="Autogit task ensure repo", env=env):
                    pre = self.autogit.ensure_git_repo(path, env=env)
            if pre.returncode != 0:
                self.display_autogit_result("Init git", pre)
                self.show_error_banner("git init failed")
                return
        result = self.autogit_with_safe_retry(lambda: self.autogit.commit_project(path, env=env), path, "Autogit task commit", env=env)
        self.display_autogit_result("Task Commit", result)

    def update_git_status_label(self, path, raw_status=""):
        env = self.git_env()
        if not self.autogit.is_git_repo(path, env=env):
            self.autogit_status_label.setText("Git: Uninitialized")
            self.autogit_status_label.setStyleSheet("color: #d2a446;")
            return
        status = raw_status.strip() if raw_status else ""
        if not status:
            self.autogit_status_label.setText("Git: Clean")
            self.autogit_status_label.setStyleSheet("color: #2e9b8f;")
        else:
            self.autogit_status_label.setText("Git: Modified")
            self.autogit_status_label.setStyleSheet("color: #d2a446;")
        proj_name = os.path.basename(path.rstrip("/"))
        if proj_name:
            commit_hash = self.last_commit_hash(path)
            if commit_hash:
                self.update_manifest_fields(proj_name, last_known_commit=commit_hash)

    def fetch_versions(self):
        proj = self.selected_project
        if not proj:
            return
        if not self.credentials_verified:
            QtWidgets.QMessageBox.warning(self, "Credentials", "Verify credentials before fetching versions.")
            return
        headers, method_used = self.build_github_headers()
        if not headers:
            QtWidgets.QMessageBox.warning(self, "Credentials", "Set GitHub credentials in Settings.")
            return
        self.show_operation("Fetching versions...", state="Executing")

        username, _, _ = self.get_credentials()

        def work():
            url = f"https://api.github.com/repos/{username}/{proj}/commits"
            req = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    code = resp.getcode()
                    data = json.load(resp)
                    return True, code, data, None
            except urllib.error.HTTPError as e:
                try:
                    err_body = e.read().decode("utf-8")
                except Exception:
                    err_body = str(e)
                return False, e.code, None, err_body
            except Exception as exc:  # noqa: BLE001
                return False, None, None, str(exc)

        def on_result(payload):
            ok, code, data, err = payload
            if not ok:
                if code == 409 and err and "empty" in err.lower():
                    # Empty repository: inform user but do not treat as hard failure
                    self.version_list.clear()
                    self.version_list.addItem("Repository is empty (no commits yet).")
                    self._set_enabled_safely(self.revert_version_btn, False)
                    info_msg = "Repository is empty; no commits to list."
                    QtWidgets.QMessageBox.information(self, "Fetch Versions", info_msg)
                    self.log_vcs(f"[fetch] {info_msg}")
                    self.finish_operation("Fetch complete (empty repo)")
                    return
                msg = f"Fetch failed (HTTP {code}): {err}"
                QtWidgets.QMessageBox.critical(self, "Fetch Versions", msg)
                self.log_vcs(f"[fetch] {msg}")
                self.finish_operation("Fetch failed")
                return
            self.version_list.clear()
            for entry in data:
                sha = entry.get("sha", "")[:8]
                msg = entry.get("commit", {}).get("message", "").split("\n")[0]
                author = entry.get("commit", {}).get("author", {}).get("name", "")
                date_str = entry.get("commit", {}).get("author", {}).get("date", "")
                item = QtWidgets.QListWidgetItem(f"{sha} | {msg} | {author} | {date_str}")
                item.setData(QtCore.Qt.UserRole, entry.get("sha", ""))
                self.version_list.addItem(item)
            if self.version_list.count() == 0:
                self.version_list.addItem("No commits found.")
            self.finish_operation("Versions fetched")
            self._set_enabled_safely(self.revert_version_btn, self.version_list.count() > 0 and self.version_list.item(0).data(QtCore.Qt.UserRole) is not None)
            self.log_vcs(f"[fetch] versions fetched via {method_used}")

        def on_error(err):
            QtWidgets.QMessageBox.critical(self, "Fetch Versions", f"Failed to fetch versions: {err}")
            self.finish_operation("Fetch failed")
            self.log_vcs(f"[fetch] error: {err}")

        self.run_in_background(work, on_result, on_error)

    def revert_version(self):
        proj = self.selected_project
        if not proj:
            return
        item = self.version_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Select Version", "Select a version to revert.")
            return
        sha = item.data(QtCore.Qt.UserRole)
        if self.active_project == proj:
            QtWidgets.QMessageBox.warning(self, "Revert Blocked", "Unfocus the project before reverting.")
            return
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Revert",
            f"Revert project '{proj}' to commit {sha}?\nThis will replace local contents.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return
        self.start_operation("revert", target=proj, dry_run=self.dry_run_checkbox.isChecked())
        if self.dry_run_checkbox.isChecked():
            QtWidgets.QMessageBox.information(self, "Dry Run", f"[Dry run] Would reset {proj} to {sha}")
            self.finalize_operation("rolled_back")
            return
        self.show_operation("Reverting project...", state="Executing")
        self.set_operation_state("executing")
        path = os.path.join(PROJECT_ROOT, proj)

        def work():
            env = self.git_env()
            subprocess.run(["git", "-C", path, "fetch", "origin"], capture_output=True, text=True, env=env)
            reset = subprocess.run(["git", "-C", path, "reset", "--hard", sha], capture_output=True, text=True, env=env)
            return reset

        def on_result(res):
            if res.returncode != 0:
                self.display_autogit_result("Revert", res)
                self.finish_operation("Revert failed")
                self.finalize_operation("failed")
                return
            self.finish_operation("Revert complete")
            self.refresh_projects()
            # optional auto commit to record reversion
            self.autogit_commit()
            self.update_manifest_fields(proj, last_known_commit=self.last_commit_hash(path))
            self.refresh_health_panel()
            self.finalize_operation("committed")

        def on_error(err):
            QtWidgets.QMessageBox.critical(self, "Revert", f"Revert failed: {err}")
            self.finish_operation("Revert failed")
            self.finalize_operation("failed")

        self.run_in_background(work, on_result, on_error)

    def apply_interface_settings(self):
        # simple dynamic tweaks; avoid heavy theme changes
        theme = self.theme_combo.currentText() if hasattr(self, "theme_combo") else "dark"
        accent = self.accent_combo.currentText() if hasattr(self, "accent_combo") else "cyan"
        density = self.density_combo.currentText() if hasattr(self, "density_combo") else "normal"
        self._apply_theme(theme=theme, density=density, scale_factor=self.scale_factor)
        dot_size = max(10, int(14 * getattr(self, "scale_factor", 1.0)))
        accent_key = accent if accent in ACCENTS else "cyan"
        self.accent_primary = ACCENTS[accent_key]["primary"]
        self.accent_glow = ACCENTS[accent_key]["glow"]
        dot_color = self.accent_primary
        self.state_dot.setFixedSize(dot_size, dot_size)
        self.state_dot.setStyleSheet(f"background-color: {dot_color}; border-radius: {max(5, dot_size//2)}px;")
        if hasattr(self, "verbosity_checkbox") and not self.verbosity_checkbox.isChecked():
            self.state_msg_label.setVisible(False)
        else:
            self.state_msg_label.setVisible(True)
        # persist interface settings
        self.settings.setdefault("interface", {})
        self.settings["interface"].update(
            {
                "theme": theme,
                "accent": accent,
                "animations": self.anim_checkbox.isChecked() if hasattr(self, "anim_checkbox") else True,
                "verbosity": self.verbosity_checkbox.isChecked() if hasattr(self, "verbosity_checkbox") else True,
                "audio_feedback": self.audio_checkbox.isChecked() if hasattr(self, "audio_checkbox") else True,
                "density": density,
                "ui_scale": int(getattr(self, "ui_scale", 100)),
                "wrap_mode": bool(getattr(self, "wrap_mode", False)),
                "spill_direction": getattr(self, "wrap_spill_direction", "horizontal"),
            }
        )
        self.save_settings()
        self.update_accent_usage()
        audio_enabled = self.audio_checkbox.isChecked() if hasattr(self, "audio_checkbox") else True
        self.sound_engine.enabled = bool(audio_enabled)
        if hasattr(self, "photon_terminal_widget"):
            self.photon_terminal_widget.set_animation_enabled(self.anim_checkbox.isChecked())
        self.update_identity_banner()
        self.log_debug(
            "SETTINGS",
            {
                "theme": theme,
                "accent": accent,
                "animations": self.anim_checkbox.isChecked() if hasattr(self, "anim_checkbox") else True,
                "verbosity": self.verbosity_checkbox.isChecked() if hasattr(self, "verbosity_checkbox") else True,
                "density": density,
                "ui_scale": int(getattr(self, "ui_scale", 100)),
            },
        )

    def apply_keybinds(self):
        edits = {
            "focus_project": self.key_edit_focus.keySequence().toString(),
            "new_task": self.key_edit_new_task.keySequence().toString(),
            "complete_task": self.key_edit_complete.keySequence().toString(),
            "commit": self.key_edit_commit.keySequence().toString(),
            "tab_prev": self.key_edit_tab_prev.keySequence().toString(),
            "tab_next": self.key_edit_tab_next.keySequence().toString(),
        }
        seqs = [v for v in edits.values() if v]
        if len(seqs) != len(set(seqs)):
            self.key_warning.setText("Conflicting key bindings detected.")
            return
        self.key_warning.setText("")
        self.keybinds.update(edits)
        # rebind shortcuts
        if hasattr(self, "shortcuts"):
            for name, shortcut in self.shortcuts.items():
                if name in self.keybinds:
                    shortcut.setKey(QtGui.QKeySequence(self.keybinds[name]))
        self.settings["controls"] = self.keybinds
        self.save_settings()

    def get_credentials(self):
        username = self.cred_username.text().strip() if hasattr(self, "cred_username") else ""
        password = self.cred_password.text().strip() if hasattr(self, "cred_password") else ""
        tokens = getattr(self, "api_tokens", []) if hasattr(self, "api_tokens") else []
        return username, password, tokens

    def _apply_git_auth_env(self):
        # Build a non-interactive auth environment for git and apply globally to subprocesses.
        username, password, tokens = self.get_credentials()
        token = tokens[0] if tokens else None
        askpass_path = None
        if token or password:
            content = f"#!/bin/sh\nexec echo {shlex.quote(token or password)}\n"
            fd, path = tempfile.mkstemp(prefix="git_askpass_", text=True)
            with os.fdopen(fd, "w") as fh:
                fh.write(content)
            os.chmod(path, 0o700)
            askpass_path = path
        self.git_askpass_path = askpass_path
        self.git_env_base = self.supervisor.subprocess_env()
        self.git_env_base["GIT_TERMINAL_PROMPT"] = "0"
        self.git_env_base["GCM_INTERACTIVE"] = "never"
        self.git_env_base["GIT_DISCOVERY_ACROSS_FILESYSTEM"] = "1"
        if askpass_path:
            self.git_env_base["GIT_ASKPASS"] = askpass_path
            os.environ["GIT_ASKPASS"] = askpass_path
        os.environ["GIT_TERMINAL_PROMPT"] = "0"
        os.environ["GCM_INTERACTIVE"] = "never"
        os.environ["GIT_DISCOVERY_ACROSS_FILESYSTEM"] = "1"

    def _git_auth_env(self):
        if hasattr(self, "git_env_base"):
            return self.git_env_base.copy()
        return self.supervisor.subprocess_env()

    def git_env(self, extra=None):
        base = self._git_auth_env()
        if extra:
            base.update(extra)
        return self.supervisor.subprocess_env(base)

    def git_divergence(self, path, env=None, branch=None):
        env = self.git_env(env or {})
        branch_cmd = subprocess.run(["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, env=env)
        branch_name = branch or (branch_cmd.stdout.strip() if branch_cmd.returncode == 0 else "main")
        fetch = subprocess.run(["git", "-C", path, "fetch", "--prune", "origin"], capture_output=True, text=True, env=env)
        if fetch.returncode != 0:
            return None
        cmp = subprocess.run(
            ["git", "-C", path, "rev-list", "--left-right", "--count", f"{branch_name}...origin/{branch_name}"],
            capture_output=True,
            text=True,
            env=env,
        )
        if cmp.returncode != 0:
            return None
        parts = cmp.stdout.strip().split()
        if len(parts) != 2:
            return None
        ahead_local, behind_remote = int(parts[0]), int(parts[1])
        return {"ahead": ahead_local, "behind": behind_remote, "branch": branch_name}

    # ---- Gemini credentials helpers ----
    def _load_gemini_settings(self):
        gem = self.settings.get("gemini", {})
        self.ai_enabled = bool(gem.get("ai_enabled", False))
        self.gemini_api_key = gem.get("api_key", "")
        self.gemini_email = gem.get("email", "")
        self.gemini_password = gem.get("password", "")
        self.gemini_verified = bool(gem.get("verified", False))

    def _save_gemini_settings(self):
        self.settings.setdefault("gemini", {})
        self.settings["gemini"]["ai_enabled"] = bool(getattr(self, "ai_enabled", False))
        self.settings["gemini"]["api_key"] = getattr(self, "gemini_api_key", "")
        self.settings["gemini"]["email"] = getattr(self, "gemini_email", "")
        self.settings["gemini"]["password"] = getattr(self, "gemini_password", "")
        self.settings["gemini"]["verified"] = bool(getattr(self, "gemini_verified", False))
        self.save_settings()

    def _gemini_ready(self):
        has_creds = bool(self.gemini_api_key or (self.gemini_email and self.gemini_password))
        return bool(self.ai_enabled and has_creds and self.gemini_verified)

    def _ensure_ai_toggle_ui(self):
        enabled = bool(self.ai_enabled and (self.gemini_api_key or (self.gemini_email and self.gemini_password)) and self.gemini_verified)
        if hasattr(self, "generate_todo_btn"):
            self.generate_todo_btn.setVisible(enabled)
            self.generate_todo_btn.setEnabled(enabled)
        if hasattr(self, "summarize_btn"):
            self.summarize_btn.setVisible(enabled)
            self.summarize_btn.setEnabled(enabled)
        if hasattr(self, "ai_toggle"):
            self.ai_toggle.blockSignals(True)
            self.ai_toggle.setChecked(bool(self.ai_enabled))
            self.ai_toggle.blockSignals(False)

    def _verify_gemini_credentials(self):
        has_api = bool(self.gemini_api_key)
        has_login = bool(self.gemini_email and self.gemini_password)
        if not (has_api or has_login):
            self.gemini_verified = False
            return False, "Missing Gemini credentials"
        gem_bin = self._resolve_gemini_cmd()
        if not gem_bin:
            self.gemini_verified = False
            return False, "Gemini CLI not found"
        env = self.supervisor.subprocess_env()
        if has_api:
            env["GEMINI_API_KEY"] = self.gemini_api_key
        if has_login:
            env["GEMINI_EMAIL"] = self.gemini_email
            env["GEMINI_PASSWORD"] = self.gemini_password
        cmd = [gem_bin, "--model", "gemini-pro", "--prompt", "OK", "--max-tokens", "1"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=20)
        except Exception as exc:  # noqa: BLE001
            self.gemini_verified = False
            self.log_debug("GEMINI_AUTH", {"ok": False, "error": str(exc)})
            try:
                self.event_bus.emit("GEMINI_AUTH", {"ok": False, "error": str(exc)})
            except Exception:
                pass
            return False, f"Gemini verification error: {exc}"
        stdout = res.stdout or ""
        stderr = res.stderr or ""
        rc = res.returncode
        ok = rc == 0 and "OK" in stdout
        if "auth" in stderr.lower() or "unauthorized" in stderr.lower():
            ok = False
        self.gemini_verified = bool(ok)
        self.ai_enabled = bool(ok and self.ai_enabled or ok)
        self._save_gemini_settings()
        self.log_debug("GEMINI_AUTH", {"ok": ok, "rc": rc, "stdout": stdout.strip(), "stderr": stderr.strip()})
        try:
            self.event_bus.emit("GEMINI_AUTH", {"ok": ok, "rc": rc, "stdout": stdout, "stderr": stderr})
        except Exception:
            pass
        if not ok:
            return False, f"Gemini authentication failed (rc={rc})"
        return True, "Gemini credentials verified"

    def build_github_headers(self):
        username, password, tokens = self.get_credentials()
        headers = {"Accept": "application/vnd.github+json"}
        method_used = "token" if tokens else "basic"
        if tokens:
            headers["Authorization"] = f"Bearer {tokens[0]}"
        elif username and password:
            basic = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {basic}"
        else:
            return None, None
        return headers, method_used

    def apply_loaded_settings(self):
        iface = self.settings.get("interface", {})
        if hasattr(self, "theme_combo"):
            self.theme_combo.setCurrentText(iface.get("theme", "dark"))
        if hasattr(self, "accent_combo"):
            self.accent_combo.setCurrentText(iface.get("accent", "cyan"))
        if hasattr(self, "anim_checkbox"):
            self.anim_checkbox.setChecked(iface.get("animations", True))
        if hasattr(self, "verbosity_checkbox"):
            self.verbosity_checkbox.setChecked(iface.get("verbosity", True))
        if hasattr(self, "audio_checkbox"):
            self.audio_checkbox.setChecked(iface.get("audio_feedback", True))
        if hasattr(self, "density_combo"):
            self.density_combo.setCurrentText(iface.get("density", "normal"))
        if hasattr(self, "ui_scale_slider"):
            scale_val = int(iface.get("ui_scale", getattr(self, "ui_scale", 100)))
            self.ui_scale_slider.blockSignals(True)
            self.ui_scale_slider.setValue(scale_val)
            self.ui_scale_slider.blockSignals(False)
            self.ui_scale = scale_val
            if hasattr(self, "ui_scale_value"):
                self.ui_scale_value.setText(f"{scale_val}%")
        self.wrap_spill_direction = iface.get("spill_direction", "horizontal")
        self.wrap_mode = bool(iface.get("wrap_mode", False)) if self.scale_factor > 1.0 else False
        self.update_wrap_mode(active=self.wrap_mode)
        if hasattr(self, "projects_splitter"):
            saved_sizes = self.load_splitter_state("projects_fs")
            if saved_sizes:
                try:
                    self.projects_splitter.setSizes([int(s) for s in saved_sizes])
                except Exception:
                    pass
        # controls
        if hasattr(self, "key_edit_focus"):
            self.key_edit_focus.setKeySequence(QtGui.QKeySequence(self.keybinds.get("focus_project", "Ctrl+Shift+F")))
            self.key_edit_new_task.setKeySequence(QtGui.QKeySequence(self.keybinds.get("new_task", "Ctrl+N")))
            self.key_edit_complete.setKeySequence(QtGui.QKeySequence(self.keybinds.get("complete_task", "Ctrl+D")))
            self.key_edit_commit.setKeySequence(QtGui.QKeySequence(self.keybinds.get("commit", "Ctrl+Shift+C")))
        self.log_debug(
            "SETTINGS",
            {
                "theme": iface.get("theme", "dark"),
                "accent": iface.get("accent", "cyan"),
                "animations": iface.get("animations", True),
                "verbosity": iface.get("verbosity", True),
                "density": iface.get("density", "normal"),
                "ui_scale": iface.get("ui_scale", getattr(self, "ui_scale", 100)),
            },
        )

    def apply_credentials_to_ui(self):
        if hasattr(self, "cred_username"):
            self.cred_username.setText(self.active_credentials.get("username", ""))
        if hasattr(self, "cred_password"):
            self.cred_password.setText(self.active_credentials.get("password", ""))
        # populate token list masked
        if hasattr(self, "token_list"):
            self.token_list.clear()
            for _ in self.api_tokens:
                item = QtWidgets.QListWidgetItem("•••••• (token)")
                item.setData(QtCore.Qt.UserRole, False)  # visibility flag
                self.token_list.addItem(item)
        if hasattr(self, "ai_toggle"):
            self.ai_toggle.setChecked(bool(self.ai_enabled))
        if hasattr(self, "gemini_api_key_edit"):
            self.gemini_api_key_edit.setText(self.gemini_api_key)
        if hasattr(self, "gemini_email_edit"):
            self.gemini_email_edit.setText(self.gemini_email)
        if hasattr(self, "gemini_password_edit"):
            self.gemini_password_edit.setText(self.gemini_password)
        self.credentials_verified = bool(self.active_credentials.get("verified", False))
        self.verified_user = self.active_credentials.get("username", "") if self.credentials_verified else ""
        self.refresh_credential_sets()

    def refresh_credential_sets(self):
        sets = self.credentials_store.get("sets", {})
        if hasattr(self, "cred_set_combo"):
            self.cred_set_combo.blockSignals(True)
            self.cred_set_combo.clear()
            for label in sets.keys():
                self.cred_set_combo.addItem(label)
            if self.selected_cred_label and self.selected_cred_label in sets:
                idx = self.cred_set_combo.findText(self.selected_cred_label)
                if idx >= 0:
                    self.cred_set_combo.setCurrentIndex(idx)
            self.cred_set_combo.blockSignals(False)
        if hasattr(self, "saved_creds_list"):
            self.saved_creds_list.clear()
            for label, entry in sets.items():
                status = "verified" if entry.get("verified") else "unverified"
                active = " (active)" if label == self.selected_cred_label else ""
                self.saved_creds_list.addItem(f"{label}: {status}{active}")
        if hasattr(self, "active_cred_label"):
            if self.selected_cred_label:
                status = "verified" if self.credentials_verified else "unverified"
                user = self.verified_user or self.active_credentials.get("username", "")
                suffix = f" as {user}" if user else ""
                self.active_cred_label.setText(f"Active: {self.selected_cred_label} ({status}{suffix})")
            else:
                self.active_cred_label.setText("Active: None")

    def save_current_credentials(self):
        label = self.cred_label.text().strip() or self.cred_username.text().strip()
        if not label:
            QtWidgets.QMessageBox.warning(self, "Label Required", "Provide a credential label or username.")
            return
        entry = {
            "username": self.cred_username.text().strip(),
            "password": self.cred_password.text(),
            "tokens": list(self.api_tokens),
            "verified": self.credentials_verified,
        }
        self.credentials_store.setdefault("sets", {})
        self.credentials_store["sets"][label] = entry
        self.credentials_store["selected"] = label
        self.selected_cred_label = label
        self.active_credentials = entry
        self.save_credentials()
        self.refresh_credential_sets()
        QtWidgets.QMessageBox.information(self, "Saved", f"Credentials saved for set '{label}'.")

    def switch_credential_set(self, label):
        sets = self.credentials_store.get("sets", {})
        if label in sets:
            self.selected_cred_label = label
            self.credentials_store["selected"] = label
            self.active_credentials = sets[label]
            self.api_tokens = list(self.active_credentials.get("tokens", []))
            self.credentials_verified = bool(self.active_credentials.get("verified", False))
            self.verified_user = self.active_credentials.get("username", "") if self.credentials_verified else ""
            self.save_credentials()
            if hasattr(self, "verify_status_label"):
                if self.credentials_verified:
                    user = self.verified_user or self.active_credentials.get("username", "")
                    suffix = f" as {user}" if user else ""
                    self.verify_status_label.setText(f"Verified{suffix}")
                    self.verify_status_label.setStyleSheet("color: #2e9b8f;")
                else:
                    self.verify_status_label.setText("Not verified")
                    self.verify_status_label.setStyleSheet("color: #d14b4b;")
            self.apply_credentials_to_ui()
            if self.active_project:
                self.update_manifest_fields(self.active_project, preferred_credentials=label)
            self.refresh_health_panel()

    def verify_credentials(self):
        username, password, tokens = self.get_credentials()
        self.verify_status_label.setText("Verifying...")
        self.verify_status_label.setStyleSheet("color: #8ad0ff;")
        if not username and not tokens:
            self.verify_status_label.setText("Missing credentials")
            self.verify_status_label.setStyleSheet("color: #d14b4b;")
            return
        self.show_operation("Verifying credentials...", state="Executing")

        def work():
            headers, method_used = self.build_github_headers()
            if not headers:
                raise ValueError("Missing credentials")
            req = urllib.request.Request("https://api.github.com/user", headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.load(resp), method_used

        def on_result(payload):
            data, method_used = payload
            login = data.get("login", "")
            self.verify_status_label.setText(f"Verified as {login} via {method_used}")
            self.verify_status_label.setStyleSheet("color: #2e9b8f;")
            self.finish_operation("Verify complete")
            self.credentials_verified = True
            self.verified_user = login
            # persist credentials on successful verify
            label = self.cred_label.text().strip() or username or "default"
            self.credentials_store.setdefault("sets", {})
            self.credentials_store["sets"][label] = {
                "username": username,
                "password": password,
                "tokens": list(tokens),
                "verified": True,
            }
            self.credentials_store["selected"] = label
            self.selected_cred_label = label
            self.active_credentials = self.credentials_store["sets"][label]
            self.save_credentials()
            self.refresh_credential_sets()
            self.log_vcs(f"[verify] success for user {login} using {method_used}")
            self.refresh_health_panel()

        def on_error(err):
            self.verify_status_label.setText(f"Verify failed: {err}")
            self.verify_status_label.setStyleSheet("color: #d14b4b;")
            self.finish_operation("Verify failed")
            self.log_vcs(f"[verify] failed: {err}")
            self.refresh_health_panel()

        self.run_in_background(work, on_result, on_error)

    def verify_gemini_credentials_ui(self):
        self.gemini_api_key = self.gemini_api_key_edit.text().strip() if hasattr(self, "gemini_api_key_edit") else self.gemini_api_key
        ok, msg = self._verify_gemini_credentials()
        if ok:
            QtWidgets.QMessageBox.information(self, "Gemini", msg)
            self._ensure_ai_toggle_ui()
        else:
            QtWidgets.QMessageBox.critical(self, "Gemini", msg)
            self.ai_enabled = False
            self.gemini_verified = False
            self._save_gemini_settings()
            self._ensure_ai_toggle_ui()

    def _on_ai_toggle_changed(self, state):
        self.ai_enabled = bool(state)
        if self.ai_enabled and not (self.gemini_api_key or (self.gemini_email and self.gemini_password)):
            QtWidgets.QMessageBox.warning(self, "Gemini", "Provide an API key or email/password before enabling AI.")
            self.ai_enabled = False
        if self.ai_enabled and not self.gemini_verified:
            ok, _ = self._verify_gemini_credentials()
            if not ok:
                self.ai_enabled = False
        self._save_gemini_settings()
        self._ensure_ai_toggle_ui()

    def _on_gemini_key_changed(self):
        self.gemini_api_key = self.gemini_api_key_edit.text().strip() if hasattr(self, "gemini_api_key_edit") else ""
        self.gemini_verified = False
        self._save_gemini_settings()
        self._ensure_ai_toggle_ui()

    def _on_gemini_email_changed(self):
        self.gemini_email = self.gemini_email_edit.text().strip() if hasattr(self, "gemini_email_edit") else ""
        self.gemini_verified = False
        self._save_gemini_settings()
        self._ensure_ai_toggle_ui()

    def _on_gemini_password_changed(self):
        self.gemini_password = self.gemini_password_edit.text().strip() if hasattr(self, "gemini_password_edit") else ""
        self.gemini_verified = False
        self._save_gemini_settings()
        self._ensure_ai_toggle_ui()

    def toggle_selected_token_visibility(self):
        item = self.token_list.currentItem()
        if not item:
            return
        idx = self.token_list.row(item)
        if idx < 0 or idx >= len(self.api_tokens):
            return
        visible = item.data(QtCore.Qt.UserRole) or False
        visible = not visible
        item.setData(QtCore.Qt.UserRole, visible)
        item.setText(self.api_tokens[idx] if visible else "•••••• (token)")
        item.setForeground(QtGui.QColor("#d2a446") if visible else QtGui.QColor("#d8f6ff"))

    # ---- Persistence helpers ----
    def _derive_key(self, salt, length):
        # Stable key derived from username + home path only, so it survives reboots.
        key_material = f"{getpass.getuser()}:{Path.home()}".encode("utf-8")
        return hashlib.pbkdf2_hmac("sha256", key_material, salt, 200000, dklen=length)

    def _encrypt(self, payload: bytes) -> str:
        salt = secrets.token_bytes(16)
        key = self._derive_key(salt, 32)
        # simple XOR keystream using derived key repeated
        cipher = bytes([b ^ key[i % len(key)] for i, b in enumerate(payload)])
        return base64.b64encode(salt + cipher).decode("utf-8")

    def _decrypt(self, payload_b64: str) -> bytes | None:
        try:
            raw = base64.b64decode(payload_b64)
            salt, cipher = raw[:16], raw[16:]
            key = self._derive_key(salt, 32)
            plain = bytes([b ^ key[i % len(key)] for i, b in enumerate(cipher)])
            return plain
        except Exception:
            return None

    def _resolve_gemini_cmd(self):
        cmd = GEMINI_CMD
        abs_cmd = _shutil.which(cmd)
        if not abs_cmd:
            return None
        if not os.access(abs_cmd, os.X_OK):
            return None
        return abs_cmd

    def _gemini_authenticated(self):
        has_creds = bool(self.gemini_api_key or (self.gemini_email and self.gemini_password))
        return bool(self.ai_enabled and self.gemini_verified and has_creds)

    def load_settings(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not SETTINGS_FILE.exists():
            return {}
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def save_settings(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
                json.dump(self.settings, fh, indent=2)
        except Exception:
            pass

    # Collapsible + splitter persistence
    def get_collapsible_state(self, key, default=False):
        return self.settings.get("collapsible_states", {}).get(key, default)

    def set_collapsible_state(self, key, collapsed):
        self.settings.setdefault("collapsible_states", {})[key] = collapsed
        self.save_settings()
        self.log_debug("SETTINGS", {"collapsible": key, "collapsed": collapsed})

    def save_splitter_state(self, key, sizes):
        self.settings.setdefault("splitters", {})[key] = sizes
        self.save_settings()

    def load_splitter_state(self, key):
        return self.settings.get("splitters", {}).get(key)

    def load_credentials(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CREDS_FILE.exists():
            return {}
        try:
            with open(CREDS_FILE, "r", encoding="utf-8") as fh:
                enc = fh.read().strip()
            plain = self._decrypt(enc)
            if not plain:
                return {}
            data = json.loads(plain.decode("utf-8"))
            gemini = data.get("gemini", {})
            self.gemini_api_key = gemini.get("api_key", "")
            self.gemini_email = gemini.get("email", "")
            self.gemini_password = gemini.get("password", "")
            self.gemini_verified = gemini.get("verified", False)
            # Migrate single-set format to multi-set
            if "sets" not in data:
                label = data.get("username", "default")
                data = {
                    "sets": {
                        label: {
                            "username": data.get("username", ""),
                            "password": data.get("password", ""),
                            "tokens": data.get("tokens", []),
                            "verified": data.get("verified", False),
                        }
                    },
                    "selected": label,
                }
            return data
        except Exception:
            return {}

    def save_credentials(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = self.credentials_store
        # persist gemini settings securely alongside credentials
        data["gemini"] = {
            "api_key": getattr(self, "gemini_api_key", ""),
            "email": getattr(self, "gemini_email", ""),
            "password": getattr(self, "gemini_password", ""),
            "verified": bool(getattr(self, "gemini_verified", False)),
        }
        try:
            enc = self._encrypt(json.dumps(data).encode("utf-8"))
            with open(CREDS_FILE, "w", encoding="utf-8") as fh:
                fh.write(enc)
        except Exception:
            pass

    # ---- Lists and tasks ----
    def populate_lists(self):
        expanded = self._capture_list_state()
        self.list_tree.clear()
        system_root = QtWidgets.QTreeWidgetItem(["System Lists", "system"])
        global_root = QtWidgets.QTreeWidgetItem(["Global Lists", "global"])
        project_root_item = QtWidgets.QTreeWidgetItem(["Project Lists", "project"])
        self.list_tree.addTopLevelItem(system_root)
        self.list_tree.addTopLevelItem(global_root)
        self.list_tree.addTopLevelItem(project_root_item)

        for sys_name in SYSTEM_LISTS:
            item = QtWidgets.QTreeWidgetItem([sys_name, "system"])
            item.setData(0, QtCore.Qt.UserRole, {"system": sys_name, "scope": "system"})
            system_root.addChild(item)

        lists = self.store.lists()
        for lst in lists:
            ref = {"id": lst["id"], "scope": lst["scope"], "project": lst["project"], "name": lst["name"]}
            item = QtWidgets.QTreeWidgetItem([lst["name"], lst["scope"]])
            item.setData(0, QtCore.Qt.UserRole, ref)
            if lst["scope"] == "project":
                proj_item = self._find_or_create_project_node(project_root_item, lst["project"] or "Unassigned")
                proj_item.addChild(item)
            elif lst["scope"] == "global":
                global_root.addChild(item)
        self._restore_list_state(expanded)
        if not self.current_list_ref:
            self.select_default_list()

    def _find_or_create_project_node(self, parent, name):
        for i in range(parent.childCount()):
            if parent.child(i).text(0) == name:
                return parent.child(i)
        node = QtWidgets.QTreeWidgetItem([name, "project"])
        parent.addChild(node)
        return node

    def select_default_list(self):
        root = self.list_tree.topLevelItem(0)
        if root and root.childCount() > 0:
            item = root.child(0)
            self.list_tree.setCurrentItem(item)
            self.on_list_selection()

    def _capture_list_state(self):
        expanded = set()
        def walk(item, path):
            if item.isExpanded():
                expanded.add(path)
            for i in range(item.childCount()):
                child = item.child(i)
                walk(child, f"{path}/{child.text(0)}")
        for i in range(self.list_tree.topLevelItemCount()):
            root = self.list_tree.topLevelItem(i)
            walk(root, root.text(0))
        return expanded

    def _restore_list_state(self, expanded_paths):
        if not expanded_paths:
            self.list_tree.expandAll()
            return
        def walk(item, path):
            if path in expanded_paths:
                item.setExpanded(True)
            for i in range(item.childCount()):
                child = item.child(i)
                walk(child, f"{path}/{child.text(0)}")
        for i in range(self.list_tree.topLevelItemCount()):
            root = self.list_tree.topLevelItem(i)
            walk(root, root.text(0))

    def on_list_selection(self):
        item = self.list_tree.currentItem()
        if not item:
            return
        data = item.data(0, QtCore.Qt.UserRole)
        if not data:
            # clicked a category header
            return
        self.current_list_ref = data
        self.load_tasks()
        self.update_task_controls_enabled()

    def list_active(self):
        if not self.current_list_ref:
            return False
        if self.current_list_ref.get("scope") == "project":
            proj = self.current_list_ref.get("project")
            return proj == self.active_project
        if self.current_list_ref.get("scope") == "system":
            return True
        return True

    def load_tasks(self):
        if not self.current_list_ref:
            return
        self.set_state("Loading", "Loading tasks...")
        rows = self.store.tasks_for_list(self.current_list_ref)
        self.task_table.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            task_uuid = row.get("uuid", "")
            title_item = QtWidgets.QTableWidgetItem(row.get("title", ""))
            due_item = QtWidgets.QTableWidgetItem(row.get("due_date") or "")
            prio_item = QtWidgets.QTableWidgetItem("★" if row["priority"] else "")
            state_item = QtWidgets.QTableWidgetItem(row.get("status", "pending"))
            list_item = QtWidgets.QTableWidgetItem(row.get("list_name", ""))
            project_item = QtWidgets.QTableWidgetItem(row.get("project") or row.get("list_project") or "")
            for item in [title_item, due_item, prio_item, state_item, list_item, project_item]:
                item.setFlags(qt_no_edit(item.flags()))
            if row.get("completed"):
                title_item.setForeground(QtGui.QColor("#6e7b8f"))
            self.task_table.setItem(idx, 0, title_item)
            self.task_table.setItem(idx, 1, due_item)
            self.task_table.setItem(idx, 2, prio_item)
            self.task_table.setItem(idx, 3, state_item)
            self.task_table.setItem(idx, 4, list_item)
            self.task_table.setItem(idx, 5, project_item)
            self.task_table.setRowHeight(idx, 28)
            header_text = task_uuid[:10] if task_uuid else ""
            self.task_table.setVerticalHeaderItem(idx, QtWidgets.QTableWidgetItem(header_text))
        self._normalize_task_table_columns()
        if rows:
            self.task_table.selectRow(0)
            self.on_task_selection()
        else:
            self.current_task_id = None
            self.clear_detail_fields()
        self.set_state("Idle", "")
        self.log_debug(
            "TASKS",
            {
                "list_scope": self.current_list_ref.get("scope") if self.current_list_ref else None,
                "list_name": self.current_list_ref.get("name") if self.current_list_ref else None,
                "task_rows": len(rows),
            },
        )

    def current_task(self):
        if self.current_task_id is None:
            return None
        return self.store.get_task(self.current_task_id)

    def on_task_selection(self):
        selected = self.task_table.selectionModel().selectedRows()
        if not selected:
            self.current_task_id = None
            self.clear_detail_fields()
            return
        row_idx = selected[0].row()
        uuid_item = self.task_table.item(row_idx, 0)
        task_id = uuid_item.text() if uuid_item else ""
        if not task_id:
            header_item = self.task_table.verticalHeaderItem(row_idx)
            task_id = header_item.text() if header_item else ""
        self.current_task_id = task_id
        task = self.store.get_task(task_id)
        if not task:
            return
        self.title_edit.setText(task["title"])
        self.notes_edit.setPlainText(task["notes"] or "")
        if task["due_date"]:
            try:
                d = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                self.due_date_edit.setDate(d)
                self.due_checkbox.setChecked(True)
            except ValueError:
                self.due_checkbox.setChecked(False)
        else:
            self.due_checkbox.setChecked(False)
        if task["reminder"]:
            try:
                dt = datetime.fromisoformat(task["reminder"])
                self.reminder_edit.setDateTime(dt)
                self.reminder_checkbox.setChecked(True)
            except ValueError:
                self.reminder_checkbox.setChecked(False)
        else:
            self.reminder_checkbox.setChecked(False)
        self.priority_checkbox.setChecked(bool(task["priority"]))
        self.recurrence_combo.setCurrentText(task["recurrence"] or "none")
        self.recur_interval_spin.setValue(task["recurrence_interval"] or 0 or 1)
        self.update_task_controls_enabled()

    def clear_detail_fields(self):
        self.title_edit.clear()
        self.notes_edit.clear()
        self.due_checkbox.setChecked(False)
        self.reminder_checkbox.setChecked(False)
        self.priority_checkbox.setChecked(False)
        self.recurrence_combo.setCurrentText("none")
        self.recur_interval_spin.setValue(1)

    def add_task_dialog(self):
        if not self.current_list_ref:
            QtWidgets.QMessageBox.warning(self, "Select List", "Choose a list to add tasks.")
            return
        if self.current_list_ref.get("scope") == "system":
            list_id = self.store.default_list_id
        else:
            list_id = self.current_list_ref.get("id") or self.store.default_list_id
        project = None
        if self.current_list_ref.get("scope") == "project":
            project = self.current_list_ref.get("project")
            if project != self.active_project:
                QtWidgets.QMessageBox.warning(self, "Inactive Project", "Focus the project to add tasks here.")
                return
        self.set_state("Awaiting User Input", "Enter task title")
        title, ok = QtWidgets.QInputDialog.getText(self, "New Task", "Title:")
        if not ok or not title.strip():
            self.set_state("Idle", "")
            return
        try:
            task_id = self.store.add_task(list_id, title.strip(), project=project)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Task Error", str(exc))
            self.set_state("Idle", "")
            return
        self.load_tasks()
        self._auto_select_task(task_id)
        self.update_project_status_from_tasks(project)
        self.set_state("Idle", "")

    def _auto_select_task(self, task_id):
        for row in range(self.task_table.rowCount()):
            header_item = self.task_table.verticalHeaderItem(row)
            if header_item and header_item.text() == str(task_id):
                self.task_table.selectRow(row)
                return

    def save_task_details(self):
        task = self.current_task()
        if not task:
            QtWidgets.QMessageBox.warning(self, "Select Task", "Select a task to save.")
            return
        title = self.title_edit.text().strip()
        if not title:
            QtWidgets.QMessageBox.warning(self, "Title Needed", "Task title is required.")
            return
        self.set_state("Executing", "Saving task...")
        due = self.due_date_edit.date().toString("yyyy-MM-dd") if self.due_checkbox.isChecked() else None
        reminder = (
            self.reminder_edit.dateTime().toString("yyyy-MM-ddTHH:mm:ss") if self.reminder_checkbox.isChecked() else None
        )
        recurrence = self.recurrence_combo.currentText()
        interval = self.recur_interval_spin.value() if recurrence == "custom" else 0
        self.store.update_task(
            task["uuid"],
            title=title,
            notes=self.notes_edit.toPlainText(),
            due_date=due,
            reminder=reminder,
            priority=1 if self.priority_checkbox.isChecked() else 0,
            recurrence=recurrence,
            recurrence_interval=interval,
        )
        self.load_tasks()
        self.update_project_status_from_tasks(task["project"])
        self.set_state("Idle", "")

    def toggle_complete_selected(self):
        task = self.current_task()
        if not task:
            QtWidgets.QMessageBox.warning(self, "Select Task", "Select a task to toggle completion.")
            return
        new_state = not bool(task["completed"])
        self.set_state("Executing", "Updating task...")
        try:
            self.store.set_complete(task["uuid"], new_state)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Status Error", str(exc))
            self.set_state("Idle", "")
            return
        if new_state:
            self.store.spawn_recurrence(task)
            self.prompt_autogit_for_task(task)
        self.load_tasks()
        self.update_project_status_from_tasks(task["project"])
        self.set_state("Idle", "")

    def add_selected_to_my_day(self):
        task = self.current_task()
        if not task:
            QtWidgets.QMessageBox.warning(self, "Select Task", "Select a task to add to My Day.")
            return
        self.set_state("Executing", "Adding to My Day...")
        self.store.add_to_my_day(task["uuid"])
        QtWidgets.QMessageBox.information(self, "My Day", "Task added to My Day for today.")
        self.load_tasks()
        self.set_state("Idle", "")

    def toggle_priority_selected(self):
        task = self.current_task()
        if not task:
            QtWidgets.QMessageBox.warning(self, "Select Task", "Select a task to toggle priority.")
            return
        self.set_state("Executing", "Updating priority...")
        self.store.update_task(task["uuid"], priority=0 if task["priority"] else 1)
        self.load_tasks()
        self.set_state("Idle", "")

    def delete_selected_task(self):
        task = self.current_task()
        if not task:
            QtWidgets.QMessageBox.warning(self, "Select Task", "Select a task to delete.")
            return
        reply = QtWidgets.QMessageBox.question(self, "Delete Task", f"Delete '{task['title']}'?")
        if reply != QtWidgets.QMessageBox.Yes:
            return
        self.set_state("Executing", "Deleting task...")
        self.store.delete_task(task["uuid"])
        self.load_tasks()
        self.update_project_status_from_tasks(task["project"])
        self.set_state("Idle", "")

    def move_task(self, direction):
        task = self.current_task()
        if not task:
            return
        if self.current_list_ref and self.current_list_ref.get("scope") == "system":
            return
        self.set_state("Executing", "Reordering task...")
        self.store.reorder(task["uuid"], task["list_id"], direction)
        self.load_tasks()
        self._auto_select_task(task["uuid"])
        self.set_state("Idle", "")

    def _on_move_task_up(self):
        if not self._ui_alive(self.task_table):
            return
        self.move_task("up")

    def _on_move_task_down(self):
        if not self._ui_alive(self.task_table):
            return
        self.move_task("down")

    def create_list(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "New List", "List name:")
        if not ok or not name.strip():
            return
        scope = "global"
        project = None
        if self.active_project:
            choice = QtWidgets.QMessageBox.question(
                self,
                "Scope",
                "Create list under active project?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if choice == QtWidgets.QMessageBox.Yes:
                scope = "project"
                project = self.active_project
        self.store.create_list(name.strip(), scope=scope, project=project)
        self.populate_lists()

    def rename_list(self):
        item = self.list_tree.currentItem()
        if not item:
            return
        data = item.data(0, QtCore.Qt.UserRole)
        if not data or data.get("scope") == "system":
            return
        self.set_state("Awaiting User Input", "Enter new list name")
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Rename List", "New name:", text=data.get("name", ""))
        if not ok or not new_name.strip():
            self.set_state("Idle", "")
            return
        self.store.rename_list(data["id"], new_name.strip())
        self.populate_lists()
        self.set_state("Idle", "")

    def import_tasks(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import CSV", str(Path.home()), "CSV Files (*.csv)")
        if not path:
            return
        target_project = None
        target_list = None
        if self.active_project:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Import Target",
                f"Import tasks into active project '{self.active_project}'\nunder new list '{self.active_project}'?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes,
            )
            if reply == QtWidgets.QMessageBox.Yes:
                target_project = self.active_project
                target_list = self.active_project
        self.set_state("Loading", "Importing tasks...")
        try:
            self.store.import_csv(path, target_project=target_project, target_list_name=target_list)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Import Error", str(exc))
            self.show_error_banner(str(exc))
            self.set_state("Idle", "")
            return
        self.populate_lists()
        self.load_tasks()
        self.set_state("Idle", "")

    def export_tasks(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export CSV", str(Path.home() / "tasks_export.csv"), "CSV Files (*.csv)")
        if not path:
            return
        self.set_state("Executing", "Exporting tasks...")
        try:
            atlas_format = str(path).lower().endswith(".tasks.csv")
            self.store.export_csv(path, atlas_format=atlas_format)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Export Error", str(exc))
            self.show_error_banner(str(exc))
            self.set_state("Idle", "")
            return
        QtWidgets.QMessageBox.information(self, "Exported", f"Tasks exported to {path}")
        self.set_state("Idle", "")

    def import_existing_folder(self):
        self.set_state("Awaiting User Input", "Select folder to import")
        source = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder to import", str(Path.home()))
        if not source:
            self.set_state("Idle", "")
            return
        validation_error = self.importer.validate_source(source)
        if validation_error:
            QtWidgets.QMessageBox.critical(self, "Invalid Source", validation_error)
            self.show_error_banner(validation_error)
            self.set_state("Idle", "")
            return
        default_name = os.path.basename(os.path.abspath(source)) or "imported_project"
        dialog = ImportOptionsDialog(source, default_name, self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            self.set_state("Idle", "")
            return
        opts = dialog.get_values()
        project_name = opts["name"] or default_name
        if not re.fullmatch(r"[A-Za-z0-9._-]+", project_name):
            QtWidgets.QMessageBox.warning(self, "Invalid Name", "Use letters, numbers, dots, underscores, or hyphens.")
            self.set_state("Idle", "")
            return
        dest = os.path.join(PROJECT_ROOT, project_name)
        if os.path.exists(dest):
            QtWidgets.QMessageBox.critical(self, "Exists", f"Project already exists at {dest}")
            self.set_state("Idle", "")
            return
        if opts["move"]:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Move Contents",
                "Move will remove files from the source directory. Continue?",
            )
            if reply != QtWidgets.QMessageBox.Yes:
                self.set_state("Idle", "")
                return
        self.start_operation("import", target=project_name, dry_run=self.dry_run_checkbox.isChecked())
        try:
            if not self.dry_run_checkbox.isChecked():
                os.makedirs(dest, exist_ok=False)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Error", f"Unable to create destination: {exc}")
            self.show_error_banner(str(exc))
            self.set_state("Idle", "")
            self.finalize_operation("failed")
            return
        skipped = []
        try:
            if self.dry_run_checkbox.isChecked():
                msg = f"[Dry run] Would {'copy' if opts['copy'] or not opts['move'] else 'move'} contents from {source} to {dest}."
                QtWidgets.QMessageBox.information(self, "Dry Run", msg)
                self.finish_operation("Dry run import")
                self.finalize_operation("rolled_back")
                return
            self.set_operation_state("executing")
            self.show_operation("Importing folder...", state="Executing")
            if opts["copy"] or not opts["move"]:
                skipped = self.importer.copy_tree_safely(source, dest)
            else:
                skipped = self.importer.move_contents(source, dest)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Import Failed", f"Error during import: {exc}")
            self.show_error_banner(f"Import failed: {exc}")
            self.finish_operation("Import failed")
            self.finalize_operation("failed")
            return
        if opts["readme"]:
            readme_path = os.path.join(dest, "README.md")
            if not os.path.exists(readme_path):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                content = f"# {project_name}\n\nImported on: {ts}\n\nDescribe the project here.\n"
                try:
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception:
                    pass
        if opts["autogit"]:
            self.run_autogit_init_for_path(dest)
        msg = f"Imported {source} -> {dest}"
        if skipped:
            msg += f"\nSkipped {len(skipped)} symlinks outside source."
        QtWidgets.QMessageBox.information(self, "Imported", msg)
        self.project_meta[project_name] = {
            "origin": "Local",
            "auto_commit": False,
            "localsync": False,
            "localsync_path": None,
            "import_method": "move" if opts["move"] else "copy",
            "origin_path": source,
            "last_sync": datetime.now().isoformat(),
        }
        self.save_project_meta()
        self.ensure_manifest(project_name, origin="Local", origin_path=source)
        self.update_manifest_fields(project_name, preferred_credentials=self.selected_cred_label, auto_commit_enabled=False, localsync_enabled=False)
        self.refresh_projects()
        self.finish_operation("Import complete")
        self.refresh_health_panel()
        self.finalize_operation("committed")

    def update_active_label(self):
        if self.active_project:
            self.active_label.setText(f"Active: {self.active_project}")
            accent = getattr(self, "accent_primary", ACCENTS["sunset"]["primary"])
            glow = getattr(self, "accent_glow", ACCENTS["sunset"]["glow"])
            self.active_label.setStyleSheet(f"color: {accent}; border: 1px solid {glow}; padding: 8px; border-radius: 8px;")
            self.focus_state_label.setText("Focused")
            self.focus_state_label.setStyleSheet(f"color: {accent};")
            self.update_auto_cd_label(enabled=True)
        else:
            marker_state = self.get_marker_project()
            if marker_state:
                self.active_label.setText(f"Active: [inconsistent] {marker_state}")
                self.active_label.setStyleSheet("color: #d2a446; border: 1px solid #d14b4b; padding: 8px; border-radius: 8px;")
                self.focus_state_label.setText("Warning: Marker only")
                self.focus_state_label.setStyleSheet("color: #d14b4b;")
                self.update_auto_cd_label(enabled=True)
            else:
                self.active_label.setText("No project focused")
                self.active_label.setStyleSheet("color: #c8b5ff; border: 1px solid #5b36b8; padding: 8px; border-radius: 8px;")
                self.focus_state_label.setText("Unfocused")
                self.focus_state_label.setStyleSheet("color: #d2a446;")
                self.update_auto_cd_label(enabled=False)
        self.update_identity_banner()

    def update_auto_cd_label(self, enabled):
        if not hasattr(self, "auto_cd_label"):
            return
        if enabled and os.path.exists(FOCUS_MARKER):
            accent = getattr(self, "accent_primary", ACCENTS["sunset"]["primary"])
            self.auto_cd_label.setText("Terminal Auto-Focus: ENABLED")
            self.auto_cd_label.setStyleSheet(f"color: {accent};")
        else:
            self.auto_cd_label.setText("Terminal Auto-Focus: DISABLED")
            self.auto_cd_label.setStyleSheet("color: #d2a446;")

    def update_project_status_from_tasks(self, project):
        if not project:
            return
        incomplete = self.store.project_incomplete_count(project)
        if incomplete == 0:
            self.status_map[project] = "Completed"
        else:
            self.status_map[project] = "In Progress (α)"
        self.refresh_projects()

    def update_task_controls_enabled(self):
        active = self.list_active()
        for btn in [
            self.new_task_btn,
            self.save_task_btn,
            self.complete_task_btn,
            self.my_day_btn,
            self.priority_btn,
            self.delete_task_btn,
            self.move_up_btn,
            self.move_down_btn,
        ]:
            btn.setEnabled(active)
        # highlight primary action when list active
        if active:
            accent = getattr(self, "accent_primary", ACCENTS["sunset"]["primary"])
            self.new_task_btn.setStyleSheet(f"background-color: #1f2d4a; border: 1px solid {accent}; color: {accent};")
        else:
            self.new_task_btn.setStyleSheet("")

    def glitch(self, widget):
        effect = QtWidgets.QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QtCore.QPropertyAnimation(effect, b"opacity")
        anim.setDuration(180)
        anim.setKeyValueAt(0, 1.0)
        anim.setKeyValueAt(0.45, 0.6)
        anim.setKeyValueAt(1, 1.0)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    # ---- Session cleanup ----
    def cleanup_session(self):
        if not self.session_active:
            return
        self.teardown_active = True
        self._ui_tearing_down = True
        if hasattr(self, "_ui_mutation_queue"):
            self._ui_mutation_queue.clear()
        self.session_active = False
        for timer in list(self.autogit_timers.values()):
            try:
                timer.stop()
            except Exception:
                pass
        self.autogit_timers.clear()
        for watcher in list(self.autogit_watchers.values()):
            try:
                watcher.deleteLater()
            except Exception:
                pass
        self.autogit_watchers.clear()
        try:
            if hasattr(self, "consistency_timer"):
                self.consistency_timer.stop()
        except Exception:
            pass
        self.detach_fs_view()
        try:
            os.chdir(Path.home())
        except Exception:
            pass
        if getattr(self, "git_askpass_path", None):
            try:
                if os.path.exists(self.git_askpass_path):
                    os.remove(self.git_askpass_path)
            except Exception:
                pass
        self._unmount_active_mount(no_prompt=True)
        self.backend.remove_focus_marker()
        self.active_project = None
        self.update_active_label()
        self.refresh_health_panel()
        if hasattr(self, "supervisor"):
            self.supervisor.clear_marker()
            self.log_debug("STABILITY", {"shutdown": "cleanup", "debug_level": getattr(self, "debug_level", "normal")})

    def _handle_termination_signal(self, *args):
        self.cleanup_session()
        sys.exit(0)

    def closeEvent(self, event):
        self.cleanup_session()
        event.accept()

    # ---- Identity banner ----
    def _current_display_name(self):
        try:
            import pwd
            return pwd.getpwuid(os.getuid()).pw_name
        except Exception:
            return getpass.getuser()

    def _colorize_accent(self, text_line: str) -> str:
        accent = BANNER_ACCENT
        accent_tokens = ["[Ø]", "⚠️", "☢️", "«", "»", "⟬", "⟭", "⟦", "⟧", "—"]
        # process left-to-right ensuring spaces preserved via pre styling
        out = ""
        i = 0
        while i < len(text_line):
            match_token = None
            for tok in sorted(accent_tokens, key=len, reverse=True):
                if text_line.startswith(tok, i):
                    match_token = tok
                    break
            if match_token:
                out += f"<span style='color:{accent}'>{html.escape(match_token)}</span>"
                i += len(match_token)
            else:
                out += html.escape(text_line[i])
                i += 1
        return out

    def update_identity_banner(self):
        if not hasattr(self, "identity_banner"):
            return
        transformed = glyph_transform("SINGULARITY CONSOLE")
        top = "«⟬ ⚠️ ⟭»—⟦ $ I Ͷ Ģ Ǚ Ⅼ ⩑ ʁ ∤ Ͳ ϓ ⟧—«⟬ ⚠️ ⟭»"
        bottom = f"[Ø]-⟦ {transformed} ⟧-[Ø]"
        normalized = normalize_lines([top, bottom])
        # Build HTML with preserved spacing
        html_lines = [self._colorize_accent(line) for line in normalized]
        font = QtGui.QFont("JetBrains Mono")
        font.setStyleHint(QtGui.QFont.TypeWriter)
        base_size = 14
        font.setPointSizeF(base_size * getattr(self, "scale_factor", 1.0))
        self.identity_banner.setFont(font)
        html_block = "<pre style='margin:0; white-space: pre; font-family: \"JetBrains Mono\", monospace; color: #d8f6ff;'>"
        html_block += "<br>".join(html_lines)
        html_block += "</pre>"
        self.identity_banner.setTextFormat(QtCore.Qt.RichText)
        self.identity_banner.setText(html_block)


def qt_message_handler(mode, context, message):
    try:
        print(f"[QT {int(mode)}] {message}")
    except Exception:
        pass


def main():
    pre_settings = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                pre_settings = json.load(fh)
        except Exception:
            pre_settings = {}
    debug_level = pre_settings.get("debug_level", "normal")
    supervisor = StabilitySupervisor(debug_level=debug_level, on_event=None, log_fn=None)
    # Apply sanitized environment globally before creating the QApplication to avoid Qt/XCB instability.
    os.environ.update(supervisor.env_base)
    # Ensure Qt logging is routed to stdout for visibility of fatal warnings.
    try:
        QtCore.qInstallMessageHandler(qt_message_handler)
    except Exception:
        pass
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    window = FocusManager(supervisor=supervisor, settings=pre_settings, debug_level=debug_level)
    window.show()
    if QT6:
        ret = app.exec()
    else:
        ret = app.exec_()
    try:
        try:
            app.aboutToQuit.disconnect()
        except Exception:
            pass
        for w in app.topLevelWidgets():
            try:
                w.close()
            except Exception:
                pass
    except Exception:
        pass
    sys.exit(ret)


if __name__ == "__main__":
    main()
