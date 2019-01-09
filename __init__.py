"""
skill laugh

Copyright (C) 2018 JarbasAI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

"""

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
        MycroftSkill.__init__(self)
        self.random_laugh = False
        self.sounds = {"male": [], "female": []}
        if "gender" not in self.settings:
            self.settings["gender"] = "male"
        if "sounds_dir" not in self.settings:
            self.settings["sounds_dir"] = join(dirname(__file__), "sounds")
        self.p = None
        self.settings.set_changed_callback(self._fix_gender)

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
        self.add_event("speak", self.stop_laugh)

    def laugh(self):
        # dont laugh over a speech message
        if is_speaking():
            wait_while_speaking()

        sound = random.choice(self.sounds[self.settings["gender"]])
        if ".mp3" in sound:
            self.p = play_mp3(sound)
        elif ".ogg" in sound:
            self.p = play_ogg(sound)
        else:
            self.p = play_wav(sound)

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
        if self.random_laugh:
            self.log.info("Laughing skill: Stopping random laugh event")
            self.random_laugh = False
            self.cancel_scheduled_event('random_laugh')
            self.speak_dialog("cancel")
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
                                seconds=random.randrange(60, 1800)),
                            name='random_laugh')

    def stop_laugh(self):
        if self.p is not None:
            self.p.terminate()
            return True
        return False

    def stop(self):
        # abort current laugh
        stopped = self.stop_laugh()
        # stop random laughs
        if self.random_laugh:
            self.halt_laughing(None)
            stopped = True
        return stopped


def create_skill():
    return LaughSkill()
