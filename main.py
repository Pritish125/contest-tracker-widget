"""
DSA Contest Tracker — Desktop Embedded Widget
Sits behind desktop icons using the Win32 WorkerW trick.

Requirements:  pip install pywin32
Run:           python contest_widget.py
"""

import tkinter as tk
from tkinter import font as tkfont
import threading, time, urllib.request, json, datetime, webbrowser, ctypes, sys, os

# ── Auto-startup (Windows Registry) ──────────────────────────────────────────

def register_startup():
    """Add this script to HKCU Run so it starts with Windows."""
    try:
        import winreg
        key  = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_SET_VALUE)
        # Use pythonw.exe so no console window appears on startup
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        script  = os.path.abspath(__file__)
        winreg.SetValueEx(key, "ContestTracker", 0, winreg.REG_SZ,
                          f'"{pythonw}" "{script}"')
        winreg.CloseKey(key)
        return True
    except Exception as ex:
        print("Startup registration failed:", ex)
        return False

def is_registered_startup():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "ContestTracker")
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def remove_startup():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "ContestTracker")
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

# ── Win32 desktop embedding ───────────────────────────────────────────────────

try:
    user32 = ctypes.windll.user32
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def _embed_behind_desktop(hwnd):
        progman = user32.FindWindowW("Progman", None)
        user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000,
                                   ctypes.byref(ctypes.c_ulong()))
        workerw = ctypes.c_void_p(0)

        def _cb(h, _):
            nonlocal workerw
            if user32.FindWindowExW(h, None, "SHELLDLL_DefView", None):
                workerw.value = user32.FindWindowExW(None, h, "WorkerW", None)
            return True

        user32.EnumWindows(EnumWindowsProc(_cb), 0)
        if workerw.value:
            user32.SetParent(hwnd, workerw.value)
            return True
        return False

    WIN32_OK = True
except Exception:
    WIN32_OK = False

# ── API helpers ───────────────────────────────────────────────────────────────

