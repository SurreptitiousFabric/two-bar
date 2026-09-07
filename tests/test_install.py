import json
from pathlib import Path
import tempfile
import unittest

from two_bar.install import GMAIL, PLUGIN, install, uninstall, jsonc, shell_install, shell_uninstall


class InstallationTests(unittest.TestCase):
    def test_widgets_moved_in_separate_passes_restore_between_neighbors(self):
        original = {"bar": {"layout": {"right": [{"id": identifier} for identifier in
                    [GMAIL, "personal", "tray", "local.connections", "audio"]]}}, "plugins": []}
        record = {"added_plugins": [], "gmail": None}
        first = shell_install(original, record, True)
        second = shell_install(first, record, True, [GMAIL, "local.connections"])
        self.assertEqual(shell_uninstall(second, record), original)

    def test_prepare_activate_repeat_restore_preserve_unrelated_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".config"
            shell_path = config / "omarchy/shell.json"
            menu_path = config / "omarchy/extensions/omarchy-menu.jsonc"
            bindings_path = config / "hypr/bindings.lua"
            gmail_path = config / "omarchy/plugins" / GMAIL
            gmail_path.mkdir(parents=True)
            (gmail_path / "manifest.json").write_text("{}")
            menu_path.parent.mkdir(parents=True)
            bindings_path.parent.mkdir(parents=True)
            original = {"version": 1, "bar": {"position": "top", "layout": {
                "left": [{"id": "omarchy.menu"}], "right": [{"id": GMAIL, "custom": 4}, {"id": "other"}]}},
                "plugins": [{"id": "existing"}], "idle": {"lock": 600}}
            shell_path.write_text(json.dumps(original))
            menu_text = '{\n // Keep this comment\n "existing": {"action":"open https://example.com"}\n}\n'
            menu_path.write_text(menu_text)
            bindings_path.write_text("-- existing bindings\n")
            project = Path(__file__).resolve().parents[1]
            install(project, home, activate=False)
            self.assertEqual(json.loads(shell_path.read_text())["bar"], original["bar"])
            install(project, home)
            first = shell_path.read_text()
            install(project, home)
            self.assertEqual(shell_path.read_text(), first)
            current = json.loads(first)
            self.assertEqual(current["bar"]["layout"]["right"], [{"id": "other"}])
            self.assertEqual(sum(x["id"] == PLUGIN for x in current["plugins"]), 1)
            self.assertIn("trigger.work", jsonc(menu_path.read_text()))
            current["idle"]["lock"] = 900
            current["plugins"].append({"id": "added-later"})
            shell_path.write_text(json.dumps(current))
            with bindings_path.open("a") as stream:
                stream.write("-- added later\n")
            uninstall(home)
            restored = json.loads(shell_path.read_text())
            self.assertEqual(restored["bar"], original["bar"])
            self.assertEqual(restored["idle"]["lock"], 900)
            self.assertIn({"id": "added-later"}, restored["plugins"])
            self.assertEqual(menu_path.read_text(), menu_text)
            self.assertEqual(bindings_path.read_text(), "-- existing bindings\n-- added later\n")
            self.assertFalse((home / ".local/bin/two-bar").exists())
            install(project, home)
            self.assertIn("trigger.work", jsonc(menu_path.read_text()))


if __name__ == "__main__":
    unittest.main()
