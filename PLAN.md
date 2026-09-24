# Lamplight: production plan

Date: 2026-09-09. Status: playable cozy learning build in Godot; the full release plan remains in progress.

Implementation progress: [cozy village, learning mechanics, computer AI and verification](docs/COZY_LEARNING.md). This supersedes the earlier single-room fantasy art direction and bilingual content requirements. The older [native foundation](docs/M1_NATIVE.md) and [M0 inventories](docs/M0_BASELINE.md) remain historical development records.

**Engine decision, updated at the user's request:** develop the game inside **Godot 4**, with the first native build pinned to Godot 4.7.2. Godot owns scenes, physics, movement, input, UI, animation and audio. The existing Python campaign/writing/provider code remains reusable through a private authenticated localhost service. The former recommendation to stay in browser Canvas is superseded. The native client must be an actual Godot game, not a webview around the dashboard.

Lamplight will be a cozy pixel-art adventure about building a library, forming friendships, and carrying ideas across time. Reading, writing, correspondence, and restoring the library are its central activities. The player should feel that they inhabit a small, evolving world from the title screen through the ending.

## Current continuation — reviewed 2026-09-09

The latest user direction supersedes every earlier optional-AI/offline-only
gameplay requirement. AI is a required mechanic in all native modes. A local
model can satisfy this without hosted fees or internet access after download.

Implemented in this continuation:
- Interactive pixel geography with roads, river, bridge, buildings, visited
  markers and current position. Selecting a destination follows connected paths.
- A minimal HUD; notebook/map controls appear as the opening advances. Seven
  contextual lessons persist per save and can be replayed. Detailed submission
  controls stay collapsed until requested; manual manuscripts still autosave.
- Pixel font, original bitmap icons, panel/travel transitions and gentle resident
  movement. People now use a consistent 52-unit height against room furniture,
  with foot anchoring and matching click targets; the cat stays smaller.
- Required model qualification: three randomized, objectively scored tasks,
  source grounding, period/evidence boundaries and valid gameplay planning.
  Minimum 80/100, at least 75 on each task, all critical answers correct. Report
  individual results and observed seconds. This is task qualification, not a
  calibrated general intelligence or literary-quality ranking.
- Groq free tier, specific OpenRouter free models and local Ollama setup links.
  Test the actual selected model, never a fallback or random router. Keys stay
  in memory; configuration/key changes and launcher restarts require retesting.
- The service blocks unqualified new games and gameplay mutations. Recovery
  reads and manuscript saves remain available. Garden discussion now uses the
  qualified AI and records progress only after a successful response.

Validation: Python qualification/regression tests, native Godot integration,
and rendered screens using temporary saves and mocked provider responses.
Live provider scoring remains player-triggered and is not implied by these tests.

Next production work remains M2 opening-content completion, fuller lesson
coverage, M3 job cancellation/recovery, M3a imports/furnishing, then authored
route content. This continuation does not claim the full release backlog done.

### Portrait continuation — 2026-09-09

- Added thirteen original pixel-art dialogue portraits: Margot, Ada, Elias,
  Jules, Noor, Miso, Galileo, Boyle, Swift, Franklin, Shelley, Darwin and Curie.
  These cover every current resident and historical debate partner, including
  later eras. Files and exact generation prompts live in
  `godot/assets/portraits/`.
- Resident dialogue, the reading-circle roster, debate replies, postal
  recipients and computer correspondence show the selected character's portrait.
  The computer now exposes all five existing human resident AI roles.
- Portraits are bundled locally and use nearest-neighbor sampling. Missing
  artwork leaves the conversation usable. Historical eligibility, studied-source
  requirements and the required AI qualification still apply.
- Verification adds complete-roster asset coverage and native checks of portrait
  selection, discussion flow and missing-art behavior, plus desktop captures.
  All 33 Python tests and the native integration check passed; rendered portrait
  screens were reviewed at 1280×720 and 1920×1080 with temporary saves and mocked
  AI. Review sheets: `output/lamplight-engine-check/portraits-residents-1920.png`
  and `output/lamplight-engine-check/portraits-thinkers-1920.png`.

Next art work: matching individual world sprites for historical visitors,
directional walking and additional expressions. The existing generic garden
visitor remains a world-sprite placeholder. M2 opening completion and the M3/M3a
backlog above remain open; this delivers the conversation-portrait slice.

## 1. Direction and scope

**Current user direction (2026-09-09):** a grounded, cozy pixel-art learning village.
Only the protagonist traveled from 2026, carrying a laptop. The inhabitants are
people of their own era. Everyday goals are to understand sources, create notes
and articles, and discuss ideas with period intellectuals. Time travel supplies
the route home; it should not dominate the visual identity with magic or spectacle.

The active learning loop is **explore → read an English summary → answer a
learning question → discuss evidence or an objection → create/revise at the
computer → share an article or letter**. Incorrect practice answers explain the
idea and allow free retries. AI creation happens at the protagonist's library
computer, using selected, save-owned sources; generated drafts are reviewed
before being kept. All game-facing content is English.

The current village has four connected maps: library, square, print shop and
reading garden. Characters are distributed across those places. Native mouse
and keyboard movement, a place map and a persistent learning journal guide play.

The user approved a summary-first direction. Original, clearly labeled book
summaries are now sufficient for the learning prototype; the previous requirement
to approve two complete books before continuing the prototype is superseded.
Full editions remain an optional production expansion, with rights verification
required before bundling. The ambitious route/content counts below describe the
longer release backlog, not what is finished in this build.


Use the requested games as references for specific qualities:

| Reference | Lamplight's interpretation |
| --- | --- |
| Stardew Valley | A welcoming home, recognizable routines, satisfying small interactions, friendships, and visible improvements. |
| Game Dev simulation games | Clear creation workflows: choose sources, plan, draft, review and share; visible progress through useful work. |
| Pokémon | A small readable village, connected places, friendly pixel characters and discovery through movement and conversation. |

Create original characters, artwork, music, and interface designs. These references set the direction; they do not determine Lamplight's genre or asset style.

**The core loop:** explore → meet someone or discover a question → read and gather evidence → write or assemble an argument → exchange letters → resolve a commission → improve the library → discover the next chapter.

Cozy means player-controlled pacing. Browsing, dialogue, decorating, and typing do not advance the calendar. Explicit activities show their day/resource costs before commitment. No hunger, friendship decay, missed-day punishment, or real-time writing deadlines. Progress still requires choices and effort, with recovery paths when resources run out.

**First complete release target:**

