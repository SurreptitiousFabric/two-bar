# Verification

Tested on Omarchy dev 4.0.0.r6589.gdec29fa-1 and Quickshell
0.3.0.r20.g28771c7-1, with Mise-selected Python 3.14.7.

- Twenty-two unit tests pass: schedule boundaries, weekends, manual overrides,
  idempotency, restart/expiry, DST, timezone/clock changes, corrupt state,
  repeat installation, restoration, and unrelated-setting preservation.
- Live smoke passes with Gmail and Connections: both mount once, unload on hide,
  and return on show. A compositor-launched toggle works.
- Hyprland reserves 47 logical pixels at the bottom when shown, zero when hidden.
  Top reservation remains 33 pixels. The terminal resizes above the work bar.
- Transparent appearance inspected live. Wallpaper contrast selects dark icons
  against the current light wallpaper. No captures or mail data are published.
- Shell restarts preserve automatic mode and load both widgets without QML errors.
- Connections reports its existing dashboard running; its backend is unchanged.
- Hyprland configuration validation is clean; menu and shortcut are installed.

## Installer review fixes (#7–#10)

Verified on 2026-09-07 with disposable synthetic home directories. No live desktop
configuration was edited and the disruptive desktop tests were not rerun for
these installer-only changes; the desktop results below describe earlier work.

- A completed uninstall resets ownership for the next lifecycle. Reordered and
  configured widgets and independently added plugin entries survive the second
  uninstall, including a legacy Gmail journal. Prepare/activate/repeat installs
  retain the active lifecycle's restoration snapshot.
- Backups from earlier lifecycles remain intact; subsequent lifecycle backups
  reflect current settings with private file permissions. Completed uninstall is
  idempotent. Older active installations with a stale `uninstalled` flag remain
  upgradeable/removable when their exact owned menu and binding blocks remain.
- Menu removal and upgrade preserve entries added before and after the owned
  block. Parsing supports comments, nested object/array trailing commas and
  literal punctuation/URLs/escaped quotes inside strings. Unchanged menus round
  trip byte-for-byte, including comments and trailing separators.
- Controls are inserted into an existing `items` object, with non-object `items`
  falling back to the outer menu. Upgrades relocate legacy outer owned blocks
  into the wrapper. All three effective work-control keys are checked for
  conflicts. Edited owned menu/binding blocks and malformed menu input fail
  before configuration writes, including backup/journal writes.
- `tests/native_menu_validation.py` passed 21 install/upgrade/uninstall checks
  against the installed `MenuModel.js` via Mise-selected Node 26.7.0. It checks
  normalized control actions/checkmarks, preservation of native unrelated items,
  wrapped and escaped wrapper keys, comments and trailing commas. The native
  source is read directly, never copied or modified.

## Scope

The owner confirmed physical video-cable unplug/replug and the keyboard shortcut
both behaved correctly on 2026-09-07. This is user-reported hardware validation,
separate from the automated tests. Other rich popup plugins are not claimed compatible.

## Issue #5 continuation

- `tests/synthetic_gmail.py` launches an isolated copy of the real panel and the
  existing Gmail widget with a temporary HOME and fake backend. Unread, zero,
  stale, error and malformed responses pass display/tooltip assertions and both
  open/refresh handler checks. No browser opens or mailbox requests are made.
  Hiding dismisses the tooltip and unloads the widget; the real bar is restored.
- `tests/desktop_validation.py` uses disposable windows. True fullscreen fills
  1728×1080 logical pixels on the laptop and 2400×1350 on the external screen;
  bar toggles preserve fullscreen state. Bottom reservation returns afterward.
  A 64-pixel external-monitor origin change and missing-monitor fallback pass.
  Original monitor geometry, focus, cursor, panel settings and mode are restored.
- `tests/manual_controls.py` exercises the registered shortcut with uinput key
  events and activates both native menu actions. The menu is also captured
  locally for visual inspection; captures are not committed.
- Found and fixed a real regression: every hidden-state poll closed the work
  menu, preventing reliable use of Follow schedule while off. Dismissal now
  occurs only on the transition to hidden. The regression check holds the menu
  open across a poll, then successfully selects Follow schedule.
- The higher-level Wayland virtual keyboard did not trigger the global shortcut;
  lower-level uinput events did. This is distinguished from a physical-key test.

These tests are opt-in and briefly affect the desktop. Use an idle session.

Compiled QML remained cached after plugin rescans on this installation; the
installer therefore restarts the shell after changes. The work monitor is
independent of the monitor where the normal Omarchy menu opens.
