"""Opt-in fullscreen/monitor checks using a disposable window; restores desktop state."""
import json
from pathlib import Path
import subprocess
import time

from two_bar.control import atomic_json


def call(*args):
    return subprocess.check_output(args, text=True, timeout=8).strip()


def info(kind):
    return json.loads(call("hyprctl", kind, "-j"))


def dispatch(expression):
    result = call("hyprctl", "dispatch", expression)
    if result != "ok":
        raise RuntimeError(result)


def wait(check):
    deadline = time.monotonic() + 7
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.15)
    raise AssertionError("Desktop test condition timed out")


def panel():
    return json.loads(call("omarchy-shell", "two-bar", "diagnostics"))


def main():
    config_path = Path.home() / ".config/two-bar/config.json"
    state_path = Path.home() / ".local/state/two-bar/override.json"
    config = json.loads(config_path.read_text())
    override = json.loads(state_path.read_text()) if state_path.exists() else {}
    focused = info("activewindow").get("address")
    cursor = info("cursorpos")
    monitors = info("monitors")
    window = None
    moved_monitor = None
    try:
        call("two-bar", "show")
        for monitor in monitors:
            name = monitor["name"]
            atomic_json(config_path, config | {"monitor": name})
            call("omarchy-shell", "two-bar", "refresh")
            wait(lambda: panel()["monitor"] == name and panel()["visible"])
            dispatch('hl.dsp.focus({monitor = ' + json.dumps(name) + '})')
            window = subprocess.Popen(["foot", "--app-id=two-bar-validation", "--title=Two-bar fullscreen validation",
                                       "-o", "colors.background=204060", "--fullscreen", "sh", "-c",
                                       "printf 'Two-bar fullscreen validation — this window will close automatically.\\n'; sleep 90"],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            def test_window():
                return next((w for w in info("clients") if w.get("pid") == window.pid), None)

            target = wait(test_window)
            address = "address:" + target["address"]
            dispatch('hl.dsp.window.fullscreen({window = ' + json.dumps(address) + ', mode = "fullscreen", action = "set", layout_aware = false})')
            wait(lambda: test_window().get("fullscreen") == 2)
            time.sleep(0.4)
            target = test_window()
            expected = [round(monitor["width"] / monitor["scale"]), round(monitor["height"] / monitor["scale"])]
            assert target["at"] == [monitor["x"], monitor["y"]], target["at"]
            assert all(abs(a - b) <= 1 for a, b in zip(target["size"], expected)), target["size"]
            print("PASS:", name, "true fullscreen fills", expected, flush=True)
            call("two-bar", "hide")
            wait(lambda: not panel()["visible"])
            call("two-bar", "show")
            wait(lambda: panel()["visible"])
            assert test_window()["fullscreen"] == 2
            print("PASS:", name, "bar toggles preserve fullscreen", flush=True)
            window.terminate()
            window.wait(timeout=5)
            window = None
            wait(lambda: next(m for m in info("monitors") if m["name"] == name)["reserved"][3] > 0)

        # Exercise the panel's origin-change remap without disabling a monitor.
        if len(monitors) > 1:
            monitor = monitors[-1]
            moved_monitor = monitor
            mode = f'{monitor["width"]}x{monitor["height"]}@{monitor["refreshRate"]}'
            expression = 'hl.monitor({output = %s, mode = %s, position = %s, scale = %s, transform = %s})' % (
                json.dumps(monitor["name"]), json.dumps(mode),
                json.dumps(f'{monitor["x"] + 64}x{monitor["y"]}'), monitor["scale"], monitor["transform"])
            result = call("hyprctl", "eval", expression)
            if result != "ok":
                raise RuntimeError(result)
            wait(lambda: next(m for m in info("monitors") if m["name"] == monitor["name"])["x"] == monitor["x"] + 64)
            time.sleep(0.6)
            assert panel()["monitor"] == monitor["name"] and panel()["visible"]
            print("PASS: configured monitor origin moved and panel remained visible", flush=True)

        atomic_json(config_path, config | {"monitor": "two-bar-nonexistent-test-output"})
        call("omarchy-shell", "two-bar", "refresh")
        wait(lambda: panel()["monitor"] == monitors[0]["name"])
        print("PASS: missing monitor name falls back to first available screen", flush=True)
    finally:
        if window is not None:
            window.terminate()
            window.wait(timeout=5)
        if moved_monitor:
            call("hyprctl", "reload")
        atomic_json(config_path, config)
        atomic_json(state_path, override)
        call("omarchy-shell", "two-bar", "refresh")
        if focused:
            dispatch('hl.dsp.focus({window = ' + json.dumps("address:" + focused) + '})')
        dispatch('hl.dsp.cursor.move({x = %s, y = %s})' % (cursor["x"], cursor["y"]))


if __name__ == "__main__":
    main()
