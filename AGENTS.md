# Instructions for AI assistants

## First-run setup

- Read `.local/settings.json`, `.local/INSTRUCTIONS.md`, and `.local/PLAN.md`
  if present. These are private local context, never public project defaults.
- If no profile exists, ask for native language, target language, conversation
  language, starting level, goal, deadline, daily time, and preferred regional
  variety. Do not assume a language pair or travel destination.
- Ask which installed macOS TTS voice to use; inspect `say -v '?'` when needed.
  Do not download voices/models, enable paid APIs, or use Mochi TTS without consent.
- Use `scripts/setup.py` to create the profile. Store personalized preferences
  in `.local/INSTRUCTIONS.md` and the study plan in `.local/PLAN.md`.
- Speak to the learner in their chosen conversation language. Keep all tracked
  documentation, code comments, prompts, and test explanations in English.
  Exception: explicitly requested documentation translations such as `README.ru.md`.
  Keep translations aligned with the primary English README and link both versions.

## Authoring

- Obtain agreement on topic and size before creating a new set. Prefer small
  practical sets. Never generate a whole curriculum without approval.
- Sources live in `cards/*.json`; use language-neutral `native` and `target`
  fields. Copy the structure in `examples/sample.json`.
- Keep one small learning unit per source record. Preserve source IDs, deck IDs,
  and existing production/listening IDs. Never assign a different meaning to an ID.
- Every set must produce BOTH production and listening decks. The builder does
  this automatically; do not manually duplicate records for reverse directions.
- Production: native-language cue + image on front; target text, target audio,
  explanation and examples on back.
- Listening: neutral instruction + audio only on front. Target text, native
  meaning, image, and explanation on back. No translation, target text, revealing
  title, or picture clues on the listening front. Test comprehension, not literal
  translation. Include useful things the learner will hear, not only their requests.
- In the learner's chosen explanation language, explain every word, components
  of fixed expressions, verb forms, word order, and omitted pronouns. Match level.
- Single-word cards also need 1–2 short contextual examples with translations.
- Provide a relevant image for every learning unit; use a situation illustration
  for abstract phrases. Reuse suitable local images. Images remain under `images/`.
- Only use images/audio with suitable rights. No scraping restricted recordings.
  Do not describe synthetic speech as a native speaker recording or mislabel its accent.
- Label regional vocabulary explicitly. Avoid native-language phonetic spellings.

## Build, test, and import

- Run `python3 scripts/build.py cards/SET.json`. Every build writes
  `exports/SET.mochi` and `exports/SET-listening.mochi`.
- The learner imports both files into Mochi manually. No account is required.
- Run `python3 scripts/test_build.py`; check actual archive references and audio
  decoding when producing real decks. Report what was and was not tested.
- ZIP/audio checks are NOT a successful Mochi import. Image rendering, playback,
  offline operation, and front/back layout require a separate app test.
- Stable IDs do NOT guarantee safe re-imports or preserved scheduling. Recommend
  exporting a backup and testing updates on a disposable deck before real re-imports.
- Never delete personal sources, media, decks, or review history automatically.

## Public/private boundary

- Track only reusable code, English docs/instructions, and a tiny generic example.
- Never stage `cards/`, `audio/`, `images/`, `exports/`, `.local/`, personal plans,
  account tokens, or local learner settings. They are intentionally ignored.
- Do not force-add ignored files. Check staged contents before committing.
- Do not rewrite published Git history without explicit permission.
