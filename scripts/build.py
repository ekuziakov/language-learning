#!/usr/bin/env python3
"""Build an offline Mochi deck using macOS speech. No Python dependencies."""

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
    # JSON string escapes used here are also valid EDN string escapes.
    return json.dumps(value, ensure_ascii=False)


def keyword(value):
    if not re.fullmatch(r"[A-Za-z0-9]{8,}", value):
        raise ValueError(f"ID must contain at least 8 ASCII letters/digits: {value!r}")
    return ":" + value


def audio_name(text, voice, rate):
    settings = json.dumps([text, voice, rate], ensure_ascii=False).encode()
    return "es-" + hashlib.sha256(settings).hexdigest()[:20] + ".mp3"


def make_audio(text, voice, rate, target):
    if target.exists():
        return
    for command in ("say", "ffmpeg"):
        if not shutil.which(command):
            raise RuntimeError(f"Required command not found: {command}")
    with tempfile.TemporaryDirectory(prefix="spanish-", dir=target.parent) as tmp:
        raw = Path(tmp) / "speech.aiff"
        encoded = Path(tmp) / "speech.mp3"
        subprocess.run(
            ["say", "-v", voice, "-r", str(rate), "-o", str(raw), text],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(raw),
             "-codec:a", "libmp3lame", "-q:a", "2", str(encoded)],
            check=True,
        )
        encoded.replace(target)


def build(source):
    data = json.loads(source.read_text())
    voice, rate = data["voice"], data["rate"]
    deck_id = keyword(data["deck_id"])
    cards = list(data["cards"])
    if data.get("include_reverse"):
        for card in data["cards"]:
            reverse = dict(card)
            listening = card.get("direction", "ru-es") == "ru-es"
            reverse["id"] = card["id"] + ("Audio" if listening else "Recall")
            reverse["direction"] = "audio-ru" if listening else "ru-es"
            reverse["image_side"] = "back" if listening else "front"
            cards.append(reverse)
    if not cards or len({card["id"] for card in cards}) != len(cards):
        raise ValueError("The deck must be nonempty and card IDs must be unique")
    for card in cards:
        keyword(card["id"])
        if not card["ru"].strip() or not card["es"].strip():
            raise ValueError("Both ru and es must be nonempty")
        if card.get("direction", "ru-es") not in {"ru-es", "audio-ru"}:
            raise ValueError("Direction must be ru-es or audio-ru")
        if card.get("image_side", "back") not in {"front", "back"}:
            raise ValueError("Image side must be front or back")
        if (card.get("direction") == "audio-ru" and card.get("image")
                and card.get("image_side", "back") == "front"):
            raise ValueError("Listening cards must not have a front image")
    media = ROOT / "audio"
    exports = ROOT / "exports"
    media.mkdir(exist_ok=True)
    exports.mkdir(exist_ok=True)
    attachments, entries = {}, []
    for index, card in enumerate(cards):
        filename = audio_name(card["es"], voice, rate)
        path = media / filename
        make_audio(card["es"], voice, rate, path)
        attachments[filename] = path
        # @media is the legacy archive syntax, explicitly still supported by Mochi.
        content = (
            f'{card["ru"]}\n\n---\n\n'
            f'## {card["es"]}\n\n'
            f'![Произношение](@media/{filename})'
        )
        listening = card.get("direction") == "audio-ru"
        if listening:
            content = (
                f'Прослушай реплику. Что она означает?\n\n'
                f'![Аудио](@media/{filename})\n\n---\n\n'
                f'## {card["es"]}\n\n{card["ru"]}'
            )
        if card.get("image"):
            image = (ROOT / card["image"]).resolve()
            image.relative_to(ROOT.resolve())
            if image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
                raise ValueError(f"Unsupported image format: {image}")
            image_name = "img-" + hashlib.sha256(image.read_bytes()).hexdigest()[:20] + image.suffix.lower()
            attachments[image_name] = image
            image_markdown = f"![](@media/{image_name})"
            if card.get("image_side", "back") == "front":
                content = content.replace("\n\n---\n\n", f"\n\n{image_markdown}\n\n---\n\n", 1)
            else:
                content += f"\n\n{image_markdown}"
        if card.get("note"):
            content += "\n\n" + card["note"]
        if card.get("tags"):
            content += "\n\n" + " ".join("#" + tag for tag in card["tags"])
        entries.append(
            "{:id " + keyword(card["id"])
            + " :name " + edn_string(f"Аудирование {index + 1}" if listening else card["es"])
            + " :pos " + edn_string(f"{index:08d}")
            + " :content " + edn_string(content) + "}"
        )
    edn = (
        "{:version 2 :decks [{:id " + deck_id
        + " :name " + edn_string(data["deck_name"])
        + " :cards [\n" + "\n".join(entries) + "\n]}]}\n"
    )
    output = exports / (source.stem + ".mochi")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("data.edn", edn)
        for name, path in attachments.items():
            archive.write(path, name)
    print(f"{output}: {len(entries)} card(s), {len(attachments)} attachment(s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=ROOT / "cards/test.json")
    build(parser.parse_args().source.resolve())
