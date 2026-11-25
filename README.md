# AI-assisted language flashcards for Mochi

English · [Русский](README.ru.md)

Turn small, personalized language lessons into offline [Mochi](https://mochi.cards/)
flashcards with an AI coding assistant. Choose your native and target languages,
describe your goals, and ask the assistant to create a set. The assistant saves
the sources locally and runs the build script; you import the resulting files
into Mochi.

This repository is a reusable workflow, **not a ready-made course or an AI service**.
It includes scripts, assistant instructions, and one tiny format example.
Your profile, plan, cards, and generated media stay local and are ignored by Git.

## What you get

Every set produces **one `.mochi` import file** containing a parent deck and
two subdecks:

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
git clone https://github.com/ekuziakov/language-learning.git
cd language-learning
```

Open this directory in your AI coding assistant.

### 2. Personalize your learning setup

Paste this prompt (replace the placeholders, or ask the assistant to interview you):

> Read AGENTS.md. Help me set up this project. My native language is [language],
> and I want to learn [language / regional variety]. Speak to me and explain
> cards in [language]. My starting level is [level]. My goal is [goal], my
> deadline is [date], and I can study [minutes] a day. Ask any missing questions
> and help me select an installed macOS voice. Propose a step-by-step study plan
> with small sets and a suitable workload, discuss it with me, then save my profile in
> .local/settings.json, personal instructions in .local/INSTRUCTIONS.md, and
> the agreed study plan in .local/PLAN.md. Do not put my personal information
> or learning material in tracked files. Do not generate a large course yet.

By the end of this step, you should have an agreed plan in `.local/PLAN.md`,
not a complete collection of generated cards. The plan guides the order of
topics and the size of each set; adjust it as you learn.

The assistant can run the interactive setup:

```sh
python3 scripts/setup.py
```

Or you can run it yourself. To select the voice first:

```sh
say -v '?'
```

The setup script creates only the profile. Your assistant creates the study plan
with you; running the script alone does not create one.

For non-interactive setup, pass `--native-language`, `--target-language`,
`--voice`, and `--locale`. Optional `--conversation-language` and
`--explanation-language` default to your native language; `--rate` defaults to 145.

Your two languages, voice, and speech rate live in `.local/settings.json`.
The `locale` describes the selected voice's accent; it does not select a voice.
Edit the profile to change settings; setup will not overwrite an existing one.
You can also translate `listening_prompt` there into your preferred language.

### 3. Generate the next set from your plan

> Read my local profile, instructions, and .local/PLAN.md. Generate only the next
> small set from our agreed plan, taking my reported progress into account.
> If the next topic or workload is unclear, agree on it with me first.
> Save the source in cards/ using a stable, unique set name.
> Include useful phrases I will say and things I may hear in reply. Add
> word-by-word explanations, examples for vocabulary, and suitable local images.
> Build one import file with Production and Listening subdecks, verify it,
> and tell me which file to import. Preserve IDs when editing an existing set.
> Record which set was generated and what comes next in my local plan.
> Do not mark it imported or learned until I confirm that.

For example, a set of 5 learning units becomes 5 production cards and 5 listening
cards. You do not need to ask for listening separately: it is generated every time.

### 4. Import the file into Mochi

For a source named `cards/lesson-01.json`, the output is:

```text
exports/lesson-01.mochi
```

Inside Mochi, the set is organized as:

```text
Lesson 01
├── Production
└── Listening
```

Choose Mochi's import option and select that one file. Media is already bundled;
do not attach audio or images separately. Check one card in each direction, play
the audio, and then test playback without internet.

**Updating a deck:** export a backup from Mochi first. Stable IDs do not by
themselves prove that re-importing will update cards without duplicates or preserve
your review schedule. Test repeat imports on a disposable deck before updating
material you have studied. Do not delete a studied deck just to load a new version.
If you have older, separate production/listening files, keep them as backups;
do not import them alongside the combined file.

### 5. Study, report progress, and repeat

Study the current set alongside due reviews. When you are ready for more, tell
the assistant how it went and repeat steps 3–4 for the next small set. You do not
need to generate or import the whole plan upfront.

> I have imported and practiced the current set. Here is what felt easy or
> difficult: [feedback]. Update my local progress and adjust the plan if needed.
> If the workload allows, generate the next small set according to the plan.
> If reviews are piling up, help me consolidate instead of adding more cards.

The assistant cannot see your Mochi review progress automatically; it relies on
what you report. Generating a file, importing it, and learning its contents are
three different milestones.

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

This writes `exports/sample.mochi`, containing both subdecks.
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
| `README.ru.md` | Russian translation of the user guide | Yes |
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
