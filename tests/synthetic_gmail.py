"""Opt-in isolated QML test. Fake HOME/backends; no mailbox or browser access."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[1]
HOME = Path.home()


def call(*args, **kwargs):
    return subprocess.check_output(args, text=True, timeout=5, **kwargs).strip()


def until(check, seconds=7):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except (subprocess.SubprocessError, ValueError):
            pass
        time.sleep(0.15)
    raise AssertionError("Timed out waiting for isolated QML test")


def main():
    override_path = HOME / ".local/state/two-bar/override.json"
    original = override_path.read_bytes() if override_path.exists() else None
    call("two-bar", "hide")
    process = None
    try:
        with tempfile.TemporaryDirectory(prefix="two-bar-qml-") as directory:
            root = Path(directory)
            for module in ("Commons", "Ui"):
                (root / module).symlink_to(Path(os.environ["OMARCHY_PATH"]) / "shell" / module)
            shutil.copy2(PROJECT / "tests/qml/GmailHarness.qml", root / "shell.qml")
            shutil.copy2(PROJECT / "plugin/Panel.qml", root / "WorkPanel.qml")
            shutil.copy2(HOME / ".config/omarchy/plugins/local.gmail-monitor/BarWidget.qml", root / "Gmail.qml")
            fake_bin = root / ".local/bin"
            fake_bin.mkdir(parents=True)
            theme = root / ".local/state/omarchy"
            theme.mkdir(parents=True)
            (theme / "current").symlink_to(HOME / ".local/state/omarchy/current")
            backend = fake_bin / "omarchy-gmail-monitor"
            backend.write_text('#!/bin/sh\ncase "$1" in\nstatus) cat "$HOME/fixture.json";;\nopen|refresh) printf "%s\\n" "$1" >> "$HOME/actions";;\n*) exit 1;;\nesac\n')
            backend.chmod(0o755)
            controller = fake_bin / "two-bar"
            controller.write_text('#!/bin/sh\ncat "$HOME/panel.json"\n')
            controller.chmod(0o755)
            status = {"visible": True, "mode": "automatic", "config": {"monitor": "", "widgets": [{"id": "local.gmail-monitor"}]}}
            (root / "panel.json").write_text(json.dumps(status))
            fixture = root / "fixture.json"
            fixture.write_text(json.dumps({"ok": True, "unread": 0, "checked_at": int(time.time() * 1000)}))
            environment = os.environ | {"HOME": str(root), "XDG_CONFIG_HOME": str(root / ".config"), "XDG_CACHE_HOME": str(root / ".cache")}
            with (root / "qml.log").open("w+") as log:
                process = subprocess.Popen(["quickshell", "--no-color", "-p", str(root)], env=environment, stdout=log, stderr=log)

                def ipc(target, method, *args):
                    return call("quickshell", "ipc", "-p", str(root), "call", target, method, *args, stderr=subprocess.DEVNULL)

                until(lambda: json.loads(ipc("validation", "snapshot")).get("ready"))
                scenarios = [
                    ("unread", {"ok": True, "unread": 3, "latest": "Synthetic test message", "checked_at": int(time.time() * 1000)}, True, False, "3 unread"),
                    ("zero", {"ok": True, "unread": 0, "checked_at": int(time.time() * 1000)}, True, True, "No unread"),
                    ("stale", {"ok": True, "unread": 2, "checked_at": int(time.time() * 1000) - 240000}, False, True, "unavailable"),
                    ("error", {"ok": False, "detail": "Synthetic backend unavailable", "checked_at": 0}, False, True, "Synthetic backend unavailable"),
                    ("malformed", "not-json", False, True, "Invalid Gmail monitor status"),
                ]
                for name, data, healthy, dimmed, text in scenarios:
                    raw = data if isinstance(data, str) else json.dumps(data)
                    fixture.write_text(raw)
                    ipc("validation", "apply", raw)
                    snapshot = json.loads(ipc("validation", "snapshot"))
                    assert snapshot["healthy"] == healthy and snapshot["dimmed"] == dimmed, snapshot
                    assert text in snapshot["tooltip"], snapshot
                    ipc("validation", "hover")
                    until(lambda: json.loads(ipc("two-bar", "diagnostics"))["tooltipVisible"])
                    for action, right in [("open", "false"), ("refresh", "true")]:
                        previous = (root / "actions").read_text().splitlines() if (root / "actions").exists() else []
                        ipc("validation", "click", right)
                        until(lambda: (root / "actions").exists() and len((root / "actions").read_text().splitlines()) > len(previous))
                        assert (root / "actions").read_text().splitlines()[-1] == action
                    print("PASS:", name, "display, tooltip, open and refresh", flush=True)
                ipc("validation", "hover")
                status["visible"] = False
                (root / "panel.json").write_text(json.dumps(status))
                ipc("two-bar", "refresh")
                until(lambda: not json.loads(ipc("two-bar", "diagnostics"))["visible"])
                assert not json.loads(ipc("two-bar", "diagnostics"))["tooltipVisible"]
                print("PASS: hide dismisses synthetic tooltip and unloads widget", flush=True)
                process.terminate()
                process.wait(timeout=5)
                process = None
    finally:
        if process is not None:
            process.terminate()
            process.wait(timeout=5)
        if original is not None:
            override_path.write_bytes(original)
        else:
            override_path.unlink(missing_ok=True)
        call("omarchy-shell", "two-bar", "refresh")


if __name__ == "__main__":
    main()
