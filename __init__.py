import random
from datetime import datetime, timedelta
from os import listdir
from os.path import dirname, join

from ovos_audio.utils import is_speaking, wait_while_speaking
from ovos_bus_client.message import Message
from ovos_workshop.intents import IntentBuilder
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill


class LaughSkill(OVOSSkill):
    @property
    def sounds_dir(self):
        if not self.settings.get("sounds_dir"):
            self.sounds_dir = join(dirname(__file__), "sounds")
        return self.settings.get("sounds_dir")

    @property
    def haunted(self):
        if not self.settings.get("haunted"):
            self.haunted = True
        return self.settings.get("haunted")

    @property
    def gender(self):
        if not self.settings.get("gender"):
            self.gender = "male"
        if "f" in self.settings.get("gender"):
            self.gender = "female"
        if self.settings.get("gender").startswith("m"):
            self.gender = "male"
        else:
            self.gender = "robot"
        return self.settings.get("gender")

    @gender.setter
    def gender(self, value):
        self.settings["gender"] = value

    @haunted.setter
    def haunted(self, value):
        self.settings["haunted"] = value

    @sounds_dir.setter
    def sounds_dir(self, value):
        self.settings["sounds_dir"] = value

    def initialize(self):
        self.random_laugh = False
        self.sounds = {"male": [], "female": [], "robot": []}
        sounds_dir = join(self.sounds_dir, "male")
        self.sounds["male"] = [join(sounds_dir, sound) for sound in
                               listdir(sounds_dir) if
                               ".wav" in sound or ".mp3" in
                               sound]
        sounds_dir = join(self.sounds_dir, "female")
        self.sounds["female"] = [join(sounds_dir, sound) for sound in
                                 listdir(sounds_dir) if
                                 ".wav" in sound or ".mp3" in sound]
        sounds_dir = join(self.sounds_dir, "robot")
        self.sounds["robot"] = [join(sounds_dir, sound) for sound in
                                listdir(sounds_dir) if
                                ".wav" in sound or ".mp3" in sound]
        # stop laughs for speech execution
        self.add_event("speak", self.stop)

        if self.haunted or self.special_day():
            self.random_laugh = True
            self.handle_laugh_event(None)

        self.add_event('skill-laugh.openvoiceos.home',
                       self.handle_homescreen)

    def handle_homescreen(self, message: Message):
        self.laugh()

    def special_day(self):
        today = datetime.today()
        if today.day == 13 and today.weekday() == 4:
            return True  # friday the 13th
        if today.day == 31 and today.month == 10:
            return True  # halloween
        return False

    def laugh(self):
        # dont laugh over a speech message
        if is_speaking():
            wait_while_speaking()

        sound = random.choice(self.sounds[self.gender])

        self.gui.clear()
        pic = random.randint(0, 3)
        self.gui.show_image(join(dirname(__file__), "ui", "images",
                                 str(pic) + ".jpg"))
        self.play_audio(sound)
        self.gui.clear()

    @intent_handler("haunted.intent")
    def handle_haunted_intent(self, message: Message):
        if self.haunted:
            self.speak_dialog("yes")
        else:
            self.speak_dialog("maybe")

    @intent_handler("Laugh.intent")
    def handle_laugh_intent(self, message: Message):
        self.laugh()

    @intent_handler("RandomLaugh.intent")
    def handle_random_intent(self, message: Message):
        # initiate random laughing
        self.log.info("Laughing skill: Triggering random laughing")
        self.random_laugh = True
        self.handle_laugh_event(message)

    @intent_handler(
        IntentBuilder('StopLaughing').require('Stop').require('Laugh'))
    def halt_laughing(self, message: Message):
        self.log.info("Laughing skill: Stopping")
        # if in random laugh mode, cancel the scheduled event
        if self.random_laugh and not self.special_day():
            self.log.info("Laughing skill: Stopping random laugh event")
            self.random_laugh = False
            self.cancel_scheduled_event('random_laugh')
            self.speak_dialog("cancel")
            # if haunted == True it will be back on reboot ;)
        else:
            self.speak_dialog("cancel_fail")

    def handle_laugh_event(self, message: Message):
        # create a scheduled event to laugh at a random interval between 1
        # minute and half an hour
        if not self.random_laugh:
            return
        self.log.info("Laughing skill: Handling laugh event")
        self.laugh()
        self.cancel_scheduled_event('random_laugh')
        self.schedule_event(self.handle_laugh_event,
                            datetime.now() + timedelta(
                                seconds=random.randrange(200, 10800)),
                            name='random_laugh')

    def stop(self, message: Message):
        self.send_stop_signal("mycroft.audio.service.stop")
        return True
