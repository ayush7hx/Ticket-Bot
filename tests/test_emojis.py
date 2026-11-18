import unittest
from unittest.mock import patch

from utils.emojis import _EMOJIS, get_emoji, sync_application_emojis


class FakeResponse:
    def __init__(self, status, payload=None, body=b""):
        self.status = status
        self.payload = payload
        self.body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def json(self):
        return self.payload

    async def read(self):
        return self.body

    async def text(self):
        return str(self.payload)


class FakeSession:
    def __init__(self, emojis, **kwargs):
        self.emojis = emojis
        self.created = 0
        self.downloaded = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def get(self, url):
        if "/applications/" in url:
            items = [{"name": name, "id": emoji_id} for name, emoji_id in self.emojis.items()]
            return FakeResponse(200, {"items": items})
        self.downloaded += 1
        return FakeResponse(200, body=b"\x89PNG\r\n\x1a\nimage")

    def post(self, url, json):
        self.created += 1
        emoji_id = str(1000 + self.created)
        self.emojis[json["name"]] = emoji_id
        return FakeResponse(200, {"name": json["name"], "id": emoji_id})


def run_immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("Mocked emoji requests unexpectedly suspended")


class ApplicationEmojiSyncTests(unittest.TestCase):
    def test_sync_creates_once_then_reuses_application_emojis(self):
        original_emojis = _EMOJIS.copy()
        self.addCleanup(lambda: _EMOJIS.update(original_emojis))
        application_emojis = {}
        sessions = []

        def create_session(**kwargs):
            session = FakeSession(application_emojis, **kwargs)
            sessions.append(session)
            return session

        with patch("utils.emojis.aiohttp.ClientSession", side_effect=create_session):
            created = run_immediate(sync_application_emojis(123, "test-token"))
            created_again = run_immediate(sync_application_emojis(123, "test-token"))

        self.assertEqual(created, 13)
        self.assertEqual(created_again, 0)
        self.assertEqual(sessions[0].downloaded, 13)
        self.assertEqual(sessions[1].downloaded, 0)
        self.assertEqual(get_emoji("success"), "<:success:1001>")
