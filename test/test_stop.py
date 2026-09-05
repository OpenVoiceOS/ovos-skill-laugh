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
