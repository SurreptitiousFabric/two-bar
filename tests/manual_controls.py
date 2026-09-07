"""Opt-in virtual-input check of the registered shortcut and native menu actions."""
import json
from pathlib import Path
import subprocess
import time

from two_bar.control import atomic_json
from desktop_validation import call, dispatch, info, panel, wait


def shortcut():
    # Linux input key codes: left Super, Control, Shift, W. Release every key.
    call("ydotool", "key", "125:1", "29:1", "42:1", "17:1", "17:0", "42:0", "29:0", "125:0")


def main():
    state_path = Path.home() / ".local/state/two-bar/override.json"
    original = json.loads(state_path.read_text()) if state_path.exists() else {}
    focused = info("activewindow").get("address")
    window = subprocess.Popen(["foot", "--app-id=two-bar-input-validation", "--title=Two-bar input validation",
                               "sh", "-c", "printf 'Temporary two-bar keyboard/menu test\\n'; sleep 60"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait(lambda: any(w.get("pid") == window.pid for w in info("clients")))
        call("two-bar", "show")
        wait(lambda: panel()["visible"])
        shortcut()
        wait(lambda: not panel()["visible"])
        shortcut()
        wait(lambda: panel()["visible"])
        print("PASS: registered Super+Ctrl+Shift+W toggles through uinput keyboard events", flush=True)

        call("omarchy", "menu", "close")
        call("omarchy", "menu", "summon", "trigger.work")
        time.sleep(0.4)
        call("grim", "-g", "650,350 430x400", "/tmp/two-bar-menu-validation.png")
        call("wtype", "-k", "Return")
        wait(lambda: not panel()["visible"])
        print("PASS: native Toggle work bar menu action hides panel", flush=True)
        call("omarchy", "menu", "summon", "trigger.work")
        # Cover at least one hidden-state poll. This formerly closed the menu.
        time.sleep(5.5)
        layers = info("layers")
        assert any(layer.get("namespace") == "omarchy-menu"
                   for monitor in layers.values() for level in monitor["levels"].values() for layer in level), "Hidden-state polling closed the work menu"
        call("wtype", "-k", "Down", "-s", "200", "-k", "Return")
        wait(lambda: panel()["mode"] == "automatic")
        print("PASS: native Follow schedule menu action restores automatic mode", flush=True)
    finally:
        call("omarchy", "menu", "close")
        window.terminate()
        window.wait(timeout=5)
        atomic_json(state_path, original)
        call("omarchy-shell", "two-bar", "refresh")
        if focused:
            dispatch('hl.dsp.focus({window = ' + json.dumps("address:" + focused) + '})')


if __name__ == "__main__":
    main()