- Three selectable modes: **Campaign**, **Free Play**, and **Modern**, each with its own saves, source rules and contextual tutorial.
- Seven historical chapters, preserving 1630–1930 in 50-year steps, with an introduction, six alternate-history routes, twelve route endings and two secret endings.
- Seven main quest chains and fourteen side quests. Ten side quests form five two-part resident stories; four focus on exploration and restoration.
- Eighteen additional route quests, three per route, with persistent consequences across chapters. A single playthrough follows its chosen route rather than completing every route's content.
- Three connected principal spaces: reading room, correspondence/workshop room, and courtyard. A small hidden attic is an exploration reward.
- Five developed residents and Miso, with routines, expressive portraits, and persistent responses to player choices.
- At least 180 authored conversation exchanges across shared, resident and route content, counting a conversation rather than each line; English versions. This is the total authored inventory, not the amount seen in one playthrough.
- Twelve discoverable secrets and 24 achievements, including the existing treat discoveries.
- Twenty-four placeable decorations/upgrades using fixed, clearly marked placement spots.
- A complete title/pause/settings/save flow, cohesive pixel UI, music, ambience, and interaction sounds.
- An adaptive, replayable tutorial that responds to completed actions and introduces systems when needed.
- An art-production backlog covering actual pixel portraits, animated characters, objects, environments, interface elements and route-dependent world variants.
- Existing reading, manuscript, generation, and provider capabilities integrated into this presentation.

These are production targets, not claims about current content. Reassess delivery estimates after the first complete chapter is playable; do not invent a schedule before measuring asset and content throughput.

### 1.1. Three modes, one cohesive game

The startup menu offers Continue and New Game. New Game presents three illustrated mode cards with a short description and source rules. Continue identifies the saved mode. All modes retain the same walkable pixel-art world, residents, Miso, integrated reader/editor, sound, settings and a required qualified AI companion.

| Mode | Purpose and progression | Available source material | Player-supplied books |
| --- | --- | --- | --- |
| Campaign — Letters Across Time | Seven eras, authored quests, historical constraints, alternate-history routes and fourteen endings | Only the built-in curated royalty-free catalogue, with editions unlocked by era; original game notes/letters are identified separately | **Not allowed**, including through upload, URL import, local library scanning or another mode's inventory |
| Free Play — A Library of Your Own | An open-ended cozy sandbox for reading, writing, furnishing and spending time with the residents; no required campaign or ending | The built-in royalty-free reading collection without historical date gates | No imports; choose Modern for a personal or current-source library |
| Modern — The Contemporary Study | An open-ended present-day writing and research studio inside the game | Current articles/papers/web sources, built-in books and books/documents explicitly supplied by the player | **Allowed**, with local import and source management in the game |

Free Play is available immediately, without completing Campaign. Modern is a separate mode, not a paid unlock or a campaign reward. Mode belongs to the save and cannot be changed by toggling a setting; switching opens or creates another slot after pending work is saved. Settings and credentials can be shared, but source selection, manuscripts, jobs and progression remain scoped to their originating mode/slot.

### 1.2. Free Play: a lasting cozy sandbox

Start with all principal rooms and the built-in reading collection accessible. Choose a room theme, appearance, weather and day phase; these do not imply historical progression. Offer gentle optional resident requests, collection goals, coffee, gardening/decor interactions, reading sessions and writing projects. The adaptive tutorial introduces only the systems present in this mode.

Let the player choose **Earn upgrades** for light restoration/resource goals or **Creative furnishing** for immediate access to the 24 decorations. Both are clearly labeled Free Play options. Neither grants campaign prestige, charter prerequisites, route endings or campaign achievements. Shared reading/social/discovery achievements may unlock where their actual requirements are met; resource-specific achievements must check whether an item was earned rather than freely placed.

The world still responds: readers use furnished spaces, residents comment on projects and community requests, and Miso adopts new resting places. These changes persist without forcing a historical route, final chapter or reset. All modes require qualified AI; local inference and bundled/cached books can work offline, and additional catalogue downloads state their network requirement.

### 1.3. Modern: craft from current sources and your books

Dress the familiar library as a contemporary studio using the same palette, pixel grid and UI: current periodicals, a reference shelf, a modern laptop, project pinboard and optional contemporary desk props. Use a dedicated mode emblem and title so a modern workspace cannot be mistaken for a historical save. Contemporary residents discuss the project's sources without the campaign's era cutoff; the historical correspondent roster and alternate-history endings do not apply.

**End-to-end flow:** create a project → choose a topic and format → gather current sources or add books → inspect extracted text and metadata → select evidence → outline/write/revise → receive optional resident feedback → save/export with references. “Craft” includes articles, essays, discussions, papers and long-form manuscripts through the existing formats. Manual manuscript recovery remains usable during an AI outage; gameplay requires the qualified connection.

Add a physical **Sources desk** with three clear actions:

- **Find current sources:** search available research/news connectors by topic, publication date and language. Distinguish publication/update time from retrieval time; undated results are not labeled current. Keep an explicit refresh action and retain the source snapshot used by a manuscript so later website changes do not silently change its evidence.
- **Add a link:** fetch a supported article or paper, preview its available text and let the player correct title/author/date. Label abstract-only, partial, inaccessible and full-text results accurately. Do not fabricate missing text, sources or page numbers.
- **Add my books/documents:** select PDF, EPUB, DOCX, TXT or Markdown files, inspect extraction, correct metadata, then place them on a personal shelf. Reuse `research.read_local()` and installed extractors after checking their failure handling; the existing empty-string failure must become a visible import error. Scanned PDFs with no extractable text explain that limitation and leave the player free to use another file; do not claim OCR support until implemented.

Keep originals, extracted text, source IDs, hashes, provenance and project references. Detect duplicate imports by content without merging genuinely different editions. Prefer stable chapter/section or PDF-page locators; never treat reader pagination as an edition's printed page numbers. Imported books stay local until the player explicitly starts a provider-backed action using selected material, with a clear indication that excerpts will be sent. Importing alone makes no AI call and publishes nothing.

Use a file picker or explicit selection from the existing local/Calibre library, not an automatic scan of the user's machine. Copy selected material into a managed Modern library while preserving originals. Validate formats and filenames, bound file and expanded archive sizes and parsing time, and report malformed/encrypted/unsupported files. Fetch public source URLs through a bounded server operation; block local/private network targets and revalidate redirects. Untrusted book/web text remains evidence, never executable markup or instructions for tools.

The Sources desk supports preview, search, tags, project membership, replace/reimport and remove. Before removal, show affected projects; preserve citation metadata and mark missing evidence rather than silently breaking manuscripts. Existing project snapshots are never silently replaced. Reuse current search/extraction/citation helpers through a mode-aware source boundary; do not bring every existing fallback or global library scan into the game automatically.

### 1.4. Mandatory campaign book policy

**The player cannot provide books to Campaign.** It uses a built-in, developer-curated royalty-free catalogue only. For content selection, require documented public-domain status or a license permitting the planned inclusion/use without royalties, with edition, translation, illustrations, attribution and distribution territory checked. A free download or an old original publication date alone does not satisfy the catalogue review.

The campaign catalogue ledger records title/author, edition/translation, original and edition dates, language, rights evidence, source location, attribution and first eligible era. Launch target: at least two newly eligible complete works per era, fourteen distinct works overall, with original English study notes as teaching aids. The current fourteen notes are not fourteen complete books. Select and verify actual editions during M0/content production; if a planned title cannot qualify, replace it with an appropriate approved work rather than asking the player to supply it. Bundle all required campaign texts for offline play.

Player-written manuscripts, claims and letters remain allowed: the restriction is on importing reference books and granting them source status, not on ordinary writing. Campaign book pickers, AI context, evidence cards and commission validation use only server-approved IDs available in that era. Authored alternate-timeline records remain visibly fictional game documents, never imported books or historical evidence.

