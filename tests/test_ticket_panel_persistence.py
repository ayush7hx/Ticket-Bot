import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cogs import tickets
from utils import store


class FakeBot:
    def __init__(self):
        self.views = []

    def add_view(self, view, message_id=None):
        self.views.append((view, message_id))


class TicketPanelPersistenceTests(unittest.TestCase):
    def test_registers_legacy_custom_categories_without_message_id(self):
        bot = FakeBot()
        configs = {
            "123": {
                "active_categories": ["Custom Help"],
                "panels": [],
            }
        }

        with patch("cogs.tickets.get_all_configs", return_value=configs):
            tickets._register_persistent_views(bot)

        legacy_view = next(
            view for view, message_id in bot.views
            if message_id is None
            and any(
                getattr(item, "custom_id", None) == "panel:custom_help"
                for item in view.children
            )
        )
        self.assertTrue(legacy_view.resolve_categories_from_config)

    def test_legacy_button_resolves_custom_category_from_config(self):
        config = {"active_categories": ["Custom Help"]}

        self.assertEqual(
            tickets._legacy_panel_category(config, "panel:custom_help", "Other"),
            "Custom Help",
        )
        self.assertEqual(
            tickets._legacy_panel_category(config, "panel:open", "Other"),
            "Custom Help",
        )

    def test_restores_button_panel_with_saved_category_ids(self):
        bot = FakeBot()
        configs = {
            "123": {
                "panels": [{
                    "message_id": "456",
                    "type": "button",
                    "categories": ["Custom Help"],
                    "show_main_button": False,
                }]
            }
        }

        with patch("cogs.tickets.get_all_configs", return_value=configs):
            tickets._register_persistent_views(bot)

        view, message_id = next(
            (view, message_id)
            for view, message_id in bot.views
            if message_id == 456
        )
        self.assertEqual(
            [item.custom_id for item in view.children],
            ["panel:custom_help"],
        )

    def test_restores_dropdown_panel_by_message_id(self):
        bot = FakeBot()
        configs = {
            "123": {
                "panels": [{
                    "message_id": "789",
                    "type": "dropdown",
                    "categories": ["Custom Help"],
                }]
            }
        }

        with patch("cogs.tickets.get_all_configs", return_value=configs):
            tickets._register_persistent_views(bot)

        view, message_id = next(
            (view, message_id)
            for view, message_id in bot.views
            if message_id == 789
        )
        self.assertEqual(message_id, 789)
        self.assertEqual(view.children[0].custom_id, "panel2:select")
        self.assertEqual(view.children[0].options[0].value, "Custom Help")

    def test_add_panel_record_preserves_config_and_previous_panels(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            with (
                patch.object(store, "DATA_DIR", data_dir),
                patch.object(store, "CONFIGS_FILE", data_dir / "configs.json"),
            ):
                existing_panel = {"message_id": "456", "type": "button"}
                store.set_config(123, {
                    "panel_title": "Support",
                    "panels": [existing_panel],
                })
                new_panel = {"message_id": "789", "type": "dropdown"}

                store.add_panel_record(123, new_panel)

                config = store.get_config(123)

        self.assertEqual(config["panel_title"], "Support")
        self.assertEqual(config["panels"], [existing_panel, new_panel])


if __name__ == "__main__":
    unittest.main()
