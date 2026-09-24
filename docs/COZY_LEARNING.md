# Lamplight: cozy learning build

Updated 2026-09-09. This supersedes the earlier single-room fantasy art direction.

Run `rtk python run_lamplight.py` to play, or add `--editor` and press F5 to work
in Godot. The native game uses a local Python service for saves, campaign rules
and explicitly requested AI calls.

## Play loop

Read an English summary at the library, study it, and answer its two learning
questions, one at a time. The service picks the current question, so the client
cannot skip ahead. An incorrect answer explains the idea without spending a day
or resources. Answering both masters the summary and gives one reputation and one
paper; retries cannot farm rewards. Mastered summaries rotate through practice
questions. Saves mastered under the earlier one-question check stay mastered.
Fourteen original summaries have twenty-eight authored questions.
Summaries are identified as summaries, not complete editions or quotations.

Walk or click between four connected locations. The library holds Margot, Miso,
the summaries, the protagonist's laptop and the time recorder. Noor is in the
town square. Jules works at the print shop, which contains the writing and
postal desks. Ada and Elias are in the garden, alongside the period reading
circle. Doors and paths work with mouse interaction or E; the village map also
shows actual pixel geography, roads, a river/bridge and location pins. Click a pin to follow the connected paths through the square. Location, discoveries and learning progress persist.

At the garden circle, discuss a living period thinker's studied work through
claim, evidence and challenge prompts. These are explicitly fictional educational
encounters. The qualified AI receives only era-eligible studied summaries and asks questions
for the player; they do not grade free-form reasoning. Save a discussion note,
make a garden observation, and develop those into your own writing.

## Computer and AI

The computer and writing desk support study notes, articles and letters through
five saved steps: question, evidence, outline, draft and revision. Choose a working
title and up to eight sources, write one step, and ask Margot to review it. Feedback
and an optional example appear beside the editor. A successful review enables
**Approve & continue**; edits invalidate that approval. Revisiting an earlier step
keeps all later text but requires new reviews. The final approval creates one new
manuscript; it does not submit or award resources. Finish an active workshop before
crossing to another era. Manual manuscripts and previous saves remain available.

Steps autosave and survive restart or AI failure. Progress counts approved steps;
AI requests show an animated waiting indicator, the current task and elapsed time.
Reduced motion disables the animation and text reveal. The editor uses a readable
body font, with separate companion feedback and collapsible sources/approved notes.
The legacy `ai_generate` API remains available, but the native creation UI uses
the supervised workshop.

Campaign generation accepts only studied, era-eligible sources from its own
slot. The prompt distinguishes summaries from full works, requests source
markers and forbids invented quotations/page numbers. The computer also offers
AI correspondence with studied thinkers active in that era. Generated historical
dialogue is fiction; prompt grounding is not a guarantee of historical accuracy.

