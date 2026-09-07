# Accept Omarchy menu trailing commas

Priority: P2. Scope: JSONC parsing and separator-aware menu insertion.

## Problem

Omarchy's native menu accepts trailing commas, including nested objects/arrays.
The installer strips comments only, so valid existing extensions fail to parse.
Insertion must also reuse an existing trailing separator instead of doubling it.

## Definition of done

- Parse Omarchy-supported comments and trailing commas in objects and arrays
  without altering quoted strings, URLs or escaped quotes.
- Install and upgrade controls into menus with existing trailing commas without
  introducing duplicate separators.
- Uninstall preserves unrelated menu content and existing comments/formatting.
- Regression coverage includes nested trailing commas, commented separators and
  punctuation inside strings; malformed JSONC still fails before config writes.
- Installer tests pass and supported syntax is documented.

## Completion evidence

String-aware JSONC parsing and insertion accept nested trailing commas and reuse
existing separators. Regression tests verify comments, literal punctuation and
escaped strings, exact round trips, and malformed input rejection before writes.
All 22 unit tests and 21 checks against Omarchy's installed native parser pass.
README and verification documentation describe supported syntax and coverage.
