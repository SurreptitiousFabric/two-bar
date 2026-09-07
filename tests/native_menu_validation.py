"""Read-only integration check against the installed Omarchy menu model."""
import argparse
import json
from pathlib import Path
import subprocess

from two_bar.install import MENU, MENU_KEYS
from two_bar.menu import insert_menu, remove_menu


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path,
                        default=Path("/usr/share/omarchy/shell/plugins/menu/MenuModel.js"))
    args = parser.parse_args()
    originals = [
        "{}\n",
        '{\n // Preserve comment\n "custom":{"action":"true"}\n}\n',
        '{"custom":{"action":"true",},}\n',
        '{\n "custom":{"action":"true","aliases":["one","two",],},\n // Keep\n}\n',
        '{"items":{}}\n',
        '{"metadata":{"label":"outside"},"items":{"custom":{"action":"true"},},"after":42,}\n',
        '{"it\\u0065ms":{"custom":{"action":"true"}},"after":{}}\n',
    ]
    cases = []
    for original in originals:
        installed, owned = insert_menu(original, MENU, MENU_KEYS)
        upgraded, new_owned = insert_menu(remove_menu(installed, owned), MENU, MENU_KEYS)
        restored = remove_menu(upgraded, new_owned)
        assert restored == original
        for stage, text in (("install", installed), ("upgrade", upgraded), ("uninstall", restored)):
            cases.append({"stage": stage, "text": text, "original": original})
    # Use the native parser itself; no packaged source is copied or modified.
    script = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const model = require(process.argv[1]);
const cases = JSON.parse(fs.readFileSync(0, "utf8"));
const expected = {
  "trigger.work": {action: "", checked: ""},
  "trigger.work.toggle": {action: "two-bar toggle", checked: "two-bar is-visible"},
  "trigger.work.auto": {action: "two-bar follow-schedule", checked: "two-bar is-automatic"}
};
for (const test of cases) {
  // A failed parse otherwise looks the same as an empty native menu.
  JSON.parse(model.stripJsonc(test.text));
  const actual = model.parseMenuJsonc(test.text);
  const original = model.parseMenuJsonc(test.original);
  assert.deepEqual(actual.filter(item => !(item.id in expected)), original);
  for (const [id, fields] of Object.entries(expected)) {
    const matches = actual.filter(item => item.id === id);
    assert.equal(matches.length, test.stage === "uninstall" ? 0 : 1);
    if (matches.length) {
      for (const [key, value] of Object.entries(fields)) assert.equal(matches[0][key], value);
    }
  }
}
console.log(`${cases.length} native menu checks passed`);
'''
    subprocess.run(["node", "-e", script, str(args.model.resolve())],
                   input=json.dumps(cases), text=True, check=True)


if __name__ == "__main__":
    main()
