"""Detection logic — the brain of the tool, fully unit-testable without OBS/Windows.

PopupDetector watches the center-screen personal confirmation popup that
appears ONLY when you get a down, e.g. "RUNNER DOWN  +15 XP". Because it's
your own reward popup, no name matching is needed. Edge-triggered: fires once
each time the popup appears, then re-arms after it disappears.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

from rapidfuzz import fuzz


@dataclass
class KillEvent:
    timestamp: float          # monotonic-ish seconds (caller supplies the clock)
    raw_line: str             # the OCR line that triggered it
    killer: str               # parsed killer text (best-effort)
    victim: str               # parsed victim text (best-effort)
    is_self_kill: bool        # True if you were the killer (vs assist)


def _normalize(s: str) -> str:
    """Lowercase and collapse whitespace/punctuation for stable matching + dedup."""
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return s


def phrase_matches(phrase_norm: str, blob_norm: str, threshold: int = 80) -> bool:
    """Guarded fuzzy match: does the (normalized) phrase appear in the blob?

    Requires the blob to be long enough to plausibly CONTAIN the phrase, so a
    short OCR scrap like 'fi' can't fuzzily match a long word like 'finisher'
    (partial matching otherwise rewards a bare prefix at full confidence)."""
    if not phrase_norm or not blob_norm:
        return False
    if phrase_norm in blob_norm:
        return True
    if len(blob_norm) < max(5, 0.6 * len(phrase_norm)):
        return False
    return fuzz.partial_ratio(phrase_norm, blob_norm) >= threshold


class PopupDetector:
    """Edge-triggered detection of the transient personal down/kill popup
    (e.g. 'RUNNER DOWN  +15 XP').

    A whole OCR'd frame is passed in per call. The popup lingers for a couple of
    seconds and re-OCRs every frame, so we fire only on the RISING EDGE — the
    first frame it appears — then re-arm once it's been absent for a few frames
    (debounce against OCR flicker). Two separate downs count separately as long
    as the popup fully disappears between them.
    """

    def __init__(
        self,
        trigger_phrases: Optional[Iterable[str]] = None,
        phrase_match_threshold: int = 80,
        absence_frames: int = 2,
        require_xp_reward: bool = False,
        confirm_frames: int = 1,
        require_reward: bool = True,
        cooldown_seconds: float = 0.0,
    ):
        self.phrases = [_normalize(p) for p in (trigger_phrases or ["runner down"]) if p.strip()]
        self.threshold = phrase_match_threshold
        self.absence_frames = max(1, absence_frames)
        self.confirm_frames = max(1, confirm_frames)
        self.require_reward = require_reward
        # Minimum seconds between fires. With confirm_frames=1 a single popup
        # whose OCR flickers (clean, garbled, clean) could otherwise re-fire the
        # same kill; the cooldown collapses those into one.
        self.cooldown = max(0.0, cooldown_seconds)
        self._streak = 0        # consecutive matched frames
        self._fired = False     # already counted this appearance
        self._absent_count = absence_frames
        self._last_fire = -1e9

    def _reward_present(self, raw: str) -> bool:
        """Real kill popups show a reward: '+15 XP', '+50', '+10 XP'. Loading /
        menu text does not. Checked on the RAW text (before '+' is stripped)."""
        t = raw.lower()
        return ("xp" in t) or (re.search(r"\+\s*\d", t) is not None)

    def _matches(self, lines: Iterable[str]) -> Optional[str]:
        blob = _normalize(" ".join(lines))
        if not blob:
            return None
        for ph in self.phrases:
            if phrase_matches(ph, blob, self.threshold):
                return ph
        return None

    def process_frame(self, lines: Iterable[str], now: float) -> Optional[KillEvent]:
        lines = list(lines)
        matched = self._matches(lines)
        if matched is not None and self.require_reward and not self._reward_present(" ".join(lines)):
            matched = None  # phrase present but no reward on screen -> not a kill

        if matched is not None:
            self._streak += 1
            self._absent_count = 0
            # only count once the popup has persisted enough frames (real popups
            # linger; single-frame OCR noise is rejected)
            if (self._streak >= self.confirm_frames and not self._fired
                    and now - self._last_fire >= self.cooldown):
                self._fired = True
                self._last_fire = now
                return KillEvent(
                    timestamp=now,
                    raw_line=" ".join(lines).strip(),
                    killer="",
                    victim="",
                    is_self_kill=True,
                )
            return None

        # no match this frame
        self._absent_count += 1
        if self._absent_count >= self.absence_frames:
            self._streak = 0
            self._fired = False
        return None