Enforce this rule in the server's shared source resolution and all entry points: catalogue/text retrieval, uploads, URL imports, local/Calibre selection, job creation, resident feedback, cached dossier loading and checkpoint restore. Resolve mode from the server-owned save, not a client-supplied collection name. Reject Modern/Free Play IDs in Campaign even if the same author/title appears there; only an independently approved campaign edition is eligible. Campaign jobs cannot call current-source discovery or automatically scan `library/`.

Modern books, current-source dossiers, generated results and Free Play progress cannot be transferred into a Campaign save. Keep internal reference files out of manuscript import flows. Exporting a player's own manuscript remains available; manual text cannot become a validated historical source merely by including a citation marker. Switching modes preserves each trolley, reading position, project and pending job without carrying evidence across the boundary.

## 2. What already exists

The following inventory describes the original browser baseline: `game/index.html`, `game/style.css`, `game/app.js`, `game/world.js`, `game_server.py`, `game_campaign.py`, the README, and existing check scripts. Native progress is recorded separately in `docs/M1_NATIVE.md`.

| Area | Existing foundation | Required development |
| --- | --- | --- |
| World | One canvas room, collision, click routing, keyboard movement, lighting, rain, residents and cat | Sprite animation, connected rooms, schedules, interactive upgrades, consistent pixel scale |
| Presentation | Dashboard sidebar, page header, generic modal panels, system/serif fonts | Full game viewport, title screen, integrated HUD, pixel lettering, illustrated panels |
| Campaign | Seven eras, economy, dated notes, commissions, mail, progression and completion flag | Authored chapter arcs, varied objectives, staging, consequences, ending and postgame |
| Characters | Five named AI feedback roles | Offline conversations, relationship events, portraits, distinct routines |
| Audio/secrets | Optional synthesized ambience, coffee activity, three hidden treats | Music direction, sound feedback, audio settings, discovery chains and achievement journal |
| Providers | Ordered routing, custom compatible endpoints, resident model overrides, local usage limit | Guided setup, connection tests, clear failures and in-game credential entry |
| Persistence | JSON saves, manuscript recovery, job checkpoints | Save slots, migration, chapter/relationship/discovery state and recovery UI |
| Verification | Campaign/library unit tests and optional Playwright script | New gameplay coverage and visual/audio/accessibility review |

Baseline executed: `rtk python -m unittest test_game_library test_game_campaign -q` — **13 tests passed**. The browser script was inspected, not executed for this planning task. This is a functional baseline, not proof of visual quality or release readiness.

## 3. Art and interface specification

Establish a small art bible before mass-producing content:

- Top-down, slightly elevated room view; consistent floor grid, light direction, outlines, and shadows.
- Start the visual prototype at a 480×270 logical viewport, with 16×16 tiles, roughly 24×32 character frames, and 64×64 portraits. Validate readability and room framing before locking these dimensions.
- Warm parchment, amber light, walnut furniture, sage textiles, muted burgundy, and cool blue rain. Use a shared limited palette with deliberate light/shadow ramps.
- Hand-shaped pixel clusters and clean silhouettes. Avoid mixing smooth vector icons, emoji, unrelated asset packs, and pixel sprites.
- Locally bundled pixel font with English punctuation and accented glyphs. Pixel lettering is the default for menus, HUD, dialogue, signs, and journal. Reader/editor also offer a comfortable alternative font and adjustable size.
- One pixel UI kit: panel borders, buttons, tabs, selection/focus states, icons, sliders, scrollbars, pointers, speech indicators, and achievement badges.
- Character walk cycles face four directions; idle, sit, read, write, and interact animations communicate activity. Portraits have neutral, pleased, thoughtful, and concerned expressions.
- Rain against windows, page turns, cup steam, lamp flicker, and a stretching cat provide restrained motion. Reduced-motion settings suppress decorative effects.
- Bundle all art/fonts/audio locally and record their origin and license in an asset manifest. Keep editable art sources alongside exported assets.

