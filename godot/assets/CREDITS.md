# Lamplight asset credits

- `portraits/*.png`: thirteen original generated pixel-art conversation portraits,
  built-in image generation, 2026-09-09. Covers all current residents and seven
  historical debate partners. Historical likenesses are stylized illustrations,
  not archival portraits. [Exact prompts and file roster](portraits/README.md).

- `cozy-world.png`: original generated four-scene atlas (library, town square,
  print shop and garden). Built-in image generation, 2026-09-09.
- `cozy-characters.png`: original generated six-character, three-pose atlas.
  Built-in image generation, 2026-09-09.
- `miso.png`: original generated three-frame ginger-cat sprite strip.
  Built-in image generation, 2026-09-09. No game-reference assets were copied.
- `pixelify.ttf`: Pixelify Sans, copyright 2021 The Pixelify Sans Project Authors,
  SIL Open Font License 1.1. Full license: `OFL-pixelify.txt`.
  Source: https://github.com/google/fonts/tree/main/ofl/pixelifysans
- `mystical-piano.ogg`: **Mystical Piano**, Indieteur, CC0. Source MP3 trimmed
  at the author's specified 1:35 loop point and encoded as Ogg Vorbis.
  Source and license declaration: https://opengameart.org/content/mystical-piano
  License: https://creativecommons.org/publicdomain/zero/1.0/
- Interaction tones, footsteps and ambience: original synthesized waveforms in
  `audio.gd`; no third-party samples.

The art references guide atmosphere and readability only. Pokémon, Stardew Valley
and Game Dev simulation games supplied no sprites, textures, music or UI assets.

## Final generation prompts

The built-in image tool produced the raster assets. Files are bundled in
this directory, not loaded from an external service at runtime.

**World:** Original cozy pixel-art atlas, exact 2×2 grid of equal 16:9 scenes.
Daylight village life; cream plaster, honey wood, green foliage, terracotta roofs.
Library with shelves, ordinary window, a desk and the traveler's modest laptop;
town square with library/print-shop doors and garden path; printer workshop;
public reading garden. Fixed slightly overhead camera, clear lower-half walking
space. No characters, text, magic, neon or fantasy palace.

**Characters:** Transparent 6×3 sprite atlas. Cozy life-sim proportions, readable
pixel clusters and simple everyday clothing. Columns: teal-sweater protagonist
with satchel, librarian in burgundy skirt, lens maker in blue apron, grey-haired
teacher, printer in ochre vest, bookbinder in sage. Rows: front idle, left-foot
walking pose, right-foot walking pose. Uniform cells, identical baseline, no
background, labels, glowing objects, capes or weapons.

**Miso:** Transparent three-cell horizontal strip of the same seated ginger
tabby with cream muzzle and dark tail tip. Attentive, blinking, and tail-curled
poses; consistent baseline and scale; warm pixel clusters, no text or background.
