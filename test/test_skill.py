# pylint: disable=missing-docstring
import random
import shutil
from datetime import datetime
from os.path import dirname, join
from typing import Any, Generator
from unittest.mock import Mock, patch

import pytest
from ovos_bus_client import Message
from ovos_plugin_manager.skills import find_skill_plugins
from ovos_utils.fakebus import FakeBus
from ovos_skill_laugh import LaughSkill


@pytest.fixture(scope="session")
def test_skill(
    test_skill_id="ovos-skill-laugh.openvoiceos", bus=FakeBus()
) -> Generator[LaughSkill, Any, None]:
    bus.emitter = bus.ee
    bus.run_forever()
    skill = LaughSkill(skill_id=test_skill_id, bus=bus)
    skill.speak = Mock()
    skill.speak_dialog = Mock()
    skill.play_audio = Mock()
    yield skill
    shutil.rmtree(join(dirname(__file__), "skill_fs"), ignore_errors=True)


@pytest.fixture(scope="function")
def reset_skill_mocks(test_skill: LaughSkill):
    test_skill.speak.reset_mock()
    test_skill.speak_dialog.reset_mock()
    test_skill.play_audio.reset_mock()


class TestLaughSkill:
    @pytest.mark.parametrize(
        "date,expected",
        [
            (datetime(2023, 10, 13), True),
            (datetime(2023, 10, 31), True),
            (datetime(2023, 10, 15), False),
        ],
    )
    def test_special_day(self, test_skill: LaughSkill, date, expected):
        with patch("ovos_skill_laugh.datetime") as mock_date:
            mock_date.today.return_value = date
            assert test_skill.special_day() == expected

    def test_laugh(self, test_skill: LaughSkill, monkeypatch):
        mock_choice = Mock(return_value="test_sound.wav")
        monkeypatch.setattr(random, "choice", mock_choice)

        mock_clear = Mock()
        mock_show_image = Mock()
        mock_play_audio = Mock()
        monkeypatch.setattr(test_skill.gui, "clear", mock_clear)
        monkeypatch.setattr(test_skill.gui, "show_image", mock_show_image)
        monkeypatch.setattr(test_skill, "play_audio", mock_play_audio)

        test_skill.laugh()

        mock_choice.assert_called_once_with(test_skill.sounds[test_skill.gender])
        mock_clear.assert_called()
        mock_show_image.assert_called_once()
        mock_play_audio.assert_called_once_with("test_sound.wav")

    def test_handle_haunted_intent(self, test_skill: LaughSkill, reset_skill_mocks):
        test_skill.haunted = True
        test_skill.handle_haunted_intent(Message(""))
        test_skill.speak_dialog.assert_called_once_with("yes")

    def test_handle_not_haunted_intent(self, test_skill: LaughSkill, reset_skill_mocks):
        test_skill.haunted = False
        test_skill.handle_haunted_intent(Message(""))
        test_skill.speak_dialog.assert_called_once_with("maybe")

    def test_halt_laughing(
        self, test_skill: LaughSkill, reset_skill_mocks, monkeypatch
    ):
        mock_cancel_scheduled_event = Mock()
        monkeypatch.setattr(
            test_skill, "cancel_scheduled_event", mock_cancel_scheduled_event
        )

        test_skill.random_laugh = True
        test_skill.special_day = Mock(return_value=False)
        test_skill.halt_laughing(Message(""))
        mock_cancel_scheduled_event.assert_called_once_with("random_laugh")
        test_skill.speak_dialog.assert_called_once_with("cancel")

    def test_handle_laugh_event(
        self, test_skill: LaughSkill, reset_skill_mocks, monkeypatch
    ):
        mock_cancel_scheduled_event = Mock()
        monkeypatch.setattr(
            test_skill, "cancel_scheduled_event", mock_cancel_scheduled_event
        )

        test_skill.random_laugh = True
        test_skill.handle_laugh_event(Message(""))
        mock_cancel_scheduled_event.assert_called_once_with("random_laugh")

    def test_shutdown(self, test_skill: LaughSkill):
        test_skill.shutdown()


def test_skill_is_a_valid_plugin():
    assert "ovos-skill-laugh.openvoiceos" in find_skill_plugins()


if __name__ == "__main__":
    pytest.main()
