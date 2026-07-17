"""Mode presets must stay in sync with the settings registry."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import webserver  # noqa: E402


def test_every_mode_key_is_a_real_setting():
    for mode in webserver.MODES:
        for k, v in mode["set"].items():
            assert k in webserver.SETTINGS, f"{mode['key']}: unknown setting {k}"
            default, typ = webserver.SETTINGS[k]
            assert isinstance(v, typ), f"{mode['key']}.{k}: wrong type"


def test_modes_apply_through_the_validated_path():
    state = webserver.LiveState()
    cfg = {}
    state.bind_config(cfg, lambda ch: None)
    sweat = next(m for m in webserver.MODES if m["key"] == "sweat")
    result = state.apply_settings(dict(sweat["set"]))
    assert result["show_overlays"] is False
    assert result["make_match_reels"] is False
    assert result["track_names"] is False
    assert cfg["announcer_medals"] is False        # live config actually changed


def test_sweat_turns_off_everything_midgame_but_standard_restores():
    state = webserver.LiveState()
    cfg = {}
    state.bind_config(cfg, lambda ch: None)
    sweat = next(m for m in webserver.MODES if m["key"] == "sweat")
    standard = next(m for m in webserver.MODES if m["key"] == "standard")
    state.apply_settings(dict(sweat["set"]))
    state.apply_settings(dict(standard["set"]))
    assert cfg["make_match_reels"] is True
    assert cfg["show_overlays"] is True
    assert cfg["announcer_medals"] is False        # voices stay opt-in


def test_mode_labels_unique():
    keys = [m["key"] for m in webserver.MODES]
    assert len(keys) == len(set(keys))
