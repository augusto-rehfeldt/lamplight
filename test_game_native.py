"""Native save/source boundary checks; temporary files and no external services."""
import copy
import json
import pathlib
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import game_native as native
from run_lamplight import single_library
from test_game_campaign import manuscript
from test_lamplight_ai import qualify, provider_reply


class NativeTests(unittest.TestCase):
    def test_portraits_cover_the_entire_conversation_roster(self):
        import struct
        portraits = pathlib.Path(__file__).parent / "godot" / "assets" / "portraits"
        for identity in (*native.RESIDENTS, *(figure["id"] for figure in native.campaign.FIGURES)):
            with self.subTest(identity=identity):
                data = (portraits / f"{identity}.png").read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", data[16:24])
                self.assertEqual(width, height)
                self.assertGreaterEqual(width, 128)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.library = native.Library(self.root)
        qualify(self.library)
        provider = patch.object(native.legacy.requests, "post", side_effect=provider_reply)
        provider.start()
        self.addCleanup(provider.stop)

    def create(self, mode):
        return self.library.request(dict(op="create", mode=mode, name=mode))

    def test_guided_writing_reviews_edits_recovery_and_final_manuscript(self):
        slot = self.create("campaign")
        def act(**data):
            return self.library.request(data | dict(slot=slot["id"]))
        with self.assertRaisesRegex(ValueError, "studied"):
            act(op="writing_start", kind="article", title="An observation", books=[-1])
        act(op="campaign", action="study", book=-1)
        started = act(op="writing_start", kind="article", title="An observation", books=[-1])
        flow_id = started["writing"]["id"]
        resources = copy.deepcopy(started["campaign"])
        for index in range(5):
            request = dict(writing=flow_id, stage=index)
            with self.assertRaisesRegex(ValueError, "review"):
                act(op="writing_advance", **request, ready=True)
            result = act(op="ai_coach", **request)
            if index != 4:
                self.assertFalse(result["slot"]["writing"]["steps"][index]["review"]["ready"])
            saved = act(op="writing_save", text="An observation supports a limited inference. [B1]", **request)
            with patch.object(native.legacy.requests, "post", side_effect=native.legacy.requests.Timeout), self.assertRaises(ValueError):
                act(op="ai_coach", **request)
            self.assertEqual(act(op="load")["writing"], saved["writing"])
            result = act(op="ai_coach", **request)
            self.assertTrue(result["slot"]["writing"]["steps"][index]["review"]["ready"])
            act(op="writing_save", text="I need a comparison to strengthen this inference. [B1]", **request)
            with self.assertRaisesRegex(ValueError, "review"):
                act(op="writing_advance", **request)
            act(op="ai_coach", **request)
            final = act(op="writing_advance", **request)
            with self.assertRaises(ValueError):
                act(op="writing_advance", **request)
        self.assertEqual(len(final["documents"]), 1)
        self.assertEqual(final["documents"][0]["text"], "I need a comparison to strengthen this inference. [B1]")
        self.assertEqual(final["documents"][0]["id"], final["writing"]["document"])
        self.assertEqual(len(final["documents"][0]["workshop"]["steps"]), 5)
        self.assertEqual(final["campaign"], resources, "Coaching does not grant rewards or spend game days")
        restored = native.Library(self.root)
        self.assertEqual(restored.request(dict(op="load", slot=slot["id"]))["writing"], final["writing"])

    def test_coach_invalid_reply_foreign_markers_and_stale_review(self):
        slot = self.create("campaign")
        def act(**data):
            return self.library.request(data | dict(slot=slot["id"]))
        act(op="campaign", action="study", book=-1)
        started = act(op="writing_start", kind="article", title="Notes", books=[-1])
        request = dict(writing=started["writing"]["id"], stage=0)
        act(op="writing_save", text="My question", **request)
        with patch.object(self.library, "send_ai", return_value='{"ready":"true","feedback":"yes"}'), self.assertRaises(ValueError):
            act(op="ai_coach", **request)
        self.assertFalse(act(op="load")["writing"]["steps"][0]["review"])
        def changed(*args, **kwargs):
            act(op="writing_save", text="Changed during request", **request)
            return '{"ready":true,"feedback":"Fine"}'
        with patch.object(self.library, "send_ai", side_effect=changed), self.assertRaisesRegex(ValueError, "changed"):
            act(op="ai_coach", **request)
        act(op="ai_coach", **request)
        act(op="writing_advance", **request)
        request["stage"] = 1
        act(op="writing_save", text="Keep this evidence draft. [B1]", **request)
        revisited = act(op="writing_revisit", target=0, **request)
        self.assertEqual(revisited["writing"]["stage"], 0)
        self.assertEqual(revisited["writing"]["steps"][1]["text"], "Keep this evidence draft. [B1]")
        self.assertFalse(revisited["writing"]["steps"][0]["review"])
        act(op="ai_coach", writing=request["writing"], stage=0)
        act(op="writing_advance", writing=request["writing"], stage=0)
        act(op="writing_save", text="An invented source. [B99]", **request)
        result = act(op="ai_coach", **request)
        self.assertFalse(result["slot"]["writing"]["steps"][1]["review"]["ready"])
        restored = native.Library(self.root)
        saved = restored.request(dict(op="writing_save", slot=slot["id"], text="Recovered without AI", **request))
        self.assertEqual(saved["writing"]["steps"][1]["text"], "Recovered without AI")

    def test_usage_counts_real_requests_errors_and_persists_without_prompt_or_key(self):
        before = self.library.request(dict(op="ai_status"))["usage"]
        def metered(*args, **kwargs):
            response = provider_reply(*args, **kwargs)
            response.iter_content.return_value = [json.dumps({"choices":[{"message":{"content":"A reply"}}],
                "usage":{"prompt_tokens":123,"completion_tokens":45}}).encode()]
            return response
        config = {"url":"http://localhost:11434/v1", "model":"test-chat"}
        with patch.object(native.legacy.requests, "post", side_effect=metered):
            self.library.send_ai(config, "SECRET-KEY", "PRIVATE-PROMPT", "PRIVATE-TEXT")
        with patch.object(native.legacy.requests, "post", side_effect=native.legacy.requests.Timeout), self.assertRaises(native.legacy.requests.Timeout):
            self.library.send_ai(config, "SECRET-KEY", "PRIVATE-PROMPT", "PRIVATE-TEXT")
        self.library.send_ai(config, "SECRET-KEY", "PRIVATE-PROMPT", "PRIVATE-TEXT")
        usage = native.Library(self.root).request(dict(op="ai_status"))["usage"]
        self.assertEqual(usage["requests"] - before["requests"], 3)
        self.assertEqual(usage["successes"] - before["successes"], 2)
        self.assertEqual(usage["failures"] - before["failures"], 1)
        self.assertEqual(usage["input_tokens"] - before["input_tokens"], 123)
        self.assertEqual(usage["output_tokens"] - before["output_tokens"], 45)
        self.assertGreater(usage["estimated_tokens"], before["estimated_tokens"])
        for private in ("SECRET-KEY", "PRIVATE-PROMPT", "PRIVATE-TEXT"):
            self.assertNotIn(private, self.library.usage_path.read_text())

    def test_modes_sources_documents_and_authority(self):
        slots = {mode: self.create(mode) for mode in native.MODES}
        campaign = slots["campaign"]
        with patch.object(native.legacy.requests, "get", side_effect=AssertionError("No network")), patch.object(native.legacy.research, "scan_library", side_effect=AssertionError("No scan")):
            text = self.library.request(dict(op="book", slot=campaign["id"], book=-1.0))["text"]
            self.assertIn("not a complete edition", text)
            for book in (1342, -14, True, -1.5, "-1", float("nan")):
                with self.assertRaises(ValueError):
                    self.library.request(dict(op="book", slot=campaign["id"], book=book))
            for mode in ("free_play", "modern"):
                with self.assertRaises(ValueError):
                    self.library.request(dict(op="book", slot=slots[mode]["id"], book=-1))
                with self.assertRaises(ValueError):
                    self.library.request(dict(op="campaign", slot=slots[mode]["id"], action="work"))
            for operation in ("load", "book", "document", "campaign"):
                with self.assertRaises(ValueError):
                    self.library.request(dict(op=operation, slot=campaign["id"], mode="modern"))
        modern = self.library.request(dict(op="document", slot=slots["modern"]["id"], title="Modern work", text="Personal writing"))
        doc = modern["documents"][0]
        self.assertEqual(doc["mode"], "modern")
        for operation in ("document", "campaign"):
            with self.assertRaises(ValueError):
                self.library.request(dict(op=operation, action="publish", slot=campaign["id"], document=doc["id"], title="Forged ownership", text="text", books=[-1]))
        self.library.request(dict(op="talk", slot=campaign["id"], resident="margot", money=900, choice="patron"))
        self.library.request(dict(op="talk", slot=campaign["id"], resident="margot"))
        restored = native.Library(self.root).request(dict(op="load", slot=campaign["id"]))
        self.assertEqual(restored["conversations"], ["margot"])
        self.assertEqual(restored["campaign"]["money"], 24)
        self.assertEqual(restored["choice"], "")
        self.assertEqual(restored["documents"], [])

    def test_opening_both_choices_and_duplicate_rewards(self):
        for choice in ("shared", "patron"):
            slot = self.create("campaign")
            slot_id = slot["id"]
            with self.assertRaises(ValueError):
                self.library.request(dict(op="choice", slot=slot_id, choice=choice))
            slot = self.library.request(dict(op="campaign", slot=slot_id, action="study", book=-1.0))
            slot = self.library.request(dict(op="campaign", slot=slot_id, action="study", book=-2.0))
            document, action = manuscript(slot["campaign"])
            slot = self.library.request(dict(op="document", slot=slot_id, title=document["title"], text=document["text"]))
            action["document"] = slot["documents"][0]["id"]
            slot = self.library.request(action | dict(op="campaign", slot=slot_id))
            paid = copy.deepcopy(slot["campaign"])
            with self.assertRaises(ValueError):
                self.library.request(action | dict(op="campaign", slot=slot_id))
            self.library.request(dict(op="choice", slot=slot_id, choice=choice))
            self.library.request(dict(op="choice", slot=slot_id, choice=choice))
            with self.assertRaises(ValueError):
                self.library.request(dict(op="choice", slot=slot_id, choice="patron" if choice == "shared" else "shared"))
            restored = native.Library(self.root).request(dict(op="load", slot=slot_id))
            self.assertEqual(restored["choice"], choice)
            self.assertEqual(restored["campaign"], paid)

    def test_failed_write_unknown_version_and_position_bounds(self):
        slot = self.create("campaign")
        before = self.library.path.read_bytes()
        state = copy.deepcopy(self.library.state)
        with patch.object(pathlib.Path, "replace", side_effect=OSError("Interrupted replacement")):
            with self.assertRaises(OSError):
                self.library.request(dict(op="guidance", slot=slot["id"], enabled=False))
        self.assertEqual(self.library.state, state)
        self.assertEqual(self.library.path.read_bytes(), before)
        for point in ([25, 115], [455, 247]):
            self.library.request(dict(op="position", slot=slot["id"], position=point))
        for point in ([0, 0], [float("inf"), 120], [True, 120]):
            with self.assertRaises(ValueError):
                self.library.request(dict(op="position", slot=slot["id"], position=point))
        self.library.path.write_text('{"version":999,"slots":{}}', encoding="utf-8")
        before = self.library.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "version"):
            native.Library(self.root)
        self.assertEqual(self.library.path.read_bytes(), before)

    def test_native_http_has_no_legacy_bypass(self):
        http = ThreadingHTTPServer(("127.0.0.1", 0), native.Handler)
        http.library = self.library
        worker = threading.Thread(target=http.serve_forever, daemon=True)
        worker.start()

        def call(path, body, token=native.legacy.TOKEN, **headers):
            request = Request(f"http://127.0.0.1:{http.server_port}" + path, json.dumps(body).encode(),
                              headers={"Content-Type":"application/json", "X-Library-Token":token} | headers)
            try:
                with urlopen(request, timeout=3) as response:
                    return json.load(response)
            except HTTPError as error:
                error.close()
                raise

        try:
            slot = call("/api/native", dict(op="create", mode="campaign", name="Native"))
            for path in ("/api/state", "/api/document", "/api/job", "/api/book", "/api/settings"):
                with self.assertRaises(HTTPError) as caught:
                    call(path, dict(collection="archive", slot=slot["id"]))
                self.assertEqual(caught.exception.code, 404)
            for headers in ({"token":"bad"}, {"Origin":"https://example.com"}, {"Host":"example.com"}):
                with self.assertRaises(HTTPError) as caught:
                    call("/api/native", dict(op="list"), **headers)
                self.assertEqual(caught.exception.code, 403)
            with self.assertRaises(HTTPError) as caught:
                call("/api/native", dict(op="book", slot=slot["id"], book=1342))
            self.assertEqual(caught.exception.code, 400)
            with self.assertRaises(HTTPError):
                call("/api/native", dict(op="import", slot=slot["id"], url="https://example.com"))
        finally:
            http.shutdown()
            http.server_close()
            worker.join(timeout=3)

    def test_two_launchers_cannot_overwrite_the_same_library(self):
        with single_library(self.root):
            with self.assertRaisesRegex(SystemExit, "already open"):
                with single_library(self.root):
                    self.fail("The second launcher acquired the first launcher's library")
        with single_library(self.root):
            pass

    def test_story_all_seven_crossings_rewards_and_return_home(self):
        slot = self.create("campaign")
        slot_id = slot["id"]
        def act(**data):
            return self.library.request(dict(slot=slot_id, **data))
        for era in range(7):
            self.assertEqual(slot["campaign"]["era"], era)
            self.assertNotIn("answer", slot["journey"]["trial"])
            act(op="story", action="intro")
            act(op="position", position=[250,143])
            slot = act(op="story", action="lens")
            for book in slot["books"]:
                if book["id"] not in slot["campaign"]["studied"]:
                    slot = act(op="campaign", action="study", book=book["id"])
            featured = native.story.TRIALS[era][4]
            for question in native.learning.CHECKS[featured]:
                result = act(op="quiz", book=featured, answer=question[2])
            slot = result["slot"]
            for place in ("town","garden"):
                slot = act(op="travel", destination=place)
            result = act(op="discuss", figure=slot["campaign"]["figures"][0]["id"], topic="challenge")
            slot = result["slot"]
            for place in ("town","workshop","town","library"):
                slot = act(op="travel", destination=place)
            before = copy.deepcopy(self.library.state)
            with self.assertRaises(ValueError):
                act(op="story", action="aligned", answer="guess")
            self.assertEqual(self.library.state, before)
            slot = act(op="story", action="aligned", answer=native.story.TRIALS[era][2])
            with self.assertRaises(ValueError):
                act(op="story", action="report", document="foreign")
            document, _ = manuscript(slot["campaign"], 99)
            slot = act(op="document", title=document["title"], text=document["text"])
            document_id = slot["documents"][-1]["id"]
            slot = act(op="story", action="report", document=document_id)
            money = slot["campaign"]["money"]
            slot = act(op="story", action="report", document=document_id)
            self.assertEqual(slot["campaign"]["money"], money)
            self.assertEqual(slot["journey"]["anchors"], era+1)
            if era:
                figure = slot["campaign"]["figures"][0]
                while slot["campaign"]["money"] < 4+era or slot["campaign"]["paper"] < 1:
                    slot = act(op="campaign", action="work")
                slot = act(op="campaign", action="letter", figure=figure["id"], text="Which observation would distinguish these explanations?", language="en")
                for _ in range(4):
                    slot = act(op="campaign", action="work")
            for number in range(slot["campaign"]["requirements"]["publications"]):
                document, submission = manuscript(slot["campaign"], number)
                slot = act(op="document", title=document["title"], text=document["text"])
                submission["document"] = slot["documents"][-1]["id"]
                while slot["campaign"]["paper"] < slot["campaign"]["commission"]["paper"]:
                    slot = act(op="campaign", action="work")
                slot = act(op="campaign", **submission)
            for _ in range(50):
                if slot["campaign"]["can_jump"]:
                    break
                slot = act(op="campaign", action="work")
            self.assertTrue(slot["campaign"]["can_jump"])
            slot = act(op="campaign", action="jump")
        self.assertTrue(slot["campaign"]["completed"])
        restored = native.Library(self.root).request(dict(op="load", slot=slot_id))
        self.assertEqual(restored["journey"]["anchors"],7)
        self.assertEqual(restored["campaign"],slot["campaign"])

    def test_ai_explicit_calls_key_isolation_context_and_failures(self):
        slot = self.create("campaign")
        config = dict(op="ai_config",url="http://localhost:11434/v1",model="local-chat",key="test-secret",enabled=True)
        self.library.request(config)
        self.assertNotIn("test-secret",self.library.path.read_text())
        self.library.request(config | {"key":""})
        self.assertTrue(self.library.request(dict(op="ai_status"))["key_present"])
        qualify(self.library)
        self.library.request(dict(op="campaign",slot=slot["id"],action="study",book=-1))
        self.library.request(dict(op="document",slot=slot["id"],title="Private",text="NEVER SEND AUTOMATICALLY"))
        with patch.object(native.legacy.requests,"post") as post:
            response = post.return_value.__enter__.return_value
            response.status_code = 200
            response.iter_content.return_value = [json.dumps({"choices":[{"message":{"content":"A test reply"}}]}).encode()]
            reply = self.library.request(dict(op="ai_ask",slot=slot["id"],resident="ada",text="How can I check this observation?"))
            self.assertEqual(reply["text"],"A test reply")
            sent = post.call_args.kwargs
            self.assertFalse(sent["allow_redirects"])
            self.assertEqual(sent["headers"]["Authorization"],"Bearer test-secret")
            context = json.dumps(sent["json"])
            self.assertIn("year is 1630",context)
            self.assertIn("Only the protagonist",context)
            self.assertIn("Jupiter",context)
            self.assertNotIn("NEVER SEND AUTOMATICALLY",context)
            self.assertNotIn("tools",sent["json"])
            for figure in ("newton", "unknown"):
                with self.assertRaisesRegex(ValueError,"living thinker"):
                    self.library.request(dict(op="ai_ask",slot=slot["id"],figure=figure,text="Explain your evidence."))
            self.assertEqual(post.call_count,1)
            self.library.request(dict(op="ai_ask",slot=slot["id"],figure="galileo",text="Explain your evidence."))
            context = post.call_args.kwargs["json"]["messages"][0]["content"]
            self.assertIn("Galileo Galilei",context)
            self.assertIn("fictional dialogue",context)
            self.assertNotIn("test-secret",context)
            response.status_code = 401
            with self.assertRaisesRegex(ValueError,"rejected the key"):
                self.library.request(dict(op="ai_test"))
            post.side_effect = native.legacy.requests.Timeout("test-secret must not leak")
            with self.assertRaisesRegex(ValueError,"connection failed") as caught:
                self.library.request(dict(op="ai_test"))
            self.assertNotIn("test-secret",str(caught.exception))
        for url in ("http://remote.example/v1","https://user:pass@example.com/v1","file:///local"):
            with self.assertRaises(ValueError):
                self.library.request(config | {"url":url})
        self.library.request(config | {"url":"https://example.com/v1","key":"","enabled":False})
        self.assertEqual(self.library.ai_key,"")
        with patch.object(native.legacy.requests,"post",side_effect=AssertionError("No automatic network")):
            self.library.request(dict(op="list"))
            self.library.request(dict(op="ai_status"))
            with self.assertRaises(ValueError):
                self.library.request(dict(op="ai_test"))

    def test_learning_feedback_free_retries_and_english_only(self):
        slot = self.create("campaign")
        def act(**data):
            return self.library.request(dict(slot=slot["id"], **data))
        with self.assertRaises(ValueError):
            act(op="quiz",book=-1,answer=1)
        slot = act(op="campaign",action="study",book=-1)
        before = copy.deepcopy(slot["campaign"])
        wrong = act(op="quiz",book=-1,answer=0)
        self.assertFalse(wrong["correct"])
        self.assertEqual(wrong["slot"]["campaign"],before)
        self.assertIn("Repeated",wrong["explanation"])
        half = act(op="quiz",book=-1,answer=1,question=0)
        self.assertTrue(half["correct"] and half["next"] and not half["first"])
        self.assertEqual(half["slot"]["campaign"],before)
        self.assertFalse(half["slot"]["learning"]["-1"]["mastered"])
        with self.assertRaisesRegex(ValueError,"changed"):
            act(op="quiz",book=-1,answer=1,question=0)
        second = act(op="book",book=-1)["quiz"]
        self.assertEqual((second["index"],second["total"],second["answered"]),(1,2,1))
        self.assertIn("leave open",second["question"])
        correct = act(op="quiz",book=-1,answer=1,question=1)
        self.assertTrue(correct["first"])
        self.assertEqual(correct["slot"]["campaign"]["paper"],before["paper"]+1)
        retry = act(op="quiz",book=-1,answer=1)
        self.assertFalse(retry["first"])
        self.assertEqual(retry["slot"]["campaign"],correct["slot"]["campaign"])
        self.assertEqual(act(op="book",book=-1)["quiz"]["index"],1)
        book = act(op="book",book=-1)
        self.assertNotIn("ESPAÑOL",book["text"])
        self.assertTrue(book["quiz"]["mastered"])
        self.assertNotIn("answer",book["quiz"])
        for book in native.campaign.BOOKS.values():
            self.assertEqual(book["languages"],["en"])
            self.assertEqual(set(book["notes"]),{"en"})
        restored = native.Library(self.root).request(dict(op="load",slot=slot["id"]))
        self.assertTrue(restored["learning"]["-1"]["mastered"])
        legacy = dict(mode="campaign",campaign=dict(studied=[-2],prestige=0,paper=0),learning={"-2":dict(attempts=1,mastered=True)})
        self.assertTrue(native.learning.public(legacy,-2)["mastered"])
        self.assertFalse(native.learning.answer(legacy,-2,0)["first"])

    def test_every_learning_check_is_well_formed(self):
        for book, questions in native.learning.CHECKS.items():
            self.assertIn(book, native.campaign.BOOKS)
            self.assertEqual(len(questions), 2)
            for question, options, answer, explanation in questions:
                self.assertEqual(len(options), 3)
                self.assertEqual(len(set(options)), 3)
                self.assertIn(answer, range(3))
                self.assertTrue(question.endswith("?") and explanation)

    def test_computer_generation_uses_selected_period_sources(self):
        slot = self.create("campaign")
        self.library.request(dict(op="ai_config",url="http://localhost:11434/v1",model="mock",key="",enabled=True))
        qualify(self.library)
        request = dict(op="ai_generate",slot=slot["id"],kind="article",text="Compare observation and interpretation",books=[-1])
        with patch.object(native.legacy.requests,"post") as post:
            with self.assertRaises(ValueError):
                self.library.request(request)
            post.assert_not_called()
            self.library.request(dict(op="campaign",slot=slot["id"],action="study",book=-1))
            self.library.request(dict(op="campaign",slot=slot["id"],action="study",book=-2))
            for books in ([-14],[1342],[],[True]):
                with self.assertRaises(ValueError):
                    self.library.request(request | {"books":books})
            response = post.return_value.__enter__.return_value
            response.status_code = 200
            response.iter_content.return_value = [json.dumps({"choices":[{"message":{"content":"A sourced draft [B1]"}}]}).encode()]
            result = self.library.request(request)
            self.assertIn("[B1]",result["text"])
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["max_tokens"],2200)
            self.assertIn("450–550",payload["messages"][0]["content"])
            self.assertIn("Jupiter",payload["messages"][0]["content"])
            self.assertNotIn("Radioactivity",payload["messages"][0]["content"])
            self.assertNotIn(native.campaign.BOOKS[-2]["notes"]["en"],payload["messages"][0]["content"])
            self.assertEqual(self.library.state["slots"][slot["id"]]["documents"],[])
            self.library.request(dict(op="travel",slot=slot["id"],destination="town"))
            with self.assertRaisesRegex(ValueError,"computer"):
                self.library.request(request)
        restored = native.Library(self.root).request(dict(op="load",slot=slot["id"]))
        self.assertEqual(restored["place"],"town")
        with self.assertRaises(ValueError):
            self.library.request(dict(op="travel",slot=slot["id"],destination="invalid"))


if __name__ == "__main__":
    unittest.main()
