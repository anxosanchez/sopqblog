"""
tests/test_telegram_notifier.py
================================
Tests unitarios para o notificador de Telegram do Editor de SOPQ // ProcessSim.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.telegram_editor_notifier import TelegramEditorNotifier


class TestTelegramEditorNotifier(unittest.TestCase):
    def setUp(self):
        self.notifier = TelegramEditorNotifier(
            bot_token="fake_bot_token",
            chat_id="fake_chat_id",
            dry_run=True,
        )
        self.sample_post = Path("posts/caso-destilacion-flash.qmd")

    def test_parse_metadata(self):
        metadata = self.notifier.parse_post_metadata(self.sample_post)
        self.assertIn("Separación Flash", metadata["title"])
        self.assertTrue(metadata["has_colab"])
        self.assertIn("Python", metadata["categories"])

    def test_format_notification_message(self):
        metadata = {
            "title": "Simulación de CSTR",
            "subtitle": "Esterificación",
            "authors": ["Laura Gómez", "Anxo Sánchez"],
            "categories": ["DWSIM", "Reactores", "Simulación DWSIM"],
            "is_draft": True,
            "has_dwxml": True,
            "has_hsc": False,
            "has_colab": False,
            "has_video": True,
        }
        msg = self.notifier.format_notification_message(
            metadata,
            pr_url="https://github.com/anxosanchez/sopqblog/pull/2",
            author_contact="laura@uvigo.gal",
        )
        self.assertIn("BORRADOR PROPOSTO", msg)
        self.assertIn("Laura Gómez", msg)
        self.assertIn("Anxo Sánchez", msg)
        self.assertIn("DWSIM", msg)
        self.assertIn("https://github.com/anxosanchez/sopqblog/pull/2", msg)

    def test_dry_run_send(self):
        result = self.notifier.send_message("Test message")
        self.assertTrue(result)

    @patch("urllib.request.urlopen")
    def test_live_send_mocked(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ok": true, "result": {"message_id": 123}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        live_notifier = TelegramEditorNotifier(
            bot_token="test_token",
            chat_id="test_chat",
            dry_run=False,
        )
        success = live_notifier.send_message("Hello from test")
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
