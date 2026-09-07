# Verification

Tested on Omarchy dev 4.0.0.r6589.gdec29fa-1 and Quickshell
0.3.0.r20.g28771c7-1, with Mise-selected Python 3.14.7.

- Ten unit tests pass: schedule boundaries, weekends, manual overrides,
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
