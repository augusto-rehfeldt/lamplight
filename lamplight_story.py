"""Authored native campaign: only the player crosses time; rewards are deterministic."""
import re

CHAPTERS = [
    ("A desk far from home", "1630 · Margot's village library", "You were cataloguing papers in 2026 when an experimental time recorder failed. You woke beside a village library with your satchel, laptop and damaged recorder. The date is 1630. Nobody else traveled. Margot offers a desk and a room while you work out how to return. Start small: read one summary, ask one good question, and write down what you learn.", "Margot", "Learn to compare observations", "The moons in Galileo's summary show why a sequence of observations is stronger than a single drawing."),
    ("A room without Margot", "1680 · Lucien's workshop", "Fifty years pass outside a single breath. Margot's chair is empty. Her grandson Lucien has kept a parcel addressed to the stranger who never grew old. Inside: your field report, and a note in her hand. 'I believed you. Keep going.'", "Lucien", "What fire changes", "Lucien can seal the cracked housing, but first you must distinguish a substance from the changes made by heat."),
    ("The printer's promise", "1730 · Sabine's reading room", "The workshop has become a print shop. Sabine knows you from a woodcut, not a memory. The family has spent fifty years keeping a lamp lit for a person who stayed one week. You can carry their words forward. You cannot bring them with you.", "Sabine", "A signal others can check", "A printed observation travels farther than its author. Make your signal reproducible before the next crossing."),
    ("A spark in the rain", "1780 · Étienne's correspondence room", "Étienne has wired a bell to the old window. During storms it rings without a hand to pull it. Your compass answers. For the first time, the voice beyond the static sounds almost like your sister.", "Étienne", "An answer in the static", "Separate what the instrument measures from what you hope to hear. Hope is not a calibration."),
    ("The cost of leaving", "1830 · Amara's salon", "Amara has collected the lives you missed. Births, closures, arguments, ordinary afternoons. The house survived because people chose to keep it open. The compass can recover your departure instant, but every crossing makes leaving harder.", "Amara", "A memory is not a record", "Compare an account with its evidence. Preserve the uncertainties alongside the discoveries."),
    ("A wire toward home", "1880 · Ivo's institute", "A telegraph chatters where Margot once dried letters. Ivo has found the same impossible pulse in records fifty years apart: your arrival. Your sister's last words were not a farewell. She was giving you a time.", "Ivo", "Find the departure pulse", "The records let you distinguish a repeated event from noise. Use the period's instruments and sources to verify the signal."),
    ("The last light", "1930 · Leila's radio room", "Leila turns a radio dial and a voice from 2026 says your name. The address was never a place. It was the instant before the accident. One final calibration can return you there, carrying the reports of everyone who helped.", "Leila", "An address in time", "Complete the final report. The return compass needs all seven anchors before it can reach 2026."),
]

TRIALS = [
    ("One telescope drawing matches your memory. Another differs. Which signal can anchor the compass?", [("brightest","Choose the brightest single sighting"),("repeat","Compare observations across several nights"),("hope","Choose the date you want to reach")], "repeat", "One sighting may be an instrument flaw. Look for a repeatable pattern.", -1),
    ("The furnace separates a sample. Has it revealed the original ingredients?", [("elements","Yes: everything left was there before"),("heat","Not necessarily: heat may have changed it"),("gold","Only if the residue shines")], "heat", "Boyle asks whether fire transforms a substance rather than merely separating it.", -3),
    ("A prism splits the compass beam. How can you test whether the colours were already present?", [("brighter","Use a brighter lamp"),("mix","Declare the glass magical"),("prism","Test a separated ray through another prism")], "prism", "Newton's arrangement tests a separated ray, not just the impressive display.", -6),
    ("A distant reader reports a different electrical effect. What belongs in your letter?", [("procedure","Apparatus, conditions, and failed trials"),("success","Only the successful result"),("certainty","A confident claim that they are mistaken")], "procedure", "Comparable procedures let distant investigators distinguish disagreement from different conditions.", -7),
    ("The archive blames its creator for a failed experiment. Whose account should you preserve?", [("creator","Only the respected creator's"),("both","Both the creator's and the excluded being's"),("erase","Neither: destroy the embarrassing record")], "both", "Frankenstein's competing narratives change the question of responsibility.", -9),
    ("Your theory fits most observations, but the archive contains exceptions. What do you record?", [("omit","Remove the exceptions"),("intention","Assume nature intended your result"),("limits","Include difficult cases and gaps in the record")], "limits", "A reliable argument preserves what the evidence still cannot establish.", -11),
    ("Two distant clocks disagree about your departure. What must the final anchor specify?", [("frame","A frame of reference and a clock-comparison procedure"),("louder","Whichever clock ticks louder"),("universal","Assume every observer shares one universal time")], "frame", "A judgment of simultaneity needs clocks, signals and a specified frame of reference.", -14),
]


