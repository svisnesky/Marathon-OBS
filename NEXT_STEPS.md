# Next Steps — Getting the Kill Recorder Running

A follow-along setup guide for the **Windows gaming PC**. Do these in order.
Each step says what to run, what you should see, and what to do if it breaks.

There are two "test before live" checkpoints on purpose — detection accuracy
depends on how Marathon's kill feed actually looks, which we can only find out
on your machine. Don't skip them.

---

## Phase 0 — Get the code onto the PC

On the gaming PC, open **Command Prompt** (or PowerShell) and clone the repo:

```bat
cd %USERPROFILE%\Documents
git clone https://github.com/svisnesky/Marathon-OBS.git
cd Marathon-OBS
```

If you don't have git on the PC: install it from https://git-scm.com/download/win
(or just download the repo as a ZIP from GitHub and extract it).

**You should see:** a folder with `main.py`, `config.yaml`, `detector.py`, etc.

---

## Phase 1 — Install Python and dependencies

1. Install **Python 3.10+** from https://www.python.org/downloads/windows/
   During install, **check "Add python.exe to PATH."**

2. Verify:
   ```bat
   python --version
   ```
   Should print `Python 3.10.x` (or higher).

3. Create an isolated environment and install the libraries:
   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

**You should see:** `(.venv)` at the start of your prompt, and pip downloading
packages. **This step is large** — EasyOCR pulls in PyTorch (~2 GB). Let it finish.

**If it's too heavy / you want it lighter:** open `config.yaml`, set
`ocr_engine: tesseract`, then install the Tesseract binary from
https://github.com/UB-Mannheim/tesseract/wiki and re-run `pip install -r requirements.txt`.

> Every time you open a new terminal to use the tool, re-run `.venv\Scripts\activate`
> first. You'll know it worked when you see `(.venv)` in the prompt.

---

## Phase 2 — Configure OBS (one time)

You need OBS 28 or newer. Do all four:

1. **WebSocket server**
   - OBS menu: *Tools → WebSocket Server Settings*
   - Check **Enable WebSocket server**
   - Note the **Server Port** (default `4455`)
   - Click **Show Connect Info**, copy the **Server Password**
   - Click OK

2. **Replay Buffer** (this is what saves the clips)
   - *Settings → Output* — at the top set **Output Mode: Advanced**
   - Go to the **Replay Buffer** tab, check **Enable Replay Buffer**
   - Set **Maximum Replay Time** to `30 s`
   - Go to the **Recording** tab and confirm a **Recording Path** exists (that's
     where clips land). Note that folder.
   - Apply / OK

3. **Kill counter text source**
   - In your Scene, under **Sources** click **+** → **Text (GDI+)**
   - Name it **exactly** `KillCounter` (capitalization matters)
   - Type any placeholder text, pick a font/size/position, OK
   - Drag it where you want the count to appear in recordings

4. **Virtual Camera** (default capture method — lowest anti-cheat exposure)
   - In OBS's **Controls** dock (bottom right), click **Start Virtual Camera**
   - Leave it running whenever you use the tool
   - *(Skip this only if you switch `config.yaml` to `capture_source: screen`.)*

Also make sure OBS is actually **capturing the game** — add a *Game Capture* or
*Display Capture* source to your scene and confirm you can see Marathon in the
OBS preview. The tool reads what OBS sees.

---

## Phase 3 — Fill in config.yaml

Open `config.yaml` in Notepad (or any editor) and set:

| Setting | What to put |
|---|---|
| `player_name` | Your **exact** in-game display name |
| `name_aliases` | Add your name again, plus any likely OCR misreads (e.g. `l`↔`I`, `0`↔`O`) |
| `obs: password` | The OBS websocket password from Phase 2, step 1 |
| `obs: port` | Match Phase 2 (default `4455` is already set) |
| `capture_source` | Leave `obs_virtualcam` (recommended) |

Leave everything else at defaults for now — you'll tune timing/OCR later if needed.

Save the file.

---

## Phase 4 — Calibrate the kill-feed region

This tells the tool *where* on the frame the kill feed appears.

1. Get Marathon (or a screenshot of it) showing the kill feed. Easiest: be in a
   match, or have a saved screenshot with feed text visible.
2. Make sure OBS **Virtual Camera is running** (Phase 2, step 4).
3. Run:
   ```bat
   python calibrate.py
   ```
