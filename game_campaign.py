"""Small, offline-playable historical campaign. No model controls money or time.

The study editions below are original summaries, not quotations or full copies.
Links identify historical source works; modern linked editions are outside play.
Unknown-date Gutenberg editions deliberately remain outside the campaign.
"""
from __future__ import annotations

import copy
import hashlib
import re
import uuid

YEARS = (1630, 1680, 1730, 1780, 1830, 1880, 1930)
PLACES = ("Private library", "Experimental society", "Printer's reading room",
          "Republic of letters", "Literary salon", "Research institute", "International institute")
CAPABILITIES = ("Quill and hand press", "Air pump and experimental notebooks",
                "Periodicals and subscription printing", "Learned correspondence and electrical apparatus",
                "Lending libraries and lithography", "Telegraph and steam printing",
                "Typewriter, radio and international journals")

# Original English study notes: date refers to the work, not a modern eBook upload.
# Keep each account within the knowledge of its publication date.
_WORKS = [(1610,
  'Sidereus Nuncius',
  'Galileo Galilei',
  'Science',
  'https://ntrs.nasa.gov/api/citations/20140016708/downloads/20140016708.pdf',
  'Repeated observations through a telescope show small lights changing position around Jupiter. A sequence '
  'of observations makes a stronger case for orbiting companions than a single drawing. Instrument defects '
  "and the reliability of another observer's telescope remain questions to test."),
 (1605,
  'Don Quijote · primera parte',
  'Miguel de Cervantes',
  'Literature',
  'https://www.gutenberg.org/ebooks/2000',
  'A reader of chivalric romances sets out to live by their rules. His expectations clash with what other '
  'people see. The distance between an adventurous account and an ordinary explanation lets a writer examine '
  'how stories shape judgment. This note concerns the first part only.'),
 (1661,
  'The Sceptical Chymist',
  'Robert Boyle',
  'Science',
  'https://www.gutenberg.org/ebooks/22914',
  'Separating a substance by fire does not by itself establish that the products were its original elements. '
  'Heat may produce changes rather than merely reveal ingredients. A useful experiment must distinguish '
  'those possibilities instead of treating the familiar account as proof.'),
 (1644,
  'Areopagitica',
  'John Milton',
  'Politics',
  'https://www.gutenberg.org/ebooks/608',
  'Milton argues against licensing books before publication. Reading opposing arguments can exercise '
  'judgment rather than simply corrupt it. This is a dispute about prior restraint, not a promise that every '
  'view receives equal protection or that printing has no consequences.'),
 (1729,
  'A Modest Proposal',
  'Jonathan Swift',
  'Literature',
  'https://www.gutenberg.org/ebooks/1080',
  'A calculating narrator presents an appalling remedy for poverty as if people were entries in an account '
  "book. The proposal is satire, not practical advice. The gap between the speaker's confidence and the "
  'cruelty of his reasoning asks readers to question whose interests respectable calculations serve.'),
 (1704,
  'Opticks',
  'Isaac Newton',
  'Science',
  'https://www.gutenberg.org/ebooks/33504',
  'Prisms separate light into colours. Testing separated rays with another prism helps distinguish a change '
  'created by the glass from a difference already present in the light. The arrangement of the apparatus '
  'matters: an impressive display is not enough to decide between explanations.'),
 (1751,
  'Experiments and Observations on Electricity',
  'Benjamin Franklin',
  'Science',
  'https://founders.archives.gov/documents/Franklin/01-04-02-0039',
  'Letters describing electrical experiments allow distant investigators to compare procedures. A report '
  'should describe the apparatus and circumstances, including trials that failed. Agreement about an '
  'observed effect need not settle the explanation of electricity. This is historical discussion, not an '
  'instruction to conduct dangerous experiments.'),
 (1776,
  'The Wealth of Nations',
  'Adam Smith',
  'Politics',
  'https://www.gutenberg.org/ebooks/3300',
  'Dividing production into specialised tasks can increase output through practice, saved time and '
  'machinery. The reach of exchange limits how far specialisation can go. A larger output alone does not '
  'tell us how gains are distributed or what repetitive work does to the worker.'),
 (1818,
  'Frankenstein · 1818',
  'Mary Shelley',
  'Literature',
  'https://www.gutenberg.org/ebooks/41445',
  "A creator recoils from the being he has made. The creature's account complicates the creator's account: "
  'abandonment and exclusion matter alongside ambition. An argument about responsibility should hear both '
  'narratives before deciding whose actions require an explanation.'),
 (1813,
  'Pride and Prejudice',
  'Jane Austen',
  'Literature',
  'https://www.gutenberg.org/ebooks/1342',
  'First impressions acquire authority before they have been tested. Letters and later encounters oblige '
  'characters to reconsider what they thought they knew. Marriage is also shaped by property and family '
  'expectations; a reading concerned only with personal attraction misses those pressures.'),
 (1859,
  'On the Origin of Species · 1859',
  'Charles Darwin',
  'Science',
  'https://www.darwinproject.ac.uk/letters',
  'Variation among organisms and the struggle for existence allow differences in survival and reproduction '
  "to accumulate. Artificial selection offers a comparison, not proof that nature has a breeder's intention. "
  'Difficult cases and gaps in the record belong in the argument; omitting them would conceal what the '
  'explanation still needs to establish.'),
 (1859,
  'On Liberty',
  'John Stuart Mill',
  'Philosophy',
  'https://www.gutenberg.org/ebooks/34901',
  'Suppressing an opinion can hide a truth or prevent a true belief from being understood through challenge. '
  "The distinction between harm to others and disapproval of someone's conduct matters. Applying that "
  'distinction requires an argument about the particular case, not merely announcing that freedom is '
  'valuable.'),
 (1911,
  'Radium and the New Concepts in Chemistry',
  'Marie Curie',
  'Science',
  'https://www.nobelprize.org/prizes/chemistry/1911/marie-curie/lecture/',
  'Radioactivity provides a way to follow small quantities of active substances during separation. Chemical '
  'isolation and measurements of activity support different parts of the case for a new element. A '
  'persuasive report explains what each measurement establishes rather than letting a striking result stand '
  'for every claim.'),
 (1920,
  'Relativity · Lawson translation, 1920',
  'Albert Einstein',
  'Science',
  'https://www.gutenberg.org/ebooks/5001',
  'A judgment that two distant events occur at the same time needs a procedure for comparing clocks and '
  'signals. Observers in relative motion need not assign the same simultaneity. An argument should specify '
  "its frame of reference instead of assuming that one observer's time is everyone's time.")]