AI setup is available from the title, settings or computer. For local inference,
install Ollama, download a chat model and enter its exact installed model ID.
The default API base is `http://localhost:11434/v1`. Hosted providers need an
HTTPS chat-completions-compatible endpoint, model ID and their own key.
The [Ollama compatibility documentation](https://docs.ollama.com/api/openai-compatibility)
describes that local endpoint.

AI is mandatory in every native mode. **Connect & benchmark** sends three
small synthetic tasks to the selected model. Scores cover source grounding,
period/evidence rules and gameplay planning. Passing requires at least 80/100,
75 per task and every critical answer correct. The UI reports failed checks and
observed response time. This is a small qualification screen, not a validated
measure of general intelligence or literary quality; prose checks cover format
and diversity. Rate limits/authentication/transport failures do not establish
that a model is weak. Retry or change providers after these failures.

Free options linked from setup: [Groq free tier](https://console.groq.com/docs/rate-limits),
[specific OpenRouter free models](https://openrouter.ai/collections/free-models),
or local Ollama (no inference API fee; requires hardware and a downloaded model).
Hosted quotas and availability vary. Use a specific model ID; random routers
such as `openrouter/free` cannot carry a qualification for a stable model.

Keys entered in the game stay in launcher memory. `LAMPLIGHT_AI_KEY` is an
optional environment alternative; keys are never written to save files.
Changing setup invalidates qualification; restarting the launcher requires
another benchmark. The last report is saved for reference, not reused as proof.
Opt-in `--hyper` (or `LAMPLIGHT_AUTO_HYPER=1` in `.env`) preloads Qwen Max
with the existing HyperCharm key. It makes no provider requests before the game
opens; run the benchmark from AI setup, with visible progress. `--no-hyper` skips
preloading. Qualification is still required once per launcher session.
Garden discussions now require successful AI
responses before progress is recorded. Failed requests never spend resources.
The server blocks unqualified gameplay, including direct API attempts; recovery
reads and manuscript saving remain available.

Only the submitted prompt and authorized source excerpts are sent. A manuscript
is not sent automatically. Responses have size/time bounds, redirects are not
followed, and errors preserve existing documents. Remote AI needs a live provider;
automated verification uses mocked responses, not paid model calls.

Workshop reviews send the current step and its approved earlier steps, plus the
selected excerpts. Each review evaluates the player's saved text, not the optional
AI suggestion. Unknown source markers block approval at evidence/draft/revision.
AI review is editorial guidance, not independent verification of factual accuracy.

The footer and **AI usage** screen expose local request counts, successes/failures,
response times and tokens, including benchmark requests. Totals survive restart in
`ai_usage.json`; the last 20 requests record model, timestamp and latency without
keys or text. Provider-reported tokens and estimates for missing usage are separate.
The connection does not supply account balance or billed cost. Older requests cannot
be reconstructed; failed calls may consume usage the provider does not report.

For an explicit live comparison using this project's existing HyperCharm setup:

```powershell
rtk python bench_lamplight.py --models gemma-4-26b-a4b-it deepseek-v4-flash qwen3.8-max --repeat 2
```

The runner reads `AW_API_KEY` and `AW_BASE_URL` from the environment or project
`.env`. Each trial uses the game's scorer and HTTP transport: 700 output tokens,
25-second read timeout, no retries or provider fallback. All models receive the
same synthetic tasks (`--seed`, default 42); the game still randomizes each trial.
Version 2 explicitly requests brackets on source markers without relaxing checks.
Truncated responses are rejected rather than accepted as complete gameplay text.

Timestamped `output/lamplight-bench-*/` directories contain `tasks.json`, raw replies
and per-request timings in `requests.jsonl`, and scores/failed checks in
`report.json`. Results are saved after each trial; completed replies survive later
request failures. Connection, malformed-response and token-limit errors have
`request_error` status with no quality score. Exit status is 0 only when every
trial qualifies. Existing output directories are never overwritten.
The runner uses temporary saves, never qualifies the running game, and never
writes the key to results. These small samples measure task fit under the game's
limits, not a general model ranking or a guarantee of future availability.
See the [measured HyperCharm results](AI_BENCHMARK.md) for the live trials.

## Story and tutorial

Only the protagonist traveled from 2026, with their laptop in a satchel. The
villagers are ordinary people of their own time. The damaged experimental
recorder supplies the science-fiction premise; everyday play is reading,
conversation, exploration and writing. Margot offers a desk and a place to stay.

Seven short contextual lessons introduce movement, reading, the map, computer,
writing, mail and recorder. Dismissals persist per slot; movement/travel also
complete their relevant tips. Replay them from the notebook. The HUD shows only
the year and current objective initially, revealing notebook/map controls as
the player progresses. Resource details live in the notebook; submission controls
are collapsed in the writer. Pixel icons and the pixel font extend across the UI,
with the readable-font option retained. Panels/travel animate unless motion is off.
People have a shared 52-unit height and gentle, walkable-area strolls; their click
targets follow the sprites. The player uses the same scale, with a smaller cat.

The journal advances from movement and introductions through reading, a learning
check, exploration, discussion, a short learning note and a published article.
The later recorder steps apply a different source-based question in each era.
Seven chapter introductions explain the changing generations; the final return
goes to 2026. Mastery of the featured source, a period discussion, a filed note,
recorder calibration and existing commission/resource requirements are needed
to cross. Walking, conversation and practice are free of calendar pressure.

## Presentation and verification

Thirteen dedicated pixel-art portraits cover the five human residents, Miso,
and all seven historical debate partners. They appear in resident dialogue,
the reading circle, debate replies, postal recipients and computer correspondence.
The computer offers all five human readers' existing AI roles. Historical
portraits only appear as conversation partners when their era permits it;
debates still require studying the relevant summary first. Art is bundled in
`godot/assets/portraits/`, with exact prompts in its README. Missing portrait
files do not prevent reading or operating the conversation.

Original cozy environment and character atlases replace the dark fantasy room.
The UI uses paper panels, green focus borders, brown text and a bundled pixel
font, with a readable-font option. Keyboard movement, click pathfinding, running,
character animation, soft contact shadows, ambient particles, piano music and
original interaction sounds run in Godot. Music/effects volume and reduced motion
are saved. See [asset credits](../godot/assets/CREDITS.md).

Checks: `rtk python -m unittest test_lamplight_ai test_game_native test_game_library test_game_campaign -q`,
`rtk python run_lamplight.py --check`, and `rtk python run_lamplight.py --capture`.
The native check covers travel, resident distribution, quiz/discussion, computer
screens, collision, mouse movement, writing and save isolation. Python tests
complete all seven eras and exercise AI source/key boundaries and failures.

This is a playable development build, not the full original release plan.
The village is four connected fixed-camera maps; it is not a seamless scrolling
world. Backgrounds and residents share visual templates across eras. Thinkers
use a generic visitor sprite in the world, with individual portraits in dialogue.
The current walk atlas has front-facing poses;
dedicated directional sheets, richer resident schedules, further learning questions,
book-length generation and a standalone installer remain future production work.
