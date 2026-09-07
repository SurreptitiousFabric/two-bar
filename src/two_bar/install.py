"""Reversible user-only installation; never edits packaged Omarchy files."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from .control import DEFAULT_CONFIG, atomic_json, validate

PLUGIN = "io.github.surreptitiousfabric.two-bar"
GMAIL = "local.gmail-monitor"
BINDING = '\n-- BEGIN two-bar\no.bind("SUPER + CTRL + SHIFT + W", "Toggle work bar", "two-bar toggle")\n-- END two-bar\n'
MENU = '''
  // BEGIN two-bar
  "trigger.work": {"icon":"󰃖","label":"Work bar","description":"Weekdays 08:00–18:00; manual overrides until the next transition"},
  "trigger.work.toggle": {"icon":"󰃖","label":"Toggle work bar","action":"two-bar toggle","checked":"two-bar is-visible"},
  "trigger.work.auto": {"icon":"󰥔","label":"Follow schedule","action":"two-bar follow-schedule","checked":"two-bar is-automatic"}
  // END two-bar
'''


def jsonc(text):
    # Keep quoted strings intact, including URLs and escaped quotes.
    clean = re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*[\s\S]*?\*/',
                   lambda match: match[1] or "", text)
    return json.loads(clean)


def widget_id(entry):
    return entry.get("id") if isinstance(entry, dict) else entry


def shell_install(config, record, activate, widget_ids=None):
    widget_ids = widget_ids or [GMAIL]
    config = json.loads(json.dumps(config))
    plugins = config.setdefault("plugins", [])
    moved = record.setdefault("moved", {})
    if record.get("gmail"):
        moved.setdefault(GMAIL, record["gmail"])
    for identifier in [PLUGIN, *widget_ids]:
        if not any(widget_id(entry) == identifier for entry in plugins):
            plugins.append({"id": identifier})
            if identifier not in record["added_plugins"]:
                record["added_plugins"].append(identifier)
    if activate:
        for section, entries in config["bar"]["layout"].items():
            for index, entry in enumerate(entries):
                identifier = widget_id(entry)
                if identifier in widget_ids and identifier not in moved:
                    moved[identifier] = {"section": section, "index": index, "entry": entry,
                                         "previous": widget_id(entries[index - 1]) if index else None,
                                         "next": widget_id(entries[index + 1]) if index + 1 < len(entries) else None}
            config["bar"]["layout"][section] = [entry for entry in entries if widget_id(entry) not in widget_ids]
    return config


def shell_uninstall(config, record):
    config = json.loads(json.dumps(config))
    config["plugins"] = [entry for entry in config.get("plugins", [])
                         if widget_id(entry) not in record["added_plugins"]]
    layout = config["bar"]["layout"]
    moved = record.get("moved", {})
    if record.get("gmail"):
        moved = {GMAIL: record["gmail"]} | moved
    for identifier, saved in sorted(moved.items(), key=lambda pair: (pair[1]["section"], pair[1]["index"])):
        if not any(widget_id(entry) == identifier for entries in layout.values() for entry in entries):
            entries = layout.setdefault(saved["section"], [])
            ids = [widget_id(entry) for entry in entries]
            if saved.get("next") in ids:
                index = ids.index(saved["next"])
            elif saved.get("previous") in ids:
                index = ids.index(saved["previous"]) + 1
            else:
                index = min(saved["index"], len(entries))
            entries.insert(index, saved["entry"])
    return config


def install(project, home, activate=True, add_widgets=()):
    config_dir = home / ".config"
    state_dir = home / ".local/state/two-bar"
    shell_path = config_dir / "omarchy/shell.json"
    menu_path = config_dir / "omarchy/extensions/omarchy-menu.jsonc"
    bindings_path = config_dir / "hypr/bindings.lua"
    plugin_dir = config_dir / "omarchy/plugins" / PLUGIN
    launcher = home / ".local/bin/two-bar"
    journal = state_dir / "installation.json"
    shell_config = json.loads(shell_path.read_text())
    work_config = config_dir / "two-bar/config.json"
    preferences = validate(json.loads(work_config.read_text()) if work_config.exists() else {})
    preferences = json.loads(json.dumps(preferences))
    for identifier in add_widgets:
        if not any(entry["id"] == identifier for entry in preferences["widgets"]):
            preferences["widgets"].append({"id": identifier})
    widget_ids = [entry["id"] for entry in preferences["widgets"]]
    for identifier in widget_ids:
        if not (config_dir / "omarchy/plugins" / identifier / "manifest.json").is_file():
            raise ValueError("Install the existing " + identifier + " plugin first")
        if identifier in shell_config.get("disabledPlugins", []):
            raise ValueError(identifier + " is explicitly disabled; enable it first")
    old_menu = menu_path.read_text() if menu_path.exists() else "{}\n"
    old_bindings = bindings_path.read_text()
    record = json.loads(journal.read_text()) if journal.exists() else None
    if not record:
        if plugin_dir.exists() or launcher.exists() or launcher.is_symlink():
            raise ValueError("Unmanaged two-bar installation exists; refusing to overwrite")
        if "trigger.work" in jsonc(old_menu) or "-- BEGIN two-bar" in old_bindings:
            raise ValueError("Existing work menu or binding conflicts with installation")
        record = {"added_plugins": [], "gmail": None, "menu_insert": "", "binding": BINDING}
        # Backups remain private and are never included in the public checkout.
        backup = state_dir / "backup"
        backup.mkdir(parents=True, mode=0o700)
        for source in [shell_path, menu_path, bindings_path]:
            if source.exists():
                shutil.copy2(source, backup / source.name)
                (backup / source.name).chmod(0o600)
    updated_shell = shell_install(shell_config, record, activate, widget_ids)
    updated_menu = old_menu
    if record["menu_insert"] and record["menu_insert"] in old_menu:
        # Upgrade only the exact block owned by this installer.
        updated_menu = old_menu.replace(record["menu_insert"], "", 1)
        offset = updated_menu.rfind("}")
        insert = ("," if jsonc(updated_menu) else "") + MENU
        updated_menu = updated_menu[:offset] + insert + updated_menu[offset:]
        jsonc(updated_menu)
        record["menu_insert"] = insert
    if "trigger.work" not in jsonc(old_menu):
        offset = old_menu.rfind("}")
        insert = ("," if jsonc(old_menu) else "") + MENU
        updated_menu = old_menu[:offset] + insert + old_menu[offset:]
        jsonc(updated_menu)  # Validate before any config write.
        record["menu_insert"] = insert
    updated_bindings = old_bindings if "-- BEGIN two-bar" in old_bindings else old_bindings + BINDING
    atomic_json(journal, record)
    plugin_dir.mkdir(parents=True, exist_ok=True)
    for source in (project / "plugin").iterdir():
        if source.is_file():
            shutil.copy2(source, plugin_dir / source.name)
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if not launcher.is_symlink():
        launcher.symlink_to(project / "bin/two-bar")
    atomic_json(work_config, preferences)
    menu_path.parent.mkdir(parents=True, exist_ok=True)
    if updated_menu != old_menu:
        menu_path.write_text(updated_menu)
    if updated_bindings != old_bindings:
        bindings_path.write_text(updated_bindings)
    atomic_json(shell_path, updated_shell)


def uninstall(home):
    state_dir = home / ".local/state/two-bar"
    journal = state_dir / "installation.json"
    record = json.loads(journal.read_text())
    config_dir = home / ".config"
    shell_path = config_dir / "omarchy/shell.json"
    menu_path = config_dir / "omarchy/extensions/omarchy-menu.jsonc"
    bindings_path = config_dir / "hypr/bindings.lua"
    menu = menu_path.read_text()
    bindings = bindings_path.read_text()
    if record["menu_insert"] and record["menu_insert"] not in menu:
        raise ValueError("Work menu was edited; merge its removal manually before uninstall")
    if record["binding"] not in bindings:
        raise ValueError("Work binding was edited; merge its removal manually before uninstall")
    updated_menu = menu.replace(record["menu_insert"], "", 1) if record["menu_insert"] else menu
    jsonc(updated_menu)
    atomic_json(shell_path, shell_uninstall(json.loads(shell_path.read_text()), record))
    menu_path.write_text(updated_menu)
    bindings_path.write_text(bindings.replace(record["binding"], "", 1))
    launcher = home / ".local/bin/two-bar"
    if launcher.is_symlink():
        launcher.unlink()
    # Retain disabled plugin files, backups and preferences for recovery/reinstall.
    record["uninstalled"] = True
    atomic_json(journal, record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "uninstall"])
    parser.add_argument("--prepare", action="store_true", help="Load panel but keep Gmail in top bar for validation")
    parser.add_argument("--widget", action="append", default=[], help="Add an existing user plugin to the work panel (repeatable)")
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[2]
    try:
        if args.action == "install":
            # Never replace an existing desktop shortcut.
            bindings = json.loads(subprocess.check_output(["hyprctl", "binds", "-j"]))
            owned_binding = ((Path.home() / ".local/state/two-bar/installation.json").exists()
                             and BINDING in (Path.home() / ".config/hypr/bindings.lua").read_text())
            conflicts = [b for b in bindings if b.get("modmask") == 69 and str(b.get("key", "")).upper() == "W"
                         and not (owned_binding and b.get("description") == "Toggle work bar")]
            if conflicts:
                raise ValueError("SUPER+CTRL+SHIFT+W is already bound; choose another shortcut")
            install(project, Path.home(), activate=not args.prepare, add_widgets=args.widget)
        else:
            uninstall(Path.home())
        subprocess.run(["hyprctl", "reload"], check=True)
        errors = subprocess.check_output(["hyprctl", "configerrors"], text=True).strip()
        if errors:
            raise ValueError("Hyprland reports configuration errors: " + errors)
        # Plugin rescans on some Omarchy builds retain compiled QML components.
        subprocess.run(["omarchy", "restart", "shell"], check=True)
        print("two-bar " + args.action + " complete")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"two-bar: {error}\n")


if __name__ == "__main__":
    main()
