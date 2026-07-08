"""One-time calibration: drag-select the detection rectangle on a live frame.

Run on the gaming PC with the relevant thing on screen:

    python calibrate.py

In popup mode: box the center "RUNNER DOWN +XP" popup area.
In killfeed mode: box the kill feed.

The pixel rectangle is written into config.yaml under `detect_region`,
preserving all comments and other settings.
"""

from __future__ import annotations

import re
import sys

import cv2
import yaml

from capture import grab_full_screenshot, grab_full_virtualcam

CONFIG_PATH = "config.yaml"


def main():
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    source = cfg.get("capture_source", "obs_virtualcam")
    mode = cfg.get("detection_mode", "popup")
    target = ("the center RUNNER DOWN / +XP popup area" if mode == "popup"
              else "the kill feed")

    if source == "screen":
        print("Grabbing a screenshot of your primary monitor...")
        shot = grab_full_screenshot(monitor_index=cfg.get("monitor_index", 1))
    else:
        print("Grabbing a frame from the OBS Virtual Camera "
              "(make sure it's started in OBS)...")
        shot = grab_full_virtualcam(cam_index=cfg.get("obs_virtualcam_index", 0))
    h, w = shot.shape[:2]
    print(f"Frame is {w}x{h}. Drag a box around {target}, then press ENTER.")

    win = f"Select region ({mode} mode) — drag a box, then ENTER (c = cancel)"
    x, y, bw, bh = cv2.selectROI(win, shot, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()

    if bw == 0 or bh == 0:
        print("No region selected — aborted. Nothing changed.")
        sys.exit(1)

    region = {"x": int(x), "y": int(y), "w": int(bw), "h": int(bh)}
    print(f"Selected detect_region: {region}")

    # Replace just the detect_region block in-place so config comments survive.
    with open(CONFIG_PATH) as f:
        text = f.read()
    new_block = (
        "detect_region:\n"
        f"  x: {region['x']}\n"
        f"  y: {region['y']}\n"
        f"  w: {region['w']}\n"
        f"  h: {region['h']}\n"
    )
    pattern = re.compile(r"detect_region:\n(?:[ \t]+\w+:.*\n?)+")
    if pattern.search(text):
        text = pattern.sub(new_block, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + new_block
    with open(CONFIG_PATH, "w") as f:
        f.write(text)
    print(f"Wrote detect_region into {CONFIG_PATH}. You're calibrated.")


if __name__ == "__main__":
    main()
