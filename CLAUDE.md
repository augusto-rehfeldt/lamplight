# Lamplight

Cozy pixel-art writing and research game. Godot 4.7.2 client (`godot/`), a browser
build (`game/`, served by `game_server.py`) and a local Python service
(`game_native.py`) that owns saves, campaign rules and AI calls. See README.md and
`docs/COZY_LEARNING.md` for the current build; `PLAN.md` is the production plan.

## Non-negotiables

- The writing engine (`llm`, `pipeline`, `research`, `style`, `humanize`, `ui`) is
  bundled in `engine/`; `game_server.py` puts it on `sys.path` (flat imports) and
  redirects its output/library folders under `output/lamplight/`. Provider keys come
  from this folder's `.env` (see `.env.example`).
- One AI suite: every completion runs on the shared ai-suite AIService (sibling `ai-suite`
  checkout, or `AI_SUITE_DIR`; a fresh clone uses the vendored `ai_suite/` copy, synced by
  ai-suite's `sync.py` -- never edit it here). `engine/llm.py` keeps the chain, roles, catalogues,
  key discovery and recovery, and sends each link through `shared_service()`/`_send()`
  (streamed, fail-fast). The in-game AI goes through `game_native.chat_request()`. Tests
  patch those seams; no SDK client or raw completion request lives here.
- Never show a thinker outside their era, in gameplay, captures, docs or screenshots:
  a figure appears only when `campaign.figures()` returns it (`active <= year < died`).
  No cross-era portrait galleries.
- Game rules live on the Python side. The Godot client never decides rewards,
  mastery, eligibility or which learning question is current.
- `output/` holds real saves (`lamplight-native/library.json` + `.bak`, legacy
  `lamplight/`). Never overwrite or migrate them from a check; tests and captures
  use temporary directories.
- Checks never call paid providers; AI is mocked. Live benchmarks are explicit
  (`bench_lamplight.py`).

## Checks

```powershell
rtk python -B -m unittest test_game_campaign test_game_library test_game_native test_lamplight_ai test_engine_llm
rtk python run_lamplight.py --check     # headless Godot against the real service
rtk python run_lamplight.py --capture   # screenshots in output/lamplight-engine-check/
```
