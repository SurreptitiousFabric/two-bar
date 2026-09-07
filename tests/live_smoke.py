"""Opt-in desktop smoke check: briefly toggles the bar, leaves schedule active.

Run with the installed panel. Reports only panel IDs and geometry, never mail data.
"""
import json
import subprocess
import time


def command(*args):
    return subprocess.check_output(args, text=True, timeout=5)


expected_widgets = json.loads(command("two-bar", "status"))["config"]["widgets"]


def wait_state(visible):
    until = time.monotonic() + 7
    while time.monotonic() < until:
        state = json.loads(command("omarchy-shell", "two-bar", "diagnostics"))
        if state["healthy"] and state["visible"] == visible:
            expected = [entry["id"] for entry in expected_widgets] if visible else []
            if state["loaded"] == expected:
                return state
        time.sleep(0.15)
    raise AssertionError("Panel did not reach requested state")


def monitors():
    return {m["name"]: m["reserved"] for m in json.loads(command("hyprctl", "monitors", "-j"))}


baseline = monitors()
try:
    command("two-bar", "show")
    shown = wait_state(True)
    time.sleep(0.2)
    visible_reservations = monitors()
    assert visible_reservations[shown["monitor"]][3] > 0
    command("two-bar", "hide")
    hidden = wait_state(False)
    time.sleep(0.2)
    hidden_reservations = monitors()
    assert hidden_reservations[shown["monitor"]][3] == 0
    assert not hidden["tooltipVisible"]
    assert all(hidden_reservations[name][1] == baseline[name][1] for name in baseline)
    command("hyprctl", "dispatch", 'hl.dsp.exec_cmd("two-bar toggle")')
    wait_state(True)
    command("two-bar", "toggle")
    wait_state(False)
    print("PASS: configured widgets mount once, unmount on hide; bottom reservation released; top reservation preserved; compositor-launched toggle works")
finally:
    command("two-bar", "follow-schedule")
