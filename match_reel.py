"""Per-match highlight reel — built automatically when the EXFILTRATED screen
appears, from the clips saved during that match.

ESPN-style: a stat title card (kills, elims, damage, run time) fades in, then
the match's clips play back-to-back. Output is an iPad-friendly mp4
(h264+aac+faststart) in <session>/reels/, which the web dashboard pops up so
the match can be rewatched from the couch seconds after exfil.
"""

from __future__ import annotations

import os
import subprocess

from matchcard import _font, _text_w, BG, LINE, TEXT, MUTED, ACCENT

CARD_SECONDS = 2.8


def _build_title_card(out_png: str, title: str, kills: int, sub_lines: list[str],
                      wordmark_path: str = "") -> bool:
    """1920x1080 stat card in the match-card style."""
    try:
        from PIL import Image, ImageDraw

        W, H = 1920, 1080
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        pad = 110

        d.rectangle([0, 0, W, 10], fill=ACCENT)
        d.rectangle([0, H - 10, W, H], fill=ACCENT)

        y = pad
        if wordmark_path and os.path.exists(wordmark_path):
            try:
                wm = Image.open(wordmark_path).convert("RGBA")
                scale = 64 / wm.height
                wm = wm.resize((int(wm.width * scale), 64), Image.LANCZOS)
                img.paste(wm, (pad, y), wm)
            except Exception:
                d.text((pad, y), "MARATHON", font=_font("black", 56), fill=ACCENT)
        else:
            d.text((pad, y), "MARATHON", font=_font("black", 56), fill=ACCENT)

        d.text((pad, y + 110), title, font=_font("black", 110), fill=TEXT)

        kf = _font("black", 380)
        ks = str(kills)
        d.text((pad - 10, 360), ks, font=kf, fill=ACCENT)
        d.text((pad + _text_w(d, ks, kf) + 40, 640), "KILLS",
               font=_font("bold", 64), fill=TEXT)

        ly = 880
        for line in sub_lines[:2]:
            d.text((pad, ly), line, font=_font("mono", 40), fill=MUTED)
            ly += 58

        d.line([pad, 840, W - pad, 840], fill=LINE, width=2)
        img.save(out_png)
        return True
    except Exception as e:
        print(f"  [reel] title card failed: {e}")
        return False


def build_match_reel(clip_paths: list[str], out_path: str, ffmpeg: str,
                     title: str, kills: int, sub_lines: list[str],
                     wordmark_path: str = "") -> bool:
    """Title card + this match's clips -> one mp4. Returns True on success."""
    clips = [c for c in clip_paths if os.path.exists(c)]
    if not clips:
        print("  [reel] no clips on disk to build a reel from")
        return False
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    card_png = os.path.splitext(out_path)[0] + "_card.png"
    have_card = _build_title_card(card_png, title, kills, sub_lines, wordmark_path)

    cmd = [ffmpeg, "-y"]
    filt = []
    n = 0

    if have_card:
        cmd += ["-loop", "1", "-framerate", "60", "-t", str(CARD_SECONDS), "-i", card_png,
                "-f", "lavfi", "-t", str(CARD_SECONDS), "-i", "anullsrc=r=48000:cl=stereo"]
        filt.append(f"[0:v]scale=1920:1080,setsar=1,format=yuv420p,"
                    f"fade=t=in:d=0.4,fade=t=out:st={CARD_SECONDS - 0.4}:d=0.4[v0];"
                    f"[1:a]anull[a0]")
        n = 1

    for i, c in enumerate(clips):
        cmd += ["-i", c]
        idx = i + (2 if have_card else 0)
        filt.append(f"[{idx}:v]scale=1920:1080,setsar=1,fps=60,format=yuv420p[v{n + i}];"
                    f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{n + i}]")

    total = n + len(clips)
    pairs = "".join(f"[v{i}][a{i}]" for i in range(total))
    filt.append(f"{pairs}concat=n={total}:v=1:a=1[v][a]")

    cmd += ["-filter_complex", ";".join(filt), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_path]

    r = subprocess.run(cmd, capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        os.remove(card_png)
    except OSError:
        pass
    if r.returncode == 0 and os.path.exists(out_path):
        return True
    tail = (r.stderr.strip().splitlines() or ["(no output)"])[-1]
    print(f"  [reel] ffmpeg failed: {tail}")
    return False
