from mycroft import MycroftSkill, intent_file_handler, intent_handler
from adapt.intent import IntentBuilder
from mycroft.audio import wait_while_speaking, is_speaking
from mycroft.util import play_wav, play_mp3, play_ogg
from os import listdir
from os.path import join, dirname
import random
from datetime import timedelta, datetime


class LaughSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.random_laugh = False
        self.sounds = {"male": [], "female": []}
        if "haunted" not in self.settings:
            self.settings["haunted"] = True
        if "gender" not in self.settings:
            self.settings["gender"] = "male"
        if "sounds_dir" not in self.settings:
            self.settings["sounds_dir"] = join(dirname(__file__), "sounds")
        self.p = None
        self.settings_change_callback = self._fix_gender

    def _fix_gender(self):
        if "f" in self.settings["gender"].lower():
            self.settings["gender"] = "female"
        elif "m" in self.settings["gender"].lower():
            self.settings["gender"] = "male"
        else:
            self.settings["gender"] = "robot"

    def initialize(self):
        sounds_dir = join(self.settings["sounds_dir"], "male")
        self.sounds["male"] = [join(sounds_dir, sound) for sound in
                               listdir(sounds_dir) if
                               ".wav" in sound or ".mp3" in
                               sound]
        sounds_dir = join(self.settings["sounds_dir"], "female")
        self.sounds["female"] = [join(sounds_dir, sound) for sound in
                                 listdir(sounds_dir) if
                                 ".wav" in sound or ".mp3" in sound]
        sounds_dir = join(self.settings["sounds_dir"], "robot")
        self.sounds["robot"] = [join(sounds_dir, sound) for sound in
                                listdir(sounds_dir) if
                                ".wav" in sound or ".mp3" in sound]
        # stop laughs for speech execution
        self.add_event("speak", self.stop)

        if self.settings["haunted"] or self.special_day():
            self.random_laugh = True
            self.handle_laugh_event(None)

        self.add_event('skill-laugh.jarbasskills.home',
                       self.handle_homescreen)

    def handle_homescreen(self, message):
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

        sound = random.choice(self.sounds[self.settings["gender"]])

        self.gui.clear()
        pic = random.randint(0, 3)
        self.gui.show_image(join(dirname(__file__), "ui", "images",
                                 str(pic) + ".jpg"))
        if ".mp3" in sound:
            self.p = play_mp3(sound)
        elif ".ogg" in sound:
            self.p = play_ogg(sound)
        else:
            self.p = play_wav(sound)
        self.p.wait()
        self.gui.clear()

    @intent_file_handler("haunted.intent")
    def handle_haunted_intent(self, message):
        if self.settings["haunted"]:
            self.speak_dialog("yes")
        else:
            self.speak_dialog("maybe")

    @intent_file_handler("Laugh.intent")
    def handle_laugh_intent(self, message):
        self.laugh()

    @intent_file_handler("RandomLaugh.intent")
    def handle_random_intent(self, message):
        # initiate random laughing
        self.log.info("Laughing skill: Triggering random laughing")
        self.random_laugh = True
        self.handle_laugh_event(message)

    @intent_handler(
        IntentBuilder('StopLaughing').require('Stop').require('Laugh'))
    def halt_laughing(self, message):
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

    def handle_laugh_event(self, message):
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

    def stop(self, message=None):
        if self.p is not None:
            self.p.terminate()
            return True
        return False


def create_skill():
    return LaughSkill()
