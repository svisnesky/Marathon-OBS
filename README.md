# Marathon Auto Kill Recorder

Automatically saves a video clip and bumps an on-screen counter every time you
get a kill (or assist) in **Marathon**.

Marathon has no public kill API, so this tool *watches your screen*. By default
it watches the center-screen personal confirmation popup that appears only when
you get a down — **"RUNNER DOWN  +XX XP"** — OCRs that region, and when the
popup appears it (1) tells **OBS** to save its **Replay Buffer** as a clip and
(2) updates a **Text source** counter in OBS.

```
popup region  ->  OCR  ->  detector (phrase seen? edge-trigger)  ->  OBS save replay + counter
```

Watching *your own* "RUNNER DOWN +XP" popup is more reliable than reading the
kill feed: it fires only for your downs, so there's no name-matching to get
wrong. (A `killfeed` fallback mode that parses `<killer> <verb> <victim>` and
matches your name is still available — see `detection_mode` in config.)

## Anti-cheat note

This tool never touches the game: it does **not** read game memory, inject code,
hook APIs, or send any input. It only reads the *picture* (your screen or OBS's
output) and controls OBS — the same category as OBS, ShadowPlay, or Medal.tv,
which give no gameplay advantage. That is not what anti-cheat targets.

To minimize even theoretical exposure, the default `capture_source` is
**`obs_virtualcam`**: OBS captures the game (universally tolerated) and this tool
only reads OBS's **Virtual Camera** (a webcam device). Set `capture_source: screen`
if you'd rather grab the monitor directly. For provably zero risk, run everything
on a **second PC** fed by a capture card so nothing runs on the game machine.

No guarantees are made about Bungie's policies — use at your own discretion.

## Requirements

- Windows PC with an **NVIDIA GPU** (the game machine — this must run there).
- **OBS 28+** (ships with obs-websocket v5).
- **Python 3.9+** on the same PC.

## 1. One-time OBS setup

1. **WebSocket:** OBS → *Tools → WebSocket Server Settings* → enable it. Note the
   **Port** (default 4455) and set/copy the **Password**.
2. **Replay Buffer:** OBS → *Settings → Output → Replay Buffer* → enable, set
   *Maximum Replay Time* to ~30s. (The tool will start the buffer for you on launch.)
   Make sure a *Recording Path* is set so clips have somewhere to land.
3. **Counter text source:** in your Scene, add *Source → Text (GDI+)*, name it
   exactly **`KillCounter`**. Position/size/font it however you like.
4. **Virtual Camera** (if using the default `capture_source: obs_virtualcam`):
   click **Start Virtual Camera** in OBS's Controls dock. Skip if you set
   `capture_source: screen`.

## 2. Install

```bat
git clone <your-repo-url> marathon-kill-recorder
cd marathon-kill-recorder
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> EasyOCR pulls in PyTorch (large). If you'd rather stay light, set
> `ocr_engine: tesseract` in `config.yaml` and install the Tesseract binary
> (https://github.com/UB-Mannheim/tesseract/wiki).

## 3. Configure

Edit `config.yaml` (defaults are set for **popup mode**):

- `obs.password` — the OBS websocket password from step 1.
- `popup_trigger_phrases` — leave `["RUNNER DOWN"]`; add the exact wording for
  kills/assists once you see them (e.g. `ELIMINATED`, `ASSIST`).
- `require_xp_reward` — set `true` if non-combat popups cause false triggers.

(Only needed for the `killfeed` fallback mode: `player_name`, `name_aliases`,
`trigger_keywords`, `match_mode`.)

## 4. Calibrate the detection region

With Marathon (or a screenshot) on screen showing the relevant area — in popup
mode, the center **"RUNNER DOWN +XP"** popup zone:

```bat
python calibrate.py
```

Drag a box around it, press **ENTER**. This writes `detect_region` into
`config.yaml`. Re-run if you change resolution or HUD scale.

## 5. Test before going live

**Detection logic only** (no OCR, no OBS) — each argument is one frame:

```bat
python main.py --test-lines "RUNNER DOWN  +15 XP" "SOUTH RELAY"
```

**OCR on a saved screenshot** (grab one at the moment the popup shows):

```bat
python main.py --test-image path\to\shot.png
```

It prints the OCR'd text from your region and whether a kill was detected. Tune
`ocr_upscale`, `popup_match_threshold`, and `popup_trigger_phrases` until it's
reliable.

**Full pipeline, but OBS actions only logged** (safe live rehearsal):

```bat
python main.py --dry-run
```

Play a bit; watch the console print `KILL #n` on your kills.

## 6. Go live

```bat
python main.py
```

On each detected kill it saves an OBS replay clip, updates the `KillCounter`
source, and appends a row to `session_log.csv`.

## Files

| file | role |
|------|------|
| `config.yaml` | all settings (mode, phrases, region, OBS, timing) |
| `calibrate.py` | drag-select the detection region |
| `capture.py` | OBS Virtual Camera / mss region grab |
| `ocr.py` | preprocess + OCR (EasyOCR / Tesseract) |
| `detector.py` | `PopupDetector` (default) + `KillDetector` (fallback) — the core logic |
| `obs_client.py` | obs-websocket: save replay + update counter |
| `main.py` | wires it together; test/dry-run modes |
| `tests/` | unit tests for the detectors (`python tests/test_detector.py`) |

## Tuning / troubleshooting

- **Missing kills:** raise `ocr_upscale`, lower `popup_match_threshold`, re-calibrate
  a tighter `detect_region`, or add the exact popup wording to `popup_trigger_phrases`.
- **False positives:** raise `popup_match_threshold`, set `require_xp_reward: true`,
  or increase `popup_absence_frames`.
- **Rapid multi-kills counted as one:** the popup didn't fully disappear between
  them; lower `popup_absence_frames` and/or raise `poll_fps`.
- **No clips saved:** confirm Replay Buffer is enabled and a recording path is set;
  check the OBS websocket password/port.
- **OCR slow:** EasyOCR's first call loads models (slow once). Ensure GPU is used;
  or switch to `tesseract`.

## Known limits

- Detection depends on the popup being visible and readable in the captured frame.
- Back-to-back downs where the popup never fully clears may count as one.
- Exact wording for kills vs assists vs finishes may differ — add those phrases
  to `popup_trigger_phrases` once you observe them.
