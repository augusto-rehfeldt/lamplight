"""Original English learning checks. Feedback teaches; retries never cost resources."""

# IDs follow the existing historical catalogue; answers stay on the Python side.
CHECKS = {
 -1:[("What makes Galileo's case stronger than one drawing?", ["The telescope's price", "A sequence of changing positions", "The observer's reputation"], 1, "Repeated positions can distinguish an orbit from a defect or a coincidental arrangement."),
     ('Which question does the summary leave open?', ['Whether Jupiter exists', 'Whether instrument defects could mislead an observer', 'Whether drawings are ever useful'], 1, "Instrument defects and another observer's telescope still need testing; a strong sequence does not end every doubt.")],
 -2:[("What does the gap between Quixote's expectations and other people's accounts invite us to examine?", ["How stories shape judgment", "Whether every narrator is dishonest", "The accuracy of a map"], 0, "The novel contrasts an inherited story with ordinary experience; it does not make every account equally unreliable."),
     ('What is the reader of romances trying to do?', ['Write a history of Spain', 'Prove that romances are fiction', 'Live by the rules of the romances he has read'], 2, "He treats chivalric stories as a guide to action; the novel's argument comes from applying them to an ordinary world.")],
 -3:[("Why doesn't heating a substance prove that its products were original elements?", ["Heat has no effect", "Every sample contains gold", "Heating may transform the substance"], 2, "An experiment must distinguish separation from transformation, rather than assume its own conclusion."),
     ('Why is a familiar account of an experiment not enough?', ['Familiarity is not proof', 'Old ideas are always wrong', 'Experiments cannot be repeated'], 0, 'A well-known explanation still has to be tested against its alternatives. It is not rejected merely for being old.')],
 -4:[("What is the main dispute in Areopagitica?", ["Whether books need titles", "Licensing before publication", "Whether every claim is equally true"], 1, "Milton argues about prior restraint. This is not a claim that all printed arguments are sound or harmless."),
     ('What can reading opposing arguments do, according to Milton?', ['Guarantee agreement', "Exercise the reader's judgment", 'Remove every consequence of printing'], 1, 'Meeting error can train judgment. The note also warns that this is not a claim that printing has no consequences.')],
 -5:[("How should we read the calculating narrator of A Modest Proposal?", ["As a literal policy recommendation", "As satire exposing cruel reasoning", "As a neutral statistical report"], 1, "The distance between the narrator's confidence and the proposal's cruelty exposes the interests behind supposedly respectable calculation."),
     ('What does the account-book image suggest?', ['Swift admired careful bookkeeping', 'People are reduced to figures in a calculation', 'The narrator is an honest accountant'], 1, "Treating people as ledger entries is the satire's target: the method looks respectable while the conclusion is monstrous.")],
 -6:[("Why pass a separated ray through another prism?", ["To test whether the glass created the colour", "To make the room brighter", "To avoid comparing explanations"], 0, "The second test helps distinguish a property of the light from a change caused by the apparatus."),
     ("Why isn't an impressive prism display enough?", ['Colours cannot be seen in daylight', 'Displays are too expensive', 'It may not decide between competing explanations'], 2, 'A striking effect can fit more than one explanation, so the arrangement of the apparatus matters.')],
 -7:[("What helps another investigator compare an electrical observation?", ["Only a claim of success", "A famous signature", "Apparatus, circumstances and unsuccessful trials"], 2, "A report is useful when another reader can understand the conditions and compare the procedure, including failures."),
     ('If investigators agree on an observed effect, what may still be unsettled?', ['Whether any letters were sent', 'The explanation of electricity', 'Whether the effect was observed'], 1, 'Agreement about what happened is different from agreement about why it happened.')],
 -8:[("What does increased output alone fail to tell us?", ["How gains are distributed and work affects people", "Whether any objects were produced", "Whether tasks can be divided"], 0, "Productivity is one question; distribution and workers' experience require further evidence and argument."),
     ('What limits how far the division of labour can go?', ['The weather', 'The number of workshops in one town', 'The reach of exchange'], 2, 'Specialised output needs buyers. When exchange is limited, dividing tasks further has little purpose.')],
 -9:[("Why read the creature's account alongside the creator's?", ["To choose the longest narrative", "To examine responsibility, abandonment and exclusion", "To excuse every action"], 1, "Competing accounts complicate responsibility without automatically excusing either person's actions."),
     ('What should an argument about responsibility do first?', ['Trust the creator because he speaks first', 'Hear both narratives', "Set the creature's abandonment aside"], 1, "The creature's account changes what the creator's account seems to show. Hearing both is not the same as excusing either.")],
 -10:[("What challenges first impressions in Pride and Prejudice?", ["Never speaking to anyone", "Treating status as proof", "Letters and later encounters"], 2, "New evidence changes judgments. Property and family expectations also shape the choices characters can make."),
     ('What does a reading concerned only with attraction miss?', ['Property and family expectations', "The novel's letters", "The characters' first names"], 0, 'Marriage in the novel is also an economic and family matter, which limits the choices characters can make.')],
 -11:[("How does artificial selection function in Darwin's argument?", ["As a useful comparison, not a claim that nature has an intention", "As proof of a conscious natural breeder", "As a reason to hide difficult cases"], 0, "An analogy can illuminate a mechanism without transferring every feature of the comparison. Gaps and difficulties remain part of the argument."),
     ('What lets differences in survival and reproduction accumulate?', ["A breeder's plan in nature", 'Variation and the struggle for existence', 'Leaving out difficult cases'], 1, 'Variation and competition do the work in the argument; no intention is required, and difficult cases stay in view.')],
 -12:[("Which distinction matters in On Liberty?", ["Popular versus unpopular people", "Long versus short opinions", "Harm to others versus disapproval"], 2, "The distinction requires an argument about the particular case; merely calling something freedom or harm does not settle it."),
     ('What can suppression prevent, even when the accepted belief is true?', ['Printing any books', 'Every future disagreement', 'Understanding the belief through challenge'], 2, 'A true belief that is never challenged can be held without being understood.')],
 -13:[("Why distinguish chemical isolation from measurements of activity?", ["Because measurements never matter", "They support different parts of the case", "Because one striking result proves everything"], 1, "A persuasive report explains what each method establishes and what remains to be shown."),
     ('What does radioactivity make possible during separation?', ['Following small quantities of active substances', 'Seeing atoms directly', 'Skipping the chemical work'], 0, 'Measuring activity tracks where a substance goes while chemical isolation continues; each supports a different part of the case.')],
 -14:[("What does a claim that distant events are simultaneous require?", ["A shared calendar alone", "A louder clock", "A procedure for comparing clocks and signals"], 2, "The argument must specify the frame of reference and comparison procedure instead of assuming one observer's time is universal."),
     ('Must observers in relative motion agree about simultaneity?', ['Yes, because time is shared by everyone', 'No, they need not assign the same simultaneity', 'Only if they use the same calendar'], 1, 'Simultaneity depends on the frame of reference, so an argument has to say which frame it uses.')],
}



