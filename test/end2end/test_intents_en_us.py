"""End-to-end intent-routing tests for ovos-skill-laugh (en-US).

Each case feeds an utterance through a MiniCroft stack running the padacioso
pipeline and asserts it routes to the expected ``.intent`` handler. Coverage
spans the on-demand laugh query (bare and the ``laugh like a demon`` variant),
the random-laugh trigger, and a negative that must reach no handler.

A single MiniCroft is shared across the class so the skill loads once. The
skill is pre-configured with ``haunted`` disabled so it does not fire its
random-laugh GUI side effect on load, keeping the run focused on intent
routing.

Run: pytest test/end2end/ -v
"""
import json
import os
import time
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_config.locations import get_xdg_config_save_path
from ovoscope import get_minicroft

SKILL_ID = "ovos-skill-laugh.openvoiceos"
LANG = "en-US"

# The .intent resources are padacioso samples. Exact expansions score in the
# -high band while looser variants land lower, so register all three bands.
PIPELINE = [
    "ovos-padacioso-pipeline-plugin-high",
    "ovos-padacioso-pipeline-plugin-medium",
    "ovos-padacioso-pipeline-plugin-low",
]

_LOCALE_VOCAB = os.path.join(
    os.path.dirname(__file__), "..", "..", "locale", "en-US", "vocab"
)


def _intent_exists(intent_file: str) -> bool:
    return os.path.isfile(os.path.join(_LOCALE_VOCAB, intent_file))


class TestLaughIntents(TestCase):
    """Per-utterance intent routing for the en-US laugh skill."""

    @classmethod
    def setUpClass(cls):
        settings_path = os.path.join(
            get_xdg_config_save_path(), "skills", SKILL_ID, "settings.json"
        )
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w") as f:
            json.dump({"haunted": False}, f)
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()

    def _route(self, utterance: str, intent_file: str, timeout: float = 15.0):
        """Emit *utterance* and return whether it reached ``intent_file``."""
        intent_msg_type = f"{SKILL_ID}:{intent_file}"
        matched = []
        handler = lambda msg: matched.append(msg)
        self.minicroft.bus.on(intent_msg_type, handler)
        try:
            session = Session(f"e2e-en_us-{intent_file}-{hash(utterance)}")
            session.lang = LANG
            session.pipeline = PIPELINE
            self.minicroft.bus.emit(Message(
                "recognizer_loop:utterance",
                {"utterances": [utterance], "lang": LANG},
                {"session": session.serialize()},
            ))
            deadline = time.monotonic() + timeout
            while not matched and time.monotonic() < deadline:
                time.sleep(0.2)
        finally:
            self.minicroft.bus.remove(intent_msg_type, handler)
        return bool(matched)

    def assert_matches(self, utterance: str, intent_file: str):
        self.assertTrue(
            self._route(utterance, intent_file),
            f"{utterance!r} did not route to {intent_file}",
        )

    def assert_no_match(self, utterance: str):
        for intent_file in ("laugh.intent", "random_laugh.intent", "haunted.intent"):
            self.assertFalse(
                self._route(utterance, intent_file, timeout=6.0),
                f"{utterance!r} unexpectedly routed to {intent_file}",
            )

    def test_can_you_laugh(self):
        self.assert_matches("can you laugh", "laugh.intent")

    def test_laugh_like_a_demon(self):
        self.assert_matches("laugh like a demon", "laugh.intent")

    def test_laugh_randomly(self):
        self.assert_matches("laugh randomly", "random_laugh.intent")

    def test_unrelated_utterance_no_match(self):
        self.assert_no_match("what is the meaning of life")
