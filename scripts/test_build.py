"""Public structural tests; no private profile, TTS, or Mochi required."""

import contextlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build

PROJECT = build.ROOT


def archive_cards(edn):
    edn = edn.split(" :cards [", 1)[1]
    decoder = json.JSONDecoder()
    result = {}
    for match in re.finditer(r"\{:id :([A-Za-z0-9]+) :name ", edn):
        name, end = decoder.raw_decode(edn[match.end():])
        if not edn[match.end() + end:].startswith(" :pos "):
            continue
        content_start = edn.index(" :content ", match.end()) + len(" :content ")
        content, _ = decoder.raw_decode(edn[content_start:])
        result[match.group(1)] = (name, content)
    return result


class BuildTests(unittest.TestCase):
    def fixture(self, root):
        data = json.loads((PROJECT / "examples/sample.json").read_text())
        (root / "examples").mkdir()
        (root / "examples/water.svg").write_bytes(
            (PROJECT / "examples/water.svg").read_bytes()
        )
        settings = root / "settings.json"
        settings.write_text(json.dumps({
            "native_language": "English", "target_language": "Spanish",
            "voice": "TestVoice", "rate": 145,
        }))
        return data, settings

    def build_data(self, root, data, settings):
        source = root / "sample.json"
        source.write_text(json.dumps(data, ensure_ascii=False))

        def fake_audio(text, voice, rate, target):
            target.write_bytes(b"test audio")

        with patch.object(build, "ROOT", root), patch.object(
            build, "make_audio", side_effect=fake_audio
        ), contextlib.redirect_stdout(io.StringIO()):
            return build.build(source, settings)

    def test_two_decks_with_correct_fronts_and_shared_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data, settings = self.fixture(root)
            card = data["cards"][0]
            outputs = self.build_data(root, data, settings)
            self.assertEqual([p.name for p in outputs], ["sample.mochi"])
            self.assertFalse((root / "exports/sample-listening.mochi").exists())
            with zipfile.ZipFile(outputs[0]) as archive:
                self.assertIsNone(archive.testzip())
                edn = archive.read("data.edn").decode()
                cards = archive_cards(edn)
                self.assertEqual(len(cards), 2)
                parent_id = data["deck_id"] + "Set"
                self.assertEqual(edn.count(" :parent-id :" + parent_id), 2)
                self.assertIn(
                    "{:id :" + data["deck_id"] + ' :name "Production" :parent-id :' + parent_id,
                    edn,
                )
                self.assertIn(
                    "{:id :" + data["deck_id"] + 'Listening :name "Listening" :parent-id :' + parent_id,
                    edn,
                )
                self.assertEqual(len([n for n in archive.namelist() if n.endswith(".mp3")]), 1)
                self.assertEqual(len([n for n in archive.namelist() if n.endswith(".svg")]), 1)
                for index in range(2):
                    card_id = card["id"] + ("Audio" if index else "")
                    name, content = cards[card_id]
                    front, back = content.split("\n\n---\n\n")
                    self.assertIn(card["note"], back)
                    self.assertIn(card["target"], back)
                    self.assertNotIn(card["target"], front)
                    if index:
                        self.assertTrue(name.startswith("Listening "))
                        self.assertNotIn(card["native"], front)
                        self.assertNotIn("@media/img-", front)
                        self.assertIn("![Audio]", front)
                        self.assertIn("@media/img-", back)
                        self.assertIn(card["native"], back)
                    else:
                        self.assertIn(card["native"], front)
                        self.assertIn("@media/img-", front)
                        self.assertIn("![Audio]", back)
                    for attachment in re.findall(r"@media/([^)\s]+)", content):
                        self.assertIn(attachment, archive.namelist())
            # Building again must not change card/deck IDs or archive names.
            self.assertEqual(self.build_data(root, data, settings), outputs)

    def test_explicit_ids_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data, settings = self.fixture(root)
            data["cards"][0].update(production_id="OriginalRecall01", listening_id="OriginalAudio01")
            data.update(parent_deck_id="OriginalParent01", listening_deck_id="OriginalListenDeck01")
            outputs = self.build_data(root, data, settings)
            with zipfile.ZipFile(outputs[0]) as archive:
                edn = archive.read("data.edn").decode()
                self.assertEqual(set(archive_cards(edn)), {"OriginalRecall01", "OriginalAudio01"})
                self.assertEqual(edn.count(" :parent-id :OriginalParent01"), 2)
                self.assertIn("{:id :OriginalListenDeck01 ", edn)

    def test_invalid_inputs_rejected(self):
        data = json.loads((PROJECT / "examples/sample.json").read_text())
        for change in (
            lambda d: d.update(cards=[]),
            lambda d: d["cards"][0].update(target=""),
            lambda d: d["cards"][0].update(listening_id=d["cards"][0]["id"]),
            lambda d: d.update(listening_deck_id=d["deck_id"]),
            lambda d: d.update(parent_deck_id=d["deck_id"]),
        ):
            changed = json.loads(json.dumps(data))
            change(changed)
            with self.subTest(change=change), self.assertRaises(ValueError):
                build.prepare(changed)

    def test_image_outside_project_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(build, "ROOT", Path(tmp)):
                with self.assertRaises(ValueError):
                    build.image_attachment("../outside.svg")

    def test_language_neutral_fields(self):
        data = json.loads((PROJECT / "examples/sample.json").read_text())
        data["cards"][0].update(native="A generic cue", target="An arbitrary target")
        cards, _, _ = build.prepare(data)
        self.assertEqual(cards[0]["target"], "An arbitrary target")


if __name__ == "__main__":
    unittest.main()
