# Preserve separators when removing the owned menu block

Priority: P2. Scope: exact owned menu-block removal during uninstall and upgrade.

## Problem

Installing into an empty extension and then appending an unrelated menu entry
leaves a leading comma when the owned block is removed. Parsing fails, blocking
uninstall and repeat-install upgrades despite the owned block being unchanged.

## Definition of done

- Removing the exact owned block handles its surrounding separators and leaves
  valid menu JSONC when unrelated entries were added before or after it.
- Uninstall and repeat-install upgrade share the corrected removal behavior.
- Unrelated entries, comments and strings are preserved; edited owned content
  still receives a clear manual-merge error before configuration writes.
- Regression coverage includes an initially empty menu followed by an unrelated
  appended entry, plus entries on both sides of the block.
- Installer tests pass and verification documentation records coverage.

## Completion evidence

Uninstall and upgrade share exact-block removal with surrounding separator
handling. Regression tests exercise initially empty/nonempty menus, later entries
on both sides, preserved comments, and edited menu/binding blocks failing before
writes. All 22 unit tests and 21 native menu checks pass.
