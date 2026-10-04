"""Log which wifi you are on and how strong it is. Opens as a csv."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
CSV_PATH = APP_DIR / "ssid_log.csv"
STARTUP_NAME = "SsidDiary.vbs"

stop_event = threading.Event()
state = {"ssid": "-", "signal": "-", "last": "starting"}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text('{"enabled": true, "seconds": 45}\n', encoding="utf-8")
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"enabled": True, "seconds": 45}


def save_config(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def startup_path() -> Path:
    return (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft/Windows/Start Menu/Programs/Startup"
        / STARTUP_NAME
    )


def set_startup(icon, want: bool) -> None:
    p = startup_path()
    script = Path(__file__).resolve()
    try:
        if want:
            p.write_text(
                'Set sh = CreateObject("WScript.Shell")\n'
                f'sh.CurrentDirectory = "{script.parent}"\n'
                f'sh.Run "pythonw ""{script}""", 0, False\n',
                encoding="ascii",
            )
        elif p.exists():
            p.unlink()
        cfg = load_config()
        cfg["start_with_windows"] = want
        save_config(cfg)
        icon.update_menu()
    except OSError:
        pass


def wifi_info() -> tuple[str, str]:
    try:
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return "", ""
    ssid, signal = "", ""
    for line in out.splitlines():
        if "SSID" in line and "BSSID" not in line:
            ssid = line.split(":", 1)[-1].strip()
        if "Signal" in line:
            signal = line.split(":", 1)[-1].strip()
    return ssid, signal


def append_row(ssid: str, signal: str) -> None:
    new = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "ssid", "signal"])
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ssid, signal])


def worker() -> None:
    prev = None
    while not stop_event.is_set():
        cfg = load_config()
        wait = max(20, int(cfg.get("seconds") or 45))
        if cfg.get("enabled", True):
            ssid, signal = wifi_info()
            state["ssid"] = ssid or "offline"
            state["signal"] = signal or "-"
            band = (signal or "").replace("%", "").strip()[:2]
            key = (ssid, band)
            if ssid and key != prev:
                append_row(ssid, signal)
                prev = key
            state["last"] = "logged"
        else:
            state["last"] = "paused"
        stop_event.wait(wait)


def open_csv(_i=None, _item=None) -> None:
    if not CSV_PATH.exists():
        append_row("(none yet)", "")
    try:
        os.startfile(str(CSV_PATH))
    except OSError:
        pass


def toggle(icon, on: bool) -> None:
    cfg = load_config()
    cfg["enabled"] = on
    save_config(cfg)
    try:
        icon.update_menu()
    except Exception:
        pass


def quit_app(icon, _item=None) -> None:
    stop_event.set()
    icon.stop()


def menu(icon):
    cfg = load_config()
    en = bool(cfg.get("enabled", True))
    return pystray.Menu(
        pystray.MenuItem(f"SSID: {state['ssid']}", None, enabled=False),
        pystray.MenuItem(f"Signal: {state['signal']}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("ON", lambda i, _: toggle(i, True), checked=lambda _: en, radio=True),
        pystray.MenuItem("OFF", lambda i, _: toggle(i, False), checked=lambda _: not en, radio=True),
        pystray.MenuItem(
            "Start with Windows",
            lambda i, _: set_startup(i, not startup_path().exists()),
            checked=lambda _: startup_path().exists(),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open log (csv)", open_csv),
        pystray.MenuItem("Quit", quit_app),
    )


def icon_img():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=(40, 90, 140, 255))
    d.arc((16, 18, 48, 50), 200, 340, fill="white", width=4)
    d.ellipse((28, 36, 36, 44), fill="white")
    return img


def main() -> None:
    load_config()
    threading.Thread(target=worker, daemon=True).start()
    icon = pystray.Icon("SsidDiary", icon_img(), "SSID diary", menu=pystray.Menu(lambda: menu(icon)))
    icon.run()


if __name__ == "__main__":
    main()
