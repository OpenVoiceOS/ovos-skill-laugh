"""End-to-end intent routing tests for the en-US locale.

Each canonical utterance is fired through a real MiniCroft and asserted to
route to the expected intent handler. Assertions cover the intent binding
(drift-proof subset match, not a full expected-message sequence) and, where
the handler speaks, the presence of a ``speak`` response.

The Laugh / RandomLaugh handlers play an audio clip and emit no ``speak``
message, so those tests assert only the intent match.
"""
import unittest

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "ovos-skill-laugh.openvoiceos"
LANG = "en-US"


class TestLaughIntentsEnUS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()

    def _run(self, text):
        session = Session("test-session")
        session.lang = LANG
        session.pipeline = [
            "ovos-adapt-pipeline-plugin-high",
            "ovos-padatious-pipeline-plugin-high",
            "ovos-padacioso-pipeline-plugin-high",
            "ovos-adapt-pipeline-plugin-medium",
            "ovos-padacioso-pipeline-plugin-medium",
            "ovos-adapt-pipeline-plugin-low",
        ]
        utterance = Message(
            "recognizer_loop:utterance",
            {"utterances": [text], "lang": LANG},
            {"session": session.serialize(), "source": "A", "destination": "B"},
        )
        capture = CaptureSession(self.minicroft)
        capture.capture(utterance, timeout=30)
        return [m.msg_type for m in capture.finish()]

    def _assert_intent(self, text, intent, expect_speak=True):
        types = self._run(text)
        self.assertIn(f"{SKILL_ID}:{intent}", types)
        if expect_speak:
            self.assertTrue(any("speak" in t for t in types))

    def test_laugh(self):
        # padatious intent; handler plays audio, emits no speak
        self._assert_intent("can you laugh", "Laugh.intent", expect_speak=False)

    def test_random_laugh(self):
        # padatious intent; handler plays audio + schedules, emits no speak
        self._assert_intent("random laugh", "RandomLaugh.intent", expect_speak=False)

    def test_haunted(self):
        # padatious intent; handler speaks a dialog
        self._assert_intent("are you haunted", "haunted.intent")

    def test_stop_laughing(self):
        # adapt intent (require Stop + Laugh); handler speaks a dialog
        self._assert_intent("stop laughing", "StopLaughing")


if __name__ == "__main__":
    unittest.main()
