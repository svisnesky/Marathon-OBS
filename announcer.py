"""Reel announcer voiceover — neural voice when possible, offline fallback.

Voice quality tiers, tried in order:
  1. edge-tts (Microsoft neural voices — sounds human; free, no API key;
     needs internet at reel-build time): pip install edge-tts
  2. Windows System.Speech via PowerShell (offline, robotic — the fallback)
  3. macOS `say` (development testing)

Pick the voice with announcer_voice in config.yaml (e.g. "en-US-GuyNeural",
"en-US-ChristopherNeural", "en-GB-RyanNeural"). List them all with:
  .venv\\Scripts\\python -m edge_tts --list-voices
"""

from __future__ import annotations

import os
import subprocess
import sys

DEFAULT_VOICE = "en-US-GuyNeural"


def synth_to_wav(text: str, out_wav: str, voice: str = DEFAULT_VOICE) -> str | None:
    """Render `text` to audio near out_wav. Returns the actual file written
    (mp3 for the neural voice, wav for fallbacks) or None."""
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)

    path = _edge_neural(text, os.path.splitext(out_wav)[0] + ".mp3", voice)
    if path:
        return path
    try:
        if sys.platform == "win32":
            return _win_sapi(text, out_wav)
        if sys.platform == "darwin":
            return _mac_say(text, out_wav)
    except Exception as e:
        print(f"  [announcer] tts failed: {e}")
    return None


def _edge_neural(text: str, out_mp3: str, voice: str) -> str | None:
    """Microsoft neural TTS via edge-tts. Quietly returns None when the
    package is missing or there's no internet — callers fall back."""
    try:
        import asyncio

        import edge_tts
    except ImportError:
        print("  [announcer] tip: for a human-sounding voice run "
              ".venv\\Scripts\\python -m pip install edge-tts")
        return None
    try:
        async def go():
            await edge_tts.Communicate(text, voice, rate="+8%").save(out_mp3)
        asyncio.run(asyncio.wait_for(go(), timeout=25))
        if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 1000:
            return out_mp3
    except Exception as e:
        print(f"  [announcer] neural voice unavailable ({type(e).__name__}) — "
              "using the offline voice")
    return None


def _win_sapi(text: str, out_wav: str) -> str | None:
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 1; "
        f"$s.SetOutputToWaveFile('{out_wav}'); "
        f"$s.Speak([Console]::In.ReadToEnd()); $s.Dispose()"
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        input=text, capture_output=True, text=True, timeout=60,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode == 0 and os.path.exists(out_wav):
        return out_wav
    print(f"  [announcer] powershell tts failed: {(r.stderr or '').strip()[:120]}")
    return None


def _mac_say(text: str, out_wav: str) -> str | None:
    aiff = out_wav + ".aiff"
    r = subprocess.run(["say", "-o", aiff, text], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    r2 = subprocess.run(["ffmpeg", "-y", "-i", aiff, "-ar", "48000", out_wav],
                        capture_output=True, text=True)
    try:
        os.remove(aiff)
    except OSError:
        pass
    return out_wav if r2.returncode == 0 and os.path.exists(out_wav) else None


def _spoken_number(n: int) -> str:
    """Numbers up to twelve read better as words."""
    words = ["zero", "one", "two", "three", "four", "five", "six", "seven",
             "eight", "nine", "ten", "eleven", "twelve"]
    return words[n] if 0 <= n < len(words) else str(n)


def stat_line(kills: int, stats: dict, potg_tag: str = "",
              player: str = "") -> str:
    """A short broadcast-style script, varied per match instead of a fixed
    monotone template. Keeps to ~2 sentences so it lands over the intro."""
    import random

    k = _spoken_number(kills)
    who = player or "our runner"

    if kills == 0:
        return random.choice([
            f"Quiet one on the kill feed, but {who} made it out. Roll the tape.",
            f"No kills this run, but an exfil is an exfil. Here's how it went.",
        ])

    openers = [
        f"Match highlights. {who} drops {k} kill{'s' if kills != 1 else ''}.",
        f"{k.capitalize()} kill{'s' if kills != 1 else ''} for {who} this run.",
        f"Highlights incoming. {k.capitalize()} kill{'s' if kills != 1 else ''} on the board.",
    ]
    parts = [random.choice(openers)]

    if potg_tag:
        tag = potg_tag.replace("+", " and ").replace("_", " ").lower()
        parts.append(random.choice([
            f"Play of the game: a {tag}.",
            f"The big one? A {tag}.",
        ]))
    elif stats.get("runner_damage"):
        parts.append(f"{stats['runner_damage']} runner damage dealt.")

    parts.append(random.choice([
        "Roll the tape.", "Watch this.", "To the footage.", "Enjoy.",
    ]))
    return " ".join(parts)
