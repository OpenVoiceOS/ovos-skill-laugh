"""stop_laughing routing for ca-ES, eu-ES and gl-ES.

Each locale's "stop laughing" phrasings route to the skill's own
stop_laughing intent, a laugh request that mentions stopping stays with
laugh.intent, and the locale's bare stop word reaches the global stop
pipeline instead of stop_laughing.
"""
import re

import pytest
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "ovos-skill-laugh.openvoiceos"
LANGS = ["ca-ES", "eu-ES", "gl-ES"]
INTENT_PIPELINE = [
    "ovos-padatious-pipeline-plugin-high",
    "ovos-padacioso-pipeline-plugin-high",
]

STOP_LAUGHING = [
    ("ca-ES", "para de riure"),
    ("ca-ES", "atura la rialla"),
    ("ca-ES", "cancel·la el riure"),
    ("ca-ES", "atura la rialla aleatòria"),
    ("eu-ES", "utzi barre egiteari"),
    ("eu-ES", "gelditu barrea"),
    ("eu-ES", "utzi bertan behera barrea"),
    ("eu-ES", "gelditu ausazko barrea"),
    ("gl-ES", "deixa de rir"),
    ("gl-ES", "detén a risa"),
    ("gl-ES", "cancela o riso"),
    ("gl-ES", "para o riso ao chou"),
]

LAUGH_REQUESTS = [
    ("ca-ES", "per què no rius"),
    ("eu-ES", "barre egin al dezakezu"),
    ("gl-ES", "que che impide rir"),
]

BARE_STOP = [
    ("ca-ES", "para"),
    ("ca-ES", "atura"),
    ("eu-ES", "gelditu"),
    ("gl-ES", "parar"),
]


def _matches_intent(msg_type: str, intent_file: str) -> bool:
    prefix = f"{SKILL_ID}:"
    if not msg_type.startswith(prefix):
        return False
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower().removesuffix(".intent"))
    return norm(msg_type[len(prefix):]) == norm(intent_file)


@pytest.fixture(scope="module")
def minicroft():
    croft = get_minicroft([SKILL_ID], lang=LANGS[0], secondary_langs=LANGS[1:])
    yield croft
    croft.stop()


def _run(minicroft, lang, text, pipeline):
    session = Session("test-session")
    session.lang = lang
    session.pipeline = pipeline
    utterance = Message(
        "recognizer_loop:utterance",
        {"utterances": [text], "lang": lang},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )
    capture = CaptureSession(minicroft)
    capture.capture(utterance, timeout=30)
    return [m.msg_type for m in capture.finish()]


@pytest.mark.parametrize("lang,text", STOP_LAUGHING)
def test_stop_laughing(minicroft, lang, text):
    types = _run(minicroft, lang, text, INTENT_PIPELINE)
    assert any(_matches_intent(t, "stop_laughing") for t in types), types
    assert any("speak" in t for t in types), types


@pytest.mark.parametrize("lang,text", LAUGH_REQUESTS)
def test_laugh_request_stays_with_laugh(minicroft, lang, text):
    types = _run(minicroft, lang, text, INTENT_PIPELINE)
    assert any(_matches_intent(t, "laugh") for t in types), types
    assert not any(_matches_intent(t, "stop_laughing") for t in types), types


@pytest.mark.parametrize("lang,text", BARE_STOP)
def test_bare_stop_goes_to_stop_pipeline(minicroft, lang, text):
    types = _run(minicroft, lang, text,
                 ["ovos-stop-pipeline-plugin-high"] + INTENT_PIPELINE)
    assert "ovos.stop" in types or "mycroft.stop" in types, types
    assert not any(_matches_intent(t, "stop_laughing") for t in types), types

    intent_only = _run(minicroft, lang, text, INTENT_PIPELINE)
    assert not any(_matches_intent(t, "stop_laughing") for t in intent_only), intent_only
