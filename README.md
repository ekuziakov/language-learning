# AI-assisted language flashcards for Mochi

Turn small, personalized language lessons into offline [Mochi](https://mochi.cards/)
flashcards with an AI coding assistant. Choose your native and target languages,
describe your goals, and ask the assistant to create a set. The assistant saves
the sources locally and runs the build script; you import the resulting files
into Mochi.

This repository is a reusable workflow, **not a ready-made course or an AI service**.
It includes scripts, assistant instructions, and one tiny format example.
Your profile, plan, cards, and generated media stay local and are ignored by Git.

## What you get

Every set produces two importable decks:

| Deck | Before revealing the answer | After revealing the answer |
| --- | --- | --- |
| Production | Native-language cue and illustration | Target-language text, audio, word breakdown, and explanation |
| Listening | Audio and a neutral instruction, with no text or picture clues | Target text, native meaning, illustration, and explanation |

- Short phrases and vocabulary tailored to your goals and level.
- Word-by-word explanations and reasons for the sentence structure.
- Contextual examples with translations for individual vocabulary words.
- Images for vocabulary and situation illustrations for phrases.
- Local synthetic speech, bundled with images inside each `.mochi` archive.
- Offline study after import; no Mochi account or Pro subscription required.
- Reusable audio files and stable card IDs for reproducible builds.

The assistant authors explanations and images; the script packages them. The
script itself does not call an LLM, translate text, or generate illustrations.
Check the language and accent with a reliable reference when accuracy matters.

## Requirements

- **Mochi** desktop or mobile app to study and import decks.
- **macOS** to generate speech with the included backend.
- **Python 3.10+** and **ffmpeg** on your PATH. No Python packages are required.
- An installed macOS voice for your target language (`say -v '?'` lists voices).
- An AI coding assistant that can read this project and run local commands
  (for example OpenCode, Claude Code, or Codex), or manual editing of JSON files.
  Tell it to read `AGENTS.md` if it does not load that file automatically.

The builder uses the macOS `say` command, not Mochi's built-in TTS. Downloading
additional voices, models, or using paid cloud services is optional and requires
your approval. An AI assistant may have its own costs or send prompts to its
provider; "local" here describes saved learning data and speech generation,
not necessarily the AI service.

## Get started

### 1. Clone and open the project

```sh
git clone https://github.com/ekuziakov/spanish-learning.git
cd spanish-learning
```

Open this directory in your AI coding assistant.

### 2. Personalize your learning setup

Paste this prompt (replace the placeholders, or ask the assistant to interview you):

> Read AGENTS.md. Help me set up this project. My native language is [language],
> and I want to learn [language / regional variety]. Speak to me and explain
> cards in [language]. My starting level is [level]. My goal is [goal], my
> deadline is [date], and I can study [minutes] a day. Ask any missing questions
> and help me select an installed macOS voice. Save my profile in
> .local/settings.json, personal instructions in .local/INSTRUCTIONS.md, and
> the agreed study plan in .local/PLAN.md. Do not put my personal information
> or learning material in tracked files. Do not generate a large course yet.

The assistant can run the interactive setup:

```sh
python3 scripts/setup.py
```

Or you can run it yourself. To select the voice first:

```sh
say -v '?'
```

For non-interactive setup, pass `--native-language`, `--target-language`,
`--voice`, and `--locale`. Optional `--conversation-language` and
`--explanation-language` default to your native language; `--rate` defaults to 145.

Your two languages, voice, and speech rate live in `.local/settings.json`.
The `locale` describes the selected voice's accent; it does not select a voice.
Edit the profile to change settings; setup will not overwrite an existing one.
You can also translate `listening_prompt` there into your preferred language.

### 3. Ask for a small set

> Read my local profile, instructions, and plan. Create a small set of [number]
> learning units about [topic], saving the source as cards/[set-name].json.
> Include useful phrases I will say and things I may hear in reply. Add
> word-by-word explanations, examples for vocabulary, and suitable local images.
> Build both production and listening decks, verify the files, and tell me which
> files to import. Preserve IDs when editing an existing set.

For example, a set of 5 learning units becomes 5 production cards and 5 listening
cards. You do not need to ask for listening separately: it is generated every time.

### 4. Import both files into Mochi

For a source named `cards/lesson-01.json`, the output is:

```text
exports/lesson-01.mochi
exports/lesson-01-listening.mochi
```

In Mochi, choose its import option and select each file. Media is already bundled;
do not attach audio or images separately. Check one card in each direction, play
the audio, and then test playback without internet.

**Updating a deck:** export a backup from Mochi first. Stable IDs do not by
themselves prove that re-importing will update cards without duplicates or preserve
your review schedule. Test repeat imports on a disposable deck before updating
material you have studied. Do not delete a studied deck just to load a new version.

## Daily use

Start with due reviews, then add a few new cards if the workload allows.
Say production answers aloud before revealing them. On listening cards, try to
understand the meaning rather than produce a word-for-word translation.
Use short role-play conversations with your assistant to apply the same material.
Text chat alone does not train listening.

## Manual build and test

After creating your local profile, build the included one-word example:

```sh
python3 scripts/build.py examples/sample.json
```

This writes `exports/sample.mochi` and `exports/sample-listening.mochi`.
The sample uses English cues and Spanish target text; choose a compatible voice
in your profile to try it. It is only a format example, not your default language pair.

For your own set:

```sh
python3 scripts/build.py cards/my-set.json
```

Structural tests require no voice, account, private data, or ffmpeg:

```sh
python3 scripts/test_build.py
```

## Files and privacy

| Location | Purpose | In Git? |
| --- | --- | --- |
| `README.md` | User guide | Yes |
| `AGENTS.md` | Universal AI assistant instructions | Yes |
| `scripts/` | Setup, build, and tests | Yes |
| `examples/` | Tiny generic format example | Yes |
| `.local/` | Profile, private instructions, and study plan | No |
| `cards/` | Your editable set sources | No |
| `images/`, `audio/` | Your illustrations and generated speech | No |
| `exports/` | Importable Mochi archives | No |

Git ignore rules are not encryption or a backup. Keep your own backup of local
learning material. Do not share API tokens or force-add personal files.
Earlier project revisions contained the original author's learning data; ignore
rules do not remove material already published in Git history.

## Limitations

- The included speech backend is macOS-only. Other systems need another backend.
- Available languages and regional voices depend on installed macOS voices.
- Speech is synthetic, not a recording of a native speaker.
- `.mochi` files use documented EDN v2 archives and embedded media references.
  Structural tests do not verify rendering, playback, or re-import behavior inside
  Mochi. In particular, test SVG illustrations on your Mochi version.
- No automatic app control, account integration, or cloud synchronization.

For card fields, ID rules, and authoring behavior, see `AGENTS.md` and
`examples/sample.json`.

References: [Mochi import documentation](https://mochi.cards/docs/import-and-export/importing/)
and [archive format](https://mochi.cards/docs/import-and-export/mochi-format-reference/).
