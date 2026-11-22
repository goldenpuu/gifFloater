# -*- coding: utf-8 -*-
import datetime
import json
import math
import os
import random
import subprocess
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageSequence, ImageTk

try:
    import ctypes
    from ctypes import wintypes
    HAS_CTYPES_WIN32 = (sys.platform == "win32")
except Exception:
    ctypes = None
    wintypes = None
    HAS_CTYPES_WIN32 = False

try:
    import win32api
    import win32con
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False


def configure_utf8():
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


configure_utf8()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIFS_DIR = os.path.join(BASE_DIR, "gifs")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
HAND_FONT_PATH = os.path.join(FONTS_DIR, "hand.ttf")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_py.json")
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico")
APP_NAME = "퇴근 친구"
AUTOSTART_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_REG_NAME = "OffworkBuddy"

TRANSPARENT_HEX = "#010203"
TRANSPARENT_RGB = (1, 2, 3)
SUPPORTED_EXTS = (".gif", ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".ico")

WM_TRAYICON = win32con.WM_USER + 20 if HAS_WIN32 else 0x0414
HOTKEY_HIDE_ID = 1
HOTKEY_LOCK_ID = 2

WEEKDAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]
SCENE_KEYS = ["rest", "wake", "type", "lunch", "enter", "back", "tired", "hold"]

SCENES_SPEC = {
    "rest": {
        "name": "출근 전",
        "caption": "출근 전 · 쉬는 날",
        "default_text": "",
        "has_switch": False,
        "has_text": False,
        "default_gif": "presets/chiikawa/rest.gif",
        "fallback_gif": "chiikawa_before_work.gif",
    },
    "wake": {
        "name": "출근",
        "caption": "출근 2분 전",
        "default_text": "벌써 출근이네",
        "has_switch": True,
        "has_text": True,
        "default_gif": "presets/chiikawa/wake.gif",
        "fallback_gif": "chiikawa_before_work.gif",
    },
    "type": {
        "name": "근무 중",
        "caption": "근무 시간",
        "default_text": "",
        "has_switch": False,
        "has_text": False,
        "default_gif": "presets/chiikawa/type.gif",
        "fallback_gif": "chiikawa_working.gif",
    },
    "lunch": {
        "name": "점심",
        "caption": "점심시간",
        "default_text": "점심시간!",
        "has_switch": True,
        "has_text": True,
        "default_gif": "presets/chiikawa/lunch.gif",
        "fallback_gif": "chiikawa_working.gif",
    },
    "enter": {
        "name": "퇴근",
        "caption": "퇴근하면",
        "default_text": "퇴근이다!",
        "has_switch": False,
        "has_text": True,
        "default_gif": "presets/chiikawa/enter.gif",
        "fallback_gif": "chiikawa_cheer.gif",
    },
    "back": {
        "name": "야근",
        "caption": "퇴근 5분 지남",
        "default_text": "야근 중…",
        "has_switch": True,
        "has_text": True,
        "default_gif": "presets/chiikawa/back.gif",
        "fallback_gif": "chiikawa_leaving_soon.gif",
    },
    "tired": {
        "name": "야근 20분",
        "caption": "퇴근 20분 지남",
        "default_text": "집에 가고 싶어…",
        "has_switch": True,
        "has_text": True,
        "default_gif": "presets/chiikawa/tired.gif",
        "fallback_gif": "chiikawa_leaving_soon.gif",
    },
    "hold": {
        "name": "누를 때",
        "caption": "캐릭터를 눌렀을 때",
        "default_text": "힘내!",
        "has_switch": True,
        "has_text": True,
        "default_gif": "presets/chiikawa/hold.gif",
        "fallback_gif": "chiikawa_cheer.gif",
    },
}

ACTIVE_INPUT_SECONDS = 60.0
WAKE_LEAD_MINUTES = 2

DEFAULT_WORK_SCHEDULE = {
    "enabled": True,
    "start_time": "08:00",
    "end_time": "17:00",
    "lunch_on": True,
    "lunch_start": "12:00",
    "lunch_end": "13:00",
    "work_days": [0, 1, 2, 3, 4],
    "stretch_interval_min": 50,
    "random_chat_enabled": True,
    "always_show_bubble": True,
    "bubble_time_format": "hm",
    "auto_state_gif": True,
    "forced_state": "auto",
}

WORK_STATE_LABELS = {k: SCENES_SPEC[k]["name"] for k in SCENE_KEYS}

PERSONALITY_KEYS = ["warm", "energetic", "laidback", "tsundere", "diligent"]

PERSONALITY_SPECS = {
    "warm": {
        "name": "다정함",
        "walk_speed": (2.2, 3.1),
        "rest_ms": (3200, 6800),
        "random_sec": (720, 1320),
        "actions": ["jump", "wiggle"],
        "cheers": [
            "힘내!",
            "잘하고 있어!",
            "오늘도 화이팅!",
            "조금만 더 힘내!",
            "천천히 해보자!",
            "아주 잘하고 있어!",
        ],
        "interactions": {
            "feed": "고마워! 잘 먹을게!",
            "highfive": "하이파이브! 최고야!",
            "poke": "부르셨나요? 힘내요!",
        },
        "greet_open": [
            "안녕! 반가워!",
            "오늘도 같이 힘내자!",
            "좋은 하루야!",
            "어? 눈 마주쳤다! 안녕!",
            "잘 지내고 있지? 안녕!",
        ],
        "greet_reply": [
            "응! 반가워!",
            "같이 화이팅하자!",
            "고마워! 힘내자!",
            "응! 눈 마주쳐서 반가워!",
            "헤헤 안녕! 화이팅!",
        ],
    },
    "energetic": {
        "name": "활발함",
        "walk_speed": (3.3, 4.5),
        "rest_ms": (2000, 4500),
        "random_sec": (540, 960),
        "actions": ["jump", "jump", "wiggle"],
        "cheers": [
            "가보자고!",
            "오늘도 전력질주!",
            "파이팅 넘치게!",
            "할 수 있어!",
            "아자아자!",
            "최고야!",
        ],
        "interactions": {
            "feed": "우와! 맛있겠다!",
            "highfive": "짝! 완벽한 호흡!",
            "poke": "앗! 간지러워!",
        },
        "greet_open": [
            "야호! 안녕!",
            "신나게 달려보자!",
            "텐션 올려보자!",
            "오! 눈 마주쳤다! 안녕!",
            "안녕안녕! 힘내자!",
        ],
        "greet_reply": [
            "오예! 가보자고!",
            "좋아! 완전 신나!",
            "아자아자! 화이팅!",
            "와! 반가워! 아자아자!",
            "안녕! 같이 화이팅!",
        ],
    },
    "laidback": {
        "name": "느긋함",
        "walk_speed": (1.4, 2.1),
        "rest_ms": (5000, 10000),
        "random_sec": (900, 1500),
        "actions": ["wiggle", "wiggle", "jump"],
        "cheers": [
            "쉬엄쉬엄 해~",
            "천천히 가자~",
            "여유롭게 해보자~",
            "숨 한 번 돌리자~",
            "무리하지 마~",
            "차분하게!",
        ],
        "interactions": {
            "feed": "냠냠~ 행복해~",
            "highfive": "터치~ 잘했어~",
            "poke": "왜 그래~ 졸려…",
        },
        "greet_open": [
            "천천히 가자~",
            "오늘 날씨 좋네~",
            "쉬엄쉬엄 하자~",
            "어라, 눈 마주쳤네~ 안녕~",
            "안녕~ 쉬엄쉬엄 해~",
        ],
        "greet_reply": [
            "그래~ 여유롭게~",
            "맞아~ 천천히 하자~",
            "응~ 반가워~",
            "오~ 안녕~ 여유롭게 가자~",
            "응~ 보고 있었구나~",
        ],
    },
    "tsundere": {
        "name": "츤데레",
        "walk_speed": (2.5, 3.5),
        "rest_ms": (3500, 7500),
        "random_sec": (720, 1260),
        "actions": ["wiggle", "jump"],
        "cheers": [
            "딱히 응원하는 건 아냐!",
            "뭐, 나쁘지 않네!",
            "할 때는 하네?",
            "조금만 더 버텨봐!",
            "실수하지 말라고!",
            "잘하고 있긴 해!",
        ],
        "interactions": {
            "feed": "딱히 배고픈 건 아니었어!",
            "highfive": "한 번만 맞춰주는 거야!",
            "poke": "갑자기 왜 찔러?!",
        },
        "greet_open": [
            "흥, 마주쳤네?",
            "딴짓하지 마!",
            "뭐야, 비켜줄까?",
            "뭐야, 왜 쳐다봐? 안녕!",
            "어? 눈 마주쳤잖아… 흥!",
        ],
        "greet_reply": [
            "흥, 반갑긴 하네!",
            "알았다고! 열심히 해!",
            "딱히 기다린 건 아냐!",
            "쳐다보긴! …안녕!",
            "어, 안녕… 딴짓하지 마!",
        ],
    },
    "diligent": {
        "name": "성실함",
        "walk_speed": (2.6, 3.4),
        "rest_ms": (2600, 5200),
        "random_sec": (660, 1140),
        "actions": ["jump", "wiggle"],
        "cheers": [
            "집중! 잘하고 있어!",
            "오늘 목표 달성하자!",
            "칼퇴를 향해!",
            "차근차근 끝내자!",
            "페이스 좋아!",
            "화이팅!",
        ],
        "interactions": {
            "feed": "에너지 충전 완료!",
            "highfive": "호흡 척척! 화이팅!",
            "poke": "딴짓 금지! 집중!",
        },
        "greet_open": [
            "오늘 업무 순조로워?",
            "칼퇴까지 힘내자!",
            "집중 모드 유지하자!",
            "눈 마주쳤다! 안녕!",
            "수고 많아! 오늘도 힘내자!",
        ],
        "greet_reply": [
            "이상 무! 화이팅!",
            "좋아, 칼퇴하자!",
            "완벽해! 계속 가자!",
            "응! 안녕! 끝까지 화이팅!",
            "고마워! 서로 힘내자!",
        ],
    },
}

STRETCH_MESSAGES = [
    "물 한 잔 마셔!",
    "기지개 한 번 켜자!",
    "어깨 쭉 펴!",
    "눈 한 번 깜빡여!",
    "잠깐 숨 돌리자!",
]

CHARACTER_PRESET_KEYS = ["chiikawa", "hachiware", "usagi", "momonga", "siren", "duo"]
CHIIKAWA_BATCH_PRESET_KEYS = ["chiikawa", "hachiware", "usagi", "momonga", "siren", "duo"]

CHARACTER_PRESETS = {
    "chiikawa": {
        "label": "치이카와",
        "name": "치이카와",
        "personality": "warm",
        "scene_gifs": {
            "rest": "presets/chiikawa/rest.gif",
            "wake": "presets/chiikawa/wake.gif",
            "type": "presets/chiikawa/type.gif",
            "lunch": "presets/chiikawa/lunch.gif",
            "enter": "presets/chiikawa/enter.gif",
            "back": "presets/chiikawa/back.gif",
            "tired": "presets/chiikawa/tired.gif",
            "hold": "presets/chiikawa/hold.gif",
        },
        "scene_texts": {
            "wake": "으응… 벌써 출근이네",
            "lunch": "점심시간이야!",
            "enter": "와아! 퇴근이다!",
            "back": "으앙… 야근 중…",
            "tired": "집에 가고 싶어…",
            "hold": "으응, 힘내!",
        },
    },
    "hachiware": {
        "label": "하치와레",
        "name": "하치와레",
        "personality": "diligent",
        "scene_gifs": {
            "rest": "presets/hachiware/rest.gif",
            "wake": "presets/hachiware/wake.gif",
            "type": "presets/hachiware/type.gif",
            "lunch": "presets/hachiware/lunch.gif",
            "enter": "presets/hachiware/enter.gif",
            "back": "presets/hachiware/back.gif",
            "tired": "presets/hachiware/rest.gif",
            "hold": "presets/hachiware/hold.gif",
        },
        "scene_texts": {
            "wake": "어떻게든 될 거야! 출근!",
            "lunch": "맛있게 점심 먹자!",
            "enter": "해냈다! 퇴근이다!",
            "back": "조금만 더… 야근 중!",
            "tired": "으음… 집에 가고 싶어…",
            "hold": "어떻게든 될 거야!",
        },
    },
    "usagi": {
        "label": "우사기",
        "name": "우사기",
        "personality": "energetic",
        "scene_gifs": {
            "rest": "presets/usagi/rest.gif",
            "wake": "presets/usagi/wake.gif",
            "type": "presets/usagi/type.gif",
            "lunch": "presets/usagi/lunch.gif",
            "enter": "presets/usagi/enter.gif",
            "back": "presets/usagi/back.gif",
            "tired": "presets/usagi/tired.gif",
            "hold": "presets/usagi/hold.gif",
        },
        "scene_texts": {
            "wake": "우라! 벌써 출근이야!",
            "lunch": "야하! 점심시간!",
            "enter": "야하!! 퇴근이다!!",
            "back": "하아? 야근 중…",
            "tired": "우라… 집에 가자…",
            "hold": "야하! 힘내!",
        },
    },
    "momonga": {
        "label": "모몽가",
        "name": "모몽가",
        "personality": "tsundere",
        "scene_gifs": {
            "rest": "presets/momonga/peek.gif",
            "wake": "presets/momonga/peek.gif",
            "type": "presets/momonga/happy.gif",
            "lunch": "presets/momonga/happy.gif",
            "enter": "presets/momonga/happy.gif",
            "back": "presets/momonga/cry.gif",
            "tired": "presets/momonga/cry.gif",
            "hold": "presets/momonga/happy.gif",
        },
        "scene_texts": {
            "wake": "빨리 출근해! 어서!",
            "lunch": "맛있는 거 내놔! 점심!",
            "enter": "칭찬해줘! 퇴근이야!",
            "back": "야근 싫어어어…!",
            "tired": "집에 보내달라고…!",
            "hold": "흥! 귀엽다고 해줘!",
        },
    },
    "siren": {
        "label": "세이렌",
        "name": "세이렌",
        "personality": "laidback",
        "scene_gifs": {
            "rest": "presets/siren/sleep.gif",
            "wake": "presets/siren/wave.gif",
            "type": "presets/siren/sing.gif",
            "lunch": "presets/siren/heart.gif",
            "enter": "presets/siren/heart.gif",
            "back": "presets/siren/angry.gif",
            "tired": "presets/siren/sleep.gif",
            "hold": "presets/siren/wave.gif",
        },
        "scene_texts": {
            "wake": "노래하며 출근하자~",
            "lunch": "점심시간이야~",
            "enter": "신나는 퇴근이야~",
            "back": "야근은 안 돼!",
            "tired": "이제 자고 싶어…",
            "hold": "내 노래 들을래?",
        },
    },
    "duo": {
        "label": "치이카와 & 하치와레",
        "name": "단짝 콤비",
        "personality": "warm",
        "scene_gifs": {
            "rest": "presets/duo/rest.gif",
            "wake": "presets/duo/wake.gif",
            "type": "presets/duo/type.gif",
            "lunch": "presets/duo/lunch.gif",
            "enter": "presets/duo/enter.gif",
            "back": "presets/duo/back.gif",
            "tired": "presets/duo/tired.gif",
            "hold": "presets/duo/hold.gif",
        },
        "scene_texts": {
            "wake": "같이 출근하자!",
            "lunch": "같이 맛점하자!",
            "enter": "같이 퇴근이다!",
            "back": "둘이서 버텨보자!",
            "tired": "얼른 같이 집에 가자…",
            "hold": "우리 둘이 응원해!",
        },
    },
}


_WIN32_CTYPES_READY = False
if HAS_CTYPES_WIN32:
    class _MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", wintypes.RECT),
            ("rcWork", wintypes.RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    try:
        _u32 = ctypes.windll.user32
        _u32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
        _u32.MonitorFromPoint.restype = wintypes.HMONITOR
        _u32.MonitorFromRect.argtypes = [ctypes.POINTER(wintypes.RECT), wintypes.DWORD]
        _u32.MonitorFromRect.restype = wintypes.HMONITOR
        _u32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(_MONITORINFO)]
        _u32.GetMonitorInfoW.restype = wintypes.BOOL
        _u32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        _u32.GetCursorPos.restype = wintypes.BOOL
        _u32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        _u32.SetWindowPos.restype = wintypes.BOOL
        _WIN32_CTYPES_READY = True
    except Exception:
        _WIN32_CTYPES_READY = False


def enable_dpi_awareness():
    if not HAS_CTYPES_WIN32:
        return
    # System DPI awareness keeps Tk 8.6 coordinates unified across mixed-DPI monitors.
    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-2)):
            return
    except Exception:
        pass
    try:
        if ctypes.windll.shcore.SetProcessDpiAwareness(1) == 0:
            return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_cursor_pos(fallback_event=None):
    """Return global (x, y) cursor coordinates in virtual screen space."""
    if _WIN32_CTYPES_READY:
        try:
            pt = wintypes.POINT()
            if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
                return int(pt.x), int(pt.y)
        except Exception:
            pass
    if HAS_WIN32:
        try:
            x, y = win32gui.GetCursorPos()
            return int(x), int(y)
        except Exception:
            pass
    if fallback_event is not None:
        try:
            return int(fallback_event.x_root), int(fallback_event.y_root)
        except Exception:
            pass
    return 0, 0


def _get_tk_hwnd(win):
    if not HAS_CTYPES_WIN32:
        return 0
    try:
        frame_hex = win.wm_frame()
        if frame_hex and frame_hex != "0x0":
            return int(frame_hex, 16)
        return int(win.winfo_id())
    except Exception:
        return 0


def _set_window_geometry(win, x, y, w=None, h=None):
    """Move/resize a Tk window consistently across multi-monitor virtual screen coordinates."""
    ix = int(round(x))
    iy = int(round(y))
    if w is not None and h is not None:
        iw = max(1, int(round(w)))
        ih = max(1, int(round(h)))
        win.geometry(f"{iw}x{ih}+{ix}+{iy}")
    else:
        iw = 0
        ih = 0
        win.geometry(f"+{ix}+{iy}")

    if _WIN32_CTYPES_READY:
        try:
            if win.winfo_ismapped():
                hwnd = _get_tk_hwnd(win)
                if hwnd:
                    flags = 0x0004 | 0x0010  # SWP_NOZORDER | SWP_NOACTIVATE
                    if w is None or h is None:
                        flags |= 0x0001  # SWP_NOSIZE
                    ctypes.windll.user32.SetWindowPos(hwnd, 0, ix, iy, iw, ih, flags)
        except Exception:
            pass


def get_available_gifs():
    os.makedirs(GIFS_DIR, exist_ok=True)
    files = []
    for root_dir, _, filenames in os.walk(GIFS_DIR):
        for name in filenames:
            if name.lower().endswith(SUPPORTED_EXTS):
                files.append(os.path.join(root_dir, name))
    files.sort(key=lambda p: os.path.relpath(p, GIFS_DIR).lower())
    return files


def format_gif_display_name(path):
    if not path:
        return "(미지정)"
    if os.path.isabs(path):
        try:
            rel = os.path.relpath(path, GIFS_DIR)
            if not rel.startswith("..") and not os.path.isabs(rel):
                return rel.replace("\\", "/")
        except ValueError:
            pass
        return os.path.basename(path)
    return path.replace("\\", "/")


def to_stored_gif_ref(path):
    if not path:
        return ""
    if os.path.isabs(path):
        try:
            rel = os.path.relpath(path, GIFS_DIR)
            if not rel.startswith("..") and not os.path.isabs(rel):
                return rel.replace("\\", "/")
        except ValueError:
            pass
        return path
    return path.replace("\\", "/")


def get_idle_seconds():
    """Return elapsed seconds since last keyboard or mouse input via Win32 GetLastInputInfo."""
    if not HAS_CTYPES_WIN32:
        return 0.0
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            tick = ctypes.windll.kernel32.GetTickCount()
            elapsed_ms = (tick - lii.dwTime) & 0xFFFFFFFF
            return elapsed_ms / 1000.0
    except Exception:
        pass
    return 0.0


def _autostart_command():
    script_path = os.path.abspath(__file__)
    exe = sys.executable
    exe_dir = os.path.dirname(exe)
    pythonw = os.path.join(exe_dir, "pythonw.exe")
    if os.path.exists(pythonw):
        exe = pythonw
    return f'"{exe}" "{script_path}"'


