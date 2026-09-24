# Lamplight M0: baseline and visual target

Started 2026-09-08. **Historical browser baseline; M0 remains in progress.**
The user subsequently requested a proper game engine. Development now targets
Godot; see `M1_NATIVE.md` for the runnable native foundation. Browser-era
implementation recommendations below are retained as inspection history and
are superseded by the engine/data boundaries in `PLAN.md`.
This first implementation slice supplies reproducible baseline captures,
an interactive art reference, an inspected data map and production inventories.
It does not yet deliver a title screen, save slots or a complete opening chapter.

## Run and review

```powershell
rtk python -m unittest test_game_library test_game_campaign -q
rtk python check_game_browser.py
rtk python game_server.py
```

The browser check uses temporary server saves and an isolated browser, a local
book fixture and no live providers. It also opens `game/reference.html` directly
from disk in an offline context. Open that HTML file in a browser to review the
reference independently; it intentionally is not a new public server route.

Evidence is generated under `output/lamplight-ui-check/` (ignored build output):

| Evidence | Coverage |
| --- | --- |
| `baseline-1280.png`, `baseline-1920.png`, `baseline-390.png` | Existing game at 1280×720, 1920×1080 and 390×844; full-page captures expose the current dashboard's vertical layout |
| `library-desktop.png`, `campaign-desktop.png`, `campaign-mobile.png` | Room → physical laptop → study → take notes → correspondence → bilingual campaign |
| `english-catalog.png`, `reader.png`, `catalog-mobile.png` | 1,200-book archive, trolley, full-text search, bookmark and typography |
| `residents-mobile.png` | Resident settings and narrow-screen presentation |
| `reference-1280.png`, `reference-1920.png`, `reference-390.png` | Art reference at the target viewport sizes, with 1.25 device scale and reduced motion |

Initial deterministic baseline: **13 tests passed**. Initial and extended browser
checks: **passed**, with no page errors. The extended check verifies different pixels
for both opening choices, three mode previews, readable font switching, no
horizontal overflow, offline loading and 125% CSS zoom. Browser-emulated scale
is not a physical Windows display-scaling test. Native browser zoom, frame-time
profiling, audio listening and first-time human playtests remain unmeasured.

## Existing asset and interaction inventory

| Location | Inspected baseline | Production decision |
| --- | --- | --- |
| `game/world.js` | Original procedural Canvas 2D art, 960×560 world, 23 object records: six shelves, five residents, four plants, laptop, post, reader, coffee, fire, sofa, cat and globe | Retain Canvas and routing; validate 480×270 target before resizing world geometry. Current generic resident shape needs distinct four-direction sheets |
| `game/index.html`, `game/style.css` | Dashboard/sidebar, HUD strips, native modal, CSS portraits, system fonts and emoji-style symbols | M1 shell work; replace icons/fonts coherently rather than count existing symbols as final pixel assets |
| `game/app.js` | Reader/editor, seven writing formats, collection switching, settings, optional resident AI, coffee timing, treats, synthesized ambience | Preserve these working flows; offline authored conversations, shared settings preview and integrated game overlays still needed |
| `game/books.json` | 1,200 English archive entries and remote Gutenberg text URLs | Future Free Play/Modern catalogue; not a historical allowlist |
| `game_campaign.py` | Seven eras, 14 original bilingual notes, seven historical correspondents, study/work/mail/publish/jump actions | Retain validated economy/mail; notes are teaching aids, not complete editions |
| External assets | No bundled font, portrait atlas, animation atlas or audio files in the baseline `game/` tree | All require origin/license records; no final asset-production completion claimed |

The reference adds an original ten-color palette, room-corner composition,
desk/lamp/book silhouettes, five resident color/prop silhouettes, Miso's tail
mark, a Margot portrait sketch, three mode descriptions and two visible room
consequences. All art is editable Canvas code in `game/reference.html`, with
no downloaded assets. Text uses explicitly provisional system fonts.

