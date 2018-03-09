from mycroft import MycroftSkill, intent_file_handler, intent_handler
from adapt.intent import IntentBuilder
from mycroft.util import play_wav
from os import listdir
from os.path import join
import random
import datetime
from datetime import timedelta, datetime


class LaughSkillSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.random_laugh = False
        self.sounds = []

    def initialize(self):
        sounds_dir = join(self.root_dir, "sounds")
        self.sounds = [join(sounds_dir, sound) for sound in
                       listdir(sounds_dir) if ".wav" in sound]

    def laugh(self):
        # TODO should i use audio service instead? supports more sound file
        #  types
        play_wav(random.choice(self.sounds))

    @intent_file_handler("Laugh.intent")
    def handle_laugh_intent(self, message):
        self.laugh()

    @intent_file_handler("RandomLaugh.intent")
    def handle_random_intent(self, message):
        # initiate random laughing
        self.log.info("Laughing skill: Triggering random laughing")
        self.random_laugh = True
        self.handle_laugh_event(message)

    @intent_handler(IntentBuilder('StopLaughing').require('Stop').require('Laugh'))
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

    def stop(self):
        if self.random_laugh:
            self.halt_laughing(None)


def create_skill():
    return LaughSkillSkill()