BOOKS = {-(i + 1): dict(id=-(i + 1), year=w[0], title=w[1] + " · study notes",
    authors=[w[2]], categories=[w[3]], languages=["en"], subjects=[w[3]],
    summary=w[5], url=w[4], rights="Original English game summary; not a quotation or a full edition.",
    notes={"en": w[5]}) for i, w in enumerate(_WORKS)}

FIGURES = [
    dict(id="galileo", name="Galileo Galilei", born=1564, died=1642, active=1610, book=-1),
    dict(id="boyle", name="Robert Boyle", born=1627, died=1691, active=1661, book=-3),
    dict(id="swift", name="Jonathan Swift", born=1667, died=1745, active=1729, book=-5),
    dict(id="franklin", name="Benjamin Franklin", born=1706, died=1790, active=1751, book=-7),
    dict(id="shelley", name="Mary Shelley", born=1797, died=1851, active=1818, book=-9),
    dict(id="darwin", name="Charles Darwin", born=1809, died=1882, active=1859, book=-11),
    dict(id="curie", name="Marie Curie", born=1867, died=1934, active=1911, book=-13),
]


def new_game():
    return dict(version=1, era=0, day=1, money=24, paper=8, prestige=0,
                knowledge=0, studied=[], letters=[], publications=[], completed=False)