## Data ownership and migration map

Inspection used code and test fixtures, not the contents of private manuscripts,
credentials or the user's personal library.

| Existing path / owner | Existing behavior | Required destination and preservation rule |
| --- | --- | --- |
| `output/lamplight/campaign.json` / server | Version 1: era, day, money, paper, prestige, knowledge, studied note IDs, letters, publications, completion | Named imported Campaign slot; preserve IDs, original completion and linked submission provenance; infer no route decisions |
| `output/lamplight/state.json` / client payload | Trolleys by collection, bookmarks, favorites, reader preferences, position, coffee/treat progress, collection selection | Separate campaign/archive reading state; archive goes to Free Play. Presentation belongs to machine settings. Unproven client counters cannot backfill authoritative rewards |
| `output/lamplight/documents.json` / server storage | Global array: id, title, text, updated; no mode/slot/source provenance | Keep campaign-linked submissions with their provenance; unknown-origin documents get a visible Modern import workspace. Never infer source eligibility from text, title or citation markers |
| `localStorage['lamplight-draft']` / browser | One unsaved manuscript backup for the origin, restored by timestamp | Capture before switching; namespace future backups by slot and document. Legacy unowned backup needs the same review treatment as unowned manuscripts |
| `output/lamplight/books/<positive-id>.txt` / server | On-demand complete archive text cache | Preserve bytes and bookmarks; shared immutable cache may serve Free Play/Modern. Existing cache membership grants no Campaign rights |
| `output/lamplight/jobs/<id>/job.json` / server | Global job metadata, collection, year, logs, result and status; no slot | Pin owning slot/mode/era/source snapshot; prevent cross-slot polling, answers, result attachment or document saves |
| Same job directory / pipeline | Topic, `02_dossier.json`, stage flags, drafts and other checkpoints | Preserve whole directory. Restored dossier must be checked against pinned sources before execution, never trusted solely because the stage is complete |
| `output/lamplight/settings.json`, `usage.json` | Machine provider/model choices and measured logical calls | Keep machine scope; separate presentation from gameplay preferences; exports omit credentials |
| `.env` / environment | Existing secrets and provider configuration | Preserve environment compatibility; never copy into saves or migration reports |
| `library/`, external Calibre library / research helpers | CLI research can find/extract local books and fall back to discovery | No automatic game migration/scan. Future Modern intake uses explicit selection; never invoke for Campaign |

Use a versioned slot manifest, backup before migration and atomic writes. Reject
unknown newer formats without overwriting. Keep old data until migrated saves
and manuscript homes have been verified; migration must be repeatable without
duplicating documents or rewards. The workspace currently has no Git repository,
so no commit or Git diff is available for this baseline.

## M1 trust boundaries found

1. `selectCollection()` writes a client-controlled collection. `book_text()` and
   `start_job()` validate IDs within that requested collection, but there is no
   immutable server-owned save mode. Thus existing collection validation is not
   the plan's cross-mode isolation.
2. `/api/bootstrap` returns all documents and recent jobs. `/api/document` has no
   owning slot. The editor can load a generation result into the global document
   list; UI-only mode cards would leave this shared state intact.
3. Campaign generation seeds a dossier and marks research complete before
   invoking the pipeline. `pipeline.do_research()` returns a completed dossier
   directly; `ask_library=False` alone is not a restore-time source boundary.
   Preserve the writing engine's CLI defaults while validating game jobs explicitly.
4. `/api/state` accepts an arbitrary object. Campaign economy already lives in
   separate validated server actions, but coffee/treat state is client-owned.
   New tutorial/preferences endpoints must not accept quest/ending/reward flags.
5. Existing `WORK` prevents campaign actions and provider changes during jobs.
   Slot switching and checkpoint cloning must use that same ownership boundary
   and wait for cancellation acknowledgement before switching.
6. `research.read_local()` catches extractor failures and returns an empty string.
   Modern needs a bounded, explicit import operation that surfaces these errors,
   preserves originals and snapshots, and never silently invokes discovery.