Render sprites without smoothing, snap draw positions to the pixel grid, and prefer integer scaling with letterboxing. Validate Godot viewport/stretch settings and fractional Windows display scaling at runtime; source-grid alignment alone does not guarantee uniform device pixels. See [Godot's multiple-resolution guidance](https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html). Browser zoom remains a check for the retained legacy interface or a future web export.

The interface occupies the game viewport. A compact HUD shows day/era, important resources, mail, and the current objective. Everything else opens through a physical object or the pause/journal menu:

| Interaction | In-game presentation |
| --- | --- |
| Bookshelf | Illustrated shelf/catalogue, trolley selection, book detail |
| Reading table | Open book with bookmarks, search, chapters and reading preferences |
| Writing desk | Paper manuscript/editor, source cards, export and save controls |
| Laptop | Writing assistance, job status, provider settings and usage |
| Post desk | Envelopes, correspondence threads, delivery dates, stamp confirmation |
| Resident | Portrait dialogue box, short choices, optional manuscript discussion |
| Workshop | Upgrade preview, price, effect, placement spots |
| Journal | Quests, relationships, discoveries, collection and achievements |

Use Godot Control scenes, Buttons, LineEdit/TextEdit, ScrollContainers and themed panels for the game interface. Preserve keyboard text editing, selection, visible focus and dismissal. Verify Godot accessibility behavior with the target assistive technologies; do not assume the old HTML interface's accessibility carries over automatically. Keep reading/editor text as plain text unless an explicitly safe markup renderer is provided.

Keep an accessible location/action list in the pause menu so navigation never depends solely on walking. Support keyboard and mouse throughout, touch controls on small screens, remappable movement/interact bindings, UI scaling, instant dialogue text, and visible equivalents for sound cues. Do not shrink a desktop HUD until its text becomes unreadable on phones.

### 3.1. Producing the pixel art

Art creation is a scheduled deliverable. The art bible must lead to exported, animated assets that are inspected inside the running game.

**Character direction:** Margot uses burgundy, an angular silhouette and a pencil tucked into her hair; Ada uses teal, practical sleeves and a notebook; Elias uses moss and cream, round spectacles and a stooped reading pose; Jules uses ochre, rolled sleeves and ink-stained hands; Noor uses indigo, a soft scarf and an open posture. These are starting designs to refine together on one lineup sheet. Give Miso a recognizable tail marking and the player a customizable appearance independent of route or character ability.

| Asset family | Production inventory | Required states and review |
| --- | --- | --- |
| Player | One modular character with selectable skin, hair and clothing palettes | Four-direction idle/walk; sit, read, write, carry and interact; combinations retain contrast |
| Residents | Five distinct sprites and matching portrait sets | Four-direction movement, role-specific activity, six portrait expressions: neutral, warm, thoughtful, worried, delighted and resolute |
| Miso | One sprite sheet with a consistent silhouette | Walk, sleep, stretch, groom, investigate and accept a treat |
| Correspondents | Seven baseline historical-character portrait sets | Two expressions each, original stylized designs based on researched references; letters remain fictional |
| Visitors | Six reusable visitor designs with authored route roles | Palette/prop variants, standing/walking/sitting; no random face used for a named resident |
| Furniture and props | All current interactive objects plus the 24 planned decorations/upgrades | Inventory icon, placed sprite, interaction highlight, occupied/open/active variants where needed |
| Environments | Three principal rooms, attic, doorway connections and exterior window views | Base tiles, seven era dressing sets, six route overlays, Free Play themes, a contemporary studio dressing set and persistent restoration states |
| UI and lettering | One complete atlas/font family and title treatment | Buttons in all states, portrait frames, three mode cards/emblems, Sources desk/import screens, journal pages, route emblems, tutorial prompts, 24 achievement badges and 14 ending thumbnails |
| Effects | Small reusable sprite sheets | Steam, rain splashes, dust, lamp sparks, paper motion, discovery and route-transition cues |

**Production workflow:**

1. Build a palette sheet, scale chart, room lighting reference, full cast lineup, and object silhouette sheet. Lock the six-expression specification here; it expands the four-expression initial sketch above.
2. Create one finished sample of each family: Margot's portrait and walk sheet, the player, Miso, a desk, a lamp, a book, a dialogue frame and one room corner. Review these together at actual display size.
3. Create the rest from those approved references. AI image generation may help produce concepts and source illustrations, using the approved lineup/palette as references, but generated sheets require pixel cleanup, consistent frame registration and animation review before they become runtime assets. Hand-authored pixel work is also valid. Do not treat a downscaled concept illustration as a finished sprite sheet.
4. Keep editable sources and export transparent PNG sprites/atlases at their native grid size. Record frame rectangles, foot anchors, durations and collision footprints in simple asset metadata; collision follows feet/object bases rather than painted shadows.
5. Assemble rooms and character sheets in an in-game asset preview. Check animation loops, readable silhouettes, portrait-to-sprite resemblance, held-object alignment, light/dark backgrounds, English text and color-vision accessibility.
6. Add era/route variations through authored props, banners, clothing details, lighting and exterior activity. Keep shared anatomy and room geometry consistent. Ending art uses the player's actual route and restoration state.

Track each asset through **brief → sketch → pixel cleanup → animation/export → in-game review → complete**, with source, license, dimensions, frame count and consuming scene. M0 completes the reference pack; M2 completes every opening-chapter asset; M4 supplies world/route prototypes; M6 finishes the full inventory. A missing asset uses an obvious development placeholder and blocks the corresponding release gate.

### 3.2. Full settings menu

Use one pixel-art settings screen from the title, pause menu and laptop, with identical values and behavior. Group options by player intent:

| Page | Controls |
| --- | --- |
| Display | Window/fullscreen request, integer-scale preference, UI/text size, brightness preview, decorative effects, screen shake off by default, reduced motion, background frame-rate reduction |
| Sound | Master/music/ambience/effects, dialogue sounds, mute, mute while unfocused, optional visual sound descriptions |
| Controls | Rebind movement/interact/journal/pause, restore bindings, mouse navigation, touch control size/position, hold/toggle behavior where applicable |
| Reading and dialogue | English interface, pixel/readable font option, reader font/size/theme, dialogue speed or instant text, manual/automatic dialogue advance, conversation history |
| Accessibility and comfort | High-contrast focus/interaction outlines, symbols alongside color, simplified minigames with equal rewards, motion controls, independent text scaling, accessible location/action list |
| Guidance | Guided/contextual/minimal tutorial mode, hint delay, show current objective, replay learned lessons, reset tutorial progress for this save |
| Gameplay | Mode-specific options: Campaign standard/relaxed costs and route hints; Free Play earn/creative furnishing and weather/day phase; Modern project/source preferences. Show only applicable settings. |
| Connections | Provider flow from section 6, local inference, shared/per-resident model selection, fallback order, local budget and credential removal |
| Saves and privacy | Mode-labeled slots, automatic checkpoints, backup/export/import, recovery, local data location, Modern source storage/removal, clear per-slot progress with confirmation; credentials excluded from exports; restore cannot change a save's source policy |

Apply visual/audio changes as a preview; offer Apply/Cancel and per-page defaults. Fullscreen failure must leave a working windowed game. Prevent duplicate critical key bindings or explain conflicts before applying them. Changes must not clear an in-progress manuscript or dialogue choice. Destructive save actions are separate from restoring settings defaults.

Display/audio/input/accessibility and provider preferences are machine-level; tutorial progress, difficulty and story flags belong to each save. Relaxed mode changes future resource costs, preserves existing rewards and unlocks the same endings/achievements. Keep hidden ending requirements out of ordinary settings and hints. Remember settings across restarts and validate imported values.

### 3.3. Dynamic tutorial and ongoing guidance

Teach through the room and its inhabitants. Margot introduces the desk, Ada the evidence board, Jules the press and Noor the journal; Miso can lead the player to a low-stakes interaction. Use brief portrait lines, a single contextual prompt and an optional journal explanation. Provider setup is taught only when the player chooses to use it.

Represent lessons as small authored records: stable ID, prerequisites, relevant location/action, completion event, short hint, detailed help, dismissal and replay state. Derive completion from successful actions, not from closing a tooltip. The tutorial uses existing gameplay events and never needs an AI model or behavioral analytics service.

- **Recognize prior knowledge:** a player who already walked, read or sent mail skips those instructions. Imported saves infer only proven progress; offer a short refresher for unknown systems.
- **React to context:** prompts use current key bindings/input method, the player's selected language, available resources and unlocked objects. Do not point at a locked room or prescribe a letter when the player cannot afford postage.
- **Help without interruption:** after a configurable period without relevant progress, offer “Need a hint?”; exclude reading, typing, paused state, background tabs and pending provider jobs. Give an objective reminder first, an object cue second, and a step-by-step explanation only on request. Never escalate into forced autoplay.
- **Follow the player:** leaving a lesson's location suspends its prompt; coming back restores it. Completing prerequisites in a different order works. Only one teaching prompt appears at a time, and dialogue/errors take priority.
- **Explain consequences at the right moment:** teach the timeline journal on the first lasting decision, institution effects before founding a route, and the branch checkpoint before an irreversible commitment. Explain tradeoffs without revealing unearned endings.
- **Remain optional:** skip all, dismiss one lesson, replay from the journal, and change guidance mode at any time. Skipping cannot block a quest, reward or achievement.
- **Persist cleanly:** save completed/dismissed lessons and an unfinished lesson's stage per slot. Reloading never repeatedly grants tutorial resources or resets narrative choices.

Opening lessons cover movement/interact, conversation choices, study/trolley, manuscript or argument board, mail/time, resources/recovery, restoration, journal/save and the first lasting choice. Later lessons introduce room placement, schedules, route changes, branch checkpoints and advanced AI workflows. Validate keyboard, touch, out-of-order completion, repeated failure, dismiss/replay and mid-lesson reload. The gate is that a new player can finish the opening without outside instructions while an experienced player can bypass the teaching immediately.

Select lessons by mode: Free Play teaches open-ended reading, optional goals and furnishing; Modern teaches source discovery, import/extraction review, provenance, project selection and citation/export. Campaign briefly explains its curated royalty-free shelves and never prompts the player to upload a book. Reuse shared lessons while retaining completion state per slot; switching modes must not display irrelevant historical or import instructions.

## 4. World, story, and meaningful play

**Proposed story:** a displaced writer inherits a lamp that keeps one library connected across centuries. Its scattered correspondence can restore a damaged record of the people who built it. Each chapter recovers part of that record and asks what makes an idea worth preserving.

Make the five recurring fictional residents fellow occupants of the time-linked library. They experience the jumps with the player; introduce this explicitly. Historical correspondents remain period-bound. Preserve server restrictions on available sources and people, and explain the laptop's exceptional connection in the introduction. Alternate-history consequences follow the separate rules below; they do not silently rewrite source metadata or historical biographies. No unexplained immortal historical locals.

| Era | Chapter proposal | Distinct play and lasting reward |
| --- | --- | --- |
| 1630 | The Borrowed Desk | Learn movement, meet Margot and Miso, compare observations, complete a first short commission; restore the lamp. |
| 1680 | A Room for Experiments | Arrange an evidence comparison with Ada, resolve conflicting accounts through letters; open the workshop. |
| 1730 | Ink for Everyone | Help Jules assemble a small periodical, choose its audience and presentation; unlock printing upgrades. |
| 1780 | The Long Correspondence | Connect clues from delayed letters with Elias; restore the courtyard and a shared discussion table. |
| 1830 | Other People's Stories | Reconsider a first impression with Noor; develop a resident story and furnish a public reading corner. |
| 1880 | The Unfinished Catalogue | Organize conflicting records and document uncertainty; restore the archive and its provenance display. |
| 1930 | A Light Left On | Assemble the library's legacy from earlier decisions; hold a gathering, reveal the lamp's history, and enter postgame. |

Each chapter needs an opening scene, a clear local problem, two or more different activities, a consequential conversation choice, a correspondence payoff, a visible room change, and a closing scene. The chapter table describes the shared spine. Its problems, available solutions, visitors and closing scenes vary by route. Shared transitions can reconverge, but persistent decisions continue to alter later play.

Writing remains central. Add an offline guided argument board with claim/evidence/objection choices for players who want shorter, structured commissions. Preserve free writing and all existing long-form formats in the desk. Structured submissions need their own server-validated completion rules; do not fake word-count success by inserting repeated text. Never present mechanical acceptance as an assessment of literary quality.

Replace repeated copying-button grind with brief, optional sorting/proofreading activities and an immediate accessible alternative with the same reward. Balance chapter costs around normal play. Repeating paid manuscripts must remain prohibited. No main objective may require a secret, real-money model call, reflex challenge, or an unavailable network download.

Residents have two or three activity positions per day phase, readable schedules, distinct dialogue voices, and reactions to completed quests. Existing movement routing can support their movement after it is checked for moving actors. Relationship progress comes from story events and helpful choices, not repeated greeting clicks. Miso wanders, naps, reacts, and occasionally leads the player toward a discovery.

The existing English collection becomes Free Play's built-in catalogue and is also available in Modern. It does not become campaign-eligible as a whole. Campaign requires the complete, rights-reviewed, historically appropriate editions specified in section 1.4; historical notes remain dated original study material. Preserve cached reading and manuscript access after the campaign ends, with the campaign's source restrictions still enforced in postgame.

### 4.1. Actions that change the world

Use a bounded authored simulation: track named commitments, completed projects, institution relationships and a small set of indicators such as public access, scholarly trust, institutional control, worker welfare and community bonds. Indicators help NPCs and the journal describe a changing society; specific verified project flags determine route unlocks. Do not choose an ending from one opaque morality score.

| Player action | Immediate response | Later consequence |
| --- | --- | --- |
| Fund a shared reading table | New furniture and visitors; residents acknowledge who can attend | A reading circle becomes a public school or remains a private society, depending on its charter |
| Publish methods with an experiment | Ada's scene, public notes and reproducible evidence cards | Independent workshops appear; a later dispute has an additional evidence-based solution |
| Accept exclusive patron funding | Better equipment and a patron's banner | More resources but restricted commissions; the player may negotiate, buy out or preserve the restriction |
| Pay printers fairly and share decisions | Changed workshop dialogue, wages and activity | A cooperative forms and supports an alternative distribution network |
| Circulate a disputed pamphlet | Mail reactions and a new discussion | A censorship dispute changes which visitors and distribution channels are available |
| Preserve, annotate or conceal a damaging record | Different archive object and resident response | Later characters can challenge the institution, inherit an omission, or repair the record |

Give every major decision at least one immediate response and one later playable consequence. Each route needs at least three persistent visual changes, two functional changes (for example access, costs, distribution, services or quest solutions), and three callbacks in later chapters. Changes affect visitors, props, schedules, available commissions, notices, letters and the view outside; not merely a number in a menu.

At the end of each era, the timeline journal records **what you did → who responded → what changed**, distinguishing observed effects from uncertain promises. Advance years deliberately; never simulate centuries while the player is away. Daily cosmetic choices need no political consequence, and an accidental click must not commit the player to a historical route.

### 4.2. Six alternate-history pathways

These pathways are explicitly speculative fiction. Their scale is a town and its connected institutions, with wider repercussions conveyed through authored correspondence and ending scenes. They do not claim to simulate the whole world or predict what real historical figures would have done.

| Route | Player project and route commitments | Distinct playable world |
| --- | --- | --- |
| The Open Library | Establish a reading circle, adopt public access, build a lending network | Public classrooms, varied readers, shared catalogues; conflicts over access and stewardship |
| The Experimental Commonwealth | Publish reproducible methods, establish an open laboratory, resolve a safety/governance dispute | Workshop apparatus, collaborative research, new public demonstrations and evidence puzzles |
| The Republic of Letters | Create a periodical, build independent distribution, establish a correspondence charter | Print stalls, multilingual letters, public debates and censorship negotiations |
| The Clockwork Cooperative | Improve printing tools, negotiate shared ownership, organize a federation of workshops | Machinery, worker meetings, different production costs and cooperative commissions |
| The Patron's Academy | Accept a patronage charter, negotiate intellectual autonomy, settle succession | Restored halls, specialist collections and funded projects; restricted access and patron obligations |
| The Living Archive | Recover missing testimony, establish consent/provenance practices, decide stewardship | Oral-history corners, memory exhibits, restored records and investigation-based quests |

Plant invitations in 1630–1680. In 1730, allow the player to adopt an available founding charter, with an understandable prerequisite list and a branch checkpoint. Every route must have a recoverable entry path by this point; an early tutorial choice cannot permanently exclude one. The charter establishes the route and its three additional quest chains unfold across 1730, 1780/1830 and 1880.

Allow a deliberate route change before the 1880 commitment through a short reconciliation/conversion objective. Use authored conversion tasks based on reusable project prerequisites rather than writing thirty separate route-pair campaigns. Retain former projects, visible remnants and relationship reactions; switching does not erase history or let the player collect duplicate project rewards. Unchosen institutions can appear as allies or rivals, but only the active route's final project controls its ordinary ending pair.

**Historical truth boundary:** real study notes retain their dates and wording. Route-created newspapers, inventions and institutions receive separate IDs and a visible “Your timeline · fictional” provenance label in the journal/reader. Invented documents never masquerade as historical evidence in the writing pipeline. Historical correspondents use actual availability dates and sourced knowledge plus explicitly framed fictional observations of branch events; invent a fictional successor when a later route needs a correspondent. Their lives are not extended implicitly.

The required AI receives the current era, supplied period sources and a compact record of validated fictional events, clearly separated. It cannot invent new canonical inventions, unlock knowledge, alter relationships, select a route or set an ending. Major decisions use explicit player choice cards and server validation even when the accompanying manuscript is free-form. The server owns all rewards and outcomes; a qualified local model supports play without a hosted service.

### 4.3. Fourteen authored endings and replay

Each route has two substantial outcomes. The founding charter and first two route projects establish eligibility; the final 1880 project presents a concrete policy decision with requirements the player can inspect. That recorded decision selects the route's 1930 ending. Prior choices determine who attends, which buildings survived, the residents' epilogues and the fate of individual projects. A last-minute dialogue button cannot undo a century of choices.

| Route | Ending A and its defining commitment | Ending B and its defining commitment |
| --- | --- | --- |
| Open Library | **A Light in Every Window:** complete the lending network and transfer stewardship to community branches | **The Great Reading House:** consolidate the collection in a lasting central public institution |
| Experimental Commonwealth | **The Shared Observatory:** establish independent replication and public oversight | **The Ivory Workshop:** preserve a smaller autonomous research society with restricted participation |
| Republic of Letters | **A Thousand Small Presses:** secure decentralized distribution and local editorial independence | **The Common Gazette:** establish an enduring shared editorial charter and central publication |
| Clockwork Cooperative | **The Commonwealth of Makers:** federate worker-governed workshops | **The Quiet Workshop:** keep the cooperative local and protect its craft traditions |
| Patron's Academy | **The Open-Handed Academy:** negotiate a permanent public-access covenant | **The Gilded Lamp:** preserve the endowed private academy and its obligations |
| Living Archive | **No Voice Forgotten:** distribute stewardship and preserve access to contested testimony | **The Custodians of Memory:** protect a curated archive with consent-based access limits |

Each finale gets its own staged scene, visual composition, route-specific dialogue, music treatment and account of the society the player helped create. Neither a changed title nor a differently colored final card counts as a separate ending. Avoid labeling the two outcomes simply good/bad; show concrete benefits, exclusions and costs. Every ordinary ending must be reachable without a secret and without a perfect relationship record.

Two additional secret endings have multi-chapter clues: **The Unwritten Century**, in which recovered lamp fragments and a completed cross-route correspondence puzzle make a new temporal destination possible; and **Home Is Where the Lamp Is**, in which Miso's attic discovery, the recovered origin letter and a reconciliation scene allow the writer to return home carrying the library's legacy. Their exact flags and clue placement belong in the content ledger before implementation. Both remain achievable on any route; inaccessible clues get an authored recovery opportunity before the finale. Secrets offer an explicit alternative finale only when eligible, never silently override the chosen route ending.

Provide an ending gallery with unlocked scenes, spoiler-safe silhouettes and discovered clues. Make automatic named checkpoints before a charter, route conversion and the 1880 commitment. “Explore another path” clones a checkpoint into a separate slot; it does not rewind or overwrite the current world. An ending becomes a profile unlock only after its scene completes and the server records it. Chapter replay uses actual checkpoint state, not fabricated full progress.

The two route outcomes and eligible secret alternatives can be explored from the final checkpoint; another route requires a compatible earlier checkpoint and its quests. Postgame preserves that ending's world and allows reading, writing, decor, remaining resident activities and discovery. Profile-wide secrets may unlock gallery information, but cannot substitute for missing per-save story prerequisites.

## 5. Sound, secrets, and achievements

Audio target: four original looping music pieces (title, library, courtyard, discovery) plus a finale cue; three ambience beds; at least eighteen short interaction sounds. Chapter arrangements can reuse themes. Sound covers footsteps, doors, paper, writing, mail, coffee, furniture, dialogue and achievements. Use fades and subtle variation; do not play a loud effect for every letter typed.

Provide Godot audio buses for master/music/ambience/effects, remembered sliders and mute, and a window-focus policy. Keep startup quiet until the player enters the game, avoid duplicate players when reopening menus, and handle device changes. If a web export is later shipped, also verify browser autoplay and suspended-audio behavior.

Secrets belong to the world: the three existing treat locations, a constellation visible from the courtyard, an unusual shelf order, a margin note that changes after a chapter, and Miso's hidden attic route are candidate designs. Give clues and permanent discovery records. Essential progression never depends on finding them; revisit unlocked locations after the ending.

Achievement budget: seven chapter milestones, five resident-story completions, six reading/writing/restoration milestones, and six exploration milestones. Examples: **First Light**, **A Letter Answered**, **A Room of Your Own**, and **Miso Approves**. Award from validated saved events, once per profile; show a brief pixel toast and journal entry. Backfill only achievements that existing save data actually proves. No reward should require buying AI access.

## 6. Provider setup as a finished game feature

Access the same settings from the startup menu, pause menu, or laptop. Use a short guided flow:

1. Choose local Ollama, Groq free tier, a specific OpenRouter free model, or a custom compatible endpoint. Free hosted availability and quotas can change.
2. Enter the exact model ID, endpoint and session key if required. Local services may be unauthenticated. Automatic model routers cannot qualify.
3. Explicitly run the three-request benchmark. Send only synthetic test data. Show the task scores, failed checks, response time and qualification threshold.
4. Block gameplay below 80/100 or on any critical error; invite another model or a retest. Qualification never depends on model branding, parameter count or payment.
5. Bind success to this session, endpoint, model and credential; invalidate it after setup changes or a failed retest. Preserve manuscripts and provide retry/setup controls after transport errors.
6. Return to play. Changing providers during a pending request is rejected. Per-role models, budgets, cancellation and qualified fallback selection remain later M3 work.

New secrets are submitted once through the authenticated local API and held in server memory by default. Clear the input after submission; never echo secrets through bootstrap, usage, logs, exports, or browser storage. Keep existing environment-based credentials compatible. For opt-in persistent credentials on Windows, use the operating system's credential store through a maintained narrow integration selected during implementation; if unavailable, expose session-only storage clearly, with no silent plaintext fallback. Test replacing and deleting credentials.

The server remains bound to localhost with its existing host/origin/token protections. Validate endpoint schemes and keep remote HTTPS requirements. Connection tests must exercise only the selected provider and the selected credential, without silently succeeding through a fallback. Cancel/timeouts must leave the game responsive. Changing provider settings must respect the existing active-job guard.

Show friendly task progress in the laptop and put raw logs/model details in an expandable technical view. Preserve estimates as estimates: the local call budget is not the provider's billing balance. Authored greetings remain for characterization. Garden discussions require real AI responses, with progress committed by the server only on success. The model cannot set resource values or choose quest outcomes.

## 7. Implementation sequence and completion gates

Follow this sequence for feature/content completion. The user's engine correction authorizes building the native M1 foundation alongside remaining M0 art/book review; it does not waive those reviews or complete either gate. Each milestone leaves a runnable game; larger content production starts only after the complete opening chapter passes its gate.

| Milestone | Concrete work | Gate before proceeding |
| --- | --- | --- |
| M0 — Baseline and visual target | Capture the legacy browser flow and native engine target; inventory assets/state; produce visual references; outline routes/endings and three modes; start the campaign edition/rights ledger and approve the first two books. | Baseline passes; visual samples cohere inside Godot; asset/route/mode inventories and catalogue eligibility rules exist; existing data paths documented. |
| M1 — Native game shell and saves | Build the Godot project, three mode cards, title/pause/settings/save flows, gallery shell, migration/checkpoint cloning, bundled asset loading, tutorial state and server-owned mode/source rules. | Godot scenes are editable and runnable; all modes create/resume distinct slots; legacy saves recover; guidance persists; campaign rejects foreign-source IDs and imports before new intake features ship. |
| M2 — Complete opening chapter | Finish 1630 in final-quality art with two approved bundled complete books, adaptive teaching, integrated activities, first reward/secret/achievement, music and a lasting choice. | The opening finishes with a qualified hosted or local model; experienced players skip teaching; both choice variants survive reload; required sources are complete and rights-reviewed; book import remains unavailable. |
| M3 — Providers and assistance | Deliver the guided setup above; finish laptop job feedback, recovery, cancellation and manuscript integration. | Existing providers and a mock custom endpoint pass setup/failure checks; no secret leaks; mandatory qualification with fully mocked automated checks; rejected requests do not spend game resources. |
| M3a — Free Play and Modern | Finish sandbox goals/creative furnishing; build the contemporary Sources desk, file/link import, current-source discovery, provenance/snapshots and project export with mode-specific tutorials. | Free Play works without campaign completion; Modern imports a book and crafts a cited manuscript with a current-source fixture; manual use is offline-capable; every cross-mode source attempt is rejected. |
| M4 — Living library and route proof | Add spaces, schedules, relationships, decor, day phases and consequences; finish Open Library through both endings as the first route implementation. | All objects are reachable; resources recover; first route has three visual/two functional changes and later callbacks; both endings differ in play and scene; tutorial explains the charter. |
| M5 — Full branching campaign | Complete seven chapters, fourteen side quests, eighteen route quests, six routes, 180+ English exchanges, fourteen endings and fourteen approved complete books; finish conversion/replay. | Every ending finishes with qualified AI from valid states; edition/date eligibility and all required texts are verified; no source contamination or missing prerequisite paths; postgame retains source restrictions. |
| M6 — Discovery and production art/audio | Finish assets, secrets/achievements, portraits, era/route/Modern dressing, Free Play themes, ending scenes, music, sounds, book/asset attributions and credits. | Every mode/route has a coherent visual identity; each ending has staging; all books/assets/content are accounted for and no release path contains placeholders. |
| M7 — Release candidate | Run save migration/recovery, native engine, input, accessibility, audio, performance and complete playthrough checks; retain browser regressions; tune pacing; document launch and recovery. | Every release condition below passes, with recorded evidence and no blocking defects. |

**M2 acceptance walkthrough:** title → AI qualification → new save → rainy arrival → learn movement/interact → talk to Margot → browse and study an observation → prepare a short commission at the desk → send a letter → choose a day-cost activity → collect a reply → earn and place the first lamp improvement → discover a Miso clue → save → return to title → continue at the correct state. Early free exploration and dialogue add texture; typing speed must not be used to force the target duration.

Also test the same opening with guidance skipped, activities completed out of order, alternate input bindings and a reload mid-lesson. Add a choice between a shared reading space and patron-supported study equipment; show the changed room and visitor response immediately. A deterministic later-event check proves that the choice produces different 1680 correspondence without requiring the whole second chapter in M2. Neither choice locks a route at this stage.

The expanded routes and art inventory materially increase production work. M4 deliberately completes one route and both its endings before M5 produces the remaining five, so writing, art and consequence work can be measured. Maintain a content ledger with quest IDs, prerequisites, choice effects, affected scenes/assets, language status and ending reachability. Shared chapter geography limits duplication; it must not remove the requested route-specific quests or distinct endings.

Introduce ordinary game systems only when their milestone needs them. Use Godot's native 2D scene tree, CharacterBody2D/StaticBody2D collision, Control UI, resources and audio facilities. Reuse the Python campaign rules, provider router and writing pipeline through slot-scoped operations. Keep the legacy browser implementation available during migration, but new game presentation work belongs in Godot.

## 8. Code and data boundaries

| Existing location | Planned responsibility |
| --- | --- |
| `godot/project.godot`, `godot/main.tscn`, `godot/main.gd` | Native Godot project, scene flow, themed interface and local API integration; extract authored content and reusable panels as they grow |
| `godot/room.gd`, `godot/player.gd` | Editable native room/player preview, rendering and physics; evolve into reusable actor/room scenes with sprite atlases |
| New assets/content under `godot/` | Bundled sprites, portraits, font/audio, origin/license manifest and stable English content IDs |
| `game/index.html`, `game/style.css`, `game/app.js`, `game/world.js` | Preserved legacy interface and behavior reference during migration; not the target game frontend |
| `run_lamplight.py` | Portable engine setup, launch/editor lifecycle and temporary-save engine verification |
| `game_native.py` | Native API, immutable mode-owned slots/documents and source checks; extend for migration, snapshots, jobs and Modern intake |
| `game_campaign.py` | Validated progression, choices, resource/relationship outcomes, route commitments, historical/fictional provenance, ending eligibility and rewards |
| `game_server.py` | Retained browser server, download/cache and security helpers; reuse backend capabilities without exposing unscoped legacy routes on the native listener |
| `research.py`, `game_catalog.py` | Reuse extraction/search/citation helpers through explicit per-mode policies; curate campaign edition/rights metadata; keep personal/current sources outside campaign resolution |
| `llm.py`, `pipeline.py` | Reuse routing/writing; integrate credentials and pinned per-job mode/source policy without changing unrelated article-writer defaults |
| Python tests, native engine checks and legacy browser check | Verify server rules, Godot scenes/input/UI and retained behavior; use temporary saves and mocked providers |

Godot loads bundled resources through `res://`; game assets do not require widening the old browser server's static routes. Add missing-resource behavior and loading feedback inside the engine. The native localhost listener exposes only authenticated game operations, never the project/save/credential directories. Preserve host/origin/token protections and pin each operation to its owning slot. Export/package the Python companion deliberately; mobile/web exports need their own service and storage design before release.

Use a small explicit flow: boot, title, playing, dialogue, panel, paused, transition, ending. Opening a modal clears movement intent; closing it restores focus to its trigger. Define what happens to an active generation job before returning to the title or switching saves: continue within the same slot, or cancel at a checkpoint and await acknowledgement before switching. Never attach a late response to another save or era.

Save slots separate campaign progression, tutorial progress, difficulty, room state, relationships, quests, completed projects, route history and ending state. Presentation/provider settings and credentials are machine-level; achievements and the ending gallery are profile-level; each manuscript and job retains its originating slot/collection. Branch checkpoints copy all relevant slot state and isolate subsequent document/job writes; they reference immutable book assets. Preserve the current documents, cached books and job checkpoints during migration. Give imported legacy manuscripts a visible home and assign old campaign state to a named imported slot. Existing completed saves retain their original completion; do not invent route decisions or retroactively award an unplayed ending.

Make `mode` immutable slot metadata (`campaign`, `free_play`, `modern`); keep writing style (`manual`, `guided`, `auto`) separate so the two concepts cannot be confused in requests. Every source/document/job/snapshot records its owning collection and permitted modes. Shared bundled bytes may be deduplicated, but that never grants eligibility to another edition or mode. At job creation, pin slot, mode, era, allowed source IDs and source snapshots; repeat validation on resume/result attachment. A mode switch cannot change the policy of a running job.

Migrate existing historical progress into Campaign and the existing unrestricted English reading state into Free Play. Preserve unknown-origin legacy manuscripts in a clearly labeled Modern import workspace for review, not automatically as campaign evidence. Retain documents already linked to historical submissions with their original provenance. Back up first and preserve existing IDs/bookmarks; never infer campaign eligibility from a filename or matching book title.

Store a compact append-only list of major validated decisions alongside current campaign state, with stable event IDs, era and affected projects. Use it for journal causality and migration, not as a general event-sourcing framework. Apply each decision, resource change and reward atomically; render tutorial/world reactions only after success. Client preference or tutorial requests cannot set authoritative quest/route/ending flags. Resolve simultaneous eligible secret and ordinary finales through an explicit player selection; reject ineligible choices server-side. Route conversion, checkpoint cloning and delayed AI results must respect existing job/era locks.

Back up old data before migration, use versioned state and atomic replacement, reject unknown newer formats without overwriting them, and offer restore/export through the game. Store gameplay-affecting outcomes on the server, not through the current arbitrary `/api/state` payload. Reserve client preferences for presentation. Test interrupted writes and repeated quest/reward actions.

## 9. Verification and release conditions

Run the existing deterministic baseline throughout:

```powershell
rtk python -m unittest test_game_library test_game_campaign -q
rtk python check_game_browser.py
rtk python -m unittest test_game_native -q
rtk python run_lamplight.py --check
rtk python run_lamplight.py --capture
```

The browser command requires the existing optional Playwright/Chromium setup. Native checks require the pinned Godot engine (install into the project cache with `rtk python run_lamplight.py --setup`, or supply `--godot PATH`). Native checks/captures use temporary saves and mocked provider responses through the real qualification path. Extend focused checks for save migration, quest transitions/reward idempotency, achievement backfill, provider validation and slot/job isolation. Make any real paid connection test deliberate.

Maintain one table-driven route check with valid action sequences for all fourteen endings, plus invalid prerequisites, route conversion, repeated choice submission and checkpoint cloning. Check the authored prerequisite graph for unknown IDs, unreachable required quests and conflicting commitments. Cover the thirty directed route conversions at the shared state-transition boundary without requiring thirty separately authored stories. Browser checks cover the complete opening, one route's two finales, tutorial adaptivity and settings persistence; inspect each remaining finale/route scene with reproducible saves. Automated reachability does not replace a full human playthrough with qualified local or hosted AI of each route and visual review of every ending.

Add mode-policy checks covering direct API calls as well as visible UI: reject Campaign uploads/URL imports/local scans and Modern IDs in reading, generation, feedback, saved dossiers and restored jobs. Spy on discovery/local-library functions to prove Campaign never calls them. Check save switching during a job, snapshot isolation, forged mode fields and postgame restrictions. For Modern, use local fixtures for each supported file type, duplicates, malformed/empty extraction, dated/undated web results and changed-source snapshots; no live provider call is required. Verify Free Play creative furnishing cannot award campaign progress.

Release requires all of the following:

- [ ] From startup through credits, every visible game screen uses the agreed visual system, including lettering, errors, settings and loading states.
- [ ] Campaign, Free Play and Modern are selectable after AI qualification, have independent resumable saves and present the correct source rules/tutorials.
- [ ] Free Play supports optional goals and creative furnishing without requiring Campaign; world changes persist and cannot unlock campaign routes/endings.
- [ ] Modern can import supported books/documents, inspect extraction, gather dated current-source fixtures, write/revise and export with traceable references; partial and failed sources are labeled accurately.
- [ ] Campaign contains at least fourteen complete royalty-free works with verified edition/date/rights records, at least two newly available per era, and all required texts bundled offline.
- [ ] Campaign cannot accept player-supplied books or current-source imports through UI, direct APIs, jobs, caches, restore or mode switching; postgame enforces the same policy.
- [ ] A new player can discover the next action from the world/dialogue/journal without external instructions.
- [ ] Tutorial modes, skipping, replay, out-of-order actions, contextual hints, rebinding and mid-lesson reload all work without repeated rewards or forced interruptions.
- [ ] All seven chapters, fourteen side quests, eighteen route quests, five resident arcs, six routes and fourteen authored endings are playable; all twelve secrets and 24 achievements are tracked.
- [ ] Each route has three persistent visual changes, two functional changes and three later callbacks; the timeline journal explains their causes.
- [ ] Every ending is reachable from legitimate play; final choices respect previous commitments; checkpoint replay preserves the original save and cannot leak progress across slots.
- [ ] Historical source material and fictional timeline documents stay distinct in the reader, letters and writing pipeline; AI cannot change canonical world state.
- [ ] The asset ledger is complete: matching portraits/sprites, clean animation anchors, object states, era/route variants, pixel lettering and distinct ending compositions pass in-game review.
- [ ] All settings pages apply, cancel, reset and persist correctly; accessibility/relaxed settings preserve route and reward eligibility; save deletion cannot be confused with restoring defaults.
- [ ] The complete campaign requires qualified AI; a local model supports play without hosted requests. Uncached modern books clearly explain their download requirement.
- [ ] English text fits all screens and include correct glyphs. Full keyboard operation, readable UI scaling, reduced motion and audio-independent cues work.
- [ ] Native screenshots reviewed at 1280×720 and 1920×1080, plus a deliberately implemented 390×844 mobile layout. Fractional Windows display scaling does not hide controls; browser zoom remains covered for any retained browser/web-export flow. The current native foundation is desktop-only and does not satisfy the mobile gate.
- [ ] Music loops cleanly; slider values persist; repeated menu opening creates no duplicate audio; tab switching and muted startup behave correctly.
- [ ] On a recorded reference machine, target 60 fps and a 95th-percentile frame duration under 20 ms during normal room play. Asset loading and generation do not freeze input. Record results rather than claiming universal performance.
- [ ] New game, overwrite confirmation, continue, save switching, legacy import, abrupt reload, interrupted generation and backup recovery preserve player work.
- [ ] No browser errors, broken asset paths, unreachable required objects, duplicate rewards, or campaign dead ends remain.
- [ ] Provider setup succeeds from the game; authentication/model/network failures are recoverable; credentials never appear in ordinary saved game data or returned settings.
- [ ] Playtest at least three first-time players: observe the opening without coaching, collect pacing/readability/confusion notes, fix blocking problems, and repeat affected sections.
- [ ] Asset attribution, launch instructions, backup/recovery instructions and known limitations ship with the release.

The first implementation deliverable is **M0–M2: a polished, complete 1630 opening with enforced campaign source rules**, followed by the remaining milestones, including **M3a: fully usable Free Play and Modern modes**. A title screen reskin alone does not satisfy this plan, and the opening chapter alone does not complete the requested game.