def available(state):
    return [b for b in BOOKS.values() if b["year"] <= YEARS[state["era"]]]


def figures(state):
    year = YEARS[state["era"]]
    return [f for f in FIGURES if f["active"] <= year < f["died"]]


def requirements(state):
    tier = state["era"]
    return dict(money=100 + 50 * tier, paper=3 + tier, prestige=4 + 3 * tier,
                knowledge=2 + tier, publications=1 + tier // 2)


def commission(state):
    tier = state["era"]
    return dict(words=150 + tier * 50, sources=1 + tier // 2, paper=2 + tier,
                payment=50 + tier * 25, prestige=2 + tier, letter=tier > 0)


def public_state(state):
    result = copy.deepcopy(state)
    for letter in result["letters"]:
        delivered = letter["era"] < state["era"] or letter["due"] <= state["day"]
        if not delivered:
            letter.pop("answer", None)
        letter["delivered"] = delivered
    for publication in result["publications"]:
        publication.pop("fingerprint", None)
    count = sum(p["era"] == state["era"] for p in state["publications"])
    needed = requirements(state)
    result.update(year=YEARS[state["era"]], place=PLACES[state["era"]],
                  capabilities=list(CAPABILITIES[:state["era"] + 1]),
                  figures=figures(state), requirements=needed, commission=commission(state),
                  era_publications=count, years=YEARS,
                  can_jump=not state["completed"] and all((count if k == "publications" else state[k]) >= v for k, v in needed.items()))
    return result


def period_context(state):
    year = YEARS[state["era"]]
    return (f"HISTORICAL CAMPAIGN: the year is {year}. You are a fictional resident of "
            f"a {PLACES[state['era']]}, not the modern laptop. Do not know or cite events, "
            "discoveries, books, terminology, or people from later years. If the player mentions "
            "future knowledge, treat it as an unverified proposal and ask for evidence available now. "
            "Use only the supplied period notes as factual context. They are original game summaries, "
            "not quotations from the historical works. Do not invent personal recollections. "
            "You cannot change campaign resources or deliver actual mail.")


def act(state, data, documents=()):
    """Return a new state or raise; a rejected action never partly spends resources."""
    s = copy.deepcopy(state)
    action = data.get("action")
    tier = s["era"]
    allowed = {b["id"] for b in available(s)}
    if s["completed"]:
        raise ValueError("Campaign complete. Your library and manuscripts remain available.")
    if action == "study":
        book_id = data.get("book")
        if type(book_id) is not int or book_id not in allowed:
            raise ValueError("That work is not available in this period")
        if book_id in s["studied"]:
            raise ValueError("Already studied; rereading is free but does not farm knowledge")
        s["studied"].append(book_id)
        s["knowledge"] += 1
        s["day"] += 1
    elif action == "work":
        s["money"] += 12 + 3 * tier
        s["paper"] += 1
        s["day"] += 1
    elif action == "wait":
        s["day"] += 1
    elif action == "letter":
        figure = next((f for f in figures(s) if f["id"] == data.get("figure")), None)
        text, lang = data.get("text"), "en"
        focus = data.get("focus", "evidence")
        if not figure or not isinstance(text, str) or not 20 <= len(text.strip()) <= 3000:
            raise ValueError("Choose an available correspondent and write 20–3000 characters")
        if focus not in ("evidence", "counterargument", "method"):
            raise ValueError("Choose a language and a debate question")
        if figure["book"] not in s["studied"]:
            raise ValueError("Study the correspondent's work before writing")
        parent = data.get("reply_to")
        if parent and not any(l["id"] == parent and l["figure"] == figure["id"] and l["era"] == tier and l["due"] <= s["day"] for l in s["letters"]):
            raise ValueError("Reply only to a delivered letter from this correspondent in this era")
        if sum(l["era"] == tier and l["due"] > s["day"] for l in s["letters"]) >= 3:
            raise ValueError("At most three letters may be in transit")
        fee = 4 + tier
        if s["money"] < fee or s["paper"] < 1:
            raise ValueError("Not enough money or paper for postage")
        questions = {"evidence": "Which observation distinguishes your explanation from an alternative?",
                     "counterargument": "Consider the strongest objection. What survives it, and what must you revise?",
                     "method": "How could another reader check your claim with the materials available?"}
        opening = "I have read your reply. Let us examine the remaining question." if parent else "Your letter raises a question worth examining."
        answer = f"{opening}\n\n{BOOKS[figure['book']]['notes']['en']}\n\n{questions[focus]}\n\n{figure['name']}"
        s["letters"].append(dict(id=uuid.uuid4().hex, figure=figure["id"], name=figure["name"], era=tier,
            sent=s["day"], due=s["day"] + max(1, 4 - tier // 2), text=text.strip(), language=lang,
            focus=focus, reply_to=parent, answer=answer, book=figure["book"],
            simulation="Curated fictional reply, not an authentic letter or a live AI response"))
        s["money"] -= fee
        s["paper"] -= 1
    elif action == "publish":
        doc = next((d for d in documents if d["id"] == data.get("document")), None)
        terms = commission(s)
        ids = data.get("books", [])
        if not isinstance(ids, list) or any(type(i) is not int or i not in allowed or i not in s["studied"] for i in ids):
            raise ValueError("Use studied sources available in this period")
        ids = set(ids)
        if len(ids) < terms["sources"] or not any(BOOKS[i]["year"] > (YEARS[tier - 1] if tier else 0) for i in ids):
            raise ValueError("Include enough studied sources and at least one new work from this era")
        if not doc:
            raise ValueError("Save a manuscript before submitting it")
        text = doc["text"]
        tokens = re.findall(r"[^\W_]+", text.lower(), re.UNICODE)
        fingerprint = hashlib.sha256(" ".join(tokens).encode()).hexdigest()
        if len(tokens) < terms["words"] or len(set(tokens)) < 45:
            raise ValueError(f"Commission requires {terms['words']} words and at least 45 distinct words")
        if any(p["document"] == doc["id"] or p["fingerprint"] == fingerprint for p in s["publications"]):
            raise ValueError("This manuscript has already been paid for")
        if any(f"[B{abs(i)}]" not in text for i in ids):
            raise ValueError("Credit each selected study note in the manuscript using its [Bnumber] marker")
        if terms["letter"]:
            letter = next((l for l in s["letters"] if l["id"] == data.get("letter") and l["era"] == tier and l["due"] <= s["day"]), None)
            if not letter or f"[L{letter['id']}]" not in text:
                raise ValueError("Address a delivered letter from this era and include its [Lid] marker")
        if s["paper"] < terms["paper"]:
            raise ValueError("Not enough paper to print the manuscript; take a copying shift")
        s["paper"] -= terms["paper"]
        s["money"] += terms["payment"]
        s["prestige"] += terms["prestige"]
        s["day"] += 2
        s["publications"].append(dict(document=doc["id"], title=doc["title"], era=tier,
            fingerprint=fingerprint, books=sorted(ids), payment=terms["payment"]))
    elif action == "jump":
        if not public_state(s)["can_jump"]:
            raise ValueError("Meet every requirement before activating the time machine")
        if any(l["era"] == tier and l["due"] > s["day"] for l in s["letters"]):
            raise ValueError("Collect the letters still in transit before jumping")
        needed = requirements(s)
        s["money"] -= needed["money"]
        s["paper"] -= needed["paper"]
        if tier == len(YEARS) - 1:
            s["completed"] = True
        else:
            s["era"] += 1
            s["day"] = 1
    else:
        raise ValueError("Unknown campaign action")
    return s
