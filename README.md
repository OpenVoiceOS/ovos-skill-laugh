# <img src='./res/icon/laugh_icon.png' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> Laugh

Makes Mycroft laugh like a maniac

![](./sshot.png)

## About

Laugh randomly or when requested, gender configurable in settings.json

## Settings

~/.config/ovos/skills/skill-laugh.openvoiceos/settings.json
~/.config/neon/skills/skill-laugh.openvoiceos/settings.json

```json
{
  "gender": "robot", // or "male" or "female"
  "haunted": false, // default true, mine is an evil laugh
  "sounds_dir": "/home/neon/venv/lib/python3.10/site-packages/skill_laugh/sounds", // default on a Neon setup, can be set to anything OVOS/Neon can access
  "__mycroft_skill_firstrun": false
}
```

## Examples

- "Laugh like Alexa"
- "can you laugh"

## Credits

- [@JarbasAl](https://jarbasal.github.io)
- [@mikejgray](https://graywind.org) (revival)
- [SoundBible](http://soundbible.com/suggest.php?q=laugh&x=0&y=0)
- [FreeSound](https://freesound.org/search/?q=female+evil+laugh)

## Category

**Entertainment**

## Tags

#laugh
#funny
#entertainment
#repeating
