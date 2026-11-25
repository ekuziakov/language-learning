#!/usr/bin/env python3
"""Create an ignored, local learner profile. Run interactively or use flags."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-language")
    parser.add_argument("--target-language")
    parser.add_argument("--voice")
    parser.add_argument("--locale")
    parser.add_argument("--conversation-language")
    parser.add_argument("--explanation-language")
    parser.add_argument("--rate", type=int, default=145)
    args = parser.parse_args()
    destination = ROOT / ".local/settings.json"
    if destination.exists():
        parser.error("A local profile already exists. Edit .local/settings.json instead.")
    if args.rate <= 0:
        parser.error("--rate must be positive")
    settings = {"rate": args.rate}
    for field, label in (
        ("native_language", "Your native language"),
        ("target_language", "The language you want to learn"),
        ("voice", "Installed macOS voice (run: say -v '?')"),
        ("locale", "Voice locale / accent, for example es-MX"),
    ):
        value = getattr(args, field) or input(label + ": ").strip()
        if not value:
            parser.error(f"{field} cannot be empty")
        settings[field] = value
    settings["listening_prompt"] = "Listen. What does it mean?"
    settings["conversation_language"] = args.conversation_language or settings["native_language"]
    settings["explanation_language"] = args.explanation_language or settings["native_language"]
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved local settings to {destination}")
    print("Ask your AI assistant to personalize .local/INSTRUCTIONS.md and .local/PLAN.md.")


if __name__ == "__main__":
    main()
