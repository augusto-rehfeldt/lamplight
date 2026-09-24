# Lamplight — Godot project

From the parent project directory:

```powershell
rtk python run_lamplight.py --editor  # work in Godot; F5 runs the game
rtk python run_lamplight.py           # play directly
rtk python run_lamplight.py --check   # headless integration check, temporary saves
rtk python run_lamplight.py --hyper   # preload HyperCharm; connect inside the game
```

Godot 4.7.2 is pinned. `rtk python run_lamplight.py --setup` installs the verified
portable engine into the project cache; `--godot PATH` uses an existing engine.
Keep the launcher running while working in the editor: it owns the Python service.

Open `main.tscn` in the 2D workspace. `ReadingRoom` has mode/choice preview fields;
`Player` uses native Godot physics. WASD/arrows move, E interacts, J/Esc opens the
journal and location/action list. Manuscripts save locally to their owning slot.

See [native progress, data paths and limitations](../docs/M1_NATIVE.md).
This is an early desktop build. Legacy saves are preserved but not yet migrated;
complete books, final art/audio, full settings and Modern imports remain unfinished.

Current play loop, computer AI setup, learning mechanics and limits: [Cozy learning build](../docs/COZY_LEARNING.md).

AI is required: use **Connect & benchmark** before creating or resuming a game.
For automatic setup, `--hyper` uses `AW_API_KEY` and `AW_BASE_URL` from `.env`,
selects Qwen Max without sending any AI request before the window opens.
Set `LAMPLIGHT_AUTO_HYPER=1` in `.env` to preload this on normal launches;
`--no-hyper` skips it. Start the qualification from the visible AI setup screen.
Keys stay in server memory. Headless checks and captures always use test doubles.
The title's **Free Play** button opens a separate save without campaign progression.
Setup links to local Ollama, Groq's free tier and specific OpenRouter free models.
Pass 80/100 and every critical rule. A restart or setup change requires a retest.
Compare models with the existing HyperCharm key:
`rtk python bench_lamplight.py --models deepseek-v4-flash qwen3.8-max --repeat 2`.
Scores, failed checks, raw replies and latency are saved under `output/lamplight-bench-*`.
The village map is interactive pixel geography; tutorial tips appear in context
and replay from the notebook. See the learning-build notes for benchmark limits.

The computer and writing desk now offer a saved five-step workshop: question,
evidence, outline, draft and revision. Margot reviews each step on request; approve
it to continue, or edit and ask again. Earlier steps can be revisited without
deleting later text; their reviews must be renewed. Suggestions are optional,
and accepting one requires reviewing the resulting text. Finishing creates one
new manuscript; submission still uses the campaign's source/resource rules.

The footer shows AI requests and tokens. **AI usage** on the title or room HUD
shows successes, failures, response times and the last 20 requests. Counts persist
in `output/lamplight-native/ai_usage.json`, starting with this update. Provider
token counts and character-based estimates are separate; these are local totals,
not an account balance or invoice. No prompts, manuscript text or keys are logged.
