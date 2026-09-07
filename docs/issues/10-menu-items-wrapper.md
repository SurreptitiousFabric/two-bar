# Insert work controls into the effective menu items object

Priority: P2. Scope: Omarchy's supported top-level items wrapper.

## Problem

For an extension such as `{"items":{"custom":{"action":"true"}}}`, Omarchy
uses the inner items object. The installer currently inserts the work controls
into the outer object, so installation succeeds but the native menu ignores them.

## Definition of done

- Detect the effective menu object according to Omarchy's parsing behavior.
- Install all three work controls inside an existing items object; retain
  unwrapped menu support and preserve unrelated wrapper fields/content.
- Check all three work-control keys for conflicts in the effective object before
  writing; strings/comments containing braces do not confuse insertion.
- Upgrade/remove owned blocks in both formats, including blocks previously
  installed outside an items wrapper.
- Regression tests verify the native menu's effective items contain the controls,
  round-trip preservation, and conflicts inside the wrapper.
- Installer tests pass and supported wrapper behavior is documented.

## Completion evidence

Insertion locates the effective object by JSONC tokens and checks all three work
keys. Tests cover wrapped/unwrapped menus, non-object fallback, surrounding fields,
legacy outer-block migration and pre-write conflicts. All 22 unit tests and 21
native parser checks pass, including normalized work actions/checkmarks inside
the wrapper and escaped wrapper keys. Supported behavior is documented.
