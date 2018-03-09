from mycroft import MycroftSkill, intent_file_handler
from mycroft.util import play_wav
from os import listdir
from os.path import join
import random


class LaughSkillSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        sounds_dir = join(self.root_dir, "sounds")
        self.sounds = [join(sounds_dir, sound) for sound in
                       listdir(sounds_dir) if ".wav" in sound]

    @intent_file_handler("LaughSkill.intent")
    def handle_laugh_skill(self, message):
        play_wav(random.choice(self.sounds))


def create_skill():
    return LaughSkillSkill()

