# Design

A persistent `panel` plugin with `keepLoaded: true` hosts work widgets in the same
Quickshell process as the normal top bar. The shell injects its widget registry
and theme context. No packaged Omarchy files are changed.

Selected widgets stay enabled through `shell.json`'s `plugins[]`, leave
`bar.layout`, and mount once in the companion. A duplicate guard prevents mounting
an item still in the top bar. Gmail and Connections use their existing backends.

## Surface

The surface anchors left/right/bottom and reserves its height plus bottom margin.
Only the compact content area receives pointer input. Hiding unmaps the surface
and unloads widgets, returning the reserved row to applications.

Transparency follows the stock bar setting. `omarchy-bar-text-color` selects a
foreground from the bottom wallpaper band and theme colors, refreshed on theme
and wallpaper changes. Tooltips open upward. Hiding dismisses the work submenu;
independent dashboard windows and backend polling remain running.

One configured screen, or the first available screen, receives the panel. A
missing named screen falls back to the first. ScreenMoveRemap handles changes to
the screen origin. Fullscreen and origin-change software checks pass; the owner
has also confirmed physical video-cable unplug/replug behavior.

## Schedule

Monday–Friday 08:00 inclusive to 18:00 exclusive, local timezone; weekends off.
Manual overrides expire at the next actual schedule transition. Follow schedule
clears them immediately. There is no holiday calendar in this version.

Atomic, locked state writes persist overrides with creation/expiry times and a
schedule/timezone identity. Invalid, expired, clock-rewound or mismatched overrides
revert to automatic mode. Calendar boundaries handle DST rather than assuming a
24-hour day. Startup/resume evaluates the current time without replaying missed
events. Five-second polling and immediate manual refresh share one controller.
Unchanged widget configuration retains mounted instances.

The shortcut and native Trigger menu use the same commands. Menu checkmarks show
visibility and automatic mode. Static entries are used because this installed
shell only supports a fixed set of dynamic providers.

## Installation

The installer saves original widget positions and private configuration backups,
preserves unrelated settings, and installs only to user paths. Uninstall removes
owned additions and restores moved widgets. Mail and connection credentials are
never migrated into this public project.
