from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_utils.log import LOG
from ovoscope import End2EndTest, get_minicroft


def assert_ordered_subsequence(testcase, msg_types, expected_subsequence):
    """Assert that `expected_subsequence` appears, in order, inside
    `msg_types`. Extra messages interleaved anywhere are tolerated - this
    is intentional: the stop flow is spec-instrumented (ovos.intent.matched,
    skill handler start/complete pairs, etc) and that instrumentation is
    expected to keep growing. Only the topics the stop flow actually needs
    to work are asserted here, not the full/exact message count, since the
    exact legacy positional sequence is tied to a compat bridge slated for
    removal at the next core major.
    """
    remaining = list(expected_subsequence)
    for msg_type in msg_types:
        if remaining and msg_type == remaining[0]:
            remaining.pop(0)
    testcase.assertEqual(
        remaining, [],
        f"❌ required messages {remaining} did not appear in order "
        f"from captured sequence: {msg_types}"
    )


def _matches_intent(msg_type: str, skill_id: str, intent_file: str) -> bool:
    """Check whether ``msg_type`` is the matched-intent event for
    ``intent_file`` (eg. ``StopLaughing``), tolerant of the ``.intent``
    suffix some pipeline plugins keep and others strip.
    """
    prefix = f"{skill_id}:"
    if not msg_type.startswith(prefix):
        return False
    observed = msg_type[len(prefix):]
    observed_base = observed.removesuffix(".intent")
    expected_base = intent_file.removesuffix(".intent")
    return observed_base.lower() == expected_base.lower()


class TestStopNoSkills(TestCase):

    def setUp(self):
        LOG.set_level("DEBUG")
        self.minicroft = get_minicroft([])  # reuse for speed, but beware if skills keeping internal state

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def test_exact(self):
        session = Session("123")
        session.pipeline = ['ovos-stop-pipeline-plugin-high']
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["stop"], "lang": "en-US"},
                          {"session": session.serialize()})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=message,
            expected_messages=[message],
            # the exact positional sequence is coupled to spec instrumentation
            # (handler start/complete pairs, ovos.intent.matched, etc) that is
            # expected to keep growing; assert the required subsequence
            # instead of a hardcoded message count
            test_message_number=False,
        )

        messages = test.execute()
        msg_types = [m.msg_type for m in messages]

        # global stop reached the pipeline and was handled end to end;
        # "mycroft.stop" is the pre-rename legacy topic for what is now
        # "ovos.stop" - it must NOT be emitted a second time alongside it
        assert_ordered_subsequence(
            self, msg_types,
            ["recognizer_loop:utterance", "ovos.intent.matched",
             "stop:global", "ovos.stop", "ovos.utterance.handled"]
        )
        self.assertEqual(
            msg_types.count("ovos.stop"), 1,
            f"❌ expected exactly one 'ovos.stop', got: {msg_types}"
        )
        self.assertNotIn(
            "mycroft.stop", msg_types,
            "❌ legacy 'mycroft.stop' topic should not fire alongside its "
            "'ovos.stop' replacement"
        )

    def test_not_exact_high(self):
        session = Session("123")
        session.pipeline = ['ovos-stop-pipeline-plugin-high']
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["could you stop that"], "lang": "en-US"},
                          {"session": session.serialize()})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=message,
            expected_messages=[message],
            # "complete_intent_failure" was renamed to "ovos.intent.unmatched";
            # ovoscope's capture only ever shows the current spec topic, never
            # the legacy twin, so assert the required subsequence instead
            # of the old exact list
            test_message_number=False,
        )

        messages = test.execute()
        msg_types = [m.msg_type for m in messages]

        assert_ordered_subsequence(
            self, msg_types,
            ["recognizer_loop:utterance", "ovos.intent.unmatched",
             "ovos.utterance.handled"]
        )


class TestStopWithLaughSkill(TestCase):
    """The laugh skill stops random laughing via its own ``StopLaughing``
    adapt intent (requires both the ``Stop`` and ``Laugh`` vocabs), not via
    a killable/``stop()``-based handler. That intent needs the word "laugh"
    alongside "stop", so it cannot match a bare "stop" utterance and does
    not shadow the vanilla global stop.
    """

    SKILL_ID = "ovos-skill-laugh.openvoiceos"

    @classmethod
    def setUpClass(cls):
        LOG.set_level("DEBUG")
        cls.minicroft = get_minicroft([cls.SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _run(self, utterance, pipeline):
        session = Session("123")
        session.pipeline = pipeline
        message = Message("recognizer_loop:utterance",
                          {"utterances": [utterance], "lang": "en-US"},
                          {"session": session.serialize()})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[self.SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=message,
            expected_messages=[message],
            test_message_number=False,
        )
        messages = test.execute()
        return [m.msg_type for m in messages]

    def test_vanilla_stop_not_shadowed_by_laugh(self):
        # the stop pipeline plugin runs alongside the skill's own adapt
        # intent; a bare "stop" must still reach the global stop pipeline
        # and must NOT be caught by the laugh skill's "StopLaughing" intent
        msg_types = self._run(
            "stop",
            ["ovos-stop-pipeline-plugin-high", "ovos-adapt-pipeline-plugin-high"],
        )

        # accept either the current "ovos.stop" topic or its pre-rename
        # legacy twin "mycroft.stop", whichever the installed core emits
        self.assertTrue(
            "ovos.stop" in msg_types or "mycroft.stop" in msg_types,
            f"❌ global stop was not reached: {msg_types}"
        )
        self.assertFalse(
            any(_matches_intent(t, self.SKILL_ID, "StopLaughing") for t in msg_types),
            f"❌ bare 'stop' was shadowed by the laugh skill's own intent: {msg_types}"
        )

        # belt-and-suspenders: even with only the skill's own adapt intent
        # in the pipeline (no stop-pipeline plugin to win on priority), a
        # bare "stop" still must not match "StopLaughing" - it requires
        # both the "Stop" and "Laugh" vocabs, and "stop" alone has no
        # "laugh" in it
        adapt_only_msg_types = self._run("stop", ["ovos-adapt-pipeline-plugin-high"])
        self.assertFalse(
            any(_matches_intent(t, self.SKILL_ID, "StopLaughing") for t in adapt_only_msg_types),
            f"❌ 'StopLaughing' requires only the 'Stop' vocab, no 'Laugh': {adapt_only_msg_types}"
        )

    def test_stop_halts_laugh(self):
        # "stop laughing" is the laugh skill's dedicated stop phrase; it
        # must halt an in-progress random laugh and speak a confirmation
        session = Session("123")
        session.pipeline = ["ovos-adapt-pipeline-plugin-high"]
        start = Message("recognizer_loop:utterance",
                        {"utterances": ["random laugh"], "lang": "en-US"},
                        {"session": session.serialize()})
        End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[self.SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=start,
            expected_messages=[start],
            test_message_number=False,
        ).execute()

        msg_types = self._run("stop laughing", ["ovos-adapt-pipeline-plugin-high"])

        self.assertTrue(
            any(_matches_intent(t, self.SKILL_ID, "StopLaughing") for t in msg_types),
            f"❌ 'stop laughing' did not route to the laugh skill's stop intent: {msg_types}"
        )
        self.assertTrue(
            any("speak" in t for t in msg_types),
            f"❌ expected a spoken confirmation after halting the laugh: {msg_types}"
        )
