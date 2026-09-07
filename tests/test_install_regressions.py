"""Installer lifecycle regressions, using only disposable synthetic settings."""
import json
from pathlib import Path
import tempfile
import unittest

from two_bar.install import GMAIL, MENU, install, jsonc, uninstall


WORK_KEYS = {"trigger.work", "trigger.work.toggle", "trigger.work.auto"}


class InstallerRegressionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.project = Path(__file__).resolve().parents[1]
        self.shell = self.home / ".config/omarchy/shell.json"
        self.menu = self.home / ".config/omarchy/extensions/omarchy-menu.jsonc"
        self.bindings = self.home / ".config/hypr/bindings.lua"
        self.journal = self.home / ".local/state/two-bar/installation.json"
        plugin = self.home / ".config/omarchy/plugins" / GMAIL
        plugin.mkdir(parents=True)
        (plugin / "manifest.json").write_text("{}")
        self.menu.parent.mkdir(parents=True)
        self.bindings.parent.mkdir(parents=True)
        self.original = {"bar": {"position": "top", "layout": {
            "left": ["menu"], "right": [GMAIL, "tray", "audio"]}},
            "plugins": [{"id": "existing"}], "idle": {"lock": 600}}
        self.shell.write_text(json.dumps(self.original))
        self.menu.write_text("{}\n")
        self.bindings.write_text("-- unrelated binding\n")

    def install(self, **kwargs):
        install(self.project, self.home, **kwargs)

    def snapshot(self):
        return {str(path.relative_to(self.home)): path.read_bytes()
                for path in self.home.rglob("*") if path.is_file()}

    def test_new_lifecycle_owns_only_new_changes(self):
        self.install()
        uninstall(self.home)
        backup_dir = self.journal.parent / "backup"
        first_backup = {path.name: path.read_bytes() for path in backup_dir.iterdir()}
        changed = json.loads(self.shell.read_text())
        gmail = {"id": GMAIL, "custom": {"label": "work"}}
        changed["bar"]["layout"]["right"] = ["audio", "tray", gmail]
        changed["plugins"].append({"id": GMAIL, "settings": {"interval": 300}})
        changed["idle"]["lock"] = 900
        self.shell.write_text(json.dumps(changed))
        # Exercise migration from the legacy Gmail restoration field too.
        stale = json.loads(self.journal.read_text())
        stale["gmail"] = stale["moved"][GMAIL]
        self.journal.write_text(json.dumps(stale))
        self.install(activate=False)
        self.assertFalse(json.loads(self.journal.read_text()).get("uninstalled"))
        self.install()
        self.install()
        uninstall(self.home)
        self.assertEqual(json.loads(self.shell.read_text()), changed)
        self.assertEqual({path.name: path.read_bytes() for path in backup_dir.iterdir()}, first_backup)
        backups = list(self.journal.parent.glob("backup-*/shell.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(json.loads(backups[0].read_text()), changed)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)

    def test_completed_uninstall_is_idempotent(self):
        self.install()
        uninstall(self.home)
        before = self.snapshot()
        uninstall(self.home)
        self.assertEqual(self.snapshot(), before)

    def test_legacy_active_install_with_stale_uninstalled_flag(self):
        for upgrade in (False, True):
            with self.subTest(upgrade=upgrade):
                self.install()
                record = json.loads(self.journal.read_text())
                record["uninstalled"] = True  # Previous installer left this set on reinstall.
                self.journal.write_text(json.dumps(record))
                if upgrade:
                    self.install()
                    self.assertFalse(json.loads(self.journal.read_text()).get("uninstalled"))
                uninstall(self.home)
                self.assertEqual(json.loads(self.shell.read_text()), self.original)
                self.assertEqual(self.menu.read_text(), "{}\n")

    def test_added_entries_survive_removal_and_upgrade(self):
        for initial in ("{}\n", '{"existing":{"action":"true"}}\n'):
            for prepend in (False, True):
                with self.subTest(initial=initial, prepend=prepend):
                    self.menu.write_text(initial)
                    self.install()
                    current = self.menu.read_text()
                    offset = current.rfind("}")
                    current = current[:offset] + ',\n // Later comment\n "later":{"action":"true"}\n' + current[offset:]
                    if prepend:
                        current = current.replace("{", '{"first":{"action":"true"},', 1)
                    self.menu.write_text(current)
                    self.install()
                    items = jsonc(self.menu.read_text())
                    self.assertTrue(WORK_KEYS <= items.keys())
                    uninstall(self.home)
                    restored = jsonc(self.menu.read_text())
                    self.assertEqual(set(restored), set(items) - WORK_KEYS)
                    self.assertIn("// Later comment", self.menu.read_text())

    def test_trailing_commas_round_trip(self):
        menus = [
            '{\n "custom":{"action":"true",},\n}\n',
            '{\n "custom":{"aliases":["one","two",],}, // Keep separator comment\n}\n',
            '{\n // Empty menu\n}\n',
            '{"custom":{"action":"true"}, /* Keep block comment */\n}\n',
        ]
        for original in menus:
            with self.subTest(menu=original):
                self.menu.write_text(original)
                self.install()
                self.install()
                self.assertTrue(WORK_KEYS <= jsonc(self.menu.read_text()).keys())
                uninstall(self.home)
                self.assertEqual(self.menu.read_text(), original)

    def test_items_wrapper_and_surrounding_content_round_trip(self):
        original = '''{
  "metadata": {"text": "items, } // not a comment"},
  "items": {
    // Keep this menu item
    "custom": {"action": "true",},
  },
  "after": ["}", {"other": true}],
}
'''
        self.menu.write_text(original)
        self.install()
        self.install()
        parsed = jsonc(self.menu.read_text())
        self.assertTrue(WORK_KEYS <= parsed["items"].keys())
        self.assertEqual(set(parsed), {"metadata", "items", "after"})
        uninstall(self.home)
        self.assertEqual(self.menu.read_text(), original)

    def test_non_object_items_uses_outer_menu(self):
        for value in (None, [], "text", False):
            with self.subTest(items=value):
                original = json.dumps({"items": value, "custom": {"action": "true"}})
                self.menu.write_text(original)
                self.install()
                self.assertTrue(WORK_KEYS <= jsonc(self.menu.read_text()).keys())
                uninstall(self.home)
                self.assertEqual(self.menu.read_text(), original)

    def test_conflicts_do_not_write_configuration(self):
        for wrapped in (False, True):
            for key in WORK_KEYS:
                with self.subTest(wrapped=wrapped, key=key):
                    items = {key: {"action": "custom"}}
                    self.menu.write_text(json.dumps({"items": items} if wrapped else items))
                    before = self.snapshot()
                    with self.assertRaisesRegex(ValueError, "conflict"):
                        self.install()
                    self.assertEqual(self.snapshot(), before)

    def test_legacy_outer_block_moves_inside_wrapper(self):
        original = '{"items":{"custom":{"action":"true"}},"metadata":42}\n'
        self.menu.write_text("{}\n")
        self.install()
        record = json.loads(self.journal.read_text())
        record["menu_insert"] = "," + MENU
        self.journal.write_text(json.dumps(record))
        offset = original.rfind("}")
        self.menu.write_text(original[:offset] + record["menu_insert"] + original[offset:])
        self.install()
        parsed = jsonc(self.menu.read_text())
        self.assertTrue(WORK_KEYS <= parsed["items"].keys())
        self.assertEqual(set(parsed), {"items", "metadata"})
        uninstall(self.home)
        self.assertEqual(self.menu.read_text(), original)

    def test_edited_owned_blocks_abort_install_and_uninstall_before_writes(self):
        self.install()
        for path, old, new in ((self.menu, "two-bar toggle", "custom toggle"),
                               (self.bindings, "two-bar toggle", "custom toggle")):
            original = path.read_text()
            path.write_text(original.replace(old, new))
            before = self.snapshot()
            for operation in (self.install, lambda: uninstall(self.home)):
                with self.subTest(path=path.name, operation=operation):
                    with self.assertRaisesRegex(ValueError, "edited"):
                        operation()
                    self.assertEqual(self.snapshot(), before)
            path.write_text(original)

    def test_malformed_menu_does_not_write_configuration(self):
        for malformed in ('{"custom":true,,}', '{"custom":1/* gap */2}', '[1,2]', '{,}'):
            with self.subTest(menu=malformed):
                self.menu.write_text(malformed)
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.install()
                self.assertEqual(self.snapshot(), before)


class JsoncRegressionTests(unittest.TestCase):
    def test_strings_are_preserved_while_comments_and_trailing_commas_are_removed(self):
        values = ['https://example.com/a//b', '/* literal */', ',}', ',]',
                  'escaped "quote" and \\ backslash']
        text = '{\n // Comment\n "values": [' + ",".join(map(json.dumps, values)) + ',],\n}'
        self.assertEqual(jsonc(text), {"values": values})


if __name__ == "__main__":
    unittest.main()