4. A window opens showing a frame from OBS. **Drag a box** tightly around the
   kill-feed area (where the "X downed Y" lines show up), then press **ENTER**.

**You should see:** `Wrote feed_region into config.yaml. You're calibrated.`

**Tips:**
- Crop tight to just the feed text — less background = better OCR.
- If you change resolution or HUD scale later, re-run this.
- If the window is black/empty, the Virtual Camera isn't running or
  `obs_virtualcam_index` is wrong (try `1` or `2` in config.yaml).

---

## Phase 5 — Test detection logic (no game needed)

Confirm the name-matching does what you expect. Replace `YourName` with your
actual name:

```bat
python main.py --test-lines "YourName downed Ripper" "SomeoneElse downed Bob" "Ripper downed YourName"
```

**You should see:**
- `[KILL ]` on the first line (your kill)
- `[  -  ]` on the second (someone else's kill — ignored)
- `[  -  ]` on the third (your death — ignored)

If your own kill shows `[  -  ]`, your `player_name` doesn't match — fix it in
config.yaml.

---

## Phase 6 — Test OCR on a real screenshot (the important checkpoint)

This is where we find out if Marathon's font reads cleanly.

1. In a match, take a screenshot when the kill feed is showing several lines.
   Save it as e.g. `shot.png` in the `Marathon-OBS` folder.
2. Run:
   ```bat
   python main.py --test-image shot.png
   ```

**You should see:** the OCR-read lines printed, then a detection verdict for each.

**Judge the result:**
- If the feed lines come back readable and your kills are flagged `[KILL ]`,
  you're in great shape — go to Phase 7.
- If the text is garbled or missed, tune (see Phase 9) and re-run this step.
- **Send me the screenshot + the console output** and I'll adjust the OCR
  preprocessing / detection to match Marathon's exact feed format (including how
  it shows assists).

Iterate on this step until detection is reliable **before** going live.

---

## Phase 7 — Dry run (full pipeline, no clips saved)

Rehearse the whole thing live, but with OBS actions only logged (nothing saved):

```bat
python main.py --dry-run
```

Jump into a match and get some kills.

**You should see:** `KILL #1`, `KILL #2`, ... printed in the console as you get
kills, and `[dry-run] save_replay()` lines. No actual clips are written.

**Check:** does the count match your real kills? Any missed kills or false
positives? Tune (Phase 9) if needed.

---

## Phase 8 — Go live

Everything confirmed? Run for real:

```bat
python main.py
```

Now on each detected kill it will:
- save an OBS Replay Buffer clip to your recording folder,
- bump the `KillCounter` text source in OBS,
- append a row to `session_log.csv`.

Play a match, then check your recording folder for clips and `session_log.csv`
for the log. Press **Ctrl-C** in the terminal to stop; it prints your session total.

---

## Phase 9 — Tuning (only if needed)

All in `config.yaml`:

| Problem | Try this |
|---|---|
| Missing your kills | Lower `name_match_threshold` (e.g. 75); add `name_aliases`; raise `ocr_upscale` to 4; re-calibrate a tighter region |
| False positives / double counts | Raise `name_match_threshold` (e.g. 88); raise `dedup_ttl_seconds` |
| Counting others' kills | Set `match_mode: self_only` |
| Wrong verb | Add the game's actual word(s) to `trigger_keywords` (e.g. `eliminated`, `killed`) |
| Too many overlapping clips | Raise `min_save_interval_seconds` |
| OCR too slow | Ensure GPU is used (EasyOCR); or switch `ocr_engine: tesseract` |

Re-run Phase 6 / Phase 7 after any change.

---

## Quick reference — everyday use

Once it's all set up, a normal session is just:

```bat
cd %USERPROFILE%\Documents\Marathon-OBS
.venv\Scripts\activate
python main.py
```

(With OBS open, Replay Buffer + Virtual Camera running.)

---

## If something breaks

| Symptom | Likely cause / fix |
|---|---|
| `Could not open OBS Virtual Camera` | Click **Start Virtual Camera** in OBS; or try `obs_virtualcam_index: 1`/`2` |
| `could not verify/start Replay Buffer` | Enable Replay Buffer in OBS Output settings |
| Counter never updates | Text source must be named exactly `KillCounter` |
| Can't connect to OBS | Wrong `password`/`port` in config; WebSocket server not enabled |
| Nothing detected at all | Re-check `feed_region` (Phase 4) and run Phase 6 on a screenshot |

When in doubt on Phase 6, send me the screenshot and console output.
