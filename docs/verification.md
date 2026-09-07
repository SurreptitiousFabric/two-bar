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

## Remaining checks

Physical monitor unplug/replug, true fullscreen behavior, and interactive click
coverage across every Gmail health state remain manual checks. Existing widget
code is reused unchanged. Other rich popup plugins are not claimed compatible.

Compiled QML remained cached after plugin rescans on this installation; the
installer therefore restarts the shell after changes. The work monitor is
independent of the monitor where the normal Omarchy menu opens.
