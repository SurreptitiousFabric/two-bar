# two-bar

A scheduled bottom-left work panel for Omarchy, alongside the normal top bar.
**Working first version**, hosting existing Gmail and Connections widgets.

The panel follows the top bar's transparency and uses Omarchy's wallpaper contrast
helper. It reserves a bottom row so tiled windows stay clear, and releases that
space when hidden. Only the compact icon area receives pointer input.

## Controls

- **Super+Ctrl+Shift+W:** toggle the work bar.
- **Omarchy menu → Trigger → Work bar:** toggle or Follow schedule. Checkmarks
  indicate visibility and automatic mode. The briefcase opens this submenu.
- CLI: `two-bar show`, `hide`, `toggle`, `follow-schedule`, or `status`.

Automatic hours: Monday–Friday **08:00–18:00 local time**, weekends off. Manual
choices last until the next schedule transition. Hiding at 10:00 lasts for that
workday; showing on Saturday lasts until Monday 08:00, when automatic mode resumes.
Follow schedule resets immediately. Mail polling and open applications continue
independently of panel visibility.

## Install

Requires Omarchy's Quickshell shell, Mise, and an existing `local.gmail-monitor`
user plugin. Connections is optional and must already be installed separately.
From this checkout:

```bash
mise trust
mise install
PYTHONPATH=src mise exec -- python -m two_bar.install install
# Add the existing Connections widget:
PYTHONPATH=src mise exec -- python -m two_bar.install install --widget local.connections
```

Installation checks the shortcut, backs up local settings, moves selected widgets,
adds menu controls, validates Hyprland and restarts the shell. Keep this checkout
in place: the launcher uses its pinned Python runtime. No Python packages needed.
Menu extensions may use trailing commas and an `items` object wrapper. Controls
are inserted into the effective menu object while preserving unrelated text;
existing work-control keys cause a conflict before configuration writes.

Settings: `~/.config/two-bar/config.json` contains local `start`/`end` times,
`weekdays` (Monday = 0), `widgets`, and `monitor`. An empty or unavailable monitor
name selects the first available screen. Schedule checks run every five seconds;
manual controls also request an immediate refresh.

```bash
PYTHONPATH=src mise exec -- python -m two_bar.install uninstall
```

Uninstall restores moved widgets, removes the owned menu block and shortcut,
and disables the panel. Backups, disabled plugin files and preferences remain
under your home directory. Unrelated subsequent settings are preserved; edited
owned menu/binding blocks require a manual merge.
Each reinstall after a completed uninstall captures the current widget positions
and plugin ownership afresh and creates a new private backup without replacing
earlier backups. Repeated installs within an active lifecycle keep its restoration
snapshot. Repeating a completed uninstall leaves the configuration untouched.

## Development

```bash
PYTHONPATH=src mise exec -- python -m unittest discover -s tests -v
# Read-only native menu compatibility check (requires installed Omarchy):
PYTHONPATH=src mise exec node@26.7.0 -- python tests/native_menu_validation.py
# Opt-in desktop check: briefly toggles the bar, then follows the schedule.
mise exec -- python tests/live_smoke.py
# Additional opt-in desktop validation (use an idle session):
mise exec -- python tests/synthetic_gmail.py
PYTHONPATH=src mise exec -- python tests/desktop_validation.py
PYTHONPATH=src mise exec -- python tests/manual_controls.py
```

See [design](docs/design.md), [backlog](docs/backlog.md), and
[verification and limitations](docs/verification.md). Rich popup widgets beyond
the tested integrations need compatibility checks before adding them.

This public repository contains generic code and documentation only. Mail,
credentials, private endpoints and machine configuration stay outside it. Existing
widget code and backends are dependencies, not copied into this project.