7. The HTTP handler serves only `/`, `/app.js`, `/world.js`, `/style.css`.
   M1 needs a narrow asset route, MIME validation, traversal rejection and
   missing-asset behavior; do not expose the project or save tree.

## Mode inventory

| Stable mode | Starting world / progression | Sources / documents | Tutorial scope |
| --- | --- | --- | --- |
| `campaign` | 1630 reading room; authored chapter and route progression | Only approved era-eligible complete editions plus explicitly original notes; own manuscripts and fictional timeline records stay distinct from historical evidence | Movement, dialogue, study, writing, post/time, recovery, restoration, saving and first choice; no import prompts |
| `free_play` | All principal rooms; earn upgrades or creative furnishing; no campaign prerequisite | Built-in archive without era gates; no personal imports or campaign rewards | Shared reading/writing/social lessons plus optional goals and placement |
| `modern` | Contemporary library, laptop, Sources desk; project progression | Built-in books and explicitly supplied local/web sources; immutable project evidence snapshots | Discovery/import, extraction review, provenance, project selection, writing and citation/export |

Writing style remains `manual`/`guided`/`auto`; it is not a save mode. A mode is
immutable within a slot. Provider settings can be shared; slot-owned sources,
manuscripts, lessons and jobs cannot be shared by switching a client selector.

## Content inventory and stable ID proposals

These IDs and effects are authored outlines, not implemented quests or dialogue.
The shared seven-chapter spine remains in `PLAN.md` section 4.
Each route below has three projects, one charter checkpoint and a final commitment.
The founding project/charter belongs to 1730, the second project to 1780/1830,
and the third to 1880. Their policy commitments determine the 1930 finale.

| Route ID | Three project IDs | Ending IDs / commitments |
| --- | --- | --- |
| `open_library` | `ol.reading_circle`, `ol.lending_network`, `ol.stewardship` | `ol.every_window`: transfer stewardship to branches; `ol.reading_house`: central public institution |
| `experimental_commonwealth` | `ec.open_methods`, `ec.open_laboratory`, `ec.oversight` | `ec.shared_observatory`: replication and public oversight; `ec.ivory_workshop`: autonomous restricted society |
| `republic_of_letters` | `rl.periodical`, `rl.distribution`, `rl.editorial_charter` | `rl.small_presses`: local editorial independence; `rl.common_gazette`: shared central publication |
| `clockwork_cooperative` | `cc.printing_tools`, `cc.shared_ownership`, `cc.federation` | `cc.makers`: federated worker workshops; `cc.quiet_workshop`: local craft protection |
| `patrons_academy` | `pa.patronage_charter`, `pa.intellectual_autonomy`, `pa.succession` | `pa.open_handed`: public-access covenant; `pa.gilded_lamp`: endowed private academy |
| `living_archive` | `la.missing_testimony`, `la.provenance`, `la.stewardship` | `la.no_voice_forgotten`: distributed contested testimony; `la.custodians`: curated consent-based access |

Opening `opening.shared_table` and `opening.patron_equipment` are mutually
exclusive first decisions, not route locks. Shared table immediately adds a
visitor; patron equipment adds a banner and instrument cabinet. Proposed 1680
callbacks are an observation-circle letter versus a request for instrument
access. Both paths must still recover entry to every 1730 charter.

Secret finale `secret.unwritten_century` proposes per-slot fragments from 1680,
1780 and 1880 plus a solved cross-route correspondence puzzle. Finale
`secret.home` proposes Miso's attic clue, the origin letter and a resident
reconciliation. Missed prerequisites get recovery quests before the 1930 finale.
Both require explicit eligible selection; profile gallery entries cannot supply
missing per-slot flags. Exact clue placements and event IDs remain to be authored.

The inventory is six routes, eighteen route-project outlines, twelve ordinary
ending commitments and two secret-ending outlines. It is **not** eighteen
finished quests or fourteen staged finales. Next content work is the complete
opening's bilingual dialogue and event graph; defer mass writing until M2 passes.

