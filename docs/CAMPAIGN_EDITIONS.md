# Campaign edition review

Review started 2026-09-08. **No complete edition is approved or bundled yet.**
This ledger is production research, not the runtime allowlist. The fourteen
records in `game_campaign.BOOKS` remain original bilingual study notes.

## Admission rule

Approve a specific edition, not a title. Record original publication date,
edition date, translator and translation date, language, source URL, rights
evidence for the text and any illustrations, permitted distribution territories,
attribution, first eligible era, and the exact bundled file and SHA-256.
Keep digitization date separate from the historical edition date. Modern
introductions, annotations and translations cannot inherit an original's date.

Eligibility starts in the first campaign era on or after the edition's latest
historically relevant contribution. A faithful digital transcription may
represent an older edition, but its source edition and omissions must be checked.
Modern editorial apparatus stays outside historical evidence. New bilingual
game notes are labeled original teaching aids and never count as complete works.

Before approval, check the beginning and end, chapter/section inventory, omitted
pages and illustrations against the identified edition. A scan-only PDF or an
uncorrected OCR dump is not yet a usable complete text for the current reader.
Record printed-page or section locators independently of reader pagination.

Rights must permit the intended inclusion without royalties in the recorded
territories. Do not infer worldwide rights from a US public-domain flag, or
reuse a scan provider's images under a transcription's license. Do not contact
rights holders automatically; use a qualifying alternative when available.

Approval later creates a distinct campaign ID and immutable bundled text. A
matching title, imported file, positive archive ID or cached dossier never
grants campaign eligibility. All access must resolve through the originating
server-owned slot; client fields cannot change its mode. This is an M1
implementation requirement, not a claim about the current collection API.

## Opening candidates

| Field | `candidate.galileo.sidereus.1610.la` | `candidate.bacon.instauratio.1620.la` |
| --- | --- | --- |
| Work / author | *Sidereus nuncius*, Galileo Galilei | *Instauratio magna*, including *Novum organum*, Francis Bacon |
| Original / proposed edition year | 1610 / 1610 | 1620 / 1620 |
| Edition | Venice, Thomas Baglioni; Library of Congress item 2010667904 | London, J. Billium; University of Toronto, Thomas Fisher Rare Book Library; BHL item 86613 |
| Language / translation | Latin; original, no translation approved | Latin; original, no translation approved |
| Earliest possible era | 1630, if this edition passes review | 1630, if this edition passes review |
| Edition evidence | [Library of Congress item record](https://www.loc.gov/item/2010667904/); catalogue search returned the 1610 imprint, but direct record access returned HTTP 403 during this review | [BHL item record](https://www.biodiversitylibrary.org/item/86613), dated 1620 and identifying the holding institution |
| Rights evidence | Item-level rights and scan reuse evidence still needed | The item explicitly supplies no copyright status; approval cannot be inferred from the download link |
| Illustrations | Original diagrams need inventory and scan-rights review; modern cover material excluded | Frontispiece/figures need inventory and scan-rights review; modern cover material excluded |
| Territories | Not cleared | Not cleared |
| Attribution proposal | Galileo Galilei; edition and holding institution above; final wording pending source terms | Francis Bacon; University of Toronto, Thomas Fisher Rare Book Library; Biodiversity Heritage Library; final wording pending source terms |
| Bundle / hash / completeness | None; not verified | None; not verified. Page listing jumps from 172 to 181; determine whether this is original pagination or missing leaves before treating it as complete |
| Decision | Candidate only; not an approved 1630 book | Candidate only; prefer an explicitly licensed transcription or another qualified edition |

Latin originals preserve the era boundary, but cannot carry the English/Spanish
opening lesson alone. M2 must provide original bilingual study aids and a usable
reader presentation. Do not silently substitute a later English translation.

## Alternatives checked

| Source | Evidence and disposition |
| --- | --- |
| Bacon, *The Advancement of Learning*, TCP A01516 | The [publisher's transcription repository](https://github.com/textcreationpartnership/A01516) identifies a CC0 transcription and enumerates 219 omitted fragments, including foreign text and page entries marked duplicate. Text licensing is promising; the digital header, underlying edition and substantive gaps need inspection. Page-image rights are separate. Not approved as a complete book. |
| Bacon, *New Atlantis*, Project Gutenberg 2434 | The [ebook record](https://www.gutenberg.org/ebooks/2434) is a discovery lead. A [Library of Congress 1627 volume](https://www.loc.gov/item/95109524/) identifies *New Atlantis* as issued with *Sylua syluarum*. That does not establish which print edition the Gutenberg transcription represents. Not approved. |
| Shakespeare, *Sonnets*, Project Gutenberg 1041 | The [ebook record](https://www.gutenberg.org/ebooks/1041) is a possible shorter opening work. Verify the precise source edition and all 154 sonnets, translation/editorial layers and distribution scope before admission. Not approved. |

Project Gutenberg's [permission guidance](https://www.gutenberg.org/policy/permission.html)
requires attention to the ebook's license and territory. Its archive catalogue
remains a separate collection; existing downloads are not campaign approvals.

## Next production action

Obtain two explicitly reusable, complete transcriptions with documented
pre-1630 source editions, replacing candidates where needed. Verify and hash
their exact bytes, record the rights scope, and bundle them independently of
the download cache. Until then, the M0 two-book approval gate remains open;
the full-campaign fourteen-book gate has made **0 / 14 approved** progress.
