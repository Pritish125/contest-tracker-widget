"""
install_command.py
Registers 'contests' as a global command so you can type it in any terminal.

Run ONCE (as Administrator for best results):
    python install_command.py

To uninstall:
    python install_command.py --uninstall
"""

import os, sys, winreg, shutil, textwrap

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
WIDGET_PATH = os.path.join(SCRIPT_DIR, "main.py")
PYTHONW     = sys.executable.replace("python.exe", "pythonw.exe")

# We'll drop a small .bat launcher into a folder that's already on PATH,
# or create one and add it to the user PATH ourselves.
INSTALL_DIR = os.path.join(os.environ.get("APPDATA", SCRIPT_DIR), "ContestTracker")
BAT_PATH    = os.path.join(INSTALL_DIR, "contests.bat")

BAT_CONTENT = textwrap.dedent(f"""\
    @echo off
    start "" "{PYTHONW}" "{WIDGET_PATH}"
""")

def add_to_user_path(directory):
    """Append directory to the user PATH in the registry (no admin needed)."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment",
            0, winreg.KEY_READ | winreg.KEY_SET_VALUE
        )
        try:
            current, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            current = ""

        paths = [p for p in current.split(";") if p.strip()]
        if directory not in paths:
            paths.append(directory)
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, ";".join(paths))
            print(f"  ✓ Added to user PATH: {directory}")
        else:
            print(f"  ✓ Already in PATH: {directory}")

        winreg.CloseKey(key)

        # Broadcast WM_SETTINGCHANGE so terminals pick up the new PATH
        import ctypes
        HWND_BROADCAST   = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 2, 5000,
            ctypes.byref(ctypes.c_ulong()))
        return True
    except Exception as e:
        print(f"  ✗ Failed to update PATH: {e}")
        return False

def remove_from_user_path(directory):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment",
            0, winreg.KEY_READ | winreg.KEY_SET_VALUE
        )
        current, _ = winreg.QueryValueEx(key, "PATH")
        paths = [p for p in current.split(";") if p.strip() and p != directory]
        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, ";".join(paths))
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def install():
    print("\n◈  Contest Tracker — Command Installer")
    print("─" * 42)

    # 1. Verify widget exists
    if not os.path.exists(WIDGET_PATH):
        print(f"\n✗ Could not find contest_widget.py at:\n  {WIDGET_PATH}")
        print("  Make sure install_command.py is in the same folder as contest_widget.py")
        return False

    # 2. Create install dir
    os.makedirs(INSTALL_DIR, exist_ok=True)
    print(f"\n  Install directory: {INSTALL_DIR}")

    # 3. Write the .bat launcher
    with open(BAT_PATH, "w") as f:
        f.write(BAT_CONTENT)
    print(f"  ✓ Created launcher: {BAT_PATH}")

    # 4. Add to user PATH
    add_to_user_path(INSTALL_DIR)

    print("\n✅ Done! Open a NEW terminal and type:\n")
    print("     contests\n")
    print("  (existing terminals need to be restarted to pick up PATH changes)")
    print("─" * 42 + "\n")
    return True

def uninstall():
    print("\n◈  Contest Tracker — Uninstall Command")
    print("─" * 42)

    removed = False
    if os.path.exists(BAT_PATH):
        os.remove(BAT_PATH)
        print(f"  ✓ Removed launcher: {BAT_PATH}")
        removed = True

    if os.path.exists(INSTALL_DIR) and not os.listdir(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR, ignore_errors=True)
        print(f"  ✓ Removed directory: {INSTALL_DIR}")

    if remove_from_user_path(INSTALL_DIR):
        print(f"  ✓ Removed from PATH")

    if removed:
        print("\n✅ 'contests' command removed.\n")
    else:
        print("\n  Nothing to uninstall.\n")
    print("─" * 42 + "\n")

if __name__ == "__main__":
    if "--uninstall" in sys.argv:
        uninstall()
    else:
        install()
    input("Press Enter to close...")