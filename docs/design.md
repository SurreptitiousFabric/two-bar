# Design notes

## Requirements

The normal top bar remains the everyday bar. Work widgets belong in a compact
bottom-left panel that can disappear independently. Gmail is the first widget;
a connections dashboard is a later extension.

## Findings from the installed shell

- Stock bar placement is a single `top`, `bottom`, `left`, or `right` value.
- Only one full-bar plugin is active at once.
- The plugin system supports panels and a bar-widget registry.
- Widgets rely on a host for theme properties, tooltips and popup coordination.
- The existing Gmail widget uses the local monitor's `status`, `refresh` and
  `open` operations. Its backend and authentication need not move.

These findings describe the inspected installation, not a promised stable API.

## Architecture spike

Prefer a companion panel if it can discover and mount selected widgets without
also mounting them in the top bar. Verify registry behavior, shared theme imports,
startup loading, IPC ownership, and teardown. A custom full-bar host managing two
surfaces is a fallback if the companion cannot provide reliable integration.

The host must provide bottom-oriented widget geometry, upward popups, tooltips,
click behavior, and appropriate focus handling. Avoid duplicate widget instances
and duplicate timers or IPC handlers.

## Work mode

Visibility is independent of the normal bar. Define show/hide/toggle/status,
restart behavior, and a discoverable desktop control. Hidden mode must dismiss
popups, unmap the surface and remove input and exclusion zones. Background Gmail
polling remains separate unless the owner requests a different policy.

## Decisions to resolve

- Manual control versus a schedule; keyboard shortcut if manual.
- Initial state and persistence across shell restarts and login.
- Which monitor receives the panel and how hotplug behaves.
- Overlay windows versus reserve bottom-edge space.
- Connections dashboard contents and whether it is status-only or interactive.

## Validation

Test Gmail healthy/unread/zero/stale/unavailable states with synthetic data.
Verify opening and refresh actions without publishing mail contents. Check normal
bar preservation, repeated work-mode toggles, popup dismissal, fullscreen behavior,
monitor removal, shell reload, and uninstall restoration.
