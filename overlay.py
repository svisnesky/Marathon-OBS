"""Transient on-screen callout (e.g. "HEADSHOT") that flashes over the game.

Launched as its own process by main.py so it never blocks the capture loop:
    pythonw overlay.py "HEADSHOT" 1400 "#ff2b25"

On Windows it makes itself click-through and non-activating (WS_EX_TRANSPARENT |
WS_EX_NOACTIVATE) so it can NEVER steal focus or eat a click mid-fight. Needs
the game in borderless windowed (same as the screen-capture method).
"""

import sys
import tkinter as tk

TRANSPARENT = "#010203"  # a color unlikely to appear in the text; made see-through


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "HEADSHOT"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 1400
    color = sys.argv[3] if len(sys.argv) > 3 else "#ff2b25"

    root = tk.Tk()
    root.overrideredirect(True)          # no title bar / borders
    root.attributes("-topmost", True)
    root.config(bg=TRANSPARENT)
    try:
        root.attributes("-transparentcolor", TRANSPARENT)  # background becomes invisible
    except tk.TclError:
        pass

    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 900, 220
    x = (sw - w) // 2
    y = int(sh * 0.20)                    # upper-center, above the kill-feed popups
    root.geometry(f"{w}x{h}+{x}+{y}")

    canvas = tk.Canvas(root, width=w, height=h, bg=TRANSPARENT, highlightthickness=0)
    canvas.pack()

    cx, cy = w // 2, h // 2
    # "Impact" ships with Windows and gives a bold, punchy look.
    font = ("Impact", 84)

    # black outline: draw the text offset in every direction, then red on top
    for dx in (-3, -2, 0, 2, 3):
        for dy in (-3, -2, 0, 2, 3):
            if dx or dy:
                canvas.create_text(cx + dx, cy + dy, text=label, fill="black", font=font)
    canvas.create_text(cx, cy, text=label, fill=color, font=font)
    # a thin accent underline
    canvas.create_rectangle(cx - 150, cy + 62, cx + 150, cy + 68, fill=color, outline="")

    # Make the window click-through + non-activating on Windows.
    root.update_idletasks()
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_NOACTIVATE = 0x08000000
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    except Exception:
        pass  # non-Windows or API hiccup: still shows, just not click-through

    root.after(duration, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