def fetch_url(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

def get_codeforces():
    data = fetch_url("https://codeforces.com/api/contest.list?gym=false")
    out, now = [], time.time()
    if not data or data.get("status") != "OK":
        return out
    for c in data["result"]:
        phase = c.get("phase","")
        start = c.get("startTimeSeconds", 0)
        end   = start + c.get("durationSeconds", 0)
        url   = f"https://codeforces.com/contest/{c['id']}"
        if phase == "CODING":
            out.append({"platform":"CF","name":c["name"],"status":"LIVE","start":start,"end":end,"url":url})
        elif phase == "BEFORE" and start > now:
            out.append({"platform":"CF","name":c["name"],"status":"UPCOMING","start":start,"end":end,"url":url})
    return out

def get_atcoder():
    data = fetch_url("https://kenkoooo.com/atcoder/resources/contests.json")
    out, now = [], time.time()
    if not data: return out
    for c in data:
        try:
            s = c.get("start_epoch_second", 0)
            e = s + c.get("duration_second", 0)
            u = f"https://atcoder.jp/contests/{c['id']}"
            if s <= now <= e:
                out.append({"platform":"AC","name":c["title"],"status":"LIVE","start":s,"end":e,"url":u})
            elif s > now:
                out.append({"platform":"AC","name":c["title"],"status":"UPCOMING","start":s,"end":e,"url":u})
        except Exception:
            pass
    return out

def get_leetcode():
    q = json.dumps({"query":"{ allContests { title titleSlug startTime duration } }"}).encode()
    try:
        req = urllib.request.Request("https://leetcode.com/graphql", data=q,
            headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return []
    out, now = [], time.time()
    for c in data.get("data",{}).get("allContests",[]):
        s = c.get("startTime", 0)
        e = s + c.get("duration", 0) * 60
        u = f"https://leetcode.com/contest/{c['titleSlug']}"
        if s <= now <= e:
            out.append({"platform":"LC","name":c["title"],"status":"LIVE","start":s,"end":e,"url":u})
        elif s > now:
            out.append({"platform":"LC","name":c["title"],"status":"UPCOMING","start":s,"end":e,"url":u})
    return out

def fmt_cd(ts):
    d = int(ts - time.time())
    if d <= 0: return "NOW"
    h, r = divmod(d, 3600)
    m, s = divmod(r, 60)
    if h >= 24:
        return f"{h//24}d {h%24:02d}h"
    return f"{h:02d}h {m:02d}m" if h > 0 else f"{m:02d}m {s:02d}s"

def fmt_dt(ts):
    """Readable date: Mon, Mar 17  09:30"""
    return datetime.datetime.fromtimestamp(ts).strftime("%a, %b %d  %H:%M")

# ── Theme ─────────────────────────────────────────────────────────────────────

PC       = {"CF":"#FF5555","LC":"#FFA116","AC":"#4D9FFF"}
BG       = "#0D0F14"
SURFACE  = "#151820"
BORDER   = "#252A38"
TEXT     = "#DDE3F0"
DIM      = "#6B7590"
LIVE_CLR = "#00FFB2"
LIVE_BG  = "#002B1E"
ACCENT   = "#7B61FF"
WARN     = "#FFD166"

# ── Widget ────────────────────────────────────────────────────────────────────

class ContestWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Contest Tracker")
        self.root.overrideredirect(True)
        self.root.configure(bg=BG)
        self.root.attributes("-alpha", 0.95)

        self.contests   = []
        self._collapsed = False
        self._dx = self._dy = 0

        # Fonts — larger and clearer
        self.f_name   = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.f_meta   = tkfont.Font(family="Segoe UI", size=9)
        self.f_cd     = tkfont.Font(family="Consolas", size=10, weight="bold")
        self.f_badge  = tkfont.Font(family="Segoe UI",  size=8, weight="bold")
        self.f_hdr    = tkfont.Font(family="Segoe UI",  size=10, weight="bold")
        self.f_status = tkfont.Font(family="Segoe UI",  size=8)
        self.f_sec    = tkfont.Font(family="Segoe UI",  size=8, weight="bold")

        self._build_ui()

        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"320x600+{sw-340}+{sh-640}")

        self.root.after(300, self._try_embed)
        self._refresh_data()
        self.root.mainloop()

    # ── Embed ─────────────────────────────────────────────────────────────────
    def _try_embed(self):
        if not WIN32_OK:
            self.root.attributes("-topmost", True)
            self._enable_drag()
            self._set_status("pywin32 missing — floating mode")
            return
        hwnd = ctypes.windll.user32.FindWindowW(None, "Contest Tracker") or self.root.winfo_id()
        if _embed_behind_desktop(hwnd):
            self.root.attributes("-topmost", False)
            self._set_status("✓ Embedded in desktop")
        else:
            self.root.attributes("-topmost", True)
            self._enable_drag()
            self._set_status("Embed failed — floating mode")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=BG)
        inner.pack(fill="both", expand=True)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(inner, bg=SURFACE, height=36)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        self._hdr = hdr

        dot_f = tk.Frame(hdr, bg=SURFACE)
        dot_f.pack(side="left", padx=10)
        for clr in (PC["CF"], PC["LC"], PC["AC"]):
            cv = tk.Canvas(dot_f, width=9, height=9, bg=SURFACE, highlightthickness=0)
            cv.create_oval(1, 1, 8, 8, fill=clr, outline="")
            cv.pack(side="left", padx=2)

        tk.Label(hdr, text="◈  CONTEST TRACKER", font=self.f_hdr,
                 fg=TEXT, bg=SURFACE).pack(side="left", padx=6)

        bk = dict(font=self.f_badge, bg=SURFACE, bd=0, cursor="hand2",
                  activebackground=BORDER, padx=5, pady=3)
        tk.Button(hdr, text="×", fg="#FF5F5F", command=self.root.destroy, **bk).pack(side="right", padx=3)
        tk.Button(hdr, text="─", fg=DIM,       command=self._toggle_collapse, **bk).pack(side="right")

        # Startup toggle button
        self._startup_on = is_registered_startup()
        self._sb_text = tk.StringVar(value="⏻" if self._startup_on else "⏻")
        self._sbtn = tk.Button(hdr, textvariable=self._sb_text,
                               fg=LIVE_CLR if self._startup_on else DIM,
                               command=self._toggle_startup, **bk)
        self._sbtn.pack(side="right")

        self.rbtn = tk.Button(hdr, text="⟳", fg=ACCENT, command=self._manual_refresh, **bk)
        self.rbtn.pack(side="right")

        # ── Body frame (collapsible) ──────────────────────────────────────────
        self._body_frame = tk.Frame(inner, bg=BG)
        self._body_frame.pack(fill="both", expand=True)
        body = self._body_frame

        # ── Status bar ────────────────────────────────────────────────────────
        self.svar = tk.StringVar(value="Fetching contests…")
        tk.Label(body, textvariable=self.svar, font=self.f_status,
                 fg=DIM, bg=BG, pady=3, anchor="w").pack(fill="x", padx=10)

        # ── Separator ─────────────────────────────────────────────────────────
        tk.Canvas(body, height=1, bg=BORDER, highlightthickness=0).pack(fill="x")

        # ── Scroll arrow buttons ───────────────────────────────────────────────
        nav = tk.Frame(body, bg=SURFACE, height=26)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        abk = dict(font=tkfont.Font(family="Segoe UI", size=10, weight="bold"),
                   bg=SURFACE, fg=DIM, bd=0, cursor="hand2",
                   activebackground=BORDER, activeforeground=TEXT, padx=10, pady=1)
        tk.Button(nav, text="▲", command=lambda: self._scroll(-3), **abk).pack(side="left", padx=(6,1))
        tk.Button(nav, text="▼", command=lambda: self._scroll( 3), **abk).pack(side="left", padx=(1,6))
        tk.Label(nav, text="scroll", font=tkfont.Font(family="Segoe UI", size=7),
                 fg=DIM, bg=SURFACE).pack(side="left")
        tk.Button(nav, text="⤒ top",
                  font=tkfont.Font(family="Segoe UI", size=8),
                  bg=SURFACE, fg=DIM, bd=0, cursor="hand2",
                  activebackground=BORDER, activeforeground=TEXT,
                  command=lambda: self._canvas.yview_moveto(0)).pack(side="right", padx=6)

        # ── Scrollable canvas ─────────────────────────────────────────────────
        wrap = tk.Frame(body, bg=BG)
        wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0, bd=0)
        self._canvas.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(wrap, orient="vertical", command=self._canvas.yview,
                          width=5, troughcolor=BG, bg=BORDER,
                          activebackground=ACCENT, relief="flat", bd=0)
        sb.pack(side="right", fill="y")
        self._canvas.configure(yscrollcommand=sb.set)

        self.lf = tk.Frame(self._canvas, bg=BG)
        self._win_id = self._canvas.create_window((0, 0), window=self.lf, anchor="nw")

        def _on_canvas_resize(e):
            self._canvas.itemconfig(self._win_id, width=e.width)
        self._canvas.bind("<Configure>", _on_canvas_resize)

        def _on_frame_resize(e):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self.lf.bind("<Configure>", _on_frame_resize)

        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-e.delta / 60), "units"))

    def _set_status(self, msg):
        self.svar.set(msg)

    # ── Startup toggle ────────────────────────────────────────────────────────
    def _toggle_startup(self):
        if self._startup_on:
            ok = remove_startup()
            self._startup_on = False
            self._sbtn.config(fg=DIM)
            self._set_status("Removed from startup" if ok else "Failed to remove startup")
        else:
            ok = register_startup()
            self._startup_on = True
            self._sbtn.config(fg=LIVE_CLR)
            self._set_status("✓ Added to startup" if ok else "Failed to add startup")

    # ── Drag (floating fallback only) ─────────────────────────────────────────
    def _enable_drag(self):
        self._hdr.bind("<ButtonPress-1>", lambda e: self._ds(e))
        self._hdr.bind("<B1-Motion>",     lambda e: self._dm(e))

    def _ds(self, e): self._dx, self._dy = e.x_root, e.y_root
    def _dm(self, e):
        x = self.root.winfo_x() + e.x_root - self._dx
        y = self.root.winfo_y() + e.y_root - self._dy
        self.root.geometry(f"+{x}+{y}")
        self._dx, self._dy = e.x_root, e.y_root

    def _scroll(self, units):
        self._canvas.yview_scroll(units, "units")

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        if self._collapsed:
            self._body_frame.pack_forget()
        else:
            self._body_frame.pack(fill="both", expand=True)

    # ── Data ──────────────────────────────────────────────────────────────────
    def _manual_refresh(self):
        self.rbtn.config(fg=DIM)
        self._refresh_data()

    def _refresh_data(self):
        def work():
            all_c = get_codeforces() + get_leetcode() + get_atcoder()
            all_c.sort(key=lambda x: (0 if x["status"]=="LIVE" else 1, x["start"]))
            live = [c for c in all_c if c["status"]=="LIVE"]
            up   = [c for c in all_c if c["status"]=="UPCOMING"][:20]
            self.contests = live + up
            self.root.after(0, self._render)
        threading.Thread(target=work, daemon=True).start()
        self.root.after(300_000, self._refresh_data)
        self._tick()

    def _tick(self):
        self._update_cd()
        self.root.after(1000, self._tick)

    # ── Render ────────────────────────────────────────────────────────────────
    def _render(self):
        for w in self.lf.winfo_children():
            w.destroy()
        if not self.contests:
            tk.Label(self.lf, text="No contests found  ¯\\_(ツ)_/¯",
                     font=self.f_meta, fg=DIM, bg=BG).pack(pady=30)
            self.svar.set("Updated " + datetime.datetime.now().strftime("%H:%M:%S"))
            return

        live = [c for c in self.contests if c["status"]=="LIVE"]
        up   = [c for c in self.contests if c["status"]=="UPCOMING"]
        if live:
            self._sec("● LIVE NOW")
            for c in live: self._row(c)
        if up:
            self._sec("◎ UPCOMING")
            for c in up: self._row(c)

        self.svar.set("↻ " + datetime.datetime.now().strftime("%H:%M:%S"))
        self.rbtn.config(fg=ACCENT)

    def _sec(self, txt):
        f = tk.Frame(self.lf, bg=BG)
        f.pack(fill="x", pady=(8, 3))
        clr = LIVE_CLR if "LIVE" in txt else ACCENT
        tk.Label(f, text=txt, font=self.f_sec, fg=clr, bg=BG).pack(side="left")
        tk.Canvas(f, height=1, bg=BORDER, highlightthickness=0).pack(
            side="left", fill="x", expand=True, padx=8, pady=6)

    def _row(self, c):
        live = c["status"] == "LIVE"
        rb   = LIVE_BG if live else SURFACE

        # Outer card
        card = tk.Frame(self.lf, bg=rb, pady=8, padx=0, cursor="hand2")
        card.pack(fill="x", pady=3)

        # Left accent stripe
        tk.Frame(card, width=4, bg=PC[c["platform"]]).pack(side="left", fill="y")

        body = tk.Frame(card, bg=rb)
        body.pack(side="left", fill="both", expand=True, padx=10)

        # ── Row 1: badge + contest name ───────────────────────────────────────
        top = tk.Frame(body, bg=rb)
        top.pack(fill="x")

        tk.Label(top, text=f" {c['platform']} ", font=self.f_badge,
                 fg="white", bg=PC[c["platform"]], padx=2).pack(side="left", padx=(0,8))

        nm = c["name"][:28] + "…" if len(c["name"]) > 30 else c["name"]
        tk.Label(top, text=nm, font=self.f_name,
                 fg=LIVE_CLR if live else TEXT, bg=rb,
                 anchor="w").pack(side="left", fill="x", expand=True)

        # ── Row 2: date ───────────────────────────────────────────────────────
        tk.Label(body, text=fmt_dt(c["start"]), font=self.f_meta,
                 fg=WARN if live else DIM, bg=rb, anchor="w").pack(fill="x", pady=(3, 0))

        # ── Row 3: countdown ──────────────────────────────────────────────────
        cd_row = tk.Frame(body, bg=rb)
        cd_row.pack(fill="x", pady=(2, 0))

        lbl_txt = "⏱ ends in" if live else "⏳ starts in"
        ts      = c["end"] if live else c["start"]
        clr     = LIVE_CLR if live else ACCENT

        tk.Label(cd_row, text=lbl_txt, font=self.f_meta, fg=DIM, bg=rb).pack(side="left")
        cd = tk.Label(cd_row, text=f"  {fmt_cd(ts)}", font=self.f_cd, fg=clr, bg=rb)
        cd.pack(side="left")
        cd._c    = c
        cd._live = live

        def bind(w, url):
            w.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            for ch in w.winfo_children(): bind(ch, url)
        bind(card, c["url"])

    def _update_cd(self):
        def walk(w):
            if isinstance(w, tk.Label) and hasattr(w, "_c"):
                ts = w._c["end"] if w._live else w._c["start"]
                w.config(text=f"  {fmt_cd(ts)}")
            for ch in w.winfo_children(): walk(ch)
        walk(self.lf)


if __name__ == "__main__":
    ContestWidget()