def is_autostart_enabled():
    if not HAS_WINREG:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_READ) as k:
            val, _ = winreg.QueryValueEx(k, AUTOSTART_REG_NAME)
            return isinstance(val, str) and bool(val.strip())
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_autostart_enabled(enabled):
    if not HAS_WINREG:
        return False
    try:
        if enabled:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH) as k:
                winreg.SetValueEx(k, AUTOSTART_REG_NAME, 0, winreg.REG_SZ, _autostart_command())
        else:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_SET_VALUE) as k:
                try:
                    winreg.DeleteValue(k, AUTOSTART_REG_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def find_missing_hand_chars(text):
    """Return characters in text that cannot be rendered with hand.ttf."""
    if not text or not os.path.exists(HAND_FONT_PATH):
        return []
    font = _load_bubble_font(16, bold=False)
    try:
        notdef = bytes(font.getmask("\ufffe"))
    except Exception:
        return []
    missing = []
    for ch in text:
        if ch.isspace() or ord(ch) <= 127:
            continue
        try:
            if bytes(font.getmask(ch)) == notdef and ch not in missing:
                missing.append(ch)
        except Exception:
            pass
    return missing


def default_scene_gif_ref(scene_key):
    spec = SCENES_SPEC.get(scene_key)
    if not spec:
        return "chiikawa_working.gif"
    primary = spec["default_gif"]
    if os.path.exists(os.path.join(GIFS_DIR, primary)):
        return primary
    return spec["fallback_gif"]


def default_scene_gifs_map():
    return {k: default_scene_gif_ref(k) for k in SCENE_KEYS}


def default_scene_texts_map():
    return {k: SCENES_SPEC[k]["default_text"] for k in SCENE_KEYS if SCENES_SPEC[k]["has_text"]}


def default_scene_on_map():
    return {k: True for k in SCENE_KEYS if SCENES_SPEC[k]["has_switch"]}


def get_character_preset_spec(preset_key):
    key = preset_key if preset_key in CHARACTER_PRESETS else "chiikawa"
    raw = CHARACTER_PRESETS[key]
    return {
        "key": key,
        "label": raw["label"],
        "name": raw["name"],
        "personality": raw["personality"],
        "scene_gifs": dict(raw["scene_gifs"]) if raw["scene_gifs"] else default_scene_gifs_map(),
        "scene_texts": dict(raw["scene_texts"]) if raw["scene_texts"] else default_scene_texts_map(),
    }


def resolve_preset_scene_gifs(preset_key):
    spec = get_character_preset_spec(preset_key)
    out = {}
    for k in SCENE_KEYS:
        ref = spec["scene_gifs"].get(k) or default_scene_gif_ref(k)
        full_path = ref if os.path.isabs(ref) else os.path.join(GIFS_DIR, ref)
        out[k] = ref if os.path.exists(full_path) else default_scene_gif_ref(k)
    return out


def build_character_preset_patch(preset_key):
    spec = get_character_preset_spec(preset_key)
    scene_gifs = resolve_preset_scene_gifs(spec["key"])
    scene_texts = {
        k: spec["scene_texts"].get(k, SCENES_SPEC[k]["default_text"])
        for k in SCENE_KEYS
        if SCENES_SPEC[k]["has_text"]
    }
    return {
        "preset": spec["key"],
        "name": spec["name"],
        "personality": spec["personality"],
        "auto_state_gif": True,
        "scene_gifs": scene_gifs,
        "scene_texts": scene_texts,
        "scene_on": default_scene_on_map(),
    }


def normalize_work_schedule(raw):
    merged = dict(DEFAULT_WORK_SCHEDULE)
    if isinstance(raw, dict):
        for key in DEFAULT_WORK_SCHEDULE:
            if key in raw and raw[key] is not None:
                merged[key] = raw[key]

    days = merged.get("work_days", [0, 1, 2, 3, 4])
    if isinstance(days, (list, tuple, set)):
        clean_days = sorted({int(d) for d in days if isinstance(d, (int, float, str)) and str(d).lstrip("-").isdigit() and 0 <= int(d) <= 6})
    else:
        clean_days = [0, 1, 2, 3, 4]
    merged["work_days"] = clean_days
    merged["lunch_on"] = bool(merged.get("lunch_on", True))

    forced = merged.get("forced_state", "auto")
    if forced not in SCENE_KEYS and forced != "auto":
        merged["forced_state"] = "auto"
    return merged


def normalize_floater_state(state, idx=0, schedule=None):
    st = dict(state) if isinstance(state, dict) else {}
    sched = normalize_work_schedule(schedule)

    raw_name = st.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        st["name"] = f"캐릭터 {idx + 1}"
    else:
        st["name"] = raw_name.strip()

    if "auto_state_gif" in st and st["auto_state_gif"] is not None:
        st["auto_state_gif"] = bool(st["auto_state_gif"])
    else:
        st["auto_state_gif"] = bool(sched.get("auto_state_gif", True))

    st["bubble_on"] = True if st.get("bubble_on") is None else bool(st.get("bubble_on"))
    st["fixed_pos"] = bool(st.get("fixed_pos", False))
    st["wander"] = False if st["fixed_pos"] else (True if st.get("wander") is None else bool(st.get("wander")))
    raw_p = st.get("personality")
    st["personality"] = raw_p if raw_p in PERSONALITY_KEYS else PERSONALITY_KEYS[idx % len(PERSONALITY_KEYS)]

    raw_scenes = st.get("scene_gifs") if isinstance(st.get("scene_gifs"), dict) else {}
    scene_gifs = {}
    for k in SCENE_KEYS:
        val = raw_scenes.get(k)
        cand = val.strip() if isinstance(val, str) else ""
        if cand:
            cand_full = cand if os.path.isabs(cand) else os.path.join(GIFS_DIR, cand)
            if os.path.exists(cand_full):
                scene_gifs[k] = cand
                continue
        scene_gifs[k] = default_scene_gif_ref(k)
    st["scene_gifs"] = scene_gifs

    raw_texts = st.get("scene_texts") if isinstance(st.get("scene_texts"), dict) else {}
    scene_texts = {}
    for k in SCENE_KEYS:
        if SCENES_SPEC[k]["has_text"]:
            val = raw_texts.get(k)
            scene_texts[k] = val.strip() if isinstance(val, str) else SCENES_SPEC[k]["default_text"]
    st["scene_texts"] = scene_texts

    raw_on = st.get("scene_on") if isinstance(st.get("scene_on"), dict) else {}
    scene_on = {}
    for k in SCENE_KEYS:
        if SCENES_SPEC[k]["has_switch"]:
            val = raw_on.get(k)
            scene_on[k] = True if val is None else bool(val)
    st["scene_on"] = scene_on
    raw_preset = st.get("preset")
    if raw_preset in CHARACTER_PRESET_KEYS or raw_preset == "custom":
        st["preset"] = raw_preset
    else:
        matched = next(
            (pk for pk in CHARACTER_PRESET_KEYS if scene_gifs == resolve_preset_scene_gifs(pk)),
            None,
        )
        st["preset"] = matched if matched else "custom"
    st.pop("state_gifs", None)
    return st


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("floaters", [])
                    data["hidden_all"] = False
                    sched = normalize_work_schedule(data.get("work_schedule"))
                    data["work_schedule"] = sched
                    data["floaters"] = [
                        normalize_floater_state(st, idx, sched)
                        for idx, st in enumerate(data["floaters"])
                    ]
                    return data
        except Exception:
            pass
    return {
        "floaters": [],
        "hidden_all": False,
        "work_schedule": dict(DEFAULT_WORK_SCHEDULE),
    }


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def normalize_hhmm_input(text):
    """Normalize '0930', '930', '9:30' etc. into 'HH:MM' if valid; else return trimmed input."""
    if not isinstance(text, str):
        return ""
    s = text.strip()
    if s.isdigit():
        if len(s) == 4:
            cand = f"{s[:2]}:{s[2:]}"
            return cand if is_valid_hhmm(cand) else s
        if len(s) == 3:
            cand = f"0{s[0]}:{s[1:]}"
            return cand if is_valid_hhmm(cand) else s
    if ":" in s:
        parts = s.split(":")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
    return s


def is_valid_hhmm(text):
    if not isinstance(text, str):
        return False
    s = text.strip()
    if s.isdigit() and len(s) in (3, 4):
        s = f"{s[:2]}:{s[2:]}" if len(s) == 4 else f"0{s[0]}:{s[1:]}"
    parts = s.split(":")
    if len(parts) != 2:
        return False
    try:
        h = int(parts[0])
        m = int(parts[1])
        return 0 <= h <= 23 and 0 <= m <= 59
    except ValueError:
        return False


def parse_hhmm(text, default_minutes):
    norm = normalize_hhmm_input(text)
    if not is_valid_hhmm(norm):
        return default_minutes
    h, m = norm.split(":")
    return int(h) * 60 + int(m)


def format_minutes_korean(mins):
    mins = max(0, int(mins))
    h, m = divmod(mins, 60)
    if h > 0 and m > 0:
        return f"{h}시간 {m}분"
    if h > 0:
        return f"{h}시간"
    return f"{m}분"


def resolve_state_gif_path(scene_key):
    """Return absolute path to the default GIF for the given scene key, or None."""
    spec = SCENES_SPEC.get(scene_key)
    candidates = [spec["default_gif"], spec["fallback_gif"]] if spec else ["chiikawa_working.gif"]
    for cand in candidates:
        if not cand:
            continue
        path = cand if os.path.isabs(cand) else os.path.join(GIFS_DIR, cand)
        if os.path.exists(path):
            return path
    return None


def resolve_floater_state_gif_path(floater_state, scene_key):
    """Return absolute path to the GIF configured for a specific character's scene."""
    st = floater_state if isinstance(floater_state, dict) else {}
    scene_gifs = st.get("scene_gifs") if isinstance(st.get("scene_gifs"), dict) else {}
    cand = scene_gifs.get(scene_key)
    if isinstance(cand, str) and cand.strip():
        path = cand if os.path.isabs(cand) else os.path.join(GIFS_DIR, cand)
        if os.path.exists(path):
            return path
    return resolve_state_gif_path(scene_key)


def resolve_floater_scene_text(floater_state, scene_key):
    st = floater_state if isinstance(floater_state, dict) else {}
    spec = SCENES_SPEC.get(scene_key, {})
    if not spec.get("has_text"):
        return ""
    texts = st.get("scene_texts") if isinstance(st.get("scene_texts"), dict) else {}
    if scene_key in texts and isinstance(texts[scene_key], str):
        return texts[scene_key]
    return spec.get("default_text", "")


def compute_work_status(schedule, now=None, idle_sec=None, scene_on=None, scene_texts=None):
    schedule = normalize_work_schedule(schedule)
    if now is None:
        now = datetime.datetime.now()
    if idle_sec is None:
        idle_sec = get_idle_seconds()

    on_map = scene_on if isinstance(scene_on, dict) else {}
    txt_map = scene_texts if isinstance(scene_texts, dict) else {}

    def is_scene_on(key):
        if key not in SCENES_SPEC or not SCENES_SPEC[key]["has_switch"]:
            return True
        return True if on_map.get(key) is None else bool(on_map.get(key))

    def scene_text(key):
        if key in txt_map and isinstance(txt_map[key], str):
            return txt_map[key]
        return SCENES_SPEC.get(key, {}).get("default_text", "")

    cur_min = now.hour * 60 + now.minute
    start_m = parse_hhmm(schedule.get("start_time"), 8 * 60)
    end_m = parse_hhmm(schedule.get("end_time"), 17 * 60)
    if end_m <= start_m:
        end_m = min(23 * 60 + 59, start_m + 60)

    lunch_on = bool(schedule.get("lunch_on", True))
    lunch_s = parse_hhmm(schedule.get("lunch_start"), 12 * 60)
    lunch_e = parse_hhmm(schedule.get("lunch_end"), 13 * 60)

    total_span = max(1, end_m - start_m)
    raw_pct = (cur_min - start_m) * 100.0 / total_span
    progress_pct = max(0.0, min(100.0, raw_pct))

    remain_to_end_min = max(0, end_m - cur_min)
    remain_to_lunch_min = max(0, lunch_s - cur_min) if cur_min < lunch_s else 0
    bubble_fmt = schedule.get("bubble_time_format", "hm")

    def format_remain_for_bubble(mins):
        if bubble_fmt == "minutes":
            return f"{max(0, int(mins))}분"
        return format_minutes_korean(mins)

    work_days = schedule.get("work_days", [0, 1, 2, 3, 4])
    is_work_day = now.weekday() in work_days

    if not is_work_day:
        phase = "holiday"
        state_key = "rest"
        status_line = "[쉬는 날] 오늘 쉬는 날"
        idle_bubble_text = "쉬는 날"
    elif cur_min < start_m:
        remain_start_min = max(0, start_m - cur_min)
        if remain_start_min <= WAKE_LEAD_MINUTES and is_scene_on("wake"):
            phase = "wake"
            state_key = "wake"
            status_line = f"[출근 임박] 출근까지 {format_minutes_korean(remain_start_min)}"
            idle_bubble_text = scene_text("wake") or f"출근 {format_remain_for_bubble(remain_start_min)} 전"
        else:
            phase = "before_work"
            state_key = "rest"
            status_line = f"[출근 전] 출근까지 {format_minutes_korean(remain_start_min)}"
            idle_bubble_text = f"출근 {format_remain_for_bubble(remain_start_min)} 전"
    elif cur_min >= end_m:
        overtime_min = cur_min - end_m
        is_pc_active = (float(idle_sec) < ACTIVE_INPUT_SECONDS)
        if overtime_min >= 20 and is_pc_active and is_scene_on("tired"):
            phase = "overtime_tired"
            state_key = "tired"
            txt = scene_text("tired")
            status_line = f"[야근 20분+] 퇴근 후 {format_minutes_korean(overtime_min)}"
            idle_bubble_text = txt
        elif overtime_min >= 5 and is_pc_active and is_scene_on("back"):
            phase = "overtime_back"
            state_key = "back"
            txt = scene_text("back")
            status_line = f"[야근] 퇴근 후 {format_minutes_korean(overtime_min)}"
            idle_bubble_text = txt
        else:
            phase = "after_work"
            state_key = "enter"
            txt = scene_text("enter")
            status_line = f"[퇴근] {txt or '퇴근이다!'}"
            idle_bubble_text = txt
    elif lunch_on and lunch_s < lunch_e and lunch_s <= cur_min < lunch_e and is_scene_on("lunch"):
        phase = "lunch"
        state_key = "lunch"
        txt = scene_text("lunch")
        status_line = f"[점심] {int(round(progress_pct))}% | 퇴근까지 {format_minutes_korean(remain_to_end_min)}"
        idle_bubble_text = txt or f"퇴근 {format_remain_for_bubble(remain_to_end_min)} 전"
    elif cur_min < lunch_s:
        phase = "working_am"
        state_key = "type"
        status_line = f"[근무 중] {int(round(progress_pct))}% | 퇴근까지 {format_minutes_korean(remain_to_end_min)}"
        idle_bubble_text = f"퇴근 {format_remain_for_bubble(remain_to_end_min)} 전"
    else:
        phase = "working_pm"
        state_key = "type"
        status_line = f"[근무 중] {int(round(progress_pct))}% | 퇴근까지 {format_minutes_korean(remain_to_end_min)}"
        idle_bubble_text = f"퇴근 {format_remain_for_bubble(remain_to_end_min)} 전"

    forced = schedule.get("forced_state", "auto")
    if forced in SCENE_KEYS:
        effective_state_key = forced
    else:
        effective_state_key = state_key

    state_label = WORK_STATE_LABELS.get(effective_state_key, "근무 중")
    if forced in SCENE_KEYS and effective_state_key != state_key:
        status_line = f"[수동: {state_label}] {status_line}"

    return {
        "phase": phase,
        "state_key": state_key,
        "effective_state_key": effective_state_key,
        "state_label": state_label,
        "is_work_day": is_work_day,
        "cur_min": cur_min,
        "start_min": start_m,
        "end_min": end_m,
        "lunch_on": lunch_on,
        "lunch_start_min": lunch_s,
        "lunch_end_min": lunch_e,
        "progress_pct": progress_pct,
        "remain_to_end_min": remain_to_end_min,
        "remain_to_lunch_min": remain_to_lunch_min,
        "status_line": status_line,
        "idle_bubble_text": idle_bubble_text,
    }


def _load_bubble_font(size=13, bold=False):
    candidates = []
    if os.path.exists(HAND_FONT_PATH):
        candidates.append(HAND_FONT_PATH)
    if bold:
        candidates.extend([
            r"C:\Windows\Fonts\malgunbd.ttf",
            r"C:\Windows\Fonts\malgun.ttf",
            r"C:\Windows\Fonts\gulim.ttc",
        ])
    else:
        candidates.extend([
            r"C:\Windows\Fonts\malgun.ttf",
            r"C:\Windows\Fonts\malgunbd.ttf",
            r"C:\Windows\Fonts\gulim.ttc",
        ])
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_bubble_lines(text, font, draw, max_width=240):
    lines = []
    for raw_line in (text or "").splitlines() or [""]:
        if not raw_line:
            lines.append("")
            continue
        current = ""
        for ch in raw_line:
            test = current + ch
            bbox = draw.textbbox((0, 0), test, font=font)
            if current and (bbox[2] - bbox[0]) > max_width:
                lines.append(current.rstrip())
                current = ch.lstrip()
            else:
                current = test
        if current:
            lines.append(current)
    return lines or [""]


def _sample_segment(x0, y0, x1, y1, step=8.0):
    dist = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(round(dist / step)))
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n)]


def _sample_arc(cx, cy, r, start_deg, end_deg, steps=5):
    pts = []
    for i in range(steps):
        ang = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    return pts


def _get_monitor_rect(x, y, info_key="Monitor", fallback_win=None, w=0, h=0):
    monitor_default_to_nearest = 2
    if _WIN32_CTYPES_READY:
        try:
            if int(w) > 0 and int(h) > 0:
                rc = wintypes.RECT(int(x), int(y), int(x) + int(w), int(y) + int(h))
                hmon = ctypes.windll.user32.MonitorFromRect(ctypes.byref(rc), monitor_default_to_nearest)
            else:
                pt = wintypes.POINT(int(x), int(y))
                hmon = ctypes.windll.user32.MonitorFromPoint(pt, monitor_default_to_nearest)
            if hmon:
                mi = _MONITORINFO()
                mi.cbSize = ctypes.sizeof(_MONITORINFO)
                if ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                    r = mi.rcWork if info_key == "Work" else mi.rcMonitor
                    return (int(r.left), int(r.top), int(r.right), int(r.bottom))
        except Exception:
            pass

    if HAS_WIN32:
        try:
            if int(w) > 0 and int(h) > 0:
                hmon = win32api.MonitorFromRect(
                    (int(x), int(y), int(x) + int(w), int(y) + int(h)),
                    win32con.MONITOR_DEFAULTTONEAREST,
                )
            else:
                hmon = win32api.MonitorFromPoint((int(x), int(y)), win32con.MONITOR_DEFAULTTONEAREST)
            info = win32api.GetMonitorInfo(hmon)
            rect = info.get(info_key)
            if rect and len(rect) == 4:
                return tuple(int(v) for v in rect)
        except Exception:
            pass

    bottom_pad = 48 if info_key == "Work" else 0
    if HAS_CTYPES_WIN32:
        try:
            u32 = ctypes.windll.user32
            vx = int(u32.GetSystemMetrics(76))
            vy = int(u32.GetSystemMetrics(77))
            vw = int(u32.GetSystemMetrics(78))
            vh = int(u32.GetSystemMetrics(79))
            if vw > 0 and vh > 0:
                return (vx, vy, vx + vw, max(vy + 200, vy + vh - bottom_pad))
        except Exception:
            pass

    if fallback_win is not None:
        try:
            sw = int(fallback_win.winfo_screenwidth())
            sh = int(fallback_win.winfo_screenheight())
            return (0, 0, sw, max(200, sh - bottom_pad))
        except Exception:
            pass
    return (0, 0, 1920, 1080 - bottom_pad)


def get_monitor_rect_for_point(x, y, fallback_win=None):
    """Return (left, top, right, bottom) of the monitor containing (x, y)."""
    return _get_monitor_rect(x, y, info_key="Monitor", fallback_win=fallback_win)


def get_monitor_work_rect_for_point(x, y, fallback_win=None):
    """Return (left, top, right, bottom) usable work area (excluding taskbar) for (x, y)."""
    return _get_monitor_rect(x, y, info_key="Work", fallback_win=fallback_win)


def get_monitor_rect_for_rect(x, y, w, h, fallback_win=None):
    """Return (left, top, right, bottom) of the monitor overlapping the given rectangle."""
    return _get_monitor_rect(x, y, info_key="Monitor", fallback_win=fallback_win, w=w, h=h)


def get_monitor_work_rect_for_rect(x, y, w, h, fallback_win=None):
    """Return (left, top, right, bottom) usable work area overlapping the given rectangle."""
    return _get_monitor_rect(x, y, info_key="Work", fallback_win=fallback_win, w=w, h=h)


def compute_bubble_scale(char_size):
    """Scale speech bubble size proportionally to character display size (base 180px)."""
    safe_size = max(48, int(char_size or 180))
    return max(0.58, min(1.60, (safe_size / 180.0) ** 0.58))


def _build_sketch_bubble_points(bx0, by0, bx1, by1, tail_top, scale, amp=0.9, phase=0.0, b_scale=1.0):
    """Build closed polygon points for a rounded speech bubble with slight hand-drawn pen wobble."""
    r = max(6.0, min(11.0 * b_scale, (by1 - by0) / 2.2, (bx1 - bx0) / 2.2))
    half_tail = max(4.0, 7.0 * b_scale)
    tail_len = max(5.5, 9.5 * b_scale)
    slant = 2.0 * b_scale
    step_len = max(5.0, 8.0 * b_scale)
    eff_amp = amp * b_scale

    cx = (bx0 + bx1) / 2.0
    raw = []

    # Top-left arc (180 -> 270)
    raw.extend(_sample_arc(bx0 + r, by0 + r, r, 180, 270, 4))
    # Top edge
    if tail_top:
        raw.extend(_sample_segment(bx0 + r, by0, cx - half_tail, by0, step_len))
        raw.append((cx - half_tail, by0))
        raw.append((cx - slant, by0 - tail_len))
        raw.append((cx + half_tail, by0))
        raw.extend(_sample_segment(cx + half_tail, by0, bx1 - r, by0, step_len))
    else:
        raw.extend(_sample_segment(bx0 + r, by0, bx1 - r, by0, step_len))

    # Top-right arc (270 -> 360)
    raw.extend(_sample_arc(bx1 - r, by0 + r, r, 270, 360, 4))
    # Right edge
    raw.extend(_sample_segment(bx1, by0 + r, bx1, by1 - r, step_len))
    # Bottom-right arc (0 -> 90)
    raw.extend(_sample_arc(bx1 - r, by1 - r, r, 0, 90, 4))

    # Bottom edge (right to left)
    if not tail_top:
        raw.extend(_sample_segment(bx1 - r, by1, cx + half_tail, by1, step_len))
        raw.append((cx + half_tail, by1))
        raw.append((cx - slant, by1 + tail_len))
        raw.append((cx - half_tail, by1))
        raw.extend(_sample_segment(cx - half_tail, by1, bx0 + r, by1, step_len))
    else:
        raw.extend(_sample_segment(bx1 - r, by1, bx0 + r, by1, step_len))

    # Bottom-left arc (90 -> 180)
    raw.extend(_sample_arc(bx0 + r, by1 - r, r, 90, 180, 4))
    # Left edge (bottom to top)
    raw.extend(_sample_segment(bx0, by1 - r, bx0, by0 + r, step_len))

    wobbled = []
    for idx, (px, py) in enumerate(raw):
        ox = eff_amp * math.sin(idx * 1.17 + phase)
        oy = eff_amp * math.cos(idx * 1.43 + phase * 1.3)
        wobbled.append(((px + ox) * scale, (py + oy) * scale))
    return wobbled


def _strip_unsupported_glyphs(text, font):
    """Drop characters missing from the active font so tofu boxes never render."""
    if not text:
        return ""
    try:
        notdef = bytes(font.getmask("\ufffe"))
    except Exception:
        return text
    out = []
    for ch in text:
        if ch == "\n" or ord(ch) <= 127:
            out.append(ch)
            continue
        try:
            if bytes(font.getmask(ch)) != notdef:
                out.append(ch)
        except Exception:
            pass
    return "".join(out)


