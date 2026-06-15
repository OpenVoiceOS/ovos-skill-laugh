"""E2E intent-routing tests for ovos-skill-laugh.

Run: pytest test/end2end/ -v
"""
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import End2EndTest, get_minicroft

SKILL_ID = "ovos-skill-laugh.openvoiceos"
LANG = "en-US"


class _IntentRoutingMixin:
    """Shared MiniCroft setup."""

    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, 'minicroft', None):
            cls.minicroft.stop()

    def _assert_padacioso(self, utterance: str, intent_file: str):
        intent_msg_type = f"{SKILL_ID}:{intent_file}"
        session = Session(f"e2e-en_us-{intent_file}-{hash(utterance)}")
        session.lang = LANG
        session.pipeline = ["ovos-padacioso-pipeline-plugin-medium"]
        message = Message(
            "recognizer_loop:utterance",
            {"utterances": [utterance], "lang": LANG},
            {"session": session.serialize()},
        )
        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=message,
            activation_points=[intent_msg_type],
            test_msg_context=False,
            expected_messages=[
                message,
                Message(f"{SKILL_ID}.activate", {}, {"skill_id": SKILL_ID}),
                Message(intent_msg_type, {}, {"skill_id": SKILL_ID}),
                Message("mycroft.skill.handler.start", {}, {"skill_id": SKILL_ID}),
                Message("mycroft.skill.handler.complete", {}, {"skill_id": SKILL_ID}),
                Message("ovos.utterance.handled", {}, {"skill_id": SKILL_ID}),
            ],
        )
        test.execute(timeout=30)


class TestPadacioso1_Laugh_intent(_IntentRoutingMixin, TestCase):
    """Padacioso intent: Laugh.intent"""

    def test_can_you_laugh(self):
        self._assert_padacioso(r"can you laugh", r"Laugh.intent")

    def test_evil_laugh(self):
        self._assert_padacioso(r"evil laugh", r"Laugh.intent")

    def test_laugh_like_a_demon(self):
        self._assert_padacioso(r"laugh like a demon", r"Laugh.intent")

    def test_show_me_how_you_laugh(self):
        self._assert_padacioso(r"show me how you laugh", r"Laugh.intent")


class TestPadacioso2_RandomLaugh_intent(_IntentRoutingMixin, TestCase):
    """Padacioso intent: RandomLaugh.intent"""

    def test_random_laugh(self):
        self._assert_padacioso(r"random laugh", r"RandomLaugh.intent")

    def test_laugh_randomly(self):
        self._assert_padacioso(r"laugh randomly", r"RandomLaugh.intent")

    def test_trigger_a_random_laugh(self):
        self._assert_padacioso(r"trigger a random laugh", r"RandomLaugh.intent")


class TestPadacioso3_haunted_intent(_IntentRoutingMixin, TestCase):
    """Padacioso intent: haunted.intent"""

    def test_are_you_haunted(self):
        self._assert_padacioso(r"are you haunted", r"haunted.intent")

    def test_are_you_possessed(self):
        self._assert_padacioso(r"are you possessed", r"haunted.intent")

    def test_do_you_need_an_exorcism(self):
        self._assert_padacioso(r"do you need an exorcism", r"haunted.intent")
