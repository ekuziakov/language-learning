"""Offline structural tests; no speech generation or Mochi installation needed."""

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
    def build_data(self, root, data):
        source = root / "sample.json"
        source.write_text(json.dumps(data, ensure_ascii=False))
        for card in data["cards"]:
            if card.get("image"):
                target = root / card["image"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((PROJECT / card["image"]).read_bytes())

        def fake_audio(text, voice, rate, target):
            target.write_bytes(b"test audio")

        with patch.object(build, "ROOT", root), patch.object(
            build, "make_audio", side_effect=fake_audio
        ), contextlib.redirect_stdout(io.StringIO()):
            build.build(source)
        return root / "exports/sample.mochi"

    def test_all_sets_have_both_directions_and_images(self):
        for source in (PROJECT / "cards").glob("*.json"):
            with self.subTest(source=source.name), tempfile.TemporaryDirectory() as tmp:
                data = json.loads(source.read_text())
                self.assertTrue(data["include_reverse"])
                output = self.build_data(Path(tmp), data)
                with zipfile.ZipFile(output) as archive:
                    self.assertIsNone(archive.testzip())
                    cards = archive_cards(archive.read("data.edn").decode())
                    self.assertEqual(len(cards), 2 * len(data["cards"]))
                    audio = [n for n in archive.namelist() if n.endswith(".mp3")]
                    self.assertEqual(len(audio), len({c["es"] for c in data["cards"]}))
                    for card in data["cards"]:
                        original_listening = card.get("direction") == "audio-ru"
                        reverse_id = card["id"] + ("Recall" if original_listening else "Audio")
                        for card_id, listening in (
                            (card["id"], original_listening),
                            (reverse_id, not original_listening),
                        ):
                            name, content = cards[card_id]
                            front, back = content.split("\n\n---\n\n")
                            self.assertIn(card["note"], back)
                            self.assertIn(card["es"], back)
                            image_side = back if listening else front
                            self.assertIn("@media/img-", image_side)
                            self.assertNotIn("@media/img-", front if listening else back)
                            if listening:
                                self.assertTrue(name.startswith("Аудирование "))
                                self.assertNotIn(card["es"], front)
                                self.assertNotIn(card["ru"], front)
                                self.assertIn(card["ru"], back)
                                self.assertIn("![Аудио]", front)
                            else:
                                self.assertIn(card["ru"], front)
                                self.assertNotIn(card["es"], front)
                                self.assertIn("![Произношение]", back)
                            for attachment in re.findall(r"@media/([^)\s]+)", content):
                                self.assertIn(attachment, archive.namelist())

    def test_generated_ids_are_unique_across_learning_sets(self):
        ids = []
        for source in (PROJECT / "cards").glob("lesson*.json"):
            for card in json.loads(source.read_text())["cards"]:
                ids.extend([
                    card["id"],
                    card["id"] + ("Recall" if card.get("direction") == "audio-ru" else "Audio"),
                ])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 38)

    def test_front_image_rejected_for_listening(self):
        data = json.loads((PROJECT / "cards/lesson-02-listening.json").read_text())
        data["cards"][0]["image_side"] = "front"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "front image"):
                self.build_data(Path(tmp), data)

    def test_generated_id_collision_rejected(self):
        data = json.loads((PROJECT / "cards/lesson-01.json").read_text())
        data["cards"][1]["id"] = data["cards"][0]["id"] + "Audio"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "IDs must be unique"):
                self.build_data(Path(tmp), data)


if __name__ == "__main__":
    unittest.main()
