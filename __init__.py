from mycroft import MycroftSkill, intent_file_handler, intent_handler
from adapt.intent import IntentBuilder
from mycroft.audio import wait_while_speaking, is_speaking
#from mycroft.skills.audioservice import AudioService
from mycroft.util import play_wav, play_mp3
from os import listdir
from os.path import join
import random
from datetime import timedelta, datetime


class LaughSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.random_laugh = False
        self.sounds = []
        self.audio = None
        self.p = None

    def initialize(self):
        sounds_dir = join(self.root_dir, "sounds")
        self.sounds = [join(sounds_dir, sound) for sound in
                       listdir(sounds_dir) if ".wav" in sound or ".mp3" in
                       sound]
        #self.audio = AudioService(self.emitter)
        # stop laughs for speech execution
        self.emitter.on("speak", self.stop_laugh)

    def laugh(self):
        # dont laugh over a speech message
        if is_speaking():
            wait_while_speaking()
        sound = random.choice(self.sounds)
        if ".mp3" in sound:
            self.p = play_mp3(sound)
        else:
            self.p = play_wav(sound)
        # self.audio.play(sound)

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

    def stop_laugh(self):
        #playing_info = self.audio.track_info()
        # TODO most audio backends dont provide the info we need, make a PR
        #  to get sound file path
        #paths = []
        #for path in paths:
        #    if path in self.sounds:
        #        self.audio.stop()
        if self.p is not None:
            self.p.terminate()

    def stop(self):
        # abort current laugh
        self.stop_laugh()
        # stop random laughs
        if self.random_laugh:
            self.halt_laughing(None)

    def shutdown(self):
        # remove speak listener
        self.emitter.remove("speak", self.stop_laugh)
        super(LaughSkill, self).shutdown()


def create_skill():
    return LaughSkill()

