"""Offline campaign regressions: python -m unittest test_game_campaign -v."""
import copy
import json
import pathlib
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import game_campaign as game
import game_server as server


def manuscript(state, number=0):
    # Mechanical commission fixture, deliberately not a literary quality example.
    ids = [b["id"] for b in game.available(state)]
    letter = next((l for l in reversed(state["letters"]) if l["era"] == state["era"] and l["due"] <= state["day"]), None)
    text = " ".join(f"argument{number}term{i}" for i in range(500))
    text += " " + " ".join(f"[B{abs(i)}]" for i in ids)
    if letter:
        text += f" [L{letter['id']}]"
    doc = dict(id=f"{state['era']:02}{number:030}", title=f"Essay {number}", text=text)
    return doc, dict(action="publish", document=doc["id"], books=ids, letter=letter["id"] if letter else None)


class CampaignTests(unittest.TestCase):
    def test_every_era_has_growing_library_and_living_correspondents(self):
        s = game.new_game()
        for i, year in enumerate(game.YEARS):
            s["era"] = i
            self.assertEqual(len(game.available(s)), (i + 1) * 2)
            for f in game.figures(s):
                self.assertLessEqual(f["active"], year)
                self.assertLess(year, f["died"])
                self.assertLessEqual(game.BOOKS[f["book"]]["year"], year)
        self.assertNotIn("darwin", [f["id"] for f in game.figures(s)])

    def test_rejected_actions_do_not_change_state(self):
        s = game.new_game()
        before = copy.deepcopy(s)
        for data in ({"action": "study", "book": -14}, {"action": "study", "book": True},
                     {"action": "jump"}, {"action": "letter", "figure": "curie", "text": "a" * 50},
                     {"action": "publish", "books": [False]}):
            with self.assertRaises(ValueError):
                game.act(s, data)
            self.assertEqual(s, before)
        s = game.act(s, {"action": "study", "book": -1})
        with self.assertRaises(ValueError):
            game.act(s, {"action": "study", "book": -1})
        self.assertEqual(s["knowledge"], 1)

    def test_postal_delays_threads_and_period_safe_replies(self):
        for lang in ("en",):
            s = game.act(game.new_game(), {"action": "study", "book": -1})
            request = dict(action="letter", figure="galileo", text="Please discuss quantum computers in 2026.", language=lang)
            s = game.act(s, request)
            letter = s["letters"][0]
            self.assertNotIn("answer", game.public_state(s)["letters"][0])
            with self.assertRaises(ValueError):
                game.act(s, request | {"reply_to": letter["id"]})
            for _ in range(4):
                s = game.act(s, {"action": "wait"})
            visible = game.public_state(s)["letters"][0]
            self.assertTrue(visible["delivered"])
            self.assertNotIn("quantum", visible["answer"])
            self.assertNotIn("2026", visible["answer"])
            self.assertIn("Jupiter", visible["answer"])
            s = game.act(s, request | {"reply_to": letter["id"], "focus": "method"})
            self.assertEqual(s["letters"][-1]["reply_to"], letter["id"])
            self.assertNotEqual(s["letters"][-1]["answer"], letter["answer"])
            s["era"] = 1
            s["day"] = 1
            self.assertTrue(game.public_state(s)["letters"][0]["delivered"])
            with self.assertRaises(ValueError):
                game.act(s, request)

    def test_commission_validation_and_duplicate_payment(self):
        s = game.new_game()
        s["studied"] = [-1, -2]
        doc, action = manuscript(s)
        for altered in (doc | {"text": "too short"}, doc | {"text": "word " * 500},
                        doc | {"text": doc["text"].replace("[B1]", "")}):
            with self.assertRaises(ValueError):
                game.act(s, action, [altered])
        result = game.act(s, action, [doc])
        self.assertEqual(result["money"], s["money"] + 50)
        with self.assertRaises(ValueError):
            game.act(result, action, [doc])
        duplicate = doc | {"id": "f" * 32, "text": doc["text"].upper() + "!!!"}
        with self.assertRaises(ValueError):
            game.act(result, action | {"document": duplicate["id"]}, [duplicate])

    def test_full_campaign_is_winnable_without_keys_or_network(self):
        s = game.new_game()
        for era in range(7):
            self.assertEqual(s["era"], era)
            for book in game.available(s):
                if book["id"] not in s["studied"]:
                    s = game.act(s, dict(action="study", book=book["id"]))
            f = game.figures(s)[-1]
            while s["money"] < 4 + era or s["paper"] < 1:
                s = game.act(s, dict(action="work"))
            s = game.act(s, dict(action="letter", figure=f["id"], text="What evidence would make you revise your argument?"))
            for _ in range(4):
                s = game.act(s, dict(action="work"))
            for number in range(max(2, game.requirements(s)["publications"])):
                while s["paper"] < game.commission(s)["paper"]:
                    s = game.act(s, dict(action="work"))
                doc, action = manuscript(s, number)
                s = game.act(s, action, [doc])
            for _ in range(100):
                if game.public_state(s)["can_jump"]:
                    break
                s = game.act(s, dict(action="work"))
            self.assertTrue(game.public_state(s)["can_jump"])
            s = game.act(s, dict(action="jump"))
            self.assertGreaterEqual(s["money"], 0)
            self.assertGreaterEqual(s["paper"], 0)
            self.assertTrue(all(l["delivered"] for l in game.public_state(s)["letters"]))
        self.assertTrue(s["completed"])
        self.assertEqual(game.public_state(s)["year"], 1930)
        with self.assertRaises(ValueError):
            game.act(s, dict(action="jump"))

    def test_era_letter_and_new_source_required(self):
        s = game.new_game() | {"era": 1, "studied": [-1, -2, -3, -4], "paper": 30}
        doc, action = manuscript(s)
        with self.assertRaisesRegex(ValueError, "letter"):
            game.act(s, action, [doc])
        with self.assertRaisesRegex(ValueError, "new work"):
            game.act(s, action | {"books": [-1]}, [doc])

    def test_http_gates_and_durable_state(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(server, "DATA", pathlib.Path(directory)), patch.object(server, "BOOKS", game.BOOKS), patch.object(server, "SETTINGS", {"language": "en"}):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            worker = threading.Thread(target=http.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{http.server_port}/api/"

            def call(path, data=None, token=server.TOKEN):
                request = Request(base + path, data=None if data is None else json.dumps(data).encode(),
                                  headers={"X-Library-Token": token, "Content-Type": "application/json"})
                try:
                    with urlopen(request, timeout=3) as response:
                        return json.load(response)
                except HTTPError as error:
                    error.close()
                    raise
            try:
                with self.assertRaises(HTTPError) as error:
                    call("campaign", token="invalid")
                self.assertEqual(error.exception.code, 403)
                with self.assertRaises(HTTPError):
                    call("book?id=-14")
                with self.assertRaises(HTTPError):
                    call("book?id=1342")  # Unknown-dated archive edition must not bypass the gate.
                self.assertNotIn("ESPAÑOL", call("book?id=-1")["text"])
                with self.assertRaises(HTTPError):
                    call("job", {"kind": "ideas", "books": [-14]})
                self.assertFalse(server.WORK.locked())
                call("state", {"era": 6, "money": 999999})
                self.assertEqual(call("campaign")["year"], 1630)
                call("campaign", {"action": "study", "book": -1})
                sent = call("campaign", {"action": "letter", "figure": "galileo", "text": "Can another observer repeat this observation?"})
                self.assertNotIn("answer", sent["letters"][0])
                self.assertNotIn("answer", call("campaign")["letters"][0])
                restored = server.campaign_state()
                self.assertEqual(restored["studied"], [-1])
                self.assertEqual(restored["money"], 20)
                with server.WORK:
                    with self.assertRaises(HTTPError):
                        call("campaign", {"action": "work"})
                self.assertEqual(call("campaign")["money"], 20)
            finally:
                http.shutdown()
                http.server_close()
                worker.join(timeout=3)

    def test_ai_letters_are_period_grounded_delayed_and_fail_without_postage(self):
        settings = dict(language="en", agent_model="test-model")
        with tempfile.TemporaryDirectory() as directory, patch.object(server, "DATA", pathlib.Path(directory)), patch.object(server, "BOOKS", game.BOOKS), patch.object(server, "SETTINGS", settings), patch.object(server.pipeline, "LANG", "en"):
            original = game.act(game.new_game(), {"action": "study", "book": -1})
            data = dict(kind="letter", figure="galileo", books=[-1], language="en", text="Could the apparent movement result from defects in the glass?")
            for index, response in enumerate(("A useful objection. Compare repeated observations made with another instrument.", "By 2026 this will be settled.", "")):
                server.save_json(server.DATA / "campaign.json", original)
                job = dict(id=f"{index:032}", kind="letter", status="running", logs=[], period_context=game.period_context(original))
                with patch.object(server.llm, "chat", return_value=response) as model:
                    self.assertTrue(server.WORK.acquire(blocking=False))
                    server.execute_job(job, data)
                self.assertFalse(server.WORK.locked())
                prompt, system = model.call_args.args[1:3]
                self.assertIn(data["text"], prompt)
                self.assertIn("1630", system)
                self.assertNotIn("Curie", prompt)
                self.assertNotIn("Frankenstein", prompt)
                updated = server.campaign_state()
                if index == 0:
                    self.assertEqual(job["status"], "complete")
                    self.assertNotIn("text", job["result"])
                    self.assertNotIn("answer", game.public_state(updated)["letters"][0])
                    self.assertEqual(updated["money"], original["money"] - 4)
                    self.assertEqual(updated["letters"][0]["answer"], response)
                else:
                    self.assertEqual(job["status"], "failed")
                    self.assertEqual(updated, original)


if __name__ == "__main__":
    unittest.main()
