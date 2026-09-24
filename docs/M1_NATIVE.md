# Lamplight: native Godot foundation

Historical foundation record. The current build and revised direction are described in [Cozy learning](COZY_LEARNING.md).

2026-09-08. **Runnable foundation; M0/M1 gates remain open.** The user requested
development inside a proper game engine. Godot replaces Canvas as the target
frontend; the existing browser build remains available for migration/reference.

## Work in the engine

From the project root:

```powershell
rtk python run_lamplight.py --editor
```

This opens `godot/project.godot` with Godot 4.7.2 and starts the local Python
service. Open `main.tscn` in the 2D editor and press **F5** to run. The room and
player draw in the editor. Select `ReadingRoom` to preview its exported mode
and opening-choice dressing. These inspector previews do not alter saved mode
or campaign outcomes; runtime state comes from the service.

To play directly, run `rtk python run_lamplight.py`. If the engine is missing,
run `rtk python run_lamplight.py --setup`, or pass `--godot PATH` to use an
existing Godot 4 executable. The portable setup downloads the official pinned
Windows archive and verifies its SHA-512 against the release checksum file
before extracting the two named executables into `.cache/godot/`.

No new Python dependencies were added. The existing requirements must be
installed. Godot requires a local graphics driver for play/capture; headless
checks do not open a visible window. This is a development launcher, not yet a
standalone release installer. The local companion needs packaging before export.

## Implemented behavior

- Native title, new-game mode selection with optional save name, Continue,
  saved-library list, pause/journal and a persisted readable-text setting.
- Godot Node2D scene, CharacterBody2D player, native static collision, movement
  and directional drawing. WASD/arrows walk; E interacts; J/Esc opens the journal.
  The journal supplies an accessible action list for shelf, desk, post and residents.
- Six authored offline resident/cat conversations, including a mode-specific
  Margot introduction and responses to both opening improvements. Conversations
  do not spend resources and are recorded once per slot.
- Campaign notes in a native plain-text reader, source study, manual manuscripts,
  autosaving, existing commission validation, authored correspondence and day-cost
  work/wait actions. Notes remain explicitly labeled summaries, not complete books.
- Free Play/Modern have distinct saves and the built-in searchable archive. Opening
  an uncached archive book explicitly downloads it using the existing bounded host
  validation/cache path. The native service does not expose personal imports yet.
- After a validated campaign commission, the player can confirm a shared reading
  table or patron equipment. The chosen room change and Margot response persist.
  Repeating a choice grants nothing; replacing a committed choice is rejected.
- Native manuscripts and actions derive their mode from the server's slot record.
  Client mode/collection overrides, foreign manuscript IDs and unavailable book IDs
  are rejected. Campaign never dispatches local-library scanning or discovery.

Room art is an editable development study ported into Godot's drawing API, not
a finished animated sprite pack. Five other resident interaction entries do not
yet imply five walking actors in the room. Only Margot and Miso have physical
interaction spots in this first scene. UI uses Godot's bundled default font;
final pixel lettering, portraits and audio remain production tasks.

## Storage and process boundaries

`game_native.py` exposes only `/api/native` on a random localhost port. It reuses
the existing Host/Origin/token protections. The launcher passes the ephemeral
session through the child process environment, never through save files or a
command-line token. Legacy `/api/state`, `/api/document`, `/api/job` and similar
routes are not mounted on the native listener. Providers are not called.

`output/lamplight-native/library.json` contains versioned slots and presentation
settings. Each slot has immutable `mode`, documents with slot/mode ownership,
campaign state where applicable, position, conversation history, guidance choice
and its opening decision. Writes use a copied transaction and atomic replacement;
the prior state is retained in `library.json.bak`. A failed write leaves the
in-memory and saved state intact. Unsupported save versions are rejected without
overwriting them. The launcher holds an OS file lock so a second native service
cannot overwrite the same library with stale state.

The current deliberate storage ceiling is 36 slots, 50 manuscripts per slot,
1,500,000 characters per manuscript, and 12 MB of total serialized state. Larger
storage will need per-document files/transactions. No deletion or restore API is
present yet. Preserve both JSON files if a save fails to load; recovery UI remains
part of the unfinished M1 work.

The editor autosaves after a typing pause and saves before leaving the editor,
returning to title or quitting. If saving fails or the text changes during a
request, the current editor stays open; newer text is not silently dismissed.
Walking position autosaves approximately every three seconds and before leaving
the slot. Abrupt process termination can still lose the last unacknowledged edit
or movement; a separate crash-recovery draft journal remains to implement.

Legacy `output/lamplight/` saves/manuscripts remain intact and are **not migrated
yet**. The only reused legacy data path is its approved archive-download cache.
Native checks and captures create their own temporary save directories.

## Verification

```powershell
rtk python -m unittest test_game_native test_game_library test_game_campaign -q
rtk python run_lamplight.py --check
rtk python run_lamplight.py --capture
```

The Python checks cover cross-mode source/manuscript rejection, forged fields,
host/origin/token protection, blocked legacy routes, both validated opening
choices, duplicate reward prevention, interrupted replacement, newer versions,
position bounds and exclusive launcher ownership. Existing library/campaign
checks remain unchanged.

The headless Godot check exercises the real scene and local API: title → create
Campaign → Margot → reader/study → manuscript → save → title → Modern → Free Play
→ resume Campaign, preserving manuscript, guidance evidence and position. It also
checks native wall collision and movement pausing. The launcher treats logged
Godot script errors as failure even if Godot exits with status zero.

Rendered evidence is under `output/lamplight-engine-check/`: native title/modes,
room, Margot dialogue, manuscript at 1280×720, plus room/Modern at 1920×1080.
The native capture runs used Godot's OpenGL Compatibility renderer on an AMD
Radeon RX 9060 XT. Screenshots were inspected for clipping/readability. This is
visual evidence, not a frame-time benchmark or a full playtest. The build has a
960×540 minimum desktop UI; a deliberate mobile layout is not implemented.

## Remaining work before M1/M2 completion

1. Finish the two complete book approvals and production art/font samples.
2. Implement reviewed legacy migration, named checkpoints/cloning and recovery,
   gallery state, and full per-slot tutorial lesson records.
3. Finish the opening's authored activity/quest graph, reward/secret/achievement,
   first lamp restoration, English content, audio and deterministic 1680 callback.
4. Port the remaining reader tools, source trolley, exports and manuscript formats;
   integrate providers/jobs with pinned slot/source snapshots in M3.
5. Deliver the full settings/input/accessibility menu and mobile layout. Finish
   Free Play furnishing and Modern intake/source management in M3a.

The native renderer and slots advance M1; they do not complete the requested
game or its polished opening. Catalogue and campaign source restrictions still
apply to every later ported capability.

Technical references: [official Windows distribution](https://godotengine.org/download/windows/),
[native 2D movement](https://docs.godotengine.org/en/stable/tutorials/2d/2d_movement.html),
[HTTPRequest](https://docs.godotengine.org/en/stable/classes/class_httprequest.html),
and [resolution handling](https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html).
