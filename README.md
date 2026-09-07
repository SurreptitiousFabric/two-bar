# two-bar

A work-only panel for Omarchy: work items at the bottom left, everyday plugins
in the existing top bar. Hide the work panel when the working day is over.

**Status: planning and implementation backlog. No runnable plugin yet.**

## Intended experience

- Keep the normal top bar and its everyday plugins.
- Show a compact, theme-aware work panel at the bottom left.
- Move the existing work Gmail widget into the work panel first.
- Provide independent work-mode visibility. Hiding must also dismiss work
  tooltips/popups and remove the panel's input and reserved-space footprint.
- Add a connections dashboard plugin in a later milestone.

The initial control mechanism and off-mode background-service policy are pending
owner confirmation. Hiding UI alone does not imply stopping Gmail polling or
disabling network connections.

## Implementation direction

Investigate a user-owned Quickshell panel plugin that reuses registered bar
widgets. Omarchy currently permits one active full-bar plugin, so a second
configured stock bar is not available. Validate widget discovery and host
services before choosing a standalone panel or custom bar host.

Do not edit packaged Omarchy files. Keep installation reversible and preserve
unrelated shell settings. See [design notes](docs/design.md) and the
[implementation backlog](docs/backlog.md).

## Public repository boundary

Publish code, generic configuration examples, and documentation only. Gmail
credentials, cached mail, account identifiers, employer connection details and
machine-specific configuration stay outside this repository. The existing Gmail
monitor remains an external dependency; this project does not copy its credentials
or private implementation.

## Development

GitHub CLI is pinned in `.mise.toml`. Run `mise trust`, `mise install`, then use
`mise exec -- gh ...`. Add other tool pins when implementation requires them.