def public(slot):
    if slot["mode"] != "campaign":
        return {}
    c = slot["campaign"]
    era = c["era"]
    progress = slot.get("story", {})
    flags = progress.get(str(era), [])
    chapter = CHAPTERS[era]
    steps = [("intro", "A new place to learn", "You alone traveled from 2026. Your laptop came in your satchel."),
             ("moved", "Find your feet", "Walk with WASD / arrows, or click the floor. Hold Shift to run."),
             ("greeted", "Meet " + chapter[3], "Click the custodian or approach and press E."),
             ("studied", "Read a short summary", "At the library shelf, choose this era's featured summary and study it."),
             ("mastered", "Check your understanding", "Answer both of the summary's learning questions. Wrong answers explain the idea; retry freely."),
             ("explored", "Explore the village", "Leave through the library door. Visit the print shop and garden from the square."),
             ("discussed", "Join the reading circle", "In the garden, discuss a studied work with a period thinker. These are fictional educational encounters."),
             ("report", "Create your first learning note", "Use your laptop at the library to draft notes with AI, or write your own. Review and save 45 words with a studied [Bnumber] reference."),
             ("published", "Share an article", "Bring a longer sourced article to the print shop. Later eras also require a delivered letter."),
             ("lens", "Inspect the time recorder", "Your repair kit is below the library window. Check it when you are ready to travel."),
             ("aligned", chapter[4], "Apply what you learned at the time recorder."),
             ("cross", "Prepare the next chapter", "Your articles preserve a record for the next generation. Review the recorder's requirements, then cross.")]
    done = set(flags)
    if progress.get("intro"):
        done.add("intro")
    if any(p["era"] == era for p in c["publications"]):
        done.add("published")
    if TRIALS[era][4] in c["studied"]:
        done.add("studied")
    if slot.get("learning",{}).get(str(TRIALS[era][4]),{}).get("mastered"):
        done.add("mastered")
    if {"garden","workshop"}.issubset(slot.get("visited",[])):
        done.add("explored")
    if any(key.startswith(str(era)+":") for key in slot.get("discussions",[])):
        done.add("discussed")
    next_step = next((s for s in steps if s[0] not in done), steps[-1])
    return dict(title=chapter[0], location=chapter[1], introduction=chapter[2], custodian=chapter[3],
                clue=chapter[5], flags=sorted(done), objective=next_step[1], hint=next_step[2],
                steps=[dict(id=k, title=t, hint=h, done=k in done) for k,t,h in steps],
                anchors=sum("report" in progress.get(str(i), []) for i in range(7)),
                introduced=progress.get("intro", False), seen_era=progress.get("seen_era", -1),
                ready={"report","aligned","mastered","discussed"}.issubset(done),
                trial=dict(question=TRIALS[era][0], options=[dict(id=k,text=v) for k,v in TRIALS[era][1]], book=TRIALS[era][4]))


def act(slot, data):
    if slot["mode"] != "campaign":
        raise ValueError("The return compass belongs to Campaign")
    c = slot["campaign"]
    progress = slot.setdefault("story", {})
    flags = progress.setdefault(str(c["era"]), [])
    action = data.get("action")
    if action == "intro":
        progress.update(intro=True, seen_era=c["era"])
        return
    if c["completed"]:
        raise ValueError("You are home. Your journal remains available.")
    if action in flags:
        return
    if action == "lens":
        x,y = slot["position"]
        if slot.get("place","library") != "library" or (x-250)**2 + (y-137)**2 > 38**2:
            raise ValueError("Approach the repair kit below the library window")
    elif action == "aligned":
        if "lens" not in flags or "studied" not in public(slot)["flags"]:
            raise ValueError("Recover the lens and study a note from this era first")
        if data.get("answer") != TRIALS[c["era"]][2]:
            raise ValueError("The signal slips away. " + TRIALS[c["era"]][3])
    elif action == "report":
        if "studied" not in public(slot)["flags"]:
            raise ValueError("Study this era's featured summary before filing a learning note")
        doc = next((d for d in slot["documents"] if d["id"] == data.get("document")), None)
        words = re.findall(r"[^\W_]+", doc["text"].lower() if doc else "")
        if len(words) < 45 or len(set(words)) < 15 or not any(f"[B{abs(i)}]" in doc["text"] for i in c["studied"]):
            raise ValueError("Save a report with 45 words, 15 distinct words and a studied [Bnumber] reference")
        c["money"] += 30 + c["era"] * 20
        c["prestige"] += 2 + c["era"]
    else:
        raise ValueError("Unknown story action")
    flags.append(action)
