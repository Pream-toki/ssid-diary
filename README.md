# SSID diary

When the wifi name or signal band changes, it appends a line to `ssid_log.csv` (time, ssid, signal).

## Setup

Python 3 → `START.bat` → blue wifi-style icon.

## Use

- Tray shows current SSID and signal.
- **Open log (csv)** — Excel / Google Sheets.
- **ON / OFF** — stop writing without quitting.
- **Start with Windows** if you want a all-day log.

**Careful**

- The csv is only on your disk. Don’t upload it if it has locations you care about.
- It needs Windows wifi (`netsh`). Ethernet-only = mostly empty.
- Logging on every tiny signal wiggle is avoided; it logs when the name or the signal *band* changes.
