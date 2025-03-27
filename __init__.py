# pylint: disable=invalid-name,attribute-defined-outside-init,unused-argument,arguments-differ
"""Make your voice assistant laugh evilly. Beware... it might be haunted!"""
import random
from datetime import datetime, timedelta
from os import listdir
from os.path import dirname, isdir, join
from typing import Literal, Optional

from ovos_bus_client.message import Message
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder
from ovos_workshop.skills import OVOSSkill


class LaughSkill(OVOSSkill):
    """Make your voice assistant laugh evilly. Beware... it might be haunted!"""

    @property
    def sounds_dir(self) -> str:
        """Path to the sounds directory."""
        default = join(dirname(__file__), "sounds")
        return self.settings.get("sounds_dir", default)

    @property
    def haunted(self) -> bool:
        """Is the voice assistant haunted? By default, it will not be."""
        # Directly return the value from settings, defaulting to True if not set
        return self.settings.get("haunted", True)

    @property
    def gender(self) -> Literal["male", "robot", "female"]:
        """The gender of the ghost in the machine."""
        gender_from_settings = self.settings.get("gender", "robot")
        # Simplified logic
        if gender_from_settings.startswith("f"):
            return "female"
        elif gender_from_settings.startswith("m"):
            return "male"
        return "robot"  # Default and fallback

    @gender.setter
    def gender(self, value: str) -> None:
        """Setter for gender property."""
        self.settings["gender"] = value

    @haunted.setter
    def haunted(self, value) -> None:
        """Setter for haunted property."""
        self.settings["haunted"] = value

    @sounds_dir.setter
    def sounds_dir(self, value) -> None:
        """Setter for sounds_dir property."""
        self.settings["sounds_dir"] = value

    def initialize(self) -> None:
        """Initialize the skill."""
        self.random_laugh = False
        self.sounds = {"male": [], "female": [], "robot": []}

        # Example adjustment: Verifying sound directories exist before populating `sounds`
        for gender in ["male", "female", "robot"]:
            sounds_dir = join(self.sounds_dir, gender)
            if isdir(sounds_dir):  # Ensure the directory exists
                self.sounds[gender] = [
                    join(sounds_dir, sound)
                    for sound in listdir(sounds_dir)
                    if sound.endswith((".wav", ".mp3"))
                ]
            else:
                self.log.warning("Sounds directory does not exist: %s", sounds_dir)
        # stop laughs for speech execution
        self.add_event("speak", self.stop)

        if self.haunted or self.special_day():
            self.random_laugh = True
            self.handle_laugh_event(None)

        self.add_event("skill-laugh.openvoiceos.home", self.handle_homescreen)

    def handle_homescreen(self, message: Message) -> None:  # noqa
        """Handle the homescreen event."""
        self.laugh()

    def special_day(self):
        """Check if today is a special day for spirits."""
        today = datetime.today()
        if today.day == 13 and today.weekday() == 4:
            return True  # friday the 13th
        if today.day == 31 and today.month == 10:
            return True  # halloween
        return False

    def laugh(self):
        """Make the voice assistant laugh."""
        sound = random.choice(self.sounds[self.gender])

        self.gui.clear()
        pic = random.randint(0, 3)
        self.gui.show_image(str(pic) + ".jpg")
        self.play_audio(sound)
        self.gui.clear()

    @intent_handler("haunted.intent")
    def handle_haunted_intent(self, message: Message) -> None:
        """Handle the haunted intent."""
        if self.haunted:
            self.speak_dialog("yes")
        else:
            self.speak_dialog("maybe")

    @intent_handler("Laugh.intent")
    def handle_laugh_intent(self, message: Message) -> None:  # noqa
        """Handle the laugh intent."""
        self.laugh()

    @intent_handler("RandomLaugh.intent")
    def handle_random_intent(self, message: Message) -> None:  # noqa
        """Initiate random laughing."""
        self.log.info("Laughing skill: Triggering random laughing")
        self.random_laugh = True
        self.handle_laugh_event(message)

    @intent_handler(IntentBuilder("StopLaughing").require("Stop").require("Laugh"))
    def halt_laughing(self, message: Message) -> None:
        """Stop the random laughing."""
        self.log.info("Laughing skill: Stopping")
        # if in random laugh mode, cancel the scheduled event
        if self.random_laugh and not self.special_day():
            self.log.info("Laughing skill: Stopping random laugh event")
            self.random_laugh = False
            self.cancel_scheduled_event("random_laugh")
            self.speak_dialog("cancel")
            # if haunted == True it will be back on reboot ;)
        else:
            self.speak_dialog("cancel_fail")

    def handle_laugh_event(self, message: Optional[Message]) -> None:
        """Create a scheduled event for random laughing."""
        if not self.random_laugh:
            return
        self.log.info("Laughing skill: Handling laugh event")
        self.laugh()
        self.cancel_scheduled_event("random_laugh")
        self.schedule_event(
            self.handle_laugh_event,
            datetime.now() + timedelta(seconds=random.randrange(200, 10800)),
            name="random_laugh",
        )
