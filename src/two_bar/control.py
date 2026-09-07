"""Local calendar schedule and atomic, process-safe manual overrides."""
import argparse
from datetime import datetime, time, timedelta
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile
from zoneinfo import ZoneInfo

DEFAULT_CONFIG = {"start": "08:00", "end": "18:00", "weekdays": [0, 1, 2, 3, 4],
                  "monitor": "", "widgets": [{"id": "local.gmail-monitor"}]}


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def timezone():
    if os.environ.get("TZ"):
        return ZoneInfo(os.environ["TZ"].removeprefix(":"))
    path = Path("/etc/localtime")
    with path.open("rb") as stream:
        return ZoneInfo.from_file(stream, key=str(path.resolve()))


def validate(config):
    result = DEFAULT_CONFIG | config
    start, end = time.fromisoformat(result["start"]), time.fromisoformat(result["end"])
    if start.tzinfo or end.tzinfo or start >= end:
        raise ValueError("Schedule requires same-day local start before end")
    days = result["weekdays"]
    if not days or any(type(day) is not int or day not in range(7) for day in days):
        raise ValueError("weekdays must contain integers 0 (Monday) through 6")
    widgets = result["widgets"]
    if not isinstance(widgets, list) or any(not isinstance(w, dict) or not isinstance(w.get("id"), str) or not w["id"] for w in widgets):
        raise ValueError("widgets must be a list of objects with nonempty ids")
    if len({w["id"] for w in widgets}) != len(widgets):
        raise ValueError("Duplicate widgets are not supported")
    if not isinstance(result["monitor"], str):
        raise ValueError("monitor must be a screen name or an empty string")
    return result


def scheduled(now, config):
    return (now.weekday() in config["weekdays"]
            and time.fromisoformat(config["start"]) <= now.time().replace(tzinfo=None)
            < time.fromisoformat(config["end"]))


def next_boundary(now, config):
    for offset in range(8):
        day = now.date() + timedelta(days=offset)
        if day.weekday() not in config["weekdays"]:
            continue
        for clock in (config["start"], config["end"]):
            candidate = datetime.combine(day, time.fromisoformat(clock), now.tzinfo)
            if candidate.timestamp() > now.timestamp():
                return candidate
    raise ValueError("No schedule boundary found")


def evaluate(now, config, state, action="status"):
    config = validate(config)
    signature = json.dumps([str(now.tzinfo), config["start"], config["end"], config["weekdays"]])
    automatic = scheduled(now, config)
    boundary = next_boundary(now, config)
    valid = (type(state.get("visible")) is bool
             and isinstance(state.get("expires"), (int, float))
             and isinstance(state.get("created"), (int, float))
             and state.get("created", float("inf")) <= now.timestamp() < state["expires"]
             and state.get("signature") == signature)
    override = dict(state) if valid else {}
    visible = override.get("visible", automatic)
    if action == "follow-schedule":
        override = {}
    elif action in ("show", "hide", "toggle"):
        # Repeating show/hide is idempotent, including the override deadline.
        desired = not visible if action == "toggle" else action == "show"
        if not override or desired != visible:
            override = {"visible": desired, "created": now.timestamp(),
                        "expires": boundary.timestamp(), "signature": signature}
    result = {"visible": override.get("visible", automatic),
              "mode": "manual" if override else "automatic", "scheduled": automatic,
              "next_boundary": boundary.isoformat(),
              "override_until": datetime.fromtimestamp(override["expires"], now.tzinfo).isoformat() if override else None,
              "config": config}
    return result, override


def paths():
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "two-bar"
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "two-bar"
    return config, state


def read_json(path, fallback):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return fallback


def run(action="status"):
    config_dir, state_dir = paths()
    config = validate(read_json(config_dir / "config.json", {}))
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state_dir / "control.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            state = read_json(state_dir / "override.json", {})
            if not isinstance(state, dict):
                state = {}
        except (ValueError, OSError):
            state = {}
        result, updated = evaluate(datetime.now(timezone()), config, state, action)
        if updated != state:
            atomic_json(state_dir / "override.json", updated)
    return result


def menu(result):
    shown = "On" if result["visible"] else "Off"
    mode = result["mode"]
    return [
        {"id": "trigger.work.toggle", "label": f"Work bar: {shown} ({mode})",
         "icon": "󰃖", "action": "two-bar toggle"},
        {"id": "trigger.work.auto", "label": "Follow schedule", "icon": "󰥔",
         "description": "Weekdays 08:00–18:00" if mode == "automatic" else "Manual until " + result["override_until"],
         "action": "two-bar follow-schedule"}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["status", "show", "hide", "toggle", "follow-schedule", "menu", "is-visible", "is-automatic"])
    args = parser.parse_args()
    try:
        result = run("status" if args.action == "menu" else args.action)
        if args.action in ("is-visible", "is-automatic"):
            raise SystemExit(0 if (result["visible"] if args.action == "is-visible" else result["mode"] == "automatic") else 1)
        if args.action not in ("status", "menu"):
            try:
                subprocess.run(["omarchy-shell", "-q", "two-bar", "refresh"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                pass  # The shell also polls; state persists when it is stopped.
        print(json.dumps(menu(result) if args.action == "menu" else result))
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"two-bar: {error}\n")


if __name__ == "__main__":
    main()
