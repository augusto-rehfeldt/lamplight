# Lamplight

Cozy pixel-art writing and research game. Godot 4.7.2 client (`godot/`), a browser
build (`game/`, served by `game_server.py`) and a local Python service
(`game_native.py`) that owns saves, campaign rules and AI calls. See README.md and
`docs/COZY_LEARNING.md` for the current build; `PLAN.md` is the production plan.

## Non-negotiables

- Split from `article-writer` on 2026-09-23. `game_server.py` puts `../article-writer`
  on `sys.path` and imports its `llm`, `pipeline`, `research` and `style` modules,
  then loads that project's `.env` (a local `.env` wins). Treat article-writer as
  read-only from here: it is managed by a separate session. If its public API
  changes, run this project's tests.
- Game rules live on the Python side. The Godot client never decides rewards,
  mastery, eligibility or which learning question is current.
- `output/` holds real saves (`lamplight-native/library.json` + `.bak`, legacy
  `lamplight/`). Never overwrite or migrate them from a check; tests and captures
  use temporary directories.
- Checks never call paid providers; AI is mocked. Live benchmarks are explicit
  (`bench_lamplight.py`).

## Checks

```powershell
rtk python -B -m unittest test_game_campaign test_game_library test_game_native test_lamplight_ai
rtk python run_lamplight.py --check     # headless Godot against the real service
rtk python run_lamplight.py --capture   # screenshots in output/lamplight-engine-check/
```
