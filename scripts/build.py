#!/usr/bin/env python3
"""Build one Mochi archive with production and listening subdecks using local TTS."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def edn_string(value):
    return json.dumps(value, ensure_ascii=False)


def keyword(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9]{8,}", value):
        raise ValueError(f"ID must contain at least 8 ASCII letters/digits: {value!r}")
    return ":" + value


def audio_name(text, voice, rate):
    settings = json.dumps([text, voice, rate], ensure_ascii=False).encode()
    return "tts-" + hashlib.sha256(settings).hexdigest()[:20] + ".mp3"


def make_audio(text, voice, rate, target):
    if target.exists():
        return
    for command in ("say", "ffmpeg"):
        if not shutil.which(command):
            raise RuntimeError(f"Required command not found: {command}")
    with tempfile.TemporaryDirectory(prefix="mochi-", dir=target.parent) as tmp:
        raw = Path(tmp) / "speech.aiff"
        encoded = Path(tmp) / "speech.mp3"
        subprocess.run(
            ["say", "-v", voice, "-r", str(rate), "-o", str(raw), text], check=True,
        )
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(raw),
             "-codec:a", "libmp3lame", "-q:a", "2", str(encoded)], check=True,
        )
        encoded.replace(target)


def load_settings(path):
    settings = json.loads(path.read_text())
    for field in ("native_language", "target_language", "voice"):
        if not isinstance(settings.get(field), str) or not settings[field].strip():
            raise ValueError(f"Missing setting: {field}")
    rate = settings.get("rate", 145)
    if type(rate) is not int or rate <= 0:
        raise ValueError("Speech rate must be a positive integer")
    settings["rate"] = rate
    return settings


def prepare(data):
    """Validate all IDs before generating media; keep each unit in one source record."""
    if not data.get("cards"):
        raise ValueError("The deck must contain at least one card")
    production_id = data["deck_id"]
    listening_id = data.get("listening_deck_id", production_id + "Listening")
    parent_id = data.get("parent_deck_id", production_id + "Set")
    for deck_id in (parent_id, production_id, listening_id):
        keyword(deck_id)
    if len({parent_id, production_id, listening_id}) != 3:
        raise ValueError("Parent, production and listening deck IDs must differ")
    if not isinstance(data.get("deck_name"), str) or not data["deck_name"].strip():
        raise ValueError("A nonempty deck_name is required")
    cards, ids = [], []
    for item in data["cards"]:
        card = dict(item)
        for field in ("native", "target"):
            if not isinstance(card.get(field), str) or not card[field].strip():
                raise ValueError(f"Each card needs nonempty {field} text")
        card["production_id"] = card.get("production_id", card["id"])
        card["listening_id"] = card.get("listening_id", card["id"] + "Audio")
        for field in ("id", "production_id", "listening_id"):
            keyword(card[field])
        ids.extend([card["production_id"], card["listening_id"]])
        cards.append(card)
    if len(ids) != len(set(ids)):
        raise ValueError("Card IDs must be unique across both directions")
    if len({c["id"] for c in cards}) != len(cards):
        raise ValueError("Source card IDs must be unique")
    return cards, production_id, listening_id


def image_attachment(relative_path):
    image = (ROOT / relative_path).resolve()
    image.relative_to(ROOT.resolve())
    if image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        raise ValueError(f"Unsupported image format: {image}")
    name = "img-" + hashlib.sha256(image.read_bytes()).hexdigest()[:20] + image.suffix.lower()
    return name, image


def write_archive(output, decks, attachments):
    serialized = []
    for deck in decks:
        content = "{:id " + keyword(deck["id"]) + " :name " + edn_string(deck["name"])
        if deck.get("parent_id"):
            content += " :parent-id " + keyword(deck["parent_id"])
        content += " :cards [\n" + "\n".join(deck["entries"]) + "\n]}"
        serialized.append(content)
    edn = "{:version 2 :decks [\n" + "\n".join(serialized) + "\n]}\n"
    # Build a complete archive before replacing an existing output.
    with tempfile.TemporaryDirectory(prefix="mochi-", dir=output.parent) as tmp:
        archive_path = Path(tmp) / output.name
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("data.edn", edn)
            for name, path in attachments.items():
                archive.write(path, name)
        archive_path.replace(output)


def build(source, settings_path=None):
    source = Path(source)
    settings = load_settings(settings_path or ROOT / ".local/settings.json")
    data = json.loads(source.read_text())
    cards, production_id, listening_id = prepare(data)
    # Validate images before starting speech generation.
    images = {
        card["id"]: image_attachment(card["image"]) if card.get("image") else None
        for card in cards
    }
    media, exports = ROOT / "audio", ROOT / "exports"
    media.mkdir(exist_ok=True)
    exports.mkdir(exist_ok=True)
    attachments, production, listening = {}, [], []
    for index, card in enumerate(cards):
        filename = audio_name(card["target"], settings["voice"], settings["rate"])
        path = media / filename
        make_audio(card["target"], settings["voice"], settings["rate"], path)
        attachments[filename] = path
        image_markdown = ""
        if images[card["id"]]:
            name, image = images[card["id"]]
            attachments[name] = image
            image_markdown = f"\n\n![](@media/{name})"
        notes = "\n\n" + card["note"] if card.get("note") else ""
        if card.get("tags"):
            notes += "\n\n" + " ".join("#" + tag for tag in card["tags"])
        content = (
            card["native"] + image_markdown + "\n\n---\n\n"
            + f'## {card["target"]}\n\n![Audio](@media/{filename})' + notes
        )
        prompt = settings.get("listening_prompt", "Listen. What does it mean?")
        audio_content = (
            f'{prompt}\n\n![Audio](@media/{filename})\n\n---\n\n'
            + f'## {card["target"]}\n\n{card["native"]}' + image_markdown + notes
        )
        for entries, card_id, name, body in (
            (production, card["production_id"], card["target"], content),
            (listening, card["listening_id"], f"Listening {index + 1}", audio_content),
        ):
            entries.append(
                "{:id " + keyword(card_id)
                + " :name " + edn_string(name)
                + " :pos " + edn_string(f"{index:08d}")
                + " :content " + edn_string(body) + "}"
            )
    parent_id = data.get("parent_deck_id", production_id + "Set")
    decks = [
        {"id": parent_id, "name": data["deck_name"], "entries": []},
        {"id": production_id, "name": data.get("production_deck_name", "Production"),
         "parent_id": parent_id, "entries": production},
        {"id": listening_id, "name": data.get("listening_deck_name", "Listening"),
         "parent_id": parent_id, "entries": listening},
    ]
    output = exports / (source.stem + ".mochi")
    write_archive(output, decks, attachments)
    print(f"{output}: {len(cards) * 2} cards in 2 subdecks, {len(attachments)} attachments")
    return [output]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="A deck JSON file, usually in cards/")
    parser.add_argument("--settings", type=Path, default=ROOT / ".local/settings.json")
    args = parser.parse_args()
    build(args.source, args.settings)
