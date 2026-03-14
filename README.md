# ◈ DSA Contest Tracker

> A live desktop widget for **Codeforces**, **LeetCode** & **AtCoder** — sits on your Windows desktop behind your icons, lives in your system tray, and launches with a single `contests` command.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Features

| | Feature | Description |
|---|---------|-------------|
| 🔴 | Live Contests | Highlighted in green with a real-time "ends in" countdown |
| 🟣 | Upcoming Contests | Sorted by start time with "starts in" countdown |
| 🖱️ | Clickable Cards | Click any contest to open it directly in your browser |
| 🖥️ | Desktop Embed | Sits behind desktop icons using the Win32 WorkerW trick |
| 🔔 | System Tray | Lives in your taskbar tray — click to show/hide |
| ⌨️ | `contests` Command | Type it in any terminal to launch the widget |
| ⏻ | Auto Startup | One-click toggle to launch silently on every Windows boot |
| ⟳ | Auto Refresh | Fetches fresh data every 5 minutes |
| ▲▼ | Scrollable | Arrow buttons + mouse wheel + scrollbar |
| ─ | Collapsible | Hide/show the list to save screen space |

> The widget stays on the desktop only — it **never hovers over your open apps**.

---

## Requirements

- **Python 3.8+** — [download here](https://www.python.org/downloads/)
- **pywin32** — desktop embedding + startup registry
- **pystray** — system tray icon
- **Pillow** — tray icon rendering

Install everything at once:

```bash
pip install pywin32 pystray pillow
```

> `tkinter` is built into Python on Windows — no extra install needed.

---

## Project Structure

```
ContestTracker/
├── contest_widget.py     ← the entire widget (single file)
├── install_command.py    ← one-time setup for the 'contests' command
├── README.md             ← this file
└── README.docx           ← formatted version of this README
```

---

## Installation

### Step 1 — Install dependencies

```bash
pip install pywin32 pystray pillow
```

### Step 2 — Run the widget

```bash
python contest_widget.py
```

The widget appears in the **bottom-right corner**, embedded behind your desktop icons, with a `◈` tray icon in the taskbar.

### Step 3 — Set up the `contests` command *(optional but recommended)*

```bash
python install_command.py
```

Open a **new terminal** and just type:

```bash
contests
```

The widget launches instantly. Works in CMD, PowerShell, and Windows Terminal.

To remove the command later:

```bash
python install_command.py --uninstall
```

---

## Auto-Start on Every Boot

### Method 1 — In-App Toggle ✅ Recommended

1. Find the **⏻ button** in the widget header
2. Click it — it turns **green** and shows `✓ Added to startup`
3. The widget now launches silently on every boot via `pythonw.exe` (no console window)
4. Click **⏻** again anytime to remove it

> Writes to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` in the registry.

### Method 2 — Startup Folder *(manual fallback)*

**Step 1:** Create `start_tracker.bat`:

```bat
@echo off
start "" pythonw "C:\full\path\to\contest_widget.py"
```

**Step 2:** Press `Win + R`, type `shell:startup`, hit Enter.

**Step 3:** Drop `start_tracker.bat` into that folder. Done.

---

## System Tray

After launching, a `◈` icon appears in your system tray (bottom-right near the clock).

> If you don't see it, click the **^** arrow in the taskbar to find hidden tray icons, then drag the `◈` icon out to always show it.

| Action | Result |
|--------|--------|
| Left-click tray icon | Show / Hide the widget |
| Right-click → Show / Hide | Toggle visibility |
| Right-click → Refresh | Fetch latest contests |
| Right-click → Exit | Close the widget completely |
| **▼** button in header | Hide widget to tray |

---

## Widget Controls

### Header Buttons

| Button | Action |
|--------|--------|
| `⟳` | Manually refresh contest data |
| `⏻` | Toggle auto-launch on boot (green = on) |
| `▼` | Hide to system tray |
| `─` | Collapse / expand the contest list |
| `×` | Exit the widget completely |

### Scrolling

| Method | Action |
|--------|--------|
| **▲ / ▼** buttons | Scroll 3 cards at a time |
| Mouse wheel | Scroll naturally while hovering |
| **⤒ top** button | Jump to the top instantly |

### Opening a Contest

Click **anywhere on a contest card** — the name, badge, date, or countdown — to open the contest page in your browser.

---

## How Desktop Embedding Works

Uses a Windows trick to sit *behind* your desktop icons (same method as Rainmeter):

1. Sends message `0x052C` to `Progman` → Windows spawns a hidden `WorkerW` layer
2. Calls `SetParent()` to move the widget window into that `WorkerW` layer
3. Widget appears above wallpaper but **below** desktop icons and all apps

> **No pywin32?** Falls back to a regular draggable window — everything else still works.

---

## Troubleshooting

**Widget won't start**
```bash
python contest_widget.py   # run from terminal to see the full error
python --version           # confirm Python 3.8+
pip install pywin32 pystray pillow
```

**Tray icon not showing**
- Click the `^` arrow near the clock — it may be hidden in the overflow tray
- Drag the `◈` icon out to pin it to the visible area
- Check for a `tray_error.log` file next to `contest_widget.py` — it logs tray startup errors

**No contests showing**
- Check your internet connection
- Click `⟳` to manually refresh
- APIs may rate-limit — wait a minute and retry

**`contests` command not found**
- Open a **new** terminal — existing ones won't pick up PATH changes
- Run `python install_command.py` again to verify the install

**Widget appears on top of other windows**
- Desktop embedding failed — try running as Administrator
- Some custom Windows shells don't support the WorkerW trick

**Auto-startup not working**
- Use Method 2 (Startup Folder) as a reliable fallback
- Check: `Win+R` → `regedit` → `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

---

## APIs Used

| Platform | Endpoint | Auth |
|----------|----------|------|
| Codeforces | `codeforces.com/api/contest.list` | None |
| LeetCode | `leetcode.com/graphql` — `allContests` | None |
| AtCoder | `kenkoooo.com/atcoder/resources/contests.json` | None |

All APIs are free and public — no API keys required.

---

## License

MIT — free to use, modify, and share.

---

*Happy coding & good luck in your contests! 🚀*