def current(record, book_id):
    """Index of the question the player faces: first unanswered, then practice rotation.

    Saves from the one-question version carry ``mastered`` without ``correct`` and stay mastered.
    """
    done = record.get("correct", [])
    if not record.get("mastered"):
        return next(i for i in range(len(CHECKS[book_id])) if i not in done)
    return record.get("practice", 0) % len(CHECKS[book_id])


def public(slot, book_id):
    record = slot.get("learning", {}).get(str(book_id), {})
    index = current(record, book_id)
    question, options, _, explanation = CHECKS[book_id][index]
    return dict(question=question, options=options, index=index, total=len(CHECKS[book_id]),
                answered=len(record.get("correct", [])), mastered=record.get("mastered",False),
                attempts=record.get("attempts",0), explanation=explanation if record.get("mastered") else "")


def answer(slot, book_id, choice, question=None):
    if slot["mode"] != "campaign" or book_id not in slot["campaign"]["studied"] or book_id not in CHECKS:
        raise ValueError("Study this period summary before checking your understanding")
    if type(choice) is not int or choice not in range(3):
        raise ValueError("Choose one of the three answers")
    record = slot.setdefault("learning", {}).setdefault(str(book_id), dict(attempts=0, mastered=False))
    index = current(record, book_id)
    if question is not None and question != index:
        raise ValueError("This question has changed. Reopen the learning check.")
    record["attempts"] += 1
    correct = choice == CHECKS[book_id][index][2]
    first = remaining = False
    if correct and record["mastered"]:
        record["practice"] = record.get("practice", 0) + 1
    elif correct:
        record.setdefault("correct", []).append(index)
        remaining = len(record["correct"]) < len(CHECKS[book_id])
        first = record["mastered"] = not remaining
        if first:
            slot["campaign"]["prestige"] += 1
            slot["campaign"]["paper"] += 1
    return dict(correct=correct, first=first, next=remaining or (correct and not first), explanation=CHECKS[book_id][index][3],
                feedback=("You explained both ideas. +1 reputation and +1 paper." if first else
                          "Correct. One more question to master this summary." if remaining else
                          "You remembered the idea." if correct else
                          "Try again after reviewing this explanation. No days or resources lost."))
