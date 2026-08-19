from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_utils.log import LOG

from ovoscope import End2EndTest, get_minicroft


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
            expected_messages=[
                message,
                Message("stop.openvoiceos.activate", {}),  # stop pipeline counts as active_skill

                Message("stop:global", {}),  # global stop, no active skill
                Message("mycroft.stop", {}),

                # the stop pipeline plugin reports itself as an active handler
                # that was stopped; no skills are loaded so no other
                # component (persona/common_query/common_play) has anything
                # registered to report back
                Message("stop.openvoiceos.stop.response",
                        {"skill_id": "stop.openvoiceos", "result": False}),

                Message("ovos.utterance.handled", {})
            ]
        )

        test.execute()

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
            expected_messages=[
                message,
                Message("mycroft.audio.play_sound", {"uri": "snd/error.mp3"}),
                Message("complete_intent_failure", {}),
                Message("ovos.utterance.handled", {}),
            ]
        )

        test.execute()
