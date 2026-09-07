# Refresh ownership after a completed uninstall

Priority: P2. Scope: installer ownership journal across installation lifecycles.

## Problem

After install → uninstall → user configuration edits → reinstall, the retained
journal reuses the first installation's moved-widget and added-plugin records.
The next uninstall can restore obsolete widget positions and remove a plugin
entry independently added by the user between installations.

## Definition of done

- A reinstall after a completed uninstall starts fresh ownership and restoration
  records from the current shell configuration, including legacy Gmail records.
- Repeated installs and prepare → activate within one lifecycle retain the
  original restoration snapshot.
- Regression coverage reorders/configures Gmail and independently adds its plugin
  entry between lifecycles; the second uninstall preserves those changes.
- Retained plugin files, preferences and backups remain compatible with reinstall.
- An active installation from an older release whose completion flag stayed set
  remains upgradeable/removable when both exact owned blocks are present.
- Repeating a completed uninstall leaves subsequent user edits untouched.
- Installer tests pass and installation documentation reflects the behavior.

## Completion evidence

Implemented with fresh lifecycle journals and separate private backups. Regression
tests cover changed widget positions/settings, independently added plugin entries,
legacy Gmail records, stale completion flags, repeat uninstall and preserved
backup contents/permissions. All 22 unit tests pass; README and verification
documentation describe the resulting lifecycle behavior.
