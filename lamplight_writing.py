"""Saved, player-led writing steps. AI feedback never grants game resources."""
import copy
import json
import re
import uuid

STEPS = (
    ("Question", "State one focused question and your tentative answer."),
    ("Evidence", "Explain what your selected sources support. Cite [Bnumber] and name a limitation."),
    ("Outline", "Plan your opening, evidence, objection and ending in a few bullets."),
    ("Draft", "Write the piece using your approved plan. Connect claims to source markers."),
    ("Revision", "Revise the draft, addressing the companion's feedback. Check every claim and citation."),
)
KINDS = {"study_notes": "180–250 words of study notes", "article": "450–550 words for an article",
         "letter": "150–220 words for a letter"}


def sources(library, slot, ids):
    if not isinstance(ids, list) or not 1 <= len(ids) <= 8:
        raise ValueError("Select 1–8 sources from this library")
    from game_native import source_id
    ids = list(dict.fromkeys(source_id(i) for i in ids))
    available = {b["id"] for b in library.books(slot)}
    if any(i not in available or (slot["mode"] == "campaign" and i not in slot["campaign"]["studied"]) for i in ids):
        raise ValueError("Use studied sources available in this save")
    return ids


def current(slot, data):
    flow = slot.get("writing", {})
    if not flow or flow.get("document") or data.get("writing") != flow["id"] or data.get("stage") != flow["stage"]:
        raise ValueError("This writing step changed. Reopen the saved workshop.")
    if flow["era"] != (slot["campaign"]["era"] if slot["mode"] == "campaign" else None):
        raise ValueError("This workshop belongs to an earlier era; its notes remain saved.")
    return flow, flow["steps"][flow["stage"]]


def act(library, slot, data):
    op = data["op"]
    if op == "writing_start":
        if slot.get("writing") and not slot["writing"].get("document"):
            raise ValueError("Resume your existing workshop before starting another piece")
        if slot.get("place") not in ("library", "workshop"):
            raise ValueError("Visit the computer or writing desk")
        kind, title = data.get("kind"), data.get("title")
        if kind not in KINDS or not isinstance(title, str) or not 1 <= len(title.strip()) <= 300:
            raise ValueError("Choose a format and a title of 1–300 characters")
        ids = sources(library, slot, data.get("books"))
        slot["writing"] = dict(id=uuid.uuid4().hex, kind=kind, title=title.strip(), books=ids, stage=0,
                               era=slot["campaign"]["era"] if slot["mode"] == "campaign" else None,
                               steps=[dict(name=name, instruction=instruction, text="", review={}) for name, instruction in STEPS])
        return
    flow, step = current(slot, data)
    if op == "writing_save":
        text = data.get("text")
        if not isinstance(text, str) or len(text) > 12000:
            raise ValueError("Keep each workshop step within 12,000 characters")
        if text != step["text"]:
            step.update(text=text, review={})
    elif op == "writing_advance":
        if not step["review"].get("ready"):
            raise ValueError("Ask your companion to review this version before continuing")
        if flow["stage"] < len(STEPS) - 1:
            flow["stage"] += 1
            if flow["stage"] == 4 and not flow["steps"][4]["text"]:
                flow["steps"][4]["text"] = step["text"]
        else:
            if len(slot["documents"]) >= 50:
                raise ValueError("This development build supports 50 manuscripts per slot")
            document = dict(id=uuid.uuid4().hex, slot=slot["id"], mode=slot["mode"],
                            title=flow["title"], text=step["text"], workshop=copy.deepcopy(flow))
            slot["documents"].append(document)
            flow["document"] = document["id"]
    elif op == "writing_revisit":
        target = data.get("target")
        if type(target) not in (int, float) or target != int(target) or not 0 <= target < flow["stage"]:
            raise ValueError("Choose an earlier writing step")
        flow["stage"] = int(target)
        for later in flow["steps"][int(target):]:
            later["review"] = {}


def prompt(flow):
    step = flow["steps"][flow["stage"]]
    return json.dumps(dict(task="Writing coach", format=KINDS[flow["kind"]], title=flow["title"],
                           stage=step["name"], instruction=step["instruction"], text=step["text"],
                           approved_steps=[dict(name=s["name"], text=s["text"], feedback=s["review"].get("feedback", "")[:2000])
                                           for s in flow["steps"][:flow["stage"]]]), ensure_ascii=False)


def review(answer, flow):
    value = json.loads(answer)
    if (not isinstance(value, dict) or type(value.get("ready")) is not bool
            or not isinstance(value.get("feedback"), str) or not value["feedback"].strip()
            or not isinstance(value.get("suggestion", ""), str)):
        raise ValueError("The companion returned an incomplete review. Your step is saved; retry.")
    result = {k: value.get(k, "") for k in ("ready", "feedback", "suggestion")}
    text = flow["steps"][flow["stage"]]["text"]
    if not text.strip():
        result["ready"] = False
    if flow["stage"] in (1, 3, 4):
        markers = set(re.findall(r"\[B(\d+)\]", text))
        if not markers or not markers <= {str(abs(i)) for i in flow["books"]}:
            result.update(ready=False, feedback="Use your selected [Bnumber] references and remove unknown source markers.\n" + result["feedback"])
    return result