## Asset backlog

All reference assets below are original source code in `game/reference.html`.
They have no third-party attribution requirement added by this change. Existing
project licensing still applies; do not infer a new distribution license.
Use stages brief → sketch → pixel cleanup → animation/export → in-game review →
complete. Final runtime assets require an origin/license manifest and editable
sources, frame rectangles, durations, foot anchors and collision bases.

| Family / stable prefix | Inventory and consumer | Current stage / next gate |
| --- | --- | --- |
| `world.reading_room` | 480×270 reference, 16×16 grid, window, fireplace, rug; opening | Sketch; compare composition with movement/collision before changing runtime dimensions |
| `world.workshop`, `world.courtyard`, `world.attic` | Two further principal rooms and hidden reward room | Brief; reachable doorways/objects, then era and route dressing |
| `actor.player` | Modular 24×32 cells, four-direction walk/idle plus sit/read/write/carry/interact | Brief; customization and anchors must agree across palettes |
| `actor.{margot,ada,elias,jules,noor}` | Five 24×32 silhouette studies, distinct clothes/props; all modes | Sketch; four-direction movement and activity exports |
| `portrait.margot` | One 64×64 portrait sketch; opening dialogue | Sketch; cleanup and six expressions before M2 |
| `portrait.{ada,elias,jules,noor}` | Four 64×64 sets, six expressions each | Brief; neutral, warm, thoughtful, worried, delighted, resolute |
| `actor.miso` | Tail-mark silhouette; walk/sleep/stretch/groom/investigate/treat | Sketch; consistent anchors and six behavior sheets |
| `portrait.correspondent.*` | Seven historically scoped portraits, two expressions each | Brief; researched references and original drawing |
| `actor.visitor.*` | Six visitors with authored roles | Brief; avoid using generic faces for named residents |
| `prop.{desk,lamp,book,post,shelf}` | Pixel silhouettes; reading/writing/mail | Sketch; transparent exports, active/highlight/occupied states |
| `decor.*` | 24 fixed-slot decorations/upgrades including first lamp/shared table/equipment | Brief; prices/effects/placement and earned-vs-creative provenance |
| `world.era.*`, `world.route.*` | Seven era sets, six route overlays, Free Play themes, Modern props | Sketch for Modern and opening choice only; each route still needs 3 visual / 2 functional changes / 3 callbacks |
| `ui.*` | Dialogue frame, three mode-card text briefs, palette | Sketch; complete pixel UI kit, emblems, focus states, font, Spanish glyphs, loading/errors and small-screen layout |
| `fx.*` | Rain/static light in reference; runtime steam/rain/dust currently procedural | Sketch; restrained animation and reduced-motion behavior |
| `audio.*` | Four music loops + finale cue, three ambience beds, at least 18 effects | Brief; original/licensed exports and gesture-driven audio mixer |
| `discovery.*`, `achievement.*`, `ending.*` | 12 secrets, 24 achievement badges, 14 thumbnails/staged endings | Brief; records and release accounting cannot count placeholders as finished |

## Remaining M0 gate

- [x] Run deterministic baseline and existing browser walkthrough.
- [x] Capture current screens and document existing data/ownership paths.
- [x] Supply editable palette, scale, room, cast, prop and mode reference studies.
- [x] Outline six routes, fourteen endings and source rules for all three modes.
- [x] Start the edition/rights ledger with evidence and explicit admission rules.
- [ ] Finish reference cleanup and walk-sheet sample; validate runtime scale and font selection.
- [ ] Approve the first two complete editions with verified rights, dates and usable text.

See `CAMPAIGN_EDITIONS.md` for the book findings. At the user's request, the
Godot M1 foundation now proceeds alongside this unfinished review. Migration,
production art and approved books remain required. Neither the old visual
reference nor the new engine foundation completes the M0–M2 opening deliverable.