def render_speech_bubble_rgba(text, tail_top=False, char_size=180):
    """Render a minimal monochrome (black & white) pen-sketch speech bubble scaled to char_size."""
    b_scale = compute_bubble_scale(char_size)
    base_pt = 16 if os.path.exists(HAND_FONT_PATH) else 13
    font_size = max(10, int(round(base_pt * b_scale)))
    font_reg = _load_bubble_font(font_size, bold=False)
    safe_text = _strip_unsupported_glyphs(text, font_reg)
    scratch = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(scratch)

    max_width = max(120, int(round(245 * b_scale)))
    lines = _wrap_bubble_lines(safe_text, font_reg, s_draw, max_width=max_width)
    line_gap = max(2, int(round(5 * b_scale)))

    line_metrics = []
    max_line_w = max(16, int(round(24 * b_scale)))
    total_text_h = 0
    for idx, line in enumerate(lines):
        sample = line if line else "가"
        lb = s_draw.textbbox((0, 0), sample, font=font_reg)
        lw = (lb[2] - lb[0]) if line else 0
        lh = max(10, lb[3] - lb[1])
        line_metrics.append((line, lb[0], lb[1], lw, lh))
        max_line_w = max(max_line_w, lw)
        total_text_h += lh + (line_gap if idx > 0 else 0)

    pad_left = max(7, int(round(14 * b_scale)))
    pad_right = pad_left
    pad_top = max(5, int(round(11 * b_scale)))
    pad_bottom = pad_top

    tail_h = max(6, int(round(11 * b_scale)))
    shadow_pad = max(2, int(round(4 * b_scale)))
    margin_x = max(2, int(round(3 * b_scale)))

    box_w = pad_left + max_line_w + pad_right
    box_h = pad_top + total_text_h + pad_bottom

    top_margin = tail_h + margin_x if tail_top else margin_x + 1
    bottom_margin = tail_h + shadow_pad + margin_x if not tail_top else shadow_pad + margin_x + 1
    total_w = box_w + shadow_pad + margin_x * 2
    total_h = top_margin + box_h + bottom_margin

    bx0 = float(margin_x)
    by0 = float(top_margin)
    bx1 = float(margin_x + box_w)
    by1 = float(top_margin + box_h)

    S = 2
    WHITE = (255, 255, 255, 255)
    BLACK = (18, 18, 18, 255)

    canvas = Image.new("RGBA", (total_w * S, total_h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)

    pts_main = _build_sketch_bubble_points(bx0, by0, bx1, by1, tail_top, S, amp=0.65, phase=0.4, b_scale=b_scale)
    pts_sketch = _build_sketch_bubble_points(bx0, by0, bx1, by1, tail_top, S, amp=1.15, phase=2.2, b_scale=b_scale)

    # Layer 1: Black diagonal pen-hatching shadow
    sh_off = max(2, int(round(3 * b_scale))) * S
    shadow_pts = [(x + sh_off, y + sh_off) for x, y in pts_main]
    hatch_mask = Image.new("L", (total_w * S, total_h * S), 0)
    ImageDraw.Draw(hatch_mask).polygon(shadow_pts, fill=255)
    hatch_layer = Image.new("RGBA", (total_w * S, total_h * S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hatch_layer)
    max_span = (total_w + total_h) * S
    hatch_step = max(4, int(round(4 * b_scale)) * S)
    hatch_w = max(1, int(round(1.0 * b_scale * S)))
    for k in range(0, max_span, hatch_step):
        hd.line([(k, 0), (0, k)], fill=BLACK, width=hatch_w)
    canvas.paste(hatch_layer, (0, 0), hatch_mask)

    # Layer 2: Pure white paper interior
    d.polygon(pts_main, fill=WHITE)

    # Layer 3: Double pen-sketch black outline
    closed_main = pts_main + [pts_main[0]]
    closed_sketch = pts_sketch + [pts_sketch[0]]
    d.line(closed_sketch, fill=BLACK, width=max(1, int(round(1.0 * b_scale * S))), joint="curve")
    d.line(closed_main, fill=BLACK, width=max(2, int(round(1.8 * b_scale * S))), joint="curve")

    # Downsample sketch art to 1x, then draw crisp centered monochrome text
    img_1x = canvas.resize((total_w, total_h), Image.Resampling.BILINEAR)
    t_draw = ImageDraw.Draw(img_1x)

    cur_y = int(by0) + pad_top
    for line, off_x, off_y, lw, lh in line_metrics:
        if line:
            text_x = int(bx0) + pad_left + max(0, (max_line_w - lw) // 2)
            t_draw.text((text_x - off_x, cur_y - off_y), line, font=font_reg, fill=BLACK)
        cur_y += lh + line_gap

    r, g, b, a = img_1x.split()
    mask = a.point(lambda p: 255 if p >= 128 else 0)
    rgb = Image.merge("RGB", (r, g, b))
    key_bg = Image.new("RGB", img_1x.size, TRANSPARENT_RGB)
    composited = Image.composite(rgb, key_bg, mask)
    return ImageTk.PhotoImage(composited)


def decode_animation(file_path):
    """Load GIF or static image into a list of (RGBA Image, delay_ms)."""
    frames = []
    with Image.open(file_path) as im:
        is_gif = getattr(im, "is_animated", False)
        if is_gif:
            for frame in ImageSequence.Iterator(im):
                rgba = frame.convert("RGBA")
                delay = int(frame.info.get("duration", im.info.get("duration", 100)) or 100)
                if delay <= 10:
                    delay = 100
                frames.append((rgba, delay))
        else:
            frames.append((im.convert("RGBA"), 500))
    if not frames:
        raise ValueError("이미지에 프레임이 없습니다.")
    return frames


def prepare_tk_photo(rgba_img, target_w, target_h, flip_h):
    """Resize/flip RGBA frame and key out transparent pixels cleanly for Tkinter."""
    img = rgba_img
    if flip_h:
        img = ImageOps.mirror(img)
    if img.size != (target_w, target_h):
        img = img.resize((target_w, target_h), Image.Resampling.BILINEAR)

    r, g, b, a = img.split()
    mask = a.point(lambda p: 255 if p >= 128 else 0)

    rgb = Image.merge("RGB", (r, g, b))
    key_bg = Image.new("RGB", (target_w, target_h), TRANSPARENT_RGB)
    composited = Image.composite(rgb, key_bg, mask)
    return ImageTk.PhotoImage(composited)


def build_placeholder_rgba():
    img = Image.new("RGBA", (210, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, 205, 115], radius=18, fill=(255, 250, 252, 255), outline=(90, 70, 65, 255), width=3)
    d.text((22, 46), "Right-click to pick GIF!", fill=(75, 58, 52, 255))
    return [(img, 500)]


class SpeechBubbleWindow:
    """Floating transparent speech bubble linked to a FloaterWindow."""

    def __init__(self, floater):
        self.floater = floater
        self.win = tk.Toplevel(floater.win)
        self.win.overrideredirect(True)
        self.win.configure(bg=TRANSPARENT_HEX)
        self.win.attributes("-transparentcolor", TRANSPARENT_HEX)
        self.win.withdraw()

        self.label = tk.Label(self.win, bg=TRANSPARENT_HEX, bd=0, highlightthickness=0)
        self.label.pack()
        self.label.bind("<Button-1>", lambda _e: self.hide())

        self._photo = None
        self._hide_after_id = None
        self._pop_after_id = None
        self._visible = False
        self._tail_top = False
        self._current_text = None
        self._temp_event_active = False
        self._is_persistent = False
        self._rendered_char_size = None
        self._apply_toolwindow_style()

    def _should_flip_tail_top(self, fx, fy, fw, fh, bh):
        _, m_top, _, _ = get_monitor_rect_for_rect(fx, fy, fw, fh, self.win)
        return (fy - bh - 4) < (m_top + 8)

    def _apply_toolwindow_style(self):
        if not HAS_WIN32:
            return
        try:
            self.win.update_idletasks()
            frame_hex = self.win.wm_frame()
            hwnd = int(frame_hex, 16) if frame_hex and frame_hex != "0x0" else self.win.winfo_id()
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TRANSPARENT | 0x08000000
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)
        except Exception:
            pass

    def _cancel_pop(self):
        if self._pop_after_id is not None:
            try:
                self.win.after_cancel(self._pop_after_id)
            except Exception:
                pass
            self._pop_after_id = None

    def show_persistent(self, text):
        if self.floater.suppressed_hidden or not self.floater.state.get("bubble_on", True):
            self.hide()
            return
        if self._temp_event_active:
            return
        if not text or not str(text).strip():
            self.hide()
            return

        fw, fh = self.floater.target_size()
        fx = int(self.floater.state.get("x", 0))
        fy = int(self.floater.state.get("y", 0))
        char_size = max(fw, fh)

        if (
            self._visible
            and self._is_persistent
            and self._current_text == text
            and self._rendered_char_size == char_size
            and self._photo
        ):
            self._place_relative(fx, fy, fw, fh, self._photo.width(), self._photo.height())
            return

        self._cancel_pop()
        if self._hide_after_id is not None:
            try:
                self.win.after_cancel(self._hide_after_id)
            except Exception:
                pass
            self._hide_after_id = None

        photo = render_speech_bubble_rgba(text, tail_top=False, char_size=char_size)
        bw, bh = photo.width(), photo.height()
        tail_top = self._should_flip_tail_top(fx, fy, fw, fh, bh)
        if tail_top:
            photo = render_speech_bubble_rgba(text, tail_top=True, char_size=char_size)
            bw, bh = photo.width(), photo.height()

        self._tail_top = tail_top
        self._photo = photo
        self._current_text = text
        self._rendered_char_size = char_size
        self._is_persistent = True
        self._temp_event_active = False
        self.label.configure(image=photo)
        self.label.image = photo

        self._place_relative(fx, fy, fw, fh, bw, bh, y_offset=0)
        self.win.attributes("-topmost", bool(self.floater.state.get("topmost", True)))
        self.win.deiconify()
        self.win.lift()
        self._apply_toolwindow_style()
        self._visible = True

    def show_message(self, text, duration_ms=6500, respect_bubble_on=True):
        if self.floater.suppressed_hidden:
            return
        if respect_bubble_on and not self.floater.state.get("bubble_on", True):
            return
        if not text or not str(text).strip():
            return

        self._cancel_pop()
        if self._hide_after_id is not None:
            try:
                self.win.after_cancel(self._hide_after_id)
            except Exception:
                pass
            self._hide_after_id = None

        fw, fh = self.floater.target_size()
        fx = int(self.floater.state.get("x", 0))
        fy = int(self.floater.state.get("y", 0))
        char_size = max(fw, fh)

        # Measure first with default bottom tail; flip to top tail if too close to top edge
        photo = render_speech_bubble_rgba(text, tail_top=False, char_size=char_size)
        bw, bh = photo.width(), photo.height()
        tail_top = self._should_flip_tail_top(fx, fy, fw, fh, bh)
        if tail_top:
            photo = render_speech_bubble_rgba(text, tail_top=True, char_size=char_size)
            bw, bh = photo.width(), photo.height()

        self._tail_top = tail_top
        self._photo = photo
        self._current_text = text
        self._rendered_char_size = char_size
        self._temp_event_active = True
        self._is_persistent = False
        self.label.configure(image=photo)
        self.label.image = photo

        self._place_relative(fx, fy, fw, fh, bw, bh, y_offset=6)
        self.win.attributes("-topmost", bool(self.floater.state.get("topmost", True)))
        self.win.deiconify()
        self.win.lift()
        self._apply_toolwindow_style()
        self._visible = True

        self._start_pop_animation()
        self._hide_after_id = self.win.after(max(1500, int(duration_ms)), self._on_temp_timeout)

    def _on_temp_timeout(self):
        self._hide_after_id = None
        self._temp_event_active = False
        self._current_text = None
        self.floater.app.refresh_idle_bubbles()

    def _start_pop_animation(self):
        offsets = (-2, 0)

        def step(idx):
            self._pop_after_id = None
            if not self._visible or not self._photo or idx >= len(offsets):
                return
            fw, fh = self.floater.target_size()
            fx = int(self.floater.state.get("x", 0))
            fy = int(self.floater.state.get("y", 0))
            self._place_relative(fx, fy, fw, fh, self._photo.width(), self._photo.height(), y_offset=offsets[idx])
            if idx + 1 < len(offsets):
                self._pop_after_id = self.win.after(25, lambda: step(idx + 1))

        self._pop_after_id = self.win.after(25, lambda: step(0))

    def _place_relative(self, fx, fy, fw, fh, bw, bh, y_offset=0):
        cx = fx + fw // 2
        cy = fy + fh // 2
        m_left, m_top, m_right, m_bottom = get_monitor_rect_for_rect(fx, fy, fw, fh, self.win)

        x = fx + (fw - bw) // 2
        if m_left <= cx < m_right and (m_right - m_left) >= bw + 8:
            x = max(m_left + 4, min(m_right - bw - 4, x))

        if self._tail_top:
            y = fy + fh + 4 + y_offset
            if m_top <= cy < m_bottom and (m_bottom - m_top) >= bh + 8:
                y = min(m_bottom - bh - 4, y)
        else:
            y = fy - bh - 4 + y_offset
            if m_top <= cy < m_bottom and (m_bottom - m_top) >= bh + 8:
                y = max(m_top + 4, y)

        _set_window_geometry(self.win, x, y, bw, bh)

    def update_position(self):
        if not self._visible or not self._photo:
            return
        self._cancel_pop()
        fw, fh = self.floater.target_size()
        fx = int(self.floater.state.get("x", 0))
        fy = int(self.floater.state.get("y", 0))
        char_size = max(fw, fh)

        if self._current_text is not None and self._rendered_char_size != char_size:
            photo = render_speech_bubble_rgba(self._current_text, tail_top=False, char_size=char_size)
            bw, bh = photo.width(), photo.height()
            tail_top = self._should_flip_tail_top(fx, fy, fw, fh, bh)
            if tail_top:
                photo = render_speech_bubble_rgba(self._current_text, tail_top=True, char_size=char_size)
                bw, bh = photo.width(), photo.height()
            self._tail_top = tail_top
            self._photo = photo
            self._rendered_char_size = char_size
            self.label.configure(image=photo)
            self.label.image = photo

        self._place_relative(fx, fy, fw, fh, self._photo.width(), self._photo.height())

    def hide(self):
        self._cancel_pop()
        if self._hide_after_id is not None:
            try:
                self.win.after_cancel(self._hide_after_id)
            except Exception:
                pass
            self._hide_after_id = None
        self._visible = False
        self._temp_event_active = False
        self._is_persistent = False
        self._current_text = None
        try:
            self.win.withdraw()
        except Exception:
            pass

    def destroy(self):
        self.hide()
        try:
            self.win.destroy()
        except Exception:
            pass


class ParticleOverlayWindow:
    """Click-through transparent celebration particle overlay around a FloaterWindow."""

    COLORS = ("#F4B6C2", "#FFD666", "#8CBEE6", "#A0DCAA", "#FFA078", "#FFFFFF")
    SHAPES = ("confetti", "star", "ribbon")

    def __init__(self, floater):
        self.floater = floater
        self.W = 640
        self.H = 520

        self.win = tk.Toplevel(floater.win)
        self.win.overrideredirect(True)
        self.win.configure(bg=TRANSPARENT_HEX)
        self.win.attributes("-transparentcolor", TRANSPARENT_HEX)
        self.win.withdraw()

        self.canvas = tk.Canvas(
            self.win,
            width=self.W,
            height=self.H,
            bg=TRANSPARENT_HEX,
            bd=0,
            highlightthickness=0,
        )
        self.canvas.pack()

        self._particles = []
        self._active = False
        self._anim_after_id = None
        self._second_burst_after_id = None
        self._end_time = 0.0
        self._win_x = 0
        self._win_y = 0
        self._apply_clickthrough_style()

    def _apply_clickthrough_style(self):
        if not HAS_WIN32:
            return
        try:
            self.win.update_idletasks()
            frame_hex = self.win.wm_frame()
            hwnd = int(frame_hex, 16) if frame_hex and frame_hex != "0x0" else self.win.winfo_id()
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TRANSPARENT | 0x08000000
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)
        except Exception:
            pass

    def _place_around_floater(self):
        fw, fh = self.floater.target_size()
        fx = int(self.floater.state.get("x", 0))
        fy = int(self.floater.state.get("y", 0))

        wx = fx + fw // 2 - self.W // 2
        _, m_top, _, _ = get_monitor_rect_for_rect(fx, fy, fw, fh, self.win)
        if fy < m_top + 240:
            wy = fy - 120
        else:
            wy = fy + fh + 80 - self.H
        self._win_x = wx
        self._win_y = wy
        _set_window_geometry(self.win, wx, wy, self.W, self.H)

    def _floater_local_center(self):
        fw, fh = self.floater.target_size()
        fx = int(self.floater.state.get("x", 0))
        fy = int(self.floater.state.get("y", 0))
        cx = fx + fw / 2.0 - self._win_x
        cy = fy + fh / 2.0 - self._win_y
        return cx, cy, fw, fh

    def _spawn_burst(self, count, mode="sides"):
        cx, cy, fw, _fh = self._floater_local_center()
        for idx in range(count):
            if mode == "sky":
                ox = cx + random.uniform(-110, 110)
                oy = max(36.0, cy - random.uniform(110, 180))
                ang = math.radians(random.uniform(-160, -20))
                spd = random.uniform(4.0, 10.5)
            else:
                side = -1 if idx % 2 == 0 else 1
                ox = cx + side * max(16.0, fw * 0.35) + random.uniform(-10, 10)
                oy = cy + random.uniform(-14, 10)
                base_deg = -62 if side > 0 else -118
                ang = math.radians(base_deg + random.uniform(-34, 34))
                spd = random.uniform(7.5, 17.5)

            self._particles.append({
                "x": ox,
                "y": oy,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "gravity": random.uniform(0.28, 0.44),
                "drag": 0.965,
                "size": random.uniform(6.0, 10.5),
                "shape": random.choice(self.SHAPES),
                "color": random.choice(self.COLORS),
                "angle": random.uniform(0, math.tau),
                "spin": random.uniform(0, math.tau),
                "v_angle": random.uniform(-0.18, 0.18),
                "v_spin": random.uniform(0.14, 0.34),
                "sway_phase": random.uniform(0, math.tau),
                "sway_amp": random.uniform(0.6, 1.8),
            })

    def burst(self, duration_ms=4800):
        if self.floater.suppressed_hidden:
            return
        self.stop()

        self._active = True
        self._end_time = time.time() + max(1000, int(duration_ms)) / 1000.0
        self._place_around_floater()

        self.win.attributes("-topmost", bool(self.floater.state.get("topmost", True)))
        self.win.deiconify()
        self.win.lift()
        if self.floater.bubble._visible:
            self.floater.bubble.win.lift()
        self._apply_clickthrough_style()

        self._spawn_burst(75, mode="sides")
        self._draw_particles()
        self._second_burst_after_id = self.win.after(650, self._trigger_second_burst)
        self._anim_after_id = self.win.after(28, self._tick)

    def _trigger_second_burst(self):
        self._second_burst_after_id = None
        if not self._active:
            return
        self._spawn_burst(45, mode="sky")

    def _tick(self):
        self._anim_after_id = None
        if not self._active:
            return
        self._step_particles()
        if time.time() >= self._end_time or not self._particles:
            self.stop()
            return
        self._anim_after_id = self.win.after(28, self._tick)

    def _step_particles(self):
        if not self._active:
            return
        alive = []
        for p in self._particles:
            p["vx"] *= p["drag"]
            p["vy"] = min(6.5, p["vy"] * p["drag"] + p["gravity"])
            p["sway_phase"] += 0.22
            p["x"] += p["vx"] + (math.sin(p["sway_phase"]) * p["sway_amp"] if p["vy"] > 0 else 0.0)
            p["y"] += p["vy"]
            p["angle"] += p["v_angle"]
            p["spin"] += p["v_spin"]
            if -40 <= p["x"] <= self.W + 40 and p["y"] <= self.H + 24:
                alive.append(p)
        self._particles = alive
        self._draw_particles()

    def _draw_particles(self):
        self.canvas.delete("all")
        outline = "#121212"
        for p in self._particles:
            x, y = p["x"], p["y"]
            sz = p["size"]
            ang = p["angle"]
            col = p["color"]
            shape = p["shape"]

            if shape == "star":
                pts = []
                for i in range(10):
                    a = ang + i * math.pi / 5.0
                    r = sz if i % 2 == 0 else sz * 0.46
                    pts.extend((x + math.cos(a) * r, y + math.sin(a) * r))
                self.canvas.create_polygon(pts, fill=col, outline=outline, width=1.4)
            elif shape == "ribbon":
                ca, sa = math.cos(ang), math.sin(ang)
                w, h = sz * 1.15, sz * 0.38
                corners = [(-w, -h), (w, -h * 0.5), (w, h), (-w, h * 0.5)]
                pts = []
                for rx, ry in corners:
                    pts.extend((x + rx * ca - ry * sa, y + rx * sa + ry * ca))
                self.canvas.create_polygon(pts, fill=col, outline=outline, width=1.3)
            else:
                # 3D fluttering confetti rectangle
                ca, sa = math.cos(ang), math.sin(ang)
                w = sz * 0.72 * max(0.24, abs(math.cos(p["spin"])))
                h = sz * 0.48
                corners = [(-w, -h), (w, -h), (w, h), (-w, h)]
                pts = []
                for rx, ry in corners:
                    pts.extend((x + rx * ca - ry * sa, y + rx * sa + ry * ca))
                self.canvas.create_polygon(pts, fill=col, outline=outline, width=1.3)

    def update_position(self):
        if not self._active:
            return
        self._place_around_floater()

    def stop(self):
        if self._anim_after_id is not None:
            try:
                self.win.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None
        if self._second_burst_after_id is not None:
            try:
                self.win.after_cancel(self._second_burst_after_id)
            except Exception:
                pass
            self._second_burst_after_id = None
        self._active = False
        self._particles = []
        try:
            self.canvas.delete("all")
            self.win.withdraw()
        except Exception:
            pass

    def destroy(self):
        self.stop()
        try:
            self.win.destroy()
        except Exception:
            pass


class FloaterWindow:
    def __init__(self, app, state):
        self.app = app
        self.state = state

        self.win = tk.Toplevel(app.root)
        self.win.title(APP_NAME)
        self.win.overrideredirect(True)
        self.win.configure(bg=TRANSPARENT_HEX)
        self.win.attributes("-transparentcolor", TRANSPARENT_HEX)

        self.label = tk.Label(self.win, bg=TRANSPARENT_HEX, bd=0, highlightthickness=0)
        self.label.pack()

        self.raw_frames = []
        self._tk_frames_normal = []
        self._tk_frames_flipped = []
        self.tk_frames = []
        self.src_w = 180
        self.src_h = 180
        self.frame_idx = 0
        self.after_id = None
        self.suppressed_hidden = False
        self._facing_left = False

        self._dragging = False
        self._drag_moved = False
        self._action_after_id = None
        self._temp_gif_after_id = None
        self._saved_anim_backup = None
        self._wander_after_id = None
        self._walking = False
        self._walk_fx = float(self.state["x"])
        self._walk_tx = float(self.state["x"])
        self._walk_speed_px = 2.6
        self._social_hold_until = 0.0
        self._last_avoid_ts = 0.0
        self._next_random_ts = time.time() + self.next_random_cheer_delay()

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._win_start_x = 0
        self._win_start_y = 0

        self.label.bind("<ButtonPress-1>", self.on_mouse_down)
        self.label.bind("<B1-Motion>", self.on_mouse_drag)
        self.label.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.label.bind("<Double-Button-1>", self.on_double_click)
        self.label.bind("<Button-3>", self.on_right_click)
        self.win.bind("<MouseWheel>", self.on_mouse_wheel)
        self.label.bind("<MouseWheel>", self.on_mouse_wheel)
        self.win.bind("<Key>", self.on_key)

        self.menu = tk.Menu(self.win, tearoff=0)
        self.bubble = SpeechBubbleWindow(self)
        self.particles = ParticleOverlayWindow(self)

        self.load_initial_gif()
        self.apply_window_flags()
        _set_window_geometry(self.win, int(self.state["x"]), int(self.state["y"]))
        self.sync_wander_state()

    def load_initial_gif(self):
        path = self.state.get("gif_path")
        if not path or not os.path.exists(path):
            gifs = get_available_gifs()
            if gifs:
                path = gifs[0]
                self.state["gif_path"] = path

        if path and os.path.exists(path):
            try:
                self.load_gif(path, save=False)
                return
            except Exception:
                pass

        self.raw_frames = build_placeholder_rgba()
        self.src_w, self.src_h = self.raw_frames[0][0].size
        self.rebuild_tk_frames()
        self.show_frame(0)

    def load_gif(self, path, save=True):
        self._cancel_temp_gif(restore=False)
        self.stop_animation()
        self.raw_frames = decode_animation(path)
        self.src_w, self.src_h = self.raw_frames[0][0].size
        self.state["gif_path"] = path
        self.frame_idx = 0
        self.rebuild_tk_frames()
        self.show_frame(0)
        self.schedule_next_frame()
        self.bubble.update_position()
        if save:
            self.app.save()

    def target_size(self):
        disp = int(self.state.get("display_size", 180))
        if disp <= 0:
            return self.src_w, self.src_h
        scale = disp / max(self.src_w, self.src_h)
        return max(24, int(round(self.src_w * scale))), max(24, int(round(self.src_h * scale)))

    def rebuild_tk_frames(self):
        tw, th = self.target_size()
        self._tk_frames_normal = [
            (prepare_tk_photo(rgba, tw, th, False), delay)
            for rgba, delay in self.raw_frames
        ]
        self._tk_frames_flipped = [
            (prepare_tk_photo(rgba, tw, th, True), delay)
            for rgba, delay in self.raw_frames
        ]
        self._update_active_tk_frames()
        _set_window_geometry(self.win, int(self.state.get("x", 0)), int(self.state.get("y", 0)), tw, th)

    def _update_active_tk_frames(self):
        effective_flip = bool(self.state.get("flip_h", False)) ^ bool(self._facing_left)
        self.tk_frames = self._tk_frames_flipped if effective_flip else self._tk_frames_normal

    def show_frame(self, idx):
        if not self.tk_frames:
            return
        self.frame_idx = idx % len(self.tk_frames)
        photo, _ = self.tk_frames[self.frame_idx]
        self.label.configure(image=photo)
        self.label.image = photo

    def schedule_next_frame(self):
        self.stop_animation()
        if self.suppressed_hidden or self.state.get("paused", False) or len(self.tk_frames) <= 1:
            return
        _, raw_delay = self.tk_frames[self.frame_idx]
        speed = max(0.25, min(3.0, float(self.state.get("speed", 1.0))))
        interval = max(15, int(round(raw_delay / speed)))
        self.after_id = self.win.after(interval, self.on_tick)

    def stop_animation(self):
        if self.after_id is not None:
            try:
                self.win.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def on_tick(self):
        self.after_id = None
        if self.suppressed_hidden or self.state.get("paused", False) or len(self.tk_frames) <= 1:
            return
        self.show_frame((self.frame_idx + 1) % len(self.tk_frames))
        self.schedule_next_frame()

    def set_suppressed_hidden(self, hidden):
        self.suppressed_hidden = hidden
        if hidden:
            self._stop_wander(reset_pos=False)
            self._cancel_mini_action()
            self._cancel_temp_gif(restore=True)
            self.bubble.hide()
            self.particles.stop()
            self.stop_animation()
            self.win.withdraw()
        else:
            self.win.deiconify()
            self.apply_window_flags()
            self.show_frame(self.frame_idx)
            self.schedule_next_frame()
            self.sync_wander_state()

    def get_personality_spec(self):
        p_key = self.state.get("personality", "warm")
        return PERSONALITY_SPECS.get(p_key, PERSONALITY_SPECS["warm"])

    def next_random_cheer_delay(self):
        lo, hi = self.get_personality_spec()["random_sec"]
        return random.randint(lo, hi)

    def set_personality(self, p_key):
        if p_key not in PERSONALITY_KEYS:
            return
        self.state["personality"] = p_key
        spec = self.get_personality_spec()
        self._next_random_ts = time.time() + self.next_random_cheer_delay()
        self.app.save()
        self.play_mini_action(spec["actions"][0])
        self.bubble.show_message(spec["cheers"][0], duration_ms=4000)

    def apply_preset(self, preset_key, announce=True):
        if preset_key not in CHARACTER_PRESETS:
            return
        patch = build_character_preset_patch(preset_key)
        self.state["preset"] = patch["preset"]
        self.state["name"] = patch["name"]
        self.state["personality"] = patch["personality"]
        self.state["auto_state_gif"] = patch["auto_state_gif"]
        self.state["scene_gifs"] = dict(patch["scene_gifs"])
        self.state["scene_texts"] = dict(patch["scene_texts"])
        self.state["scene_on"] = dict(patch["scene_on"])
        self._next_random_ts = time.time() + self.next_random_cheer_delay()

        self.app._sync_state_gif(force=True, target_floater=self)
        self.app.refresh_idle_bubbles()
        self.app.save()

        if announce and not self.suppressed_hidden:
            spec = self.get_personality_spec()
            msg = resolve_floater_scene_text(self.state, "hold") or f"{self.state['name']} 등장!"
            self.play_mini_action(spec["actions"][0])
            self.bubble.show_message(msg, duration_ms=4000)

    def is_facing_left(self):
        return bool(self.state.get("flip_h", False)) ^ bool(self._facing_left)

    def face_towards(self, target_x):
        tw, _ = self.target_size()
        my_cx = int(self.state.get("x", 0)) + tw // 2
        if abs(int(target_x) - my_cx) < 4:
            return
        want_facing_left = (int(target_x) < my_cx)
        want_internal = want_facing_left ^ bool(self.state.get("flip_h", False))
        if want_internal != self._facing_left:
            self._facing_left = want_internal
            self._update_active_tk_frames()
            self.show_frame(self.frame_idx)

    def _can_wander(self):
        return (
            bool(self.state.get("wander", True))
            and not bool(self.state.get("fixed_pos", False))
            and not self.suppressed_hidden
            and not bool(self.state.get("paused", False))
        )

    def _stop_wander(self, reset_pos=True, reset_facing=False):
        if self._wander_after_id is not None:
            try:
                self.win.after_cancel(self._wander_after_id)
            except Exception:
                pass
            self._wander_after_id = None
        self._walking = False
        if reset_pos and not self._dragging:
            try:
                _set_window_geometry(self.win, int(self.state["x"]), int(self.state["y"]))
                self.bubble.update_position()
                self.particles.update_position()
            except Exception:
                pass
        if reset_facing and self._facing_left:
            self._facing_left = False
            self._update_active_tk_frames()
            self.show_frame(self.frame_idx)

    def sync_wander_state(self):
        if self._can_wander():
            if not self._walking and self._wander_after_id is None and self._action_after_id is None and not self._dragging:
                self._schedule_wander()
        else:
            self._stop_wander(reset_pos=True, reset_facing=False)

    def _schedule_wander(self, delay_ms=None):
        if self._wander_after_id is not None:
            try:
                self.win.after_cancel(self._wander_after_id)
            except Exception:
                pass
            self._wander_after_id = None
        if not self._can_wander():
            return
        if delay_ms is None:
            lo, hi = self.get_personality_spec()["rest_ms"]
            delay_ms = random.randint(lo, hi)
        self._wander_after_id = self.win.after(int(delay_ms), self._start_wander_walk)

    def _start_wander_walk(self):
        self._wander_after_id = None
        if not self._can_wander() or self._dragging or self._action_after_id is not None:
            if self._can_wander():
                self._schedule_wander(1500)
            return

        hold_rem = self._social_hold_until - time.time()
        if hold_rem > 0.05:
            self._schedule_wander(int(hold_rem * 1000) + 300)
            return

        tw, th = self.target_size()
        cur_x = int(self.state.get("x", 0))
        cur_y = int(self.state.get("y", 0))
        w_left, _w_top, w_right, _w_bottom = get_monitor_work_rect_for_rect(
            cur_x, cur_y, tw, th, self.win
        )
        min_x = w_left + 12
        max_x = max(min_x, w_right - tw - 12)

        tx = self.app.choose_wander_target(self, min_x, max_x)
        if tx is None or abs(tx - cur_x) < 12:
            self._schedule_wander()
            return

        self.face_towards(tx + tw // 2)

        self._walking = True
        self._walk_fx = float(cur_x)
        self._walk_tx = float(tx)
        lo_s, hi_s = self.get_personality_spec()["walk_speed"]
        self._walk_speed_px = random.uniform(lo_s, hi_s)
        self._wander_after_id = self.win.after(40, self._wander_step)

    def _wander_step(self):
        self._wander_after_id = None
        if not self._walking or not self._can_wander() or self._dragging or self._action_after_id is not None:
            self._walking = False
            if self._can_wander() and not self._dragging and self._action_after_id is None:
                self._schedule_wander(1500)
            return

        cur_x = int(self.state.get("x", 0))
        ny = int(self.state.get("y", 0))
        rem_x = self._walk_tx - self._walk_fx
        arrived = abs(rem_x) <= self._walk_speed_px
        if arrived:
            nx = int(round(self._walk_tx))
        else:
            step = self._walk_speed_px if rem_x > 0 else -self._walk_speed_px
            self._walk_fx += step
            nx = int(round(self._walk_fx))

        yielded, stop_x, blocker = self.app.should_yield_step(self, cur_x, nx, ny)
        if yielded:
            nx = stop_x
            self.state["x"] = nx
            self._walking = False
            _set_window_geometry(self.win, nx, ny)
            self.bubble.update_position()
            self.particles.update_position()
            if blocker is not None:
                bt_w, _ = blocker.target_size()
                self.face_towards(int(blocker.state.get("x", 0)) + bt_w // 2)
            self.app.save()
            self.app.check_proximity_interaction(self)
            if not self._walking and self._action_after_id is None:
                self._schedule_wander()
            return

        self.state["x"] = nx
        if arrived:
            self._walking = False
        _set_window_geometry(self.win, nx, ny)
        self.bubble.update_position()
        self.particles.update_position()
        if arrived:
            self.app.save()
        self.app.check_proximity_interaction(self)
        if arrived:
            if not self._walking and self._action_after_id is None:
                self._schedule_wander()
        elif self._walking:
            self._wander_after_id = self.win.after(40, self._wander_step)

    def apply_window_flags(self):
        self.win.attributes("-topmost", bool(self.state.get("topmost", True)))
        self.win.attributes("-alpha", max(0.2, min(1.0, float(self.state.get("opacity", 1.0)))))

        if not HAS_WIN32:
            return
        try:
            self.win.update_idletasks()
            frame_hex = self.win.wm_frame()
            hwnd = int(frame_hex, 16) if frame_hex and frame_hex != "0x0" else self.win.winfo_id()
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW
            if self.state.get("click_through", False):
                ex |= win32con.WS_EX_TRANSPARENT
            else:
                ex &= ~win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)
        except Exception:
            pass

    def _cancel_mini_action(self):
        if self._action_after_id is not None:
            try:
                self.win.after_cancel(self._action_after_id)
            except Exception:
                pass
            self._action_after_id = None
        if not self._dragging:
            try:
                _set_window_geometry(self.win, int(self.state["x"]), int(self.state["y"]))
            except Exception:
                pass

    def _cancel_temp_gif(self, restore=True):
        if self._temp_gif_after_id is not None:
            try:
                self.win.after_cancel(self._temp_gif_after_id)
            except Exception:
                pass
            self._temp_gif_after_id = None

        if restore and self._saved_anim_backup is not None:
            raw_frames, src_w, src_h = self._saved_anim_backup
            self._saved_anim_backup = None
            self.raw_frames = raw_frames
            self.src_w = src_w
            self.src_h = src_h
            self.frame_idx = 0
            self.rebuild_tk_frames()
            self.show_frame(0)
            self.schedule_next_frame()
            self.bubble.update_position()
        elif not restore:
            self._saved_anim_backup = None

    def play_mini_action(self, kind="jump", temp_cheer_ms=0, temp_scene_key=None):
        if self.suppressed_hidden or self._dragging:
            return

        self._stop_wander(reset_pos=False)
        self._cancel_mini_action()

        if temp_cheer_ms > 0:
            scene_to_load = temp_scene_key or "enter"
            cheer_path = resolve_floater_state_gif_path(self.state, scene_to_load)
            cur_path = os.path.normcase(self.state.get("gif_path") or "")
            if cheer_path and os.path.exists(cheer_path) and os.path.normcase(cheer_path) != cur_path:
                try:
                    if self._saved_anim_backup is None:
                        self._saved_anim_backup = (self.raw_frames, self.src_w, self.src_h)
                    self.raw_frames = decode_animation(cheer_path)
                    self.src_w, self.src_h = self.raw_frames[0][0].size
                    self.frame_idx = 0
                    self.rebuild_tk_frames()
                    self.show_frame(0)
                    self.schedule_next_frame()
                    if self._temp_gif_after_id is not None:
                        self.win.after_cancel(self._temp_gif_after_id)
                    self._temp_gif_after_id = self.win.after(
                        int(temp_cheer_ms), lambda: self._cancel_temp_gif(restore=True)
                    )
                except Exception:
                    self._saved_anim_backup = None

        total_steps = 28
        step_ms = 26

        def step(i):
            self._action_after_id = None
            if self.suppressed_hidden or self._dragging:
                return
            if i >= total_steps:
                _set_window_geometry(self.win, int(self.state["x"]), int(self.state["y"]))
                self.sync_wander_state()
                return

            t = i / float(total_steps)
            base_x = int(self.state["x"])
            base_y = int(self.state["y"])
            if kind == "wiggle":
                dx = int(round(math.sin(t * math.pi * 6) * 10))
                dy = -int(round(abs(math.sin(t * math.pi * 6)) * 5))
            else:
                dx = 0
                dy = -int(round(abs(math.sin(t * math.pi * 3)) * 22))

            _set_window_geometry(self.win, base_x + dx, base_y + dy)
            self._action_after_id = self.win.after(step_ms, lambda: step(i + 1))

        step(0)

    def on_mouse_down(self, event):
        self._dragging = True
        self._drag_moved = False
        self._stop_wander(reset_pos=False)
        self._cancel_mini_action()
        cx, cy = get_cursor_pos(event)
        self._drag_start_x = cx
        self._drag_start_y = cy
        try:
            if self.win.winfo_ismapped():
                self._win_start_x = int(self.win.winfo_x())
                self._win_start_y = int(self.win.winfo_y())
            else:
                self._win_start_x = int(self.state.get("x", 0))
                self._win_start_y = int(self.state.get("y", 0))
        except Exception:
            self._win_start_x = int(self.state.get("x", 0))
            self._win_start_y = int(self.state.get("y", 0))
        self.win.focus_force()

    def on_mouse_drag(self, event):
        if self.state.get("fixed_pos", False):
            return
        cx, cy = get_cursor_pos(event)
        dx = cx - self._drag_start_x
        dy = cy - self._drag_start_y
        if abs(dx) > 3 or abs(dy) > 3:
            self._drag_moved = True
        nx = self._win_start_x + dx
        ny = self._win_start_y + dy
        self.state["x"] = nx
        self.state["y"] = ny
        _set_window_geometry(self.win, nx, ny)
        self.bubble.update_position()
        self.particles.update_position()

    def on_mouse_up(self, _event):
        moved = self._drag_moved
        self._dragging = False
        self._drag_moved = False
        if moved:
            self.app.save()
            self.app.on_floater_dropped(self)
        else:
            self.app.trigger_hold_scene(self)
        self.sync_wander_state()

    def on_double_click(self, _event):
        self._dragging = False
        self._drag_moved = False
        self.app.trigger_interactive_pet(self)

    def on_mouse_wheel(self, event):
        cur = int(self.state.get("display_size", 180))
        if cur <= 0:
            cur = max(self.src_w, self.src_h)
        step = 16 if event.delta > 0 else -16
        self.resize_keeping_center(max(48, min(600, cur + step)))

    def on_key(self, event):
        if event.keysym in ("plus", "equal", "KP_Add"):
            cur = int(self.state.get("display_size", 180)) or max(self.src_w, self.src_h)
            self.resize_keeping_center(min(600, cur + 16))
        elif event.keysym in ("minus", "KP_Subtract"):
            cur = int(self.state.get("display_size", 180)) or max(self.src_w, self.src_h)
            self.resize_keeping_center(max(48, cur - 16))
        elif event.keysym == "space":
            self.toggle_pause()
        elif event.keysym.lower() == "f":
            self.toggle_flip()

    def resize_keeping_center(self, new_size):
        self._stop_wander(reset_pos=False)
        old_w, old_h = self.target_size()
        self.state["display_size"] = new_size
        new_w, new_h = self.target_size()
        nx = int(self.state["x"]) + (old_w - new_w) // 2
        ny = int(self.state["y"]) + (old_h - new_h) // 2
        self.state["x"] = nx
        self.state["y"] = ny
        self.rebuild_tk_frames()
        _set_window_geometry(self.win, nx, ny, new_w, new_h)
        self.show_frame(self.frame_idx)
        self.bubble.update_position()
        self.particles.update_position()
        self.app.save()
        self.app.schedule_overlap_separation(base_delay_ms=320)
        self.sync_wander_state()

    def toggle_pause(self):
        self.state["paused"] = not self.state.get("paused", False)
        if self.state["paused"]:
            self.stop_animation()
            self._stop_wander(reset_pos=True)
        else:
            self.schedule_next_frame()
            self.sync_wander_state()
        self.app.save()

    def toggle_flip(self):
        self.state["flip_h"] = not self.state.get("flip_h", False)
        self._update_active_tk_frames()
        self.show_frame(self.frame_idx)
        self.app.save()
        if not self.suppressed_hidden and not self.state.get("paused", False):
            self.win.after(600, lambda: self.app.check_proximity_interaction(self))

    def cycle_next_gif(self):
        gifs = get_available_gifs()
        if not gifs:
            return
        cur = os.path.normcase(self.state.get("gif_path") or "")
        idx = next((i for i, p in enumerate(gifs) if os.path.normcase(p) == cur), -1)
        next_path = gifs[(idx + 1) % len(gifs)]
        try:
            self.load_gif(next_path, save=True)
        except Exception as e:
            messagebox.showerror("오류", f"GIF를 불러올 수 없습니다:\n{e}")

    def pick_gif_dialog(self):
        path = filedialog.askopenfilename(
            parent=self.win,
            title="띄울 GIF / 이미지 선택",
            initialdir=GIFS_DIR if os.path.isdir(GIFS_DIR) else BASE_DIR,
            filetypes=[
                ("GIF 및 이미지", "*.gif;*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
                ("모든 파일", "*.*"),
            ],
        )
        if path:
            try:
                self.load_gif(path, save=True)
            except Exception as e:
                messagebox.showerror("오류", f"이미지를 불러올 수 없습니다:\n{e}")

    def toggle_wander(self):
        new_val = not bool(self.state.get("wander", True))
        self.state["wander"] = new_val
        if new_val:
            self.state["fixed_pos"] = False
        self.app.save()
        self.sync_wander_state()

    def toggle_fixed_pos(self):
        new_val = not bool(self.state.get("fixed_pos", False))
        self.state["fixed_pos"] = new_val
        if new_val:
            self.state["wander"] = False
        self.app.save()
        self.sync_wander_state()

    def toggle_bubble_on(self):
        self.state["bubble_on"] = not bool(self.state.get("bubble_on", True))
        self.app.save()
        if not self.state["bubble_on"]:
            self.bubble.hide()
        else:
            self.bubble._temp_event_active = False
            self.app.refresh_idle_bubbles()

    def on_right_click(self, event):
        self.menu.delete(0, tk.END)

        sched = self.app.get_work_schedule()
        status = compute_work_status(
            sched,
            scene_on=self.state.get("scene_on"),
            scene_texts=self.state.get("scene_texts"),
        )
        self.menu.add_command(
            label=f"{status['status_line']}",
            command=lambda: self.app.open_work_schedule_dialog(self),
        )

        inter_sub = tk.Menu(self.menu, tearoff=0)
        inter_sub.add_command(
            label="쓰담쓰담 / 응원 받기 (더블클릭)",
            command=lambda: self.app.trigger_character_interaction(self, "cheer"),
        )
        inter_sub.add_command(
            label="간식 주기",
            command=lambda: self.app.trigger_character_interaction(self, "feed"),
        )
        inter_sub.add_command(
            label="하이파이브!",
            command=lambda: self.app.trigger_character_interaction(self, "highfive"),
        )
        inter_sub.add_command(
            label="콕 찌르기",
            command=lambda: self.app.trigger_character_interaction(self, "poke"),
        )
        inter_sub.add_separator()
        inter_sub.add_command(
            label="옆 캐릭터와 인사/대화하기",
            state=(tk.NORMAL if len(self.app.floaters) > 1 else tk.DISABLED),
            command=lambda: self.app.trigger_social_interaction(self),
        )
        inter_sub.add_command(
            label="모두 함께 합동 응원!",
            command=self.app.trigger_group_cheer,
        )
        self.menu.add_cascade(label="상호작용 하기", menu=inter_sub)

        self.menu.add_command(
            label="퇴근 축하 파티클 ★",
            command=lambda: self.app.trigger_leave_celebration(self),
        )

        preview_sub = tk.Menu(self.menu, tearoff=0)
        for p_label, p_key in [
            ("출근 (2분 전)", "wake"),
            ("점심시간", "lunch"),
            ("퇴근 (파티클)", "enter"),
            ("야근 5분", "back"),
            ("야근 20분", "tired"),
            ("누를 때", "hold"),
        ]:
            preview_sub.add_command(
                label=p_label,
                command=lambda k=p_key: self.app.preview_scene(k, floater=self),
            )
        self.menu.add_cascade(label="미리보기", menu=preview_sub)

        state_sub = tk.Menu(self.menu, tearoff=0)
        self.app.populate_work_state_menu(state_sub, status)
        self.menu.add_cascade(label="근무 상태 모드 전환", menu=state_sub)

        char_name = self.state.get("name", "캐릭터")
        self.menu.add_command(
            label=f"[{char_name}] 캐릭터 설정...",
            command=lambda: self.app.open_work_schedule_dialog(self),
        )

        cur_preset = self.state.get("preset", "custom")
        preset_sub = tk.Menu(self.menu, tearoff=0)
        for pk in CHARACTER_PRESET_KEYS:
            pspec = CHARACTER_PRESETS[pk]
            pname = PERSONALITY_SPECS[pspec["personality"]]["name"]
            p_var = tk.BooleanVar(value=(cur_preset == pk))
            preset_sub.add_checkbutton(
                label=f"{pspec['label']} ({pname})",
                variable=p_var,
                command=lambda k=pk: self.apply_preset(k),
            )
        self.menu.add_cascade(label=f"[{char_name}] 캐릭터 프리셋 적용", menu=preset_sub)

        cur_p = self.state.get("personality", "warm")
        pers_sub = tk.Menu(self.menu, tearoff=0)
        for p_key in PERSONALITY_KEYS:
            p_var = tk.BooleanVar(value=(cur_p == p_key))
            pers_sub.add_checkbutton(
                label=PERSONALITY_SPECS[p_key]["name"],
                variable=p_var,
                command=lambda k=p_key: self.set_personality(k),
            )
        self.menu.add_cascade(label=f"[{char_name}] 성격 설정", menu=pers_sub)

        self.menu.add_command(
            label="출근·퇴근 시간 설정...",
            command=lambda: self.app.open_work_schedule_dialog(self),
        )

        bubble_sub = tk.Menu(self.menu, tearoff=0)
        self.app.populate_bubble_format_menu(bubble_sub, target_floater=self)
        self.menu.add_cascade(label="남은 시간 표시", menu=bubble_sub)
        self.menu.add_separator()

        gifs = get_available_gifs()
        self.menu.add_command(label="GIF 파일 직접 선택...", command=self.pick_gif_dialog)

        gifs_sub = tk.Menu(self.menu, tearoff=0)
        cur = os.path.normcase(self.state.get("gif_path") or "")
        if not gifs:
            gifs_sub.add_command(label="(gifs 폴더가 비어 있음)", state=tk.DISABLED)
        else:
            root_gifs = []
            folder_groups = {}
            for gpath in gifs:
                rel = format_gif_display_name(gpath)
                if "/" in rel:
                    rel_dir = rel.rsplit("/", 1)[0]
                    folder_groups.setdefault(rel_dir, []).append((os.path.basename(rel), gpath))
                else:
                    root_gifs.append((rel, gpath))
            for label, gpath in root_gifs:
                var = tk.BooleanVar(value=(os.path.normcase(gpath) == cur))
                gifs_sub.add_checkbutton(
                    label=label,
                    variable=var,
                    command=lambda p=gpath: self.load_gif(p, save=True),
                )
            if root_gifs and folder_groups:
                gifs_sub.add_separator()
            for rel_dir in sorted(folder_groups, key=str.lower):
                leaf = rel_dir.rsplit("/", 1)[-1]
                if rel_dir.startswith("presets/") and leaf in CHARACTER_PRESETS:
                    folder_label = f"프리셋: {CHARACTER_PRESETS[leaf]['label']}"
                else:
                    folder_label = rel_dir
                folder_sub = tk.Menu(gifs_sub, tearoff=0)
                for fname, gpath in folder_groups[rel_dir]:
                    var = tk.BooleanVar(value=(os.path.normcase(gpath) == cur))
                    folder_sub.add_checkbutton(
                        label=fname,
                        variable=var,
                        command=lambda p=gpath: self.load_gif(p, save=True),
                    )
                gifs_sub.add_cascade(label=folder_label, menu=folder_sub)
        gifs_sub.add_separator()
        gifs_sub.add_command(label="gifs 폴더 열기", command=self.app.open_gifs_folder)
        self.menu.add_cascade(label="gifs 폴더에서 선택", menu=gifs_sub)

        self.menu.add_command(
            label="다음 GIF로 변경",
            state=(tk.NORMAL if len(gifs) > 1 else tk.DISABLED),
            command=self.cycle_next_gif,
        )
        self.menu.add_separator()

        size_sub = tk.Menu(self.menu, tearoff=0)
        cur_size = int(self.state.get("display_size", 180))
        for label, val in [
            ("아주 작게 (80px)", 80),
            ("작게 (120px)", 120),
            ("보통 (180px)", 180),
            ("크게 (250px)", 250),
            ("아주 크게 (340px)", 340),
            ("원본 크기", 0),
        ]:
            var = tk.BooleanVar(value=(cur_size == val))
            size_sub.add_checkbutton(label=label, variable=var, command=lambda v=val: self.resize_keeping_center(v))
        self.menu.add_cascade(label="크기 (휠 스크롤 가능)", menu=size_sub)

        op_sub = tk.Menu(self.menu, tearoff=0)
        cur_op = float(self.state.get("opacity", 1.0))
        for val in (1.0, 0.85, 0.70, 0.50, 0.30):
            var = tk.BooleanVar(value=(abs(cur_op - val) < 0.03))
            op_sub.add_checkbutton(
                label=f"{int(round(val * 100))}%",
                variable=var,
                command=lambda v=val: self.set_opacity(v),
            )
        self.menu.add_cascade(label="투명도", menu=op_sub)

        sp_sub = tk.Menu(self.menu, tearoff=0)
        cur_sp = float(self.state.get("speed", 1.0))
        paused = bool(self.state.get("paused", False))
        for val in (0.5, 0.75, 1.0, 1.5, 2.0):
            var = tk.BooleanVar(value=(not paused and abs(cur_sp - val) < 0.05))
            sp_sub.add_checkbutton(
                label=f"{val:g}x",
                variable=var,
                command=lambda v=val: self.set_speed(v),
            )
        sp_sub.add_separator()
        pause_var = tk.BooleanVar(value=paused)
        sp_sub.add_checkbutton(label="일시정지", variable=pause_var, command=self.toggle_pause)
        self.menu.add_cascade(label="재생 속도", menu=sp_sub)

        flip_var = tk.BooleanVar(value=bool(self.state.get("flip_h", False)))
        self.menu.add_checkbutton(label="좌우 반전", variable=flip_var, command=self.toggle_flip)
        self.menu.add_separator()

        tm_var = tk.BooleanVar(value=bool(self.state.get("topmost", True)))
        self.menu.add_checkbutton(
            label="항상 위",
            variable=tm_var,
            command=self.toggle_topmost,
        )

        w_var = tk.BooleanVar(value=bool(self.state.get("wander", True)))
        self.menu.add_checkbutton(
            label="돌아다니기 (좌우 이동)",
            variable=w_var,
            command=self.toggle_wander,
        )

        fix_var = tk.BooleanVar(value=bool(self.state.get("fixed_pos", False)))
        self.menu.add_checkbutton(
            label="위치 고정",
            variable=fix_var,
            command=self.toggle_fixed_pos,
        )

        ct_var = tk.BooleanVar(value=bool(self.state.get("click_through", False)))
        self.menu.add_checkbutton(
            label="클릭 통과 모드 (Ctrl+Alt+L)",
            variable=ct_var,
            command=lambda: self.set_click_through(not self.state.get("click_through", False)),
        )

        if HAS_WINREG:
            auto_var = tk.BooleanVar(value=is_autostart_enabled())
            self.menu.add_checkbutton(
                label="Windows 시작 시 자동 실행",
                variable=auto_var,
                command=self.app.toggle_autostart,
            )

        self.menu.add_command(label="시계 위로 돌아가기", command=self.app.move_to_clock_area)
        self.menu.add_separator()

        self.menu.add_command(label="새 캐릭터 추가 (+)", command=self.app.add_floater)
        add_preset_sub = tk.Menu(self.menu, tearoff=0)
        self.app.populate_add_preset_menu(add_preset_sub)
        self.menu.add_cascade(label="프리셋으로 캐릭터 추가 (+)", menu=add_preset_sub)
        self.menu.add_command(
            label="이 캐릭터 닫기",
            state=(tk.NORMAL if len(self.app.floaters) > 1 else tk.DISABLED),
            command=lambda: self.app.close_floater(self),
        )
        self.menu.add_separator()
        self.menu.add_command(label="모두 숨기기 / 보이기 (Ctrl+Alt+H)", command=self.app.toggle_hide_all)
        self.menu.add_command(label="종료", command=self.app.quit)

        self.menu.tk_popup(event.x_root, event.y_root)

    def set_opacity(self, val):
        self.state["opacity"] = val
        self.apply_window_flags()
        self.app.save()

    def set_speed(self, val):
        self.state["paused"] = False
        self.state["speed"] = val
        self.schedule_next_frame()
        self.app.save()

    def set_click_through(self, enable):
        self.state["click_through"] = enable
        self.apply_window_flags()
        self.app.save()

    def toggle_topmost(self):
        self.state["topmost"] = not self.state.get("topmost", True)
        self.apply_window_flags()
        self.app.save()

    def destroy(self):
        self._stop_wander(reset_pos=False)
        self._cancel_mini_action()
        self._cancel_temp_gif(restore=False)
        self.stop_animation()
        self.bubble.destroy()
        self.particles.destroy()
        self.win.destroy()


class WorkScheduleDialog:
    """Modal/floating dialog to configure work days, work hours, and per-character 8 scenes."""

    def __init__(self, app, initial_floater=None):
        self.app = app
        self.win = tk.Toplevel(app.root)
        self.win.title(f"{APP_NAME} - 시간 및 캐릭터 설정")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        if os.path.exists(ICON_PATH):
            try:
                self.win.iconbitmap(ICON_PATH)
            except Exception:
                pass

        sched = app.get_work_schedule()
        self.enabled_var = tk.BooleanVar(value=bool(sched.get("enabled", True)))
        self.start_var = tk.StringVar(value=str(sched.get("start_time", "08:00")))
        self.end_var = tk.StringVar(value=str(sched.get("end_time", "17:00")))
        self.lunch_on_var = tk.BooleanVar(value=bool(sched.get("lunch_on", True)))
        self.lunch_s_var = tk.StringVar(value=str(sched.get("lunch_start", "12:00")))
        self.lunch_e_var = tk.StringVar(value=str(sched.get("lunch_end", "13:00")))
        work_days_set = set(sched.get("work_days", [0, 1, 2, 3, 4]))
        self.work_day_vars = [tk.BooleanVar(value=(i in work_days_set)) for i in range(7)]

        self.stretch_var = tk.IntVar(value=int(sched.get("stretch_interval_min", 50)))
        self.random_var = tk.BooleanVar(value=bool(sched.get("random_chat_enabled", True)))
        self.always_bubble_var = tk.BooleanVar(value=bool(sched.get("always_show_bubble", True)))
        self.bubble_format_var = tk.StringVar(value=str(sched.get("bubble_time_format", "hm")))

        self._drafts = []
        for idx, fl in enumerate(app.floaters):
            norm = normalize_floater_state(fl.state, idx, sched)
            self._drafts.append({
                "preset": norm.get("preset", "custom"),
                "name": norm["name"],
                "personality": norm["personality"],
                "auto_state_gif": bool(norm["auto_state_gif"]),
                "bubble_on": bool(norm["bubble_on"]),
                "wander": bool(norm["wander"]),
                "scene_gifs": dict(norm["scene_gifs"]),
                "scene_texts": dict(norm["scene_texts"]),
                "scene_on": dict(norm["scene_on"]),
            })

        self.selected_idx = 0
        if initial_floater is not None and initial_floater in app.floaters:
            self.selected_idx = app.floaters.index(initial_floater)

        self.char_choice_var = tk.StringVar()
        self.char_preset_var = tk.StringVar()
        self.char_name_var = tk.StringVar()
        self.char_personality_var = tk.StringVar()
        self.char_auto_var = tk.BooleanVar(value=True)
        self.char_bubble_var = tk.BooleanVar(value=True)
        self.char_wander_var = tk.BooleanVar(value=True)

        self._char_opt = None
        self._preset_opt = None
        self._personality_opt = None
        self._char_menu_labels = []
        self._scene_opt_widgets = {}
        self._scene_gif_vars = {k: tk.StringVar() for k in SCENE_KEYS}
        self._scene_text_vars = {
            k: tk.StringVar() for k in SCENE_KEYS if SCENES_SPEC[k]["has_text"]
        }
        self._scene_on_vars = {
            k: tk.BooleanVar(value=True) for k in SCENE_KEYS if SCENES_SPEC[k]["has_switch"]
        }
        self._scene_text_entries = {}

        self._build_ui(sched)
        self._load_draft(self.selected_idx)
        self._center_on_screen(initial_floater)
        self.win.protocol("WM_DELETE_WINDOW", self.close)

    def _bind_hhmm_autoformat(self, entry, var):
        def on_focus_out(_e=None):
            norm = normalize_hhmm_input(var.get())
            if is_valid_hhmm(norm):
                var.set(norm)
        entry.bind("<FocusOut>", on_focus_out)

    def _set_workdays_preset(self, days_list):
        s = set(days_list)
        for i, var in enumerate(self.work_day_vars):
            var.set(i in s)

    def _build_ui(self, sched):
        frame = tk.Frame(self.win, padx=14, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        top_row = tk.Frame(frame)
        top_row.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 6))
        tk.Label(
            top_row,
            text=f"{APP_NAME} 설정",
            font=("Malgun Gothic", 11, "bold"),
        ).pack(side=tk.LEFT)
        tk.Checkbutton(
            top_row,
            text="근무시간 알림 및 자동 상태 켜기",
            variable=self.enabled_var,
            font=("Malgun Gothic", 9),
        ).pack(side=tk.RIGHT)

        # Work schedule box
        sched_box = tk.LabelFrame(
            frame,
            text=" 출근·퇴근 시간 & 근무 요일 (0930 입력 가능) ",
            padx=8,
            pady=6,
            font=("Malgun Gothic", 9, "bold"),
        )
        sched_box.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 6))

        days_row = tk.Frame(sched_box)
        days_row.grid(row=0, column=0, columnspan=6, sticky="ew", pady=(0, 4))
        tk.Label(days_row, text="근무 요일:", font=("Malgun Gothic", 9)).pack(side=tk.LEFT, padx=(0, 4))
        for idx, dname in enumerate(WEEKDAY_NAMES):
            tk.Checkbutton(
                days_row,
                text=dname,
                variable=self.work_day_vars[idx],
                font=("Malgun Gothic", 8),
                padx=2,
            ).pack(side=tk.LEFT)
        tk.Button(
            days_row,
            text="매일",
            font=("Malgun Gothic", 8),
            padx=5,
            command=lambda: self._set_workdays_preset([0, 1, 2, 3, 4, 5, 6]),
        ).pack(side=tk.RIGHT, padx=(2, 0))
        tk.Button(
            days_row,
            text="월~금",
            font=("Malgun Gothic", 8),
            padx=5,
            command=lambda: self._set_workdays_preset([0, 1, 2, 3, 4]),
        ).pack(side=tk.RIGHT, padx=(4, 2))

        time_row = tk.Frame(sched_box)
        time_row.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(2, 2))

        tk.Label(time_row, text="출근:", font=("Malgun Gothic", 9)).pack(side=tk.LEFT)
        e_start = tk.Entry(time_row, textvariable=self.start_var, width=6, justify="center")
        e_start.pack(side=tk.LEFT, padx=(3, 10))
        self._bind_hhmm_autoformat(e_start, self.start_var)

        tk.Label(time_row, text="퇴근:", font=("Malgun Gothic", 9)).pack(side=tk.LEFT)
        e_end = tk.Entry(time_row, textvariable=self.end_var, width=6, justify="center")
        e_end.pack(side=tk.LEFT, padx=(3, 12))
        self._bind_hhmm_autoformat(e_end, self.end_var)

        tk.Checkbutton(
            time_row,
            text="점심:",
            variable=self.lunch_on_var,
            font=("Malgun Gothic", 9),
        ).pack(side=tk.LEFT)
        e_ls = tk.Entry(time_row, textvariable=self.lunch_s_var, width=6, justify="center")
        e_ls.pack(side=tk.LEFT, padx=(2, 2))
        self._bind_hhmm_autoformat(e_ls, self.lunch_s_var)
        tk.Label(time_row, text="~", font=("Malgun Gothic", 9)).pack(side=tk.LEFT)
        e_le = tk.Entry(time_row, textvariable=self.lunch_e_var, width=6, justify="center")
        e_le.pack(side=tk.LEFT, padx=(2, 0))
        self._bind_hhmm_autoformat(e_le, self.lunch_e_var)

        opt_row = tk.Frame(sched_box)
        opt_row.grid(row=2, column=0, columnspan=6, sticky="ew", pady=(4, 0))
        tk.Checkbutton(
            opt_row,
            text="상시 말풍선:",
            variable=self.always_bubble_var,
            font=("Malgun Gothic", 8),
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            opt_row,
            text="*시간 *분 전",
            variable=self.bubble_format_var,
            value="hm",
            font=("Malgun Gothic", 8),
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            opt_row,
            text="***분 전",
            variable=self.bubble_format_var,
            value="minutes",
            font=("Malgun Gothic", 8),
        ).pack(side=tk.LEFT, padx=(0, 10))
        tk.Checkbutton(
            opt_row,
            text="랜덤 응원",
            variable=self.random_var,
            font=("Malgun Gothic", 8),
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(opt_row, text="스트레칭:", font=("Malgun Gothic", 8)).pack(side=tk.LEFT)
        for label, mins in [("끄기", 0), ("30m", 30), ("50m", 50), ("90m", 90)]:
            tk.Radiobutton(
                opt_row,
                text=label,
                variable=self.stretch_var,
                value=mins,
                font=("Malgun Gothic", 8),
                padx=2,
            ).pack(side=tk.LEFT)

        # Per-character 8 scenes section
        char_box = tk.LabelFrame(
            frame,
            text=" 캐릭터 설정 (8가지 장면 이미지 & 말풍선 문구) ",
            padx=8,
            pady=6,
            font=("Malgun Gothic", 9, "bold"),
        )
        char_box.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, 6))

        sel_row = tk.Frame(char_box)
        sel_row.grid(row=0, column=0, columnspan=6, sticky="ew", pady=(0, 4))
        tk.Label(sel_row, text="대상:", font=("Malgun Gothic", 9)).pack(side=tk.LEFT)
        self._char_opt = tk.OptionMenu(sel_row, self.char_choice_var, "")
        self._char_opt.config(width=11, anchor="w", font=("Malgun Gothic", 8))
        self._char_opt.pack(side=tk.LEFT, padx=(2, 5))

        tk.Label(sel_row, text="이름:", font=("Malgun Gothic", 9)).pack(side=tk.LEFT)
        tk.Entry(sel_row, textvariable=self.char_name_var, width=8).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(sel_row, text="성격:", font=("Malgun Gothic", 9)).pack(side=tk.LEFT)
        p_names = [PERSONALITY_SPECS[k]["name"] for k in PERSONALITY_KEYS]
        self._personality_opt = tk.OptionMenu(sel_row, self.char_personality_var, *p_names)
        self._personality_opt.config(width=7, anchor="w", font=("Malgun Gothic", 8))
        self._personality_opt.pack(side=tk.LEFT, padx=(2, 6))

        tk.Button(
            sel_row,
            text="모두 기본으로",
            font=("Malgun Gothic", 8),
            command=self.reset_current_character_defaults,
        ).pack(side=tk.RIGHT, padx=(4, 0))
        tk.Button(
            sel_row,
            text="+ 캐릭터 추가",
            font=("Malgun Gothic", 8),
            command=self.add_character_in_dialog,
        ).pack(side=tk.RIGHT)

        preset_row = tk.Frame(char_box)
        preset_row.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(0, 4))
        tk.Label(preset_row, text="프리셋:", font=("Malgun Gothic", 9)).pack(side=tk.LEFT)
        preset_labels = [CHARACTER_PRESETS[k]["label"] for k in CHARACTER_PRESET_KEYS]
        self._preset_opt = tk.OptionMenu(preset_row, self.char_preset_var, *preset_labels)
        self._preset_opt.config(width=18, anchor="w", font=("Malgun Gothic", 8))
        self._preset_opt.pack(side=tk.LEFT, padx=(4, 8))
        pmenu = self._preset_opt["menu"]
        pmenu.delete(0, tk.END)
        for pk in CHARACTER_PRESET_KEYS:
            pspec = CHARACTER_PRESETS[pk]
            pname = PERSONALITY_SPECS[pspec["personality"]]["name"]
            pmenu.add_command(
                label=f"{pspec['label']} ({pname})",
                command=lambda k=pk: self.apply_preset_to_draft(k),
            )
        tk.Button(
            preset_row,
            text="+ 이 프리셋으로 추가",
            font=("Malgun Gothic", 8),
            command=self.add_preset_character_in_dialog,
        ).pack(side=tk.RIGHT)

        flag_row = tk.Frame(char_box)
        flag_row.grid(row=2, column=0, columnspan=6, sticky="ew", pady=(0, 4))
        tk.Checkbutton(
            flag_row,
            text="근무 상태에 맞춰 이미지 자동 전환",
            variable=self.char_auto_var,
            font=("Malgun Gothic", 8),
        ).pack(side=tk.LEFT, padx=(0, 10))
        tk.Checkbutton(
            flag_row,
            text="말풍선 보이기 (끄면 그림만 표시)",
            variable=self.char_bubble_var,
            font=("Malgun Gothic", 8),
        ).pack(side=tk.LEFT, padx=(0, 10))
        tk.Checkbutton(
            flag_row,
            text="돌아다니기 (좌우 이동)",
            variable=self.char_wander_var,
            font=("Malgun Gothic", 8),
        ).pack(side=tk.LEFT)

        # Header row
        tk.Label(char_box, text="켜기", font=("Malgun Gothic", 8, "bold"), fg="#555").grid(row=3, column=0, padx=2)
        tk.Label(char_box, text="장면 (시점)", font=("Malgun Gothic", 8, "bold"), fg="#555").grid(row=3, column=1, sticky="w", padx=4)
        tk.Label(char_box, text="이미지 (GIF/PNG)", font=("Malgun Gothic", 8, "bold"), fg="#555").grid(row=3, column=2, sticky="w", padx=4)
        tk.Label(char_box, text="선택/미리", font=("Malgun Gothic", 8, "bold"), fg="#555").grid(row=3, column=3, columnspan=2)
        tk.Label(char_box, text="말풍선 문구", font=("Malgun Gothic", 8, "bold"), fg="#555").grid(row=3, column=5, sticky="w", padx=4)

        for idx, s_key in enumerate(SCENE_KEYS):
            spec = SCENES_SPEC[s_key]
            row_idx = 4 + idx

            if spec["has_switch"]:
                tk.Checkbutton(
                    char_box,
                    variable=self._scene_on_vars[s_key],
                    command=lambda k=s_key: self._update_scene_row_state(k),
                ).grid(row=row_idx, column=0, padx=2, pady=1)
            else:
                tk.Label(char_box, text="항상", font=("Malgun Gothic", 8), fg="#888").grid(row=row_idx, column=0, padx=2, pady=1)

            tk.Label(
                char_box,
                text=f"{spec['name']} ({spec['caption']})",
                font=("Malgun Gothic", 8),
                anchor="w",
            ).grid(row=row_idx, column=1, sticky="w", padx=(2, 6), pady=1)

            gvar = self._scene_gif_vars[s_key]
            combo = ttk.Combobox(
                char_box,
                textvariable=gvar,
                state="readonly",
                width=23,
                height=14,
                font=("Malgun Gothic", 8),
            )
            combo.grid(row=row_idx, column=2, sticky="ew", padx=(0, 4), pady=1)
            self._scene_opt_widgets[s_key] = combo

            tk.Button(
                char_box,
                text="파일",
                width=5,
                font=("Malgun Gothic", 8),
                command=lambda k=s_key, v=gvar: self.pick_state_file(k, v),
            ).grid(row=row_idx, column=3, padx=(0, 2), pady=1)

            tk.Button(
                char_box,
                text="보기",
                width=5,
                font=("Malgun Gothic", 8),
                command=lambda k=s_key, v=gvar: self.preview_selected_state(k, v.get()),
            ).grid(row=row_idx, column=4, padx=(0, 6), pady=1)

            if spec["has_text"]:
                ent = tk.Entry(char_box, textvariable=self._scene_text_vars[s_key], width=14, font=("Malgun Gothic", 8))
                ent.grid(row=row_idx, column=5, sticky="ew", pady=1)
                self._scene_text_entries[s_key] = ent
            else:
                tk.Label(
                    char_box,
                    text="남은 시간이 나와요",
                    font=("Malgun Gothic", 8),
                    fg="#777777",
                    anchor="w",
                ).grid(row=row_idx, column=5, sticky="w", padx=2, pady=1)

        status = compute_work_status(sched)
        tk.Label(
            frame,
            text=f"현재 상태: {status['status_line']}",
            fg="#55443D",
            font=("Malgun Gothic", 9),
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(2, 6))

        btn_row = tk.Frame(frame)
        btn_row.grid(row=4, column=0, columnspan=4, sticky="e")

        tk.Button(btn_row, text="퇴근 축하 효과", command=self.app.trigger_leave_celebration, width=13).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(btn_row, text="이벤트 미리보기", command=self.preview, width=13).pack(side=tk.LEFT, padx=(0, 12))
        tk.Button(btn_row, text="취소", command=self.close, width=8).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(btn_row, text="저장", command=self.save, width=9, bg="#FFE6EC").pack(side=tk.LEFT)

    def _update_scene_row_state(self, scene_key):
        if scene_key in self._scene_on_vars and scene_key in self._scene_text_entries:
            is_on = bool(self._scene_on_vars[scene_key].get())
            self._scene_text_entries[scene_key].config(state=(tk.NORMAL if is_on else tk.DISABLED))

    def _rebuild_char_menu(self):
        menu = self._char_opt["menu"]
        menu.delete(0, tk.END)
        self._char_menu_labels = []
        for idx, d in enumerate(self._drafts):
            label = f"{idx + 1}. {d['name']}"
            self._char_menu_labels.append(label)
            menu.add_command(
                label=label,
                command=lambda i=idx: self._switch_to_character(i),
            )
        if 0 <= self.selected_idx < len(self._char_menu_labels):
            self.char_choice_var.set(self._char_menu_labels[self.selected_idx])

    def _refresh_state_option_menus(self):
        gif_refs = [format_gif_display_name(p) for p in get_available_gifs()]
        for s_key, widget in self._scene_opt_widgets.items():
            var = self._scene_gif_vars[s_key]
            cur_val = var.get().strip()
            choices = list(gif_refs)
            if cur_val and cur_val not in choices:
                choices.insert(0, cur_val)
            if not choices:
                choices = ["(gifs 폴더 비어 있음)"]
            widget["values"] = tuple(choices)

    def _save_current_draft(self):
        if not (0 <= self.selected_idx < len(self._drafts)):
            return
        d = self._drafts[self.selected_idx]
        name = self.char_name_var.get().strip()
        d["name"] = name if name else f"캐릭터 {self.selected_idx + 1}"
        p_label = self.char_personality_var.get().strip()
        d["personality"] = next(
            (k for k in PERSONALITY_KEYS if PERSONALITY_SPECS[k]["name"] == p_label),
            d.get("personality", PERSONALITY_KEYS[self.selected_idx % len(PERSONALITY_KEYS)]),
        )
        d["auto_state_gif"] = bool(self.char_auto_var.get())
        d["bubble_on"] = bool(self.char_bubble_var.get())
        d["wander"] = bool(self.char_wander_var.get())
        for s_key, var in self._scene_gif_vars.items():
            val = var.get().strip()
            if val and val != "(gifs 폴더 비어 있음)":
                d["scene_gifs"][s_key] = val
        for s_key, var in self._scene_text_vars.items():
            d["scene_texts"][s_key] = var.get().strip()
        for s_key, var in self._scene_on_vars.items():
            d["scene_on"][s_key] = bool(var.get())

    def _selected_preset_key(self):
        label = self.char_preset_var.get().strip()
        return next(
            (k for k in CHARACTER_PRESET_KEYS if CHARACTER_PRESETS[k]["label"] == label),
            None,
        )

    def apply_preset_to_draft(self, preset_key, preview=True):
        if not (0 <= self.selected_idx < len(self._drafts)) or preset_key not in CHARACTER_PRESETS:
            return
        patch = build_character_preset_patch(preset_key)
        d = self._drafts[self.selected_idx]
        d["preset"] = patch["preset"]
        d["name"] = patch["name"]
        d["personality"] = patch["personality"]
        d["auto_state_gif"] = patch["auto_state_gif"]
        d["scene_gifs"] = dict(patch["scene_gifs"])
        d["scene_texts"] = dict(patch["scene_texts"])
        d["scene_on"] = dict(patch["scene_on"])
        self._load_draft(self.selected_idx)
        if preview and 0 <= self.selected_idx < len(self.app.floaters):
            fl = self.app.floaters[self.selected_idx]
            self.app.preview_state_gif(
                "hold",
                d["scene_gifs"].get("hold", ""),
                floater=fl,
                custom_text=d["scene_texts"].get("hold"),
            )

    def _load_draft(self, idx):
        if not self._drafts:
            return
        idx = max(0, min(len(self._drafts) - 1, idx))
        self.selected_idx = idx
        d = self._drafts[idx]
        pk = d.get("preset", "custom")
        self.char_preset_var.set(CHARACTER_PRESETS[pk]["label"] if pk in CHARACTER_PRESETS else "사용자 지정")
        self.char_name_var.set(d["name"])
        p_key = d.get("personality", PERSONALITY_KEYS[idx % len(PERSONALITY_KEYS)])
        if p_key not in PERSONALITY_SPECS:
            p_key = PERSONALITY_KEYS[0]
        self.char_personality_var.set(PERSONALITY_SPECS[p_key]["name"])
        self.char_auto_var.set(bool(d["auto_state_gif"]))
        self.char_bubble_var.set(bool(d["bubble_on"]))
        self.char_wander_var.set(bool(d["wander"]))
        for s_key, var in self._scene_gif_vars.items():
            var.set(d["scene_gifs"].get(s_key, default_scene_gif_ref(s_key)))
        for s_key, var in self._scene_text_vars.items():
            var.set(d["scene_texts"].get(s_key, SCENES_SPEC[s_key]["default_text"]))
        for s_key, var in self._scene_on_vars.items():
            var.set(bool(d["scene_on"].get(s_key, True)))
            self._update_scene_row_state(s_key)
        self._rebuild_char_menu()
        self._refresh_state_option_menus()

    def reset_current_character_defaults(self):
        if not (0 <= self.selected_idx < len(self._drafts)):
            return
        d = self._drafts[self.selected_idx]
        cur_pk = d.get("preset")
        target_pk = cur_pk if cur_pk in CHARACTER_PRESET_KEYS else "chiikawa"
        patch = build_character_preset_patch(target_pk)
        d["preset"] = patch["preset"]
        d["personality"] = patch["personality"] if cur_pk in CHARACTER_PRESET_KEYS else PERSONALITY_KEYS[self.selected_idx % len(PERSONALITY_KEYS)]
        d["auto_state_gif"] = True
        d["bubble_on"] = True
        d["wander"] = True
        d["scene_gifs"] = dict(patch["scene_gifs"])
        d["scene_texts"] = dict(patch["scene_texts"])
        d["scene_on"] = dict(patch["scene_on"])
        self._load_draft(self.selected_idx)

    def _switch_to_character(self, new_idx):
        if new_idx == self.selected_idx:
            return
        self._save_current_draft()
        self._load_draft(new_idx)

    def select_floater(self, floater):
        if floater is None or floater not in self.app.floaters:
            return
        idx = self.app.floaters.index(floater)
        if idx < len(self._drafts):
            self._switch_to_character(idx)

    def add_preset_character_in_dialog(self):
        pk = self._selected_preset_key() or "chiikawa"
        self.add_character_in_dialog(preset_key=pk)

    def add_character_in_dialog(self, preset_key=None):
        self._save_current_draft()
        self.app.add_floater(preset_key=preset_key)
        idx = len(self.app.floaters) - 1
        norm = normalize_floater_state(self.app.floaters[idx].state, idx, self.app.get_work_schedule())
        self._drafts.append({
            "preset": norm.get("preset", "custom"),
            "name": norm["name"],
            "personality": norm["personality"],
            "auto_state_gif": bool(norm["auto_state_gif"]),
            "bubble_on": bool(norm["bubble_on"]),
            "wander": bool(norm["wander"]),
            "scene_gifs": dict(norm["scene_gifs"]),
            "scene_texts": dict(norm["scene_texts"]),
            "scene_on": dict(norm["scene_on"]),
        })
        self._load_draft(len(self._drafts) - 1)

    def pick_state_file(self, state_key, var):
        char_name = self.char_name_var.get().strip() or f"캐릭터 {self.selected_idx + 1}"
        title = SCENES_SPEC.get(state_key, {}).get("name", state_key)
        path = filedialog.askopenfilename(
            parent=self.win,
            title=f"[{char_name}] {title} 이미지 선택",
            initialdir=GIFS_DIR if os.path.isdir(GIFS_DIR) else BASE_DIR,
            filetypes=[
                ("GIF 및 이미지", "*.gif;*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
                ("모든 파일", "*.*"),
            ],
        )
        if path:
            var.set(to_stored_gif_ref(path))
            self._refresh_state_option_menus()
            self.preview_selected_state(state_key, var.get())

    def preview_selected_state(self, state_key, gif_name):
        floater = None
        if 0 <= self.selected_idx < len(self.app.floaters):
            floater = self.app.floaters[self.selected_idx]
        custom_text = None
        if state_key in self._scene_text_vars:
            custom_text = self._scene_text_vars[state_key].get().strip()
        self.app.preview_state_gif(state_key, gif_name, floater=floater, custom_text=custom_text)

    def _center_on_screen(self, anchor_floater=None):
        self.win.update_idletasks()
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        if anchor_floater is not None and anchor_floater in self.app.floaters:
            fw, fh = anchor_floater.target_size()
            ax = int(anchor_floater.state.get("x", 0))
            ay = int(anchor_floater.state.get("y", 0))
            m_left, m_top, m_right, m_bottom = get_monitor_work_rect_for_rect(ax, ay, fw, fh, self.win)
        else:
            cx, cy = get_cursor_pos()
            m_left, m_top, m_right, m_bottom = get_monitor_work_rect_for_point(cx, cy, self.win)
        x = max(m_left + 8, min(m_right - w - 8, m_left + (m_right - m_left - w) // 2))
        y = max(m_top + 8, min(m_bottom - h - 8, m_top + (m_bottom - m_top - h) // 2))
        _set_window_geometry(self.win, x, y)

    def preview(self):
        self.app.preview_work_event()

    def save(self):
        start_s = normalize_hhmm_input(self.start_var.get())
        end_s = normalize_hhmm_input(self.end_var.get())
        lunch_s = normalize_hhmm_input(self.lunch_s_var.get())
        lunch_e = normalize_hhmm_input(self.lunch_e_var.get())

        for label, val in [
            ("출근 시간", start_s),
            ("퇴근 시간", end_s),
            ("점심 시작", lunch_s),
            ("점심 종료", lunch_e),
        ]:
            if not is_valid_hhmm(val):
                messagebox.showwarning("입력 확인", f"{label}은(는) HH:MM 또는 0930 형식으로 입력해주세요.", parent=self.win)
                return

        if parse_hhmm(end_s, 0) <= parse_hhmm(start_s, 0):
            messagebox.showwarning("입력 확인", "퇴근 시간은 출근 시간보다 뒤여야 합니다.", parent=self.win)
            return

        if self.lunch_on_var.get() and parse_hhmm(lunch_e, 0) <= parse_hhmm(lunch_s, 0):
            messagebox.showwarning("입력 확인", "점심 종료 시간은 시작 시간보다 뒤여야 합니다.", parent=self.win)
            return

        self._save_current_draft()

        for d in self._drafts:
            for s_key, txt in d["scene_texts"].items():
                missing = find_missing_hand_chars(txt)
                if missing:
                    s_name = SCENES_SPEC.get(s_key, {}).get("name", s_key)
                    messagebox.showwarning(
                        "글꼴 확인",
                        f"[{d['name']}] '{s_name}' 말풍선의 '{''.join(missing)}' 글자는 손글씨 글꼴(감자꽃)에 없어서 표시할 수 없어요.",
                        parent=self.win,
                    )
                    return

        for idx, d in enumerate(self._drafts):
            if idx < len(self.app.floaters):
                fl = self.app.floaters[idx]
                st = fl.state
                old_p = st.get("personality", PERSONALITY_KEYS[0])
                new_p = d.get("personality", PERSONALITY_KEYS[0])
                if new_p not in PERSONALITY_SPECS:
                    new_p = PERSONALITY_KEYS[0]
                st["preset"] = d.get("preset", "custom")
                st["name"] = d["name"]
                st["personality"] = new_p
                st["auto_state_gif"] = bool(d["auto_state_gif"])
                st["bubble_on"] = bool(d["bubble_on"])
                st["wander"] = bool(d["wander"])
                if st["wander"]:
                    st["fixed_pos"] = False
                st["scene_gifs"] = dict(d["scene_gifs"])
                st["scene_texts"] = dict(d["scene_texts"])
                st["scene_on"] = dict(d["scene_on"])
                st.pop("state_gifs", None)
                if new_p != old_p:
                    fl._next_random_ts = time.time() + fl.next_random_cheer_delay()
                fl.sync_wander_state()

        work_days = [i for i, v in enumerate(self.work_day_vars) if v.get()]
        cur_sched = self.app.get_work_schedule()
        first_draft = self._drafts[0] if self._drafts else None
        new_sched = {
            "enabled": bool(self.enabled_var.get()),
            "start_time": start_s,
            "end_time": end_s,
            "lunch_on": bool(self.lunch_on_var.get()),
            "lunch_start": lunch_s,
            "lunch_end": lunch_e,
            "work_days": work_days,
            "stretch_interval_min": int(self.stretch_var.get()),
            "random_chat_enabled": bool(self.random_var.get()),
            "always_show_bubble": bool(self.always_bubble_var.get()),
            "bubble_time_format": self.bubble_format_var.get(),
            "auto_state_gif": bool(first_draft["auto_state_gif"]) if first_draft else bool(cur_sched.get("auto_state_gif", True)),
            "forced_state": cur_sched.get("forced_state", "auto"),
        }
        self.app.apply_work_schedule(new_sched)
        self.close()

    def close(self):
        self.app.on_schedule_dialog_closed()
        self.win.destroy()


class Win32TrayAndHotkeys:
    """Provides a native system tray icon and Ctrl+Alt+H / Ctrl+Alt+L hotkeys via pywin32."""

    def __init__(self, app):
        self.app = app
        self.hwnd = None
        self.hicon = None
        self.tray_added = False

        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = f"ChiikawaPyTray_{os.getpid()}"
        wc.lpfnWndProc = self._wnd_proc
        self.class_atom = win32gui.RegisterClass(wc)

        self.hwnd = win32gui.CreateWindow(
            self.class_atom,
            "ChiikawaPyTray",
            0, 0, 0, 0, 0,
            0,
            0,
            wc.hInstance,
            None,
        )

        if os.path.exists(ICON_PATH):
            try:
                self.hicon = win32gui.LoadImage(
                    0, ICON_PATH, win32con.IMAGE_ICON, 0, 0,
                    win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE,
                )
            except Exception:
                self.hicon = None
        if not self.hicon:
            self.hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        nid = (
            self.hwnd,
            1,
            win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
            WM_TRAYICON,
            self.hicon,
            APP_NAME,
        )
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            self.tray_added = True
        except Exception:
            self.tray_added = False

        try:
            ctypes.windll.user32.RegisterHotKey(self.hwnd, HOTKEY_HIDE_ID, 0x4003, ord("H"))
            ctypes.windll.user32.RegisterHotKey(self.hwnd, HOTKEY_LOCK_ID, 0x4003, ord("L"))
        except Exception:
            pass

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_HOTKEY:
            if wparam == HOTKEY_HIDE_ID:
                self.app.root.after(0, self.app.toggle_hide_all)
            elif wparam == HOTKEY_LOCK_ID:
                self.app.root.after(0, self.app.toggle_click_through_all)
            return 0
        if msg == WM_TRAYICON:
            if lparam == win32con.WM_LBUTTONDBLCLK:
                self.app.root.after(0, self.app.toggle_hide_all)
            elif lparam == win32con.WM_RBUTTONUP:
                self.app.root.after(0, self.app.show_tray_menu)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def poll(self):
        if not self.hwnd:
            return
        try:
            while True:
                has_msg, msg = win32gui.PeekMessage(self.hwnd, 0, 0, win32con.PM_REMOVE)
                if not has_msg:
                    break
                win32gui.TranslateMessage(msg)
                win32gui.DispatchMessage(msg)
        except Exception:
            pass

    def cleanup(self):
        if self.hwnd:
            try:
                ctypes.windll.user32.UnregisterHotKey(self.hwnd, HOTKEY_HIDE_ID)
                ctypes.windll.user32.UnregisterHotKey(self.hwnd, HOTKEY_LOCK_ID)
            except Exception:
                pass
            if self.tray_added:
                try:
                    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 1))
                except Exception:
                    pass
                self.tray_added = False
            try:
                win32gui.DestroyWindow(self.hwnd)
            except Exception:
                pass
            self.hwnd = None


class GifFloaterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.withdraw()

        self.config = load_config()
        self.config["hidden_all"] = False
        self.floaters = []
        self.tray = Win32TrayAndHotkeys(self) if HAS_WIN32 else None
        self.tray_menu = tk.Menu(self.root, tearoff=0)
        self._schedule_dialog = None

        now = datetime.datetime.now()
        init_status = compute_work_status(self.get_work_schedule(), now)
        self._last_event_date = now.strftime("%Y-%m-%d")
        self._last_checked_min = init_status["cur_min"]
        self._last_progress_pct = init_status["progress_pct"]
        self._triggered_keys = set()
        self._last_stretch_ts = time.time()
        self._last_social_ts = 0.0
        self._last_social_probe_ts = 0.0
        self._next_auto_social_ts = 0.0
        self._pair_social_until = {}
        self._pair_probe_ts = {}
        self._social_after_ids = []
        self._ambient_after_id = None

        if not self.config["floaters"]:
            self.config["floaters"].append(self._default_state(0))
            save_config(self.config)

        for state in self.config["floaters"]:
            self._spawn(state)

        self._sync_state_gif()
        self.refresh_idle_bubbles()

        if self.tray:
            self._poll_tray()

        if not self.get_work_schedule().get("always_show_bubble", True):
            self.root.after(1500, self._show_startup_greeting)
        self.root.after(450, self.schedule_overlap_separation)
        self._ambient_after_id = self.root.after(3500, self._check_ambient_social_and_spacing)
        self.root.after(10000, self._check_work_events)

    def get_work_schedule(self):
        return normalize_work_schedule(self.config.get("work_schedule"))

    def refresh_idle_bubbles(self, idle_sec=None):
        sched = self.get_work_schedule()
        now = datetime.datetime.now()
        if idle_sec is None:
            idle_sec = get_idle_seconds()
        always = bool(sched.get("always_show_bubble", True))
        hidden_all = bool(self.config.get("hidden_all", False))

        for floater in self.floaters:
            if hidden_all or floater.suppressed_hidden or not floater.state.get("bubble_on", True):
                floater.bubble.hide()
                continue
            if floater.bubble._temp_event_active:
                continue
            if always:
                st = compute_work_status(
                    sched,
                    now=now,
                    idle_sec=idle_sec,
                    scene_on=floater.state.get("scene_on"),
                    scene_texts=floater.state.get("scene_texts"),
                )
                floater.bubble.show_persistent(st["idle_bubble_text"])
            else:
                floater.bubble.hide()

    def toggle_autostart(self):
        set_autostart_enabled(not is_autostart_enabled())

    def set_bubble_time_format(self, fmt):
        sched = self.get_work_schedule()
        if fmt == "off":
            sched["always_show_bubble"] = False
        else:
            sched["always_show_bubble"] = True
            sched["bubble_time_format"] = fmt if fmt in ("hm", "minutes") else "hm"
        self.config["work_schedule"] = sched
        self.save()
        for floater in self.floaters:
            floater.bubble._temp_event_active = False
        self.refresh_idle_bubbles()

    def populate_bubble_format_menu(self, sub_menu, target_floater=None):
        sched = self.get_work_schedule()
        always = bool(sched.get("always_show_bubble", True))
        cur_fmt = sched.get("bubble_time_format", "hm")

        min_var = tk.BooleanVar(value=(always and cur_fmt == "minutes"))
        sub_menu.add_checkbutton(
            label="분으로 (125분 전)",
            variable=min_var,
            command=lambda: self.set_bubble_time_format("minutes"),
        )
        hm_var = tk.BooleanVar(value=(always and cur_fmt != "minutes"))
        sub_menu.add_checkbutton(
            label="시간·분으로 (2시간 5분 전)",
            variable=hm_var,
            command=lambda: self.set_bubble_time_format("hm"),
        )
        sub_menu.add_separator()
        off_var = tk.BooleanVar(value=(not always))
        sub_menu.add_checkbutton(
            label="상시 말풍선 숨기기",
            variable=off_var,
            command=lambda: self.set_bubble_time_format("off"),
        )
        if target_floater is not None:
            sub_menu.add_separator()
            b_var = tk.BooleanVar(value=bool(target_floater.state.get("bubble_on", True)))
            char_name = target_floater.state.get("name", "캐릭터")
            sub_menu.add_checkbutton(
                label=f"[{char_name}] 말풍선 보이기",
                variable=b_var,
                command=target_floater.toggle_bubble_on,
            )

    def _primary_visible_floater(self):
        for f in self.floaters:
            if not f.suppressed_hidden:
                return f
        return self.floaters[0] if self.floaters else None

    def _sync_state_gif(self, force=False, target_floater=None, idle_sec=None):
        sched = self.get_work_schedule()
        forced = sched.get("forced_state", "auto")
        now = datetime.datetime.now()
        if idle_sec is None:
            idle_sec = get_idle_seconds()

        targets = [target_floater] if target_floater is not None else list(self.floaters)
        for floater in targets:
            if not floater:
                continue
            char_auto = bool(floater.state.get("auto_state_gif", True))
            if not force and not char_auto and forced not in SCENE_KEYS:
                continue

            status = compute_work_status(
                sched,
                now=now,
                idle_sec=idle_sec,
                scene_on=floater.state.get("scene_on"),
                scene_texts=floater.state.get("scene_texts"),
            )
            state_key = status["effective_state_key"]
            target_path = resolve_floater_state_gif_path(floater.state, state_key)
            if not target_path:
                continue

            cur_path = floater.state.get("gif_path") or ""
            if os.path.normcase(target_path) != os.path.normcase(cur_path):
                try:
                    floater.load_gif(target_path, save=True)
                except Exception:
                    pass

    def set_work_state_mode(self, mode):
        if mode != "auto" and mode not in SCENE_KEYS:
            mode = "auto"
        sched = self.get_work_schedule()
        sched["forced_state"] = mode
        if mode in SCENE_KEYS:
            sched["auto_state_gif"] = True
        self.config["work_schedule"] = sched
        self.save()
        self._sync_state_gif(force=(mode != "auto"))
        self.refresh_idle_bubbles()

        floater = self._primary_visible_floater()
        if not floater or floater.suppressed_hidden:
            return

        if mode == "auto":
            msg = "자동 전환 모드!"
            action = "jump"
        else:
            label = WORK_STATE_LABELS.get(mode, mode)
            msg = f"{label} 모드!"
            action = "jump" if mode in ("enter", "hold", "wake") else "wiggle"
        floater.play_mini_action(action)
        floater.bubble.show_message(msg, duration_ms=4000)

    def preview_scene(self, scene_key, floater=None):
        if floater is None:
            floater = self._primary_visible_floater()
        if not floater:
            return
        if self.config.get("hidden_all"):
            self.toggle_hide_all()

        msg = resolve_floater_scene_text(floater.state, scene_key)
        if not msg:
            st = compute_work_status(
                self.get_work_schedule(),
                scene_on=floater.state.get("scene_on"),
                scene_texts=floater.state.get("scene_texts"),
            )
            msg = st["idle_bubble_text"] or SCENES_SPEC.get(scene_key, {}).get("name", "미리보기!")

        action = "jump" if scene_key in ("enter", "hold", "wake") else "wiggle"
        floater.play_mini_action(action, temp_cheer_ms=4500, temp_scene_key=scene_key)
        floater.bubble.show_message(msg, duration_ms=4500)
        if scene_key == "enter":
            floater.particles.burst(duration_ms=4200)

    def preview_state_gif(self, state_key, gif_name, floater=None, custom_text=None):
        if floater is None:
            floater = self._primary_visible_floater()
        if not floater:
            return
        if self.config.get("hidden_all"):
            self.toggle_hide_all()

        path = gif_name if os.path.isabs(gif_name) else os.path.join(GIFS_DIR, gif_name)
        if os.path.exists(path):
            try:
                floater.load_gif(path, save=False)
            except Exception:
                pass

        msg = custom_text if (isinstance(custom_text, str) and custom_text.strip()) else resolve_floater_scene_text(floater.state, state_key)
        if not msg:
            msg = "출근 준비 중!" if state_key == "rest" else "열심히 일하는 중!"
        action = "jump" if state_key in ("enter", "hold", "wake") else "wiggle"
        floater.play_mini_action(action)
        floater.bubble.show_message(msg, duration_ms=4500)
        if state_key == "enter":
            floater.particles.burst(duration_ms=4200)

    def populate_work_state_menu(self, sub_menu, status=None):
        sched = self.get_work_schedule()
        if status is None:
            status = compute_work_status(sched)
        forced = sched.get("forced_state", "auto")

        auto_var = tk.BooleanVar(value=(forced == "auto"))
        sub_menu.add_checkbutton(
            label=f"시간에 맞춰 자동 전환 (현재: {WORK_STATE_LABELS.get(status['state_key'], '근무 중')})",
            variable=auto_var,
            command=lambda: self.set_work_state_mode("auto"),
        )
        sub_menu.add_separator()
        for mode_key in ("rest", "wake", "type", "lunch", "enter", "back", "tired"):
            spec = SCENES_SPEC[mode_key]
            var = tk.BooleanVar(value=(forced == mode_key))
            sub_menu.add_checkbutton(
                label=f"{spec['name']} ({spec['caption']})",
                variable=var,
                command=lambda k=mode_key: self.set_work_state_mode(k),
            )

    def _show_startup_greeting(self):
        sched = self.get_work_schedule()
        if not sched.get("enabled", True):
            return
        floater = self._primary_visible_floater()
        if not floater or floater.suppressed_hidden:
            return

        status = compute_work_status(
            sched,
            scene_on=floater.state.get("scene_on"),
            scene_texts=floater.state.get("scene_texts"),
        )
        phase = status["phase"]
        if phase == "holiday":
            msg = "오늘 쉬는 날!"
        elif phase in ("before_work", "wake"):
            msg = "좋은 아침!"
        elif phase == "lunch":
            msg = "맛점해!"
        elif phase in ("after_work", "overtime_back", "overtime_tired"):
            msg = "오늘도 고생했어!"
        else:
            msg = "오늘도 힘내!"

        floater.play_mini_action("jump")
        floater.bubble.show_message(msg, duration_ms=4500)

    def trigger_hold_scene(self, floater=None):
        if floater is None:
            floater = self._primary_visible_floater()
        if not floater or floater.suppressed_hidden:
            return
        if not floater.state.get("scene_on", {}).get("hold", True):
            return

        msg = resolve_floater_scene_text(floater.state, "hold") or "힘내!"
        floater.play_mini_action("jump", temp_cheer_ms=2200, temp_scene_key="hold")
        floater.bubble.show_message(msg, duration_ms=2600)

    def trigger_character_interaction(self, floater, kind):
        if floater is None:
            floater = self._primary_visible_floater()
        if not floater or floater.suppressed_hidden:
            return

        spec = floater.get_personality_spec()
        if kind == "cheer":
            msg = random.choice(spec["cheers"])
            action = random.choice(spec["actions"])
            temp_scene = "hold"
        else:
            msg = spec["interactions"].get(kind) or random.choice(spec["cheers"])
            if kind == "highfive":
                action = "jump"
                temp_scene = "hold"
            elif kind == "poke":
                action = "wiggle"
                temp_scene = "hold"
            else:
                action = random.choice(spec["actions"])
                temp_scene = None

        floater.play_mini_action(action, temp_cheer_ms=3500, temp_scene_key=temp_scene)
        floater.bubble.show_message(msg, duration_ms=5500)
        if kind == "highfive":
            floater.particles.burst(duration_ms=2600)

    def trigger_interactive_pet(self, floater=None):
        self.trigger_character_interaction(floater, "cheer")

    @staticmethod
    def _vertical_band_overlaps(y1, h1, y2, h2, pad_y=8):
        return (y1 < y2 + h2 + pad_y) and (y2 < y1 + h1 + pad_y)

    @staticmethod
    def _desired_horizontal_sep(tw, otw):
        body_span = (tw + otw) * 0.5
        gap = max(10.0, min(28.0, min(tw, otw) * 0.18))
        return body_span, body_span + gap

    @staticmethod
    def _pair_key(a, b):
        ia, ib = id(a), id(b)
        return (ia, ib) if ia < ib else (ib, ia)

    def get_floater_bounds(self, floater, x_override=None, y_override=None):
        tw, th = floater.target_size()
        x = int(floater.state.get("x", 0)) if x_override is None else int(round(x_override))
        y = int(floater.state.get("y", 0)) if y_override is None else int(round(y_override))
        cx = x + tw * 0.5
        cy = y + th * 0.5
        mon = get_monitor_work_rect_for_rect(x, y, tw, th, floater.win)
        return x, y, tw, th, cx, cy, mon

    def compute_crowding_penalty(self, floater, cand_x, cand_y=None):
        x, y, tw, th, cx, _cy, mon = self.get_floater_bounds(floater, x_override=cand_x, y_override=cand_y)
        penalty = 0.0
        for other in self.floaters:
            if other is floater or other.suppressed_hidden:
                continue
            ox, oy, otw, oth, ocx, _ocy, omon = self.get_floater_bounds(other)
            if omon != mon or not self._vertical_band_overlaps(y, th, oy, oth):
                continue
            body_span, comfort_sep = self._desired_horizontal_sep(tw, otw)
            dx = abs(cx - ocx)
            if dx < body_span:
                penalty += 1000.0 + (body_span - dx) * 18.0
            elif dx < comfort_sep:
                penalty += 120.0 + (comfort_sep - dx) * 6.0
            elif dx < comfort_sep + 24.0:
                penalty += (comfort_sep + 24.0 - dx) * 0.4

            if other._walking:
                dest_cx = float(other._walk_tx) + otw * 0.5
                ddx = abs(cx - dest_cx)
                if ddx < body_span:
                    penalty += 420.0 + (body_span - ddx) * 8.0
                elif ddx < comfort_sep:
                    penalty += 60.0 + (comfort_sep - ddx) * 3.0
        return penalty

    def is_overlapping_any(self, floater, x_override=None):
        x, y, tw, th, cx, _cy, mon = self.get_floater_bounds(floater, x_override=x_override)
        for other in self.floaters:
            if other is floater or other.suppressed_hidden:
                continue
            _ox, oy, otw, oth, ocx, _ocy, omon = self.get_floater_bounds(other)
            if omon != mon or not self._vertical_band_overlaps(y, th, oy, oth):
                continue
            min_sep = (tw + otw) * 0.5 + max(6.0, min(tw, otw) * 0.10)
            if abs(cx - ocx) < min_sep:
                return True
        return False

    def choose_wander_target(self, floater, min_x, max_x):
        if max_x - min_x < 12:
            return None
        cur_x, cur_y, tw, th, _cx, _cy, mon = self.get_floater_bounds(floater)
        cur_penalty = self.compute_crowding_penalty(floater, cur_x, cur_y)
        currently_overlapped = self.is_overlapping_any(floater)

        candidates = set()
        for step_dist in (70, 110, 150, 190, 230):
            candidates.add(max(min_x, min(max_x, cur_x - step_dist)))
            candidates.add(max(min_x, min(max_x, cur_x + step_dist)))
        for _ in range(6):
            d = random.randint(60, 220)
            candidates.add(max(min_x, min(max_x, cur_x + random.choice((-1, 1)) * d)))

        neighbors = []
        for other in self.floaters:
            if other is floater or other.suppressed_hidden:
                continue
            ox, oy, otw, oth, _ocx, _ocy, omon = self.get_floater_bounds(other)
            if omon == mon and self._vertical_band_overlaps(cur_y, th, oy, oth):
                neighbors.append((ox, ox + otw, otw))
        neighbors.sort(key=lambda n: n[0])

        for ox, ox_end, otw in neighbors:
            gap = int(round(max(12.0, min(28.0, min(tw, otw) * 0.20))))
            candidates.add(max(min_x, min(max_x, ox - tw - gap)))
            candidates.add(max(min_x, min(max_x, ox_end + gap)))

        if neighbors:
            edges = [(min_x, neighbors[0][0])]
            for idx in range(len(neighbors) - 1):
                edges.append((neighbors[idx][1], neighbors[idx + 1][0]))
            edges.append((neighbors[-1][1], max_x + tw))
            for left_edge, right_edge in edges:
                span = right_edge - left_edge
                if span >= tw + 8:
                    mid = int(round((left_edge + right_edge - tw) * 0.5))
                    candidates.add(max(min_x, min(max_x, mid)))
                    candidates.add(max(min_x, min(max_x, int(left_edge) + 12)))
                    candidates.add(max(min_x, min(max_x, int(right_edge) - tw - 12)))

        sample_count = 10
        span_x = max_x - min_x
        for i in range(sample_count + 1):
            candidates.add(int(round(min_x + span_x * (i / float(sample_count)))))

        valid = [cx for cx in candidates if abs(cx - cur_x) >= 12]
        if not valid:
            return None

        scored = [(self.compute_crowding_penalty(floater, cx, cur_y), abs(cx - cur_x), cx) for cx in valid]
        clean = [item for item in scored if item[0] < 25.0]
        if clean:
            if currently_overlapped:
                clean.sort(key=lambda item: (item[0] > 1.0, item[1]))
                best_dist = clean[0][1]
                nearby = [item for item in clean if item[1] <= best_dist + 40 and (item[0] <= 1.0 or clean[0][0] > 1.0)]
                return random.choice(nearby[:3])[2]
            natural = [item for item in clean if 55 <= item[1] <= 240 and item[0] <= 10.0]
            pool = natural if natural else clean
            pool.sort(key=lambda item: (round(item[0], 1), random.random()))
            return random.choice(pool[:min(6, len(pool))])[2]

        best_pen, _best_dist, best_x = min(scored, key=lambda item: (item[0], item[1]))
        if currently_overlapped:
            return best_x if (best_pen + 40.0 < cur_penalty) else None
        if best_pen <= cur_penalty + 15.0 and best_pen < 500.0:
            return best_x
        return None

    def should_yield_step(self, floater, cur_x, next_x, cur_y):
        if next_x == cur_x:
            return False, cur_x, None
        move_dir = 1 if next_x > cur_x else -1
        tw, th = floater.target_size()
        mon = get_monitor_work_rect_for_rect(cur_x, cur_y, tw, th, floater.win)
        cur_cx = cur_x + tw * 0.5
        next_cx = next_x + tw * 0.5
        tx_center = float(floater._walk_tx) + tw * 0.5

        for other in self.floaters:
            if other is floater or other.suppressed_hidden:
                continue
            ox, oy, otw, oth, ocx, _ocy, omon = self.get_floater_bounds(other)
            if omon != mon or not self._vertical_band_overlaps(cur_y, th, oy, oth):
                continue
            body_span, comfort_sep = self._desired_horizontal_sep(tw, otw)
            cur_dist = abs(cur_cx - ocx)
            next_dist = abs(next_cx - ocx)
            if next_dist >= cur_dist or next_dist >= comfort_sep:
                continue
            if cur_dist < (tw + otw) * 0.45:
                continue

            other_dir = (1 if other._walk_tx > float(other.state.get("x", 0)) else -1) if other._walking else 0
            head_on = other._walking and (other_dir == -move_dir)
            target_blocked = abs(tx_center - ocx) < comfort_sep
            other_dest_blocked = other._walking and abs(tx_center - (float(other._walk_tx) + otw * 0.5)) < comfort_sep

            if target_blocked or other_dest_blocked or head_on:
                if cur_cx < ocx:
                    ideal = int(math.floor(ocx - comfort_sep - tw * 0.5))
                    stop_x = max(cur_x, min(next_x, ideal))
                else:
                    ideal = int(math.ceil(ocx + comfort_sep - tw * 0.5))
                    stop_x = min(cur_x, max(next_x, ideal))
                return True, stop_x, other
        return False, next_x, None

    def schedule_overlap_separation(self, exclude=None, base_delay_ms=280):
        if self.config.get("hidden_all", False):
            return
        now_ts = time.time()
        stagger = 0
        for f in list(self.floaters):
            if f is exclude or f.suppressed_hidden or f._dragging or f._walking:
                continue
            if not f._can_wander() or f._action_after_id is not None:
                continue
            if now_ts < f._social_hold_until or (now_ts - f._last_avoid_ts) < 3.0:
                continue
            if not self.is_overlapping_any(f):
                continue
            cur_x, cur_y, tw, th, _cx, _cy, mon = self.get_floater_bounds(f)
            min_x = mon[0] + 12
            max_x = max(min_x, mon[2] - tw - 12)
            cand = self.choose_wander_target(f, min_x, max_x)
            if cand is not None and abs(cand - cur_x) >= 12:
                f._last_avoid_ts = now_ts
                f._schedule_wander(base_delay_ms + stagger)
                stagger += 160

    def on_floater_dropped(self, dropped):
        if dropped is None or dropped.suppressed_hidden:
            return
        self.schedule_overlap_separation(exclude=dropped, base_delay_ms=260)
        if dropped._can_wander() and self.is_overlapping_any(dropped):
            dropped._last_avoid_ts = time.time()
            dropped._schedule_wander(900)
        self.root.after(220, lambda: self.check_proximity_interaction(dropped))

    def _is_social_eligible(self, floater):
        if floater is None or floater not in self.floaters:
            return False
        if floater.suppressed_hidden or floater._dragging or bool(floater.state.get("paused", False)):
            return False
        if floater._action_after_id is not None or floater.bubble._temp_event_active:
            return False
        if time.time() < floater._social_hold_until:
            return False
        return True

    def are_facing_each_other(self, a, b):
        if a is None or b is None or a is b:
            return False
        if a.suppressed_hidden or b.suppressed_hidden or a._dragging or b._dragging:
            return False
        ax, ay, aw, ah, acx, acy, amon = self.get_floater_bounds(a)
        bx, by, bw, bh, bcx, bcy, bmon = self.get_floater_bounds(b)
        if amon != bmon:
            return False
        max_dy = max(110, int((ah + bh) * 0.85))
        if abs(acy - bcy) > max_dy:
            return False
        dx = abs(acx - bcx)
        min_dx = max(24, int((aw + bw) * 0.32))
        max_dx = max(210, int((aw + bw) * 1.65))
        if not (min_dx <= dx <= max_dx):
            return False

        if acx < bcx:
            left_char, right_char = a, b
            left_cx, right_cx = acx, bcx
        else:
            left_char, right_char = b, a
            left_cx, right_cx = bcx, acx

        if left_char.is_facing_left() or not right_char.is_facing_left():
            return False

        for c in self.floaters:
            if c is a or c is b or c.suppressed_hidden:
                continue
            _cx, cy, _cw, ch, ccx, _ccy, cmon = self.get_floater_bounds(c)
            if cmon != amon:
                continue
            if self._vertical_band_overlaps(ay, ah, cy, ch) or self._vertical_band_overlaps(by, bh, cy, ch):
                if left_cx < ccx < right_cx:
                    return False
        return True

    def trigger_social_interaction(self, initiator=None, partner=None, auto=False):
        visible = [f for f in self.floaters if not f.suppressed_hidden and not f._dragging]
        if len(visible) < 2:
            return False

        if initiator is None or initiator not in visible:
            initiator = random.choice(visible)
        others = [f for f in visible if f is not initiator]
        if partner is None or partner not in others:
            itw, _ = initiator.target_size()
            icx = int(initiator.state.get("x", 0)) + itw // 2
            partner = min(
                others,
                key=lambda f: abs((int(f.state.get("x", 0)) + f.target_size()[0] // 2) - icx),
            )

        if initiator._dragging or partner._dragging:
            return False
        if auto and (initiator.bubble._temp_event_active or partner.bubble._temp_event_active):
            return False

        try:
            if not initiator.win.winfo_exists() or not partner.win.winfo_exists():
                return False
        except Exception:
            return False

        itw, _ = initiator.target_size()
        ptw, _ = partner.target_size()
        ix = int(initiator.state.get("x", 0)) + itw // 2
        px = int(partner.state.get("x", 0)) + ptw // 2

        now_ts = time.time()
        hold_until = now_ts + 5.8
        initiator._social_hold_until = hold_until
        partner._social_hold_until = hold_until

        initiator._stop_wander(reset_pos=False, reset_facing=False)
        partner._stop_wander(reset_pos=False, reset_facing=False)
        initiator.face_towards(px)
        partner.face_towards(ix)

        pk = self._pair_key(initiator, partner)
        self._pair_social_until[pk] = now_ts + random.uniform(45.0, 80.0)
        self._pair_probe_ts[pk] = now_ts
        self._next_auto_social_ts = now_ts + random.uniform(20.0, 35.0)
        self._last_social_ts = now_ts
        self._last_social_probe_ts = now_ts

        i_spec = initiator.get_personality_spec()
        initiator.play_mini_action(random.choice(i_spec["actions"]))
        initiator.bubble.show_message(random.choice(i_spec["greet_open"]), duration_ms=5200)

        holder = [None]

        def _reply():
            if holder[0] in self._social_after_ids:
                self._social_after_ids.remove(holder[0])
            if partner not in self.floaters or partner.suppressed_hidden or partner._dragging:
                return
            try:
                if not partner.win.winfo_exists():
                    return
            except Exception:
                return
            p_spec = partner.get_personality_spec()
            target_cx = (
                int(initiator.state.get("x", 0)) + initiator.target_size()[0] // 2
                if initiator in self.floaters
                else ix
            )
            partner.face_towards(target_cx)
            partner.play_mini_action(random.choice(p_spec["actions"]))
            partner.bubble.show_message(random.choice(p_spec["greet_reply"]), duration_ms=5200)

        aid = self.root.after(1100, _reply)
        holder[0] = aid
        self._social_after_ids.append(aid)
        return True

    def check_proximity_interaction(self, moving_floater):
        if self.config.get("hidden_all", False) or not self._is_social_eligible(moving_floater):
            return False
        now_ts = time.time()
        if now_ts < self._next_auto_social_ts:
            return False

        for other in list(self.floaters):
            if other is moving_floater or not self._is_social_eligible(other):
                continue
            if not self.are_facing_each_other(moving_floater, other):
                continue
            pk = self._pair_key(moving_floater, other)
            if now_ts < self._pair_social_until.get(pk, 0.0):
                continue
            if (now_ts - self._pair_probe_ts.get(pk, 0.0)) < 2.8:
                continue
            self._pair_probe_ts[pk] = now_ts
            if random.random() < 0.42:
                first, second = (moving_floater, other) if random.random() < 0.5 else (other, moving_floater)
                return self.trigger_social_interaction(first, second, auto=True)
        return False

    def _check_ambient_social_and_spacing(self):
        self._ambient_after_id = None
        try:
            if not self.config.get("hidden_all", False):
                self.schedule_overlap_separation(base_delay_ms=260)
                now_ts = time.time()
                if now_ts >= self._next_auto_social_ts:
                    eligible = [f for f in self.floaters if self._is_social_eligible(f)]
                    pairs = []
                    for i in range(len(eligible)):
                        for j in range(i + 1, len(eligible)):
                            a, b = eligible[i], eligible[j]
                            if not self.are_facing_each_other(a, b):
                                continue
                            pk = self._pair_key(a, b)
                            if now_ts < self._pair_social_until.get(pk, 0.0):
                                continue
                            if (now_ts - self._pair_probe_ts.get(pk, 0.0)) < 2.8:
                                continue
                            pairs.append((a, b, pk))
                    if pairs:
                        random.shuffle(pairs)
                        for a, b, pk in pairs:
                            self._pair_probe_ts[pk] = now_ts
                            if random.random() < 0.35:
                                first, second = (a, b) if random.random() < 0.5 else (b, a)
                                if self.trigger_social_interaction(first, second, auto=True):
                                    break
        finally:
            self._ambient_after_id = self.root.after(3500, self._check_ambient_social_and_spacing)

    def trigger_group_cheer(self):
        visible = [f for f in self.floaters if not f.suppressed_hidden]
        if not visible:
            return
        for idx, floater in enumerate(visible):
            spec = floater.get_personality_spec()
            floater.play_mini_action("jump", temp_cheer_ms=3500, temp_scene_key="hold")
            floater.bubble.show_message(random.choice(spec["cheers"]), duration_ms=6000)
            if idx == 0:
                floater.particles.burst(duration_ms=3200)

    def preview_work_event(self):
        floater = self._primary_visible_floater()
        if not floater or floater.suppressed_hidden:
            if self.config.get("hidden_all"):
                self.toggle_hide_all()
            floater = self._primary_visible_floater()
        if not floater or floater.suppressed_hidden:
            return
        floater.play_mini_action("jump", temp_cheer_ms=4000, temp_scene_key="hold")
        floater.bubble.show_message(
            "잘하고 있어! 힘내!",
            duration_ms=5500,
        )

    def trigger_leave_celebration(self, floater=None):
        if self.config.get("hidden_all"):
            self.toggle_hide_all()
        if floater is None:
            floater = self._primary_visible_floater()
        if not floater or floater.suppressed_hidden:
            return
        msg = resolve_floater_scene_text(floater.state, "enter") or "퇴근이다!"
        floater.play_mini_action("jump", temp_cheer_ms=6000, temp_scene_key="enter")
        floater.bubble.show_message(
            msg,
            duration_ms=7500,
        )
        floater.particles.burst(duration_ms=4800)

    def open_work_schedule_dialog(self, initial_floater=None):
        if self._schedule_dialog is not None:
            try:
                if initial_floater is not None:
                    self._schedule_dialog.select_floater(initial_floater)
                self._schedule_dialog.win.lift()
                self._schedule_dialog.win.focus_force()
                return
            except Exception:
                self._schedule_dialog = None
        self._schedule_dialog = WorkScheduleDialog(self, initial_floater=initial_floater)

    def on_schedule_dialog_closed(self):
        self._schedule_dialog = None

    def apply_work_schedule(self, new_sched):
        self.config["work_schedule"] = normalize_work_schedule(new_sched)
        self.save()

        now = datetime.datetime.now()
        status = compute_work_status(self.config["work_schedule"], now)
        self._last_event_date = now.strftime("%Y-%m-%d")
        self._last_checked_min = status["cur_min"]
        self._last_progress_pct = status["progress_pct"]
        self._triggered_keys.clear()
        self._last_stretch_ts = time.time()

        self._sync_state_gif(force=False)
        for f in self.floaters:
            f.bubble._temp_event_active = False
        self.refresh_idle_bubbles()

        floater = self._primary_visible_floater()
        if floater and not floater.suppressed_hidden and floater.state.get("bubble_on", True):
            floater.play_mini_action("jump")
            floater.bubble.show_message(
                f"설정 저장 완료! ({status['idle_bubble_text']})",
                duration_ms=4000,
            )

    def _fire_event(self, text, action="jump", temp_cheer_ms=0, temp_scene_key=None):
        floater = self._primary_visible_floater()
        if not floater or floater.suppressed_hidden:
            return
        floater.play_mini_action(action, temp_cheer_ms=temp_cheer_ms, temp_scene_key=temp_scene_key)
        floater.bubble.show_message(text, duration_ms=7500)

    def _check_work_events(self):
        try:
            self._run_work_event_tick()
        finally:
            self.root.after(10000, self._check_work_events)

    def _run_work_event_tick(self):
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        if today != self._last_event_date:
            self._last_event_date = today
            self._triggered_keys.clear()
            self._last_checked_min = -1
            self._last_progress_pct = 0.0

        idle_sec = get_idle_seconds()
        sched = self.get_work_schedule()
        status = compute_work_status(sched, now, idle_sec=idle_sec)
        cur_min = status["cur_min"]
        cur_pct = status["progress_pct"]

        prev_min = self._last_checked_min
        prev_pct = self._last_progress_pct
        self._last_checked_min = cur_min
        self._last_progress_pct = cur_pct

        if not self.config.get("hidden_all", False):
            self._sync_state_gif(idle_sec=idle_sec)
            self.refresh_idle_bubbles(idle_sec=idle_sec)

        if not sched.get("enabled", True) or self.config.get("hidden_all", False):
            return
        if not status["is_work_day"]:
            return

        def hit_time(key, target_min):
            if (today, key) in self._triggered_keys:
                return False
            if target_min < 0:
                return False
            if prev_min < target_min <= cur_min:
                self._triggered_keys.add((today, key))
                return True
            return False

        start_m = status["start_min"]
        end_m = status["end_min"]
        lunch_on = status["lunch_on"]
        lunch_s = status["lunch_start_min"]
        lunch_e = status["lunch_end_min"]

        if hit_time("work_start", start_m):
            self._fire_event("출근 완료! 힘내!", "jump", temp_cheer_ms=3000, temp_scene_key="type")
            return
        if lunch_on and lunch_s > start_m + 10 and hit_time("lunch_soon", lunch_s - 10):
            self._fire_event("점심 10분 전!", "wiggle")
            return
        if lunch_on and lunch_s < lunch_e and hit_time("lunch_start", lunch_s):
            self._fire_event("점심시간! 맛있게 먹어!", "jump", temp_cheer_ms=5000, temp_scene_key="lunch")
            return
        if lunch_on and lunch_s < lunch_e and hit_time("lunch_end", lunch_e):
            self._fire_event("오후도 힘내자!", "wiggle")
            return

        if end_m - start_m >= 120 and hit_time("end_60", end_m - 60):
            self._fire_event("퇴근 1시간 전! 힘내!", "wiggle")
            return
        if end_m - start_m >= 60 and hit_time("end_30", end_m - 30):
            self._fire_event("퇴근 30분 전!", "wiggle")
            return
        if end_m - start_m >= 30 and hit_time("end_15", end_m - 15):
            self._fire_event("퇴근 15분 전! 마무리하자!", "jump")
            return
        if hit_time("end_10", end_m - 10):
            self._fire_event("퇴근 10분 전! 저장 잊지 마!", "jump")
            return
        if hit_time("end_1", end_m - 1):
            self._fire_event("퇴근 1분 전!", "jump")
            return
        if hit_time("work_end", end_m):
            self.trigger_leave_celebration()
            return

        # Progress milestones: 25%, 50%, 75%
        milestone_msgs = [
            (25, "벌써 25% 지났어!", "wiggle"),
            (50, "절반 왔어! 잘하고 있어!", "jump"),
            (75, "75% 돌파! 조금만 더 힘내!", "jump"),
        ]
        for pct_mark, msg, action in milestone_msgs:
            key = f"pct_{pct_mark}"
            if (today, key) not in self._triggered_keys and prev_pct < pct_mark <= cur_pct:
                self._triggered_keys.add((today, key))
                self._fire_event(msg, action)
                return

        now_ts = time.time()
        in_working = status["phase"] in ("working_am", "working_pm")
        if not in_working:
            return

        # Stretch / hydration reminder
        stretch_min = int(sched.get("stretch_interval_min", 0))
        if stretch_min > 0 and (now_ts - self._last_stretch_ts) >= stretch_min * 60:
            self._last_stretch_ts = now_ts
            for f in self.floaters:
                f._next_random_ts = max(f._next_random_ts, now_ts + 300)
            self._fire_event(random.choice(STRETCH_MESSAGES), "wiggle")
            return

        # Random cheerful pop-up (independent per character)
        if sched.get("random_chat_enabled", True):
            for floater in list(self.floaters):
                if floater.suppressed_hidden:
                    continue
                if now_ts >= floater._next_random_ts:
                    spec = floater.get_personality_spec()
                    floater._next_random_ts = now_ts + floater.next_random_cheer_delay()
                    floater.play_mini_action(random.choice(spec["actions"]))
                    floater.bubble.show_message(
                        random.choice(spec["cheers"]),
                        duration_ms=7500,
                    )

    def _get_clock_anchor(self, offset_idx, tw, th):
        work_left, work_top, work_right, work_bottom = get_monitor_work_rect_for_point(0, 0, self.root)
        spacing = max(tw + 14, 160)
        x = max(work_left + 12, work_right - tw - 24 - offset_idx * spacing)
        y = max(work_top + 12, work_bottom - th - 6)
        return x, y

    def _find_non_overlapping_anchor(self, offset_idx, tw, th):
        work_left, work_top, work_right, work_bottom = get_monitor_work_rect_for_point(0, 0, self.root)
        base_x, y = self._get_clock_anchor(offset_idx, tw, th)
        if not self.floaters:
            return base_x, y

        spacing = max(tw + 14, 160)
        max_slots = max(1, (work_right - work_left - tw - 36) // spacing + 1)
        best_x = base_x
        best_overlap = float("inf")
        for slot in range(max_slots):
            cand_x = max(work_left + 12, work_right - tw - 24 - slot * spacing)
            cand_cx = cand_x + tw * 0.5
            overlap_score = 0.0
            for f in self.floaters:
                if f.suppressed_hidden:
                    continue
                fx, fy, otw, oth, ocx, _ocy, omon = self.get_floater_bounds(f)
                if omon != (work_left, work_top, work_right, work_bottom):
                    continue
                if not self._vertical_band_overlaps(y, th, fy, oth):
                    continue
                _body_span, comfort_sep = self._desired_horizontal_sep(tw, otw)
                dx = abs(cand_cx - ocx)
                if dx < comfort_sep:
                    overlap_score += (comfort_sep - dx)
            if overlap_score == 0.0:
                return cand_x, y
            if overlap_score < best_overlap:
                best_overlap = overlap_score
                best_x = cand_x
        return best_x, y

    def _default_state(self, offset_idx, preset_key=None):
        gifs = get_available_gifs()
        gif_path = gifs[offset_idx % len(gifs)] if gifs else None
        size = 180
        x, y = self._find_non_overlapping_anchor(offset_idx, size, size)
        base = {
            "name": f"캐릭터 {offset_idx + 1}",
            "personality": PERSONALITY_KEYS[offset_idx % len(PERSONALITY_KEYS)],
            "gif_path": gif_path,
            "x": x,
            "y": y,
            "display_size": size,
            "opacity": 1.0,
            "speed": 1.0,
            "flip_h": False,
            "click_through": False,
            "topmost": True,
            "paused": False,
            "bubble_on": True,
            "fixed_pos": False,
            "wander": True,
            "auto_state_gif": True,
            "scene_gifs": default_scene_gifs_map(),
            "scene_texts": default_scene_texts_map(),
            "scene_on": default_scene_on_map(),
        }
        if preset_key in CHARACTER_PRESETS:
            patch = build_character_preset_patch(preset_key)
            base.update(patch)
            type_ref = patch["scene_gifs"].get("type")
            if type_ref:
                type_path = type_ref if os.path.isabs(type_ref) else os.path.join(GIFS_DIR, type_ref)
                if os.path.exists(type_path):
                    base["gif_path"] = type_path
        return normalize_floater_state(base, offset_idx, self.get_work_schedule())

    def _spawn(self, state):
        floater = FloaterWindow(self, state)
        self.floaters.append(floater)
        if self.config.get("hidden_all", False):
            floater.set_suppressed_hidden(True)
        else:
            floater.schedule_next_frame()

    def _poll_tray(self):
        if self.tray:
            self.tray.poll()
            self.root.after(40, self._poll_tray)

    def populate_add_preset_menu(self, sub_menu):
        for pk in CHARACTER_PRESET_KEYS:
            spec = CHARACTER_PRESETS[pk]
            pname = PERSONALITY_SPECS[spec["personality"]]["name"]
            sub_menu.add_command(
                label=f"{spec['label']} ({pname})",
                command=lambda k=pk: self.add_floater(preset_key=k),
            )

    def add_floater(self, preset_key=None):
        state = self._default_state(len(self.floaters), preset_key=preset_key)
        self.config["floaters"].append(state)
        self.config["hidden_all"] = False
        for f in self.floaters:
            f.set_suppressed_hidden(False)
        self._spawn(state)
        new_floater = self.floaters[-1]
        self._sync_state_gif(force=False, target_floater=new_floater)
        self.refresh_idle_bubbles()
        self.save()
        if preset_key in CHARACTER_PRESETS and not new_floater.suppressed_hidden:
            spec = new_floater.get_personality_spec()
            msg = resolve_floater_scene_text(new_floater.state, "hold") or f"{new_floater.state['name']} 등장!"
            new_floater.play_mini_action(spec["actions"][0])
            new_floater.bubble.show_message(msg, duration_ms=4000)

    def apply_chiikawa_presets_to_all(self):
        if not self.floaters:
            return
        self.config["hidden_all"] = False
        for idx, fl in enumerate(self.floaters):
            fl.set_suppressed_hidden(False)
            pk = CHIIKAWA_BATCH_PRESET_KEYS[idx % len(CHIIKAWA_BATCH_PRESET_KEYS)]
            fl.apply_preset(pk, announce=False)
        self.refresh_idle_bubbles()
        self.save()
        for fl in self.floaters:
            if not fl.suppressed_hidden:
                spec = fl.get_personality_spec()
                msg = resolve_floater_scene_text(fl.state, "hold") or f"{fl.state['name']} 등장!"
                fl.play_mini_action(spec["actions"][0])
                fl.bubble.show_message(msg, duration_ms=4200)

    def close_floater(self, floater):
        if len(self.floaters) <= 1:
            self.config["hidden_all"] = True
            floater.set_suppressed_hidden(True)
            self.save()
            return
        fid = id(floater)
        self._pair_social_until = {k: v for k, v in self._pair_social_until.items() if fid not in k}
        self._pair_probe_ts = {k: v for k, v in self._pair_probe_ts.items() if fid not in k}
        self.floaters.remove(floater)
        self.config["floaters"].remove(floater.state)
        floater.destroy()
        self.save()

    def toggle_hide_all(self):
        hidden = not self.config.get("hidden_all", False)
        self.config["hidden_all"] = hidden
        for f in self.floaters:
            f.set_suppressed_hidden(hidden)
        if not hidden:
            self.refresh_idle_bubbles()
        self.save()

    def toggle_click_through_all(self):
        any_locked = any(f.state.get("click_through", False) for f in self.floaters)
        target = not any_locked
        for f in self.floaters:
            f.set_click_through(target)
        self.save()

    def toggle_wander_all(self):
        any_wandering = any(f.state.get("wander", True) for f in self.floaters)
        target = not any_wandering
        for f in self.floaters:
            f.state["wander"] = target
            if target:
                f.state["fixed_pos"] = False
            f.sync_wander_state()
        self.save()

    def move_to_clock_area(self):
        self.config["hidden_all"] = False
        for i, f in enumerate(self.floaters):
            f._stop_wander(reset_pos=False)
            f.set_suppressed_hidden(False)
            tw, th = f.target_size()
            nx, ny = self._get_clock_anchor(i, tw, th)
            f.state["x"] = nx
            f.state["y"] = ny
            _set_window_geometry(f.win, nx, ny)
            f.bubble.update_position()
            f.particles.update_position()
            f.sync_wander_state()
        self.refresh_idle_bubbles()
        self.save()

    def open_gifs_folder(self):
        os.makedirs(GIFS_DIR, exist_ok=True)
        try:
            subprocess.Popen(["explorer", GIFS_DIR])
        except Exception:
            pass

    def show_tray_menu(self):
        self.tray_menu.delete(0, tk.END)
        self.tray_menu.add_command(label=APP_NAME, state=tk.DISABLED)

        status = compute_work_status(self.get_work_schedule())
        self.tray_menu.add_command(label=f"{status['status_line']}", command=self.open_work_schedule_dialog)
        self.tray_menu.add_separator()

        self.tray_menu.add_command(label="응원 한마디 (더블클릭)", command=self.trigger_interactive_pet)
        self.tray_menu.add_command(
            label="캐릭터끼리 인사/대화하기",
            state=(tk.NORMAL if len(self.floaters) > 1 else tk.DISABLED),
            command=self.trigger_social_interaction,
        )
        self.tray_menu.add_command(label="모두 함께 합동 응원!", command=self.trigger_group_cheer)
        self.tray_menu.add_command(label="퇴근 축하 파티클 ★", command=self.trigger_leave_celebration)

        tray_preview_sub = tk.Menu(self.tray_menu, tearoff=0)
        for p_label, p_key in [
            ("출근 (2분 전)", "wake"),
            ("점심시간", "lunch"),
            ("퇴근 (파티클)", "enter"),
            ("야근 5분", "back"),
            ("야근 20분", "tired"),
            ("누를 때", "hold"),
        ]:
            tray_preview_sub.add_command(
                label=p_label,
                command=lambda k=p_key: self.preview_scene(k),
            )
        self.tray_menu.add_cascade(label="미리보기", menu=tray_preview_sub)

        tray_state_sub = tk.Menu(self.tray_menu, tearoff=0)
        self.populate_work_state_menu(tray_state_sub, status)
        self.tray_menu.add_cascade(label="근무 상태 모드 전환", menu=tray_state_sub)

        self.tray_menu.add_command(label="근무시간 및 캐릭터 설정...", command=self.open_work_schedule_dialog)
        tray_bubble_sub = tk.Menu(self.tray_menu, tearoff=0)
        self.populate_bubble_format_menu(tray_bubble_sub)
        self.tray_menu.add_cascade(label="남은 시간 표시", menu=tray_bubble_sub)
        self.tray_menu.add_separator()

        hide_label = "모두 보이기 (Ctrl+Alt+H)" if self.config.get("hidden_all") else "모두 숨기기 (Ctrl+Alt+H)"
        self.tray_menu.add_command(label=hide_label, command=self.toggle_hide_all)

        ct_var = tk.BooleanVar(value=any(f.state.get("click_through", False) for f in self.floaters))
        self.tray_menu.add_checkbutton(
            label="클릭 통과 모드 (Ctrl+Alt+L)",
            variable=ct_var,
            command=self.toggle_click_through_all,
        )

        wander_var = tk.BooleanVar(value=any(f.state.get("wander", True) for f in self.floaters))
        self.tray_menu.add_checkbutton(
            label="모두 돌아다니기 (좌우 이동)",
            variable=wander_var,
            command=self.toggle_wander_all,
        )
        if HAS_WINREG:
            auto_var = tk.BooleanVar(value=is_autostart_enabled())
            self.tray_menu.add_checkbutton(
                label="Windows 시작 시 자동 실행",
                variable=auto_var,
                command=self.toggle_autostart,
            )
        self.tray_menu.add_separator()
        self.tray_menu.add_command(label="새 캐릭터 추가 (+)", command=self.add_floater)
        tray_preset_sub = tk.Menu(self.tray_menu, tearoff=0)
        self.populate_add_preset_menu(tray_preset_sub)
        self.tray_menu.add_cascade(label="프리셋으로 캐릭터 추가 (+)", menu=tray_preset_sub)
        self.tray_menu.add_command(
            label="모든 캐릭터에 치이카와 프리셋 배정",
            command=self.apply_chiikawa_presets_to_all,
        )
        self.tray_menu.add_command(label="gifs 폴더 열기", command=self.open_gifs_folder)
        self.tray_menu.add_command(label="시계 위로 돌아가기", command=self.move_to_clock_area)
        self.tray_menu.add_separator()
        self.tray_menu.add_command(label="종료", command=self.quit)

        try:
            x, y = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.tray.hwnd)
            self.tray_menu.tk_popup(x, y)
        except Exception:
            pass

    def save(self):
        save_config(self.config)

    def quit(self):
        self.save()
        if getattr(self, "_ambient_after_id", None) is not None:
            try:
                self.root.after_cancel(self._ambient_after_id)
            except Exception:
                pass
            self._ambient_after_id = None
        for aid in list(getattr(self, "_social_after_ids", [])):
            try:
                self.root.after_cancel(aid)
            except Exception:
                pass
        self._social_after_ids = []
        if self._schedule_dialog is not None:
            try:
                self._schedule_dialog.close()
            except Exception:
                pass
        if self.tray:
            self.tray.cleanup()
        for f in list(self.floaters):
            f.destroy()
        self.root.quit()

    def run(self):
        try:
            self.root.mainloop()
        finally:
            if self.tray:
                self.tray.cleanup()


if __name__ == "__main__":
    enable_dpi_awareness()
    GifFloaterApp().run()
