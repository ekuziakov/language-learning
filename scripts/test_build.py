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
        name, _ = decoder.raw_decode(edn[match.end():])
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
            self.assertEqual([p.name for p in outputs], ["sample.mochi", "sample-listening.mochi"])
            attachment_names = []
            for index, output in enumerate(outputs):
                with zipfile.ZipFile(output) as archive:
                    self.assertIsNone(archive.testzip())
                    cards = archive_cards(archive.read("data.edn").decode())
                    self.assertEqual(len(cards), 1)
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
                    attachment_names.append(sorted(archive.namelist()))
            self.assertEqual(attachment_names[0], attachment_names[1])
            # Building again must not change card/deck IDs or archive names.
            self.assertEqual(self.build_data(root, data, settings), outputs)

    def test_explicit_ids_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data, settings = self.fixture(root)
            data["cards"][0].update(production_id="OriginalRecall01", listening_id="OriginalAudio01")
            for output, expected in zip(
                self.build_data(root, data, settings), ["OriginalRecall01", "OriginalAudio01"]
            ):
                with zipfile.ZipFile(output) as archive:
                    self.assertIn(expected, archive_cards(archive.read("data.edn").decode()))

    def test_invalid_inputs_rejected(self):
        data = json.loads((PROJECT / "examples/sample.json").read_text())
        for change in (
            lambda d: d.update(cards=[]),
            lambda d: d["cards"][0].update(target=""),
            lambda d: d["cards"][0].update(listening_id=d["cards"][0]["id"]),
            lambda d: d.update(listening_deck_id=d["deck_id"]),
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
