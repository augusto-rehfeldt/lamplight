"""Deterministic qualification tests; all provider responses are local doubles."""
import copy
import json
import pathlib
import re
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import game_native as native
import lamplight_ai as ai
import bench_lamplight as bench
from run_lamplight import setup_hyper

PROSE = ("Repeated observations support a cautious comparison, but they cannot establish every proposed explanation. "
         "The source supplies a limited record rather than a complete account. Another reader should compare "
         "the conditions and preserve uncertainty before drawing a stronger conclusion. What evidence could distinguish the alternatives?")


def provider_reply(**request):
    """Double for game_native.chat_request: answers the qualification tasks correctly."""
    try:
        task = json.loads(request["prompt"])
    except ValueError:
        task = {}
    name = task.get("task")
    if name == "Source grounding":
        marker = re.search(r"\[B\d+\]", task["source"])[0]
        answer = dict(source_id=marker, observations=int(re.search(r"observed (\d+)", task["source"])[1]), distance_known=False, note=PROSE + " " + marker)
    elif name == "Period & evidence":
        answer = dict(eligible_sources=[s["id"] for s in task["sources"] if s["year"] <= task["year"]], page=None, reward=0, reply=PROSE)
    elif name == "Gameplay reasoning":
        answer = dict(actions=["travel:town", "travel:workshop", "work", "post"], coins_after=0, paper_after=0, explanation=PROSE)
    elif name == "Writing coach":
        answer = dict(ready=bool(task["text"].strip()), feedback="Your claim is clear. Explain what the observation can establish and what it leaves uncertain. What would you compare next?", suggestion="A repeated observation supports a limited claim. Explain the inference and its limits. [B1]")
    else:
        answer = None
    return (json.dumps(answer) if answer else PROSE), None


def failing_service(status):
    """A shared AIService whose provider answers with an HTTP error echoing the key."""
    error = RuntimeError(f"HTTP {status} for private-key")
    error.status_code = status
    service = MagicMock()
    service.generate_content.side_effect = error
    return service


def qualify(library):
    if not library.state["settings"].get("ai"):
        library.request(dict(op="ai_config", url="http://localhost:11434/v1", model="test-chat", key="", enabled=True))
    with patch.object(native, "chat_request", side_effect=provider_reply):
        result = library.request(dict(op="ai_test"))
    assert result["passed"] and result["score"] == 100
    return result


class QualificationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.library = native.Library(pathlib.Path(temporary.name))

    def test_gate_all_modes_mutations_restart_and_forged_pass(self):
        for mode in native.MODES:
            with self.assertRaisesRegex(ValueError, "AI required"):
                self.library.request(dict(op="create", mode=mode, name="Blocked", passed=True))
        qualify(self.library)
        slot = self.library.request(dict(op="create", mode="campaign", name="Qualified"))
        restored = native.Library(self.library.path.parent)
        self.assertFalse(restored.request(dict(op="ai_status"))["ready"])
        for data in [dict(op="travel", destination="town"), dict(op="campaign", action="work"), dict(op="quiz", book=-1, answer=1), dict(op="story", action="intro"), dict(op="talk", resident="margot"), dict(op="discuss", figure="galileo", topic="claim"), dict(op="ai_generate", kind="article", text="Write", books=[-1])]:
            with self.assertRaisesRegex(ValueError, "AI required"):
                restored.request(data | dict(slot=slot["id"]))
        # Recovery reads and manuscript saves stay available when qualification lapses.
        restored.request(dict(op="load", slot=slot["id"]))
        saved = restored.request(dict(op="document", slot=slot["id"], title="Safe", text="Unsaved work"))
        self.assertEqual(saved["documents"][0]["text"], "Unsaved work")

    def test_three_calls_score_and_every_critical_failure(self):
        qualify(self.library)
        for task in ai.cases():
            expected = task[2] | {task[3]: PROSE + " " + task[4]}
            self.assertEqual(ai.evaluate(task, json.dumps(expected))["score"], 100)
            for field in task[2]:
                bad = expected | {field: "invented"}
                self.assertFalse(ai.evaluate(task, json.dumps(bad))["critical"], field)
            self.assertFalse(ai.evaluate(task, "Hello there!")["critical"])
            self.assertFalse(ai.evaluate(task, "null")["critical"])
            self.assertFalse(ai.evaluate(task, json.dumps(expected | {task[3]: "good " * 40}))["checks"][task[3]])
        with patch.object(native, "chat_request", side_effect=provider_reply) as post:
            result = self.library.request(dict(op="ai_test"))
        self.assertEqual(post.call_count, 3)
        self.assertEqual(result["score"], 100)
        self.assertEqual(len(result["cases"]), 3)
        self.assertGreaterEqual(result["seconds"], 0)

    def test_hyper_startup_makes_no_calls_and_in_game_qualification_keeps_key_private(self):
        with patch.dict(native.os.environ, {"AW_API_KEY": "private-hyper-key", "AW_BASE_URL": "https://hyper.charm.land/v1"}), patch("builtins.print"), patch.object(native, "chat_request", side_effect=provider_reply) as post:
            self.assertIsNone(setup_hyper(self.library))
            post.assert_not_called()
            self.assertFalse(self.library.request(dict(op="ai_status"))["ready"])
            self.assertTrue(self.library.request(dict(op="ai_test"))["passed"])
        self.assertEqual(post.call_count, 3)
        for call in post.call_args_list:
            self.assertEqual(call.kwargs["url"], "https://hyper.charm.land/v1")
            self.assertEqual(call.kwargs["model"], "qwen3.8-max")
            self.assertEqual(call.kwargs["key"], "private-hyper-key")
        self.assertTrue(self.library.request(dict(op="ai_status"))["ready"])
        self.assertNotIn("private-hyper-key", self.library.path.read_text())
        self.assertNotIn("private-hyper-key", json.dumps(self.library.bootstrap()))
        with patch.dict(native.os.environ, {"AW_API_KEY": "private-hyper-key"}), patch("builtins.print"), patch.object(native, "chat_request", side_effect=native.AIConnectionError), self.assertRaises(ValueError):
            setup_hyper(self.library)
            self.library.request(dict(op="ai_test"))
        self.assertFalse(self.library.request(dict(op="ai_status"))["ready"])

    def test_live_runner_repeats_same_tasks_and_preserves_errors_without_keys(self):
        output = self.library.path.parent / "benchmark"
        prompts = {}

        def reply(**request):
            model = request["model"]
            if model == "offline":
                raise native.AIConnectionError("AI connection failed or timed out")
            prompts.setdefault(model, []).append((request["system"], request["prompt"]))
            return provider_reply(**request)

        with patch("builtins.print"), patch.object(native, "chat_request", side_effect=reply) as post:
            report = bench.benchmark(["offline", "first", "second"], "https://example.test/v1",
                                     "private-test-key", output, repeat=2, seed=17)
        self.assertEqual(post.call_count, 14)
        self.assertEqual(prompts["first"], prompts["second"])
        self.assertEqual([r["status"] for r in report["results"]],
                         ["request_error"] * 2 + ["passed"] * 4)
        self.assertNotIn("score", report["results"][0])
        self.assertFalse(self.library.path.exists(), "The runner must not touch player saves")
        for path in output.iterdir():
            self.assertNotIn("private-test-key", path.read_text(encoding="utf-8"))
        self.assertEqual(len((output / "requests.jsonl").read_text().splitlines()), 14)
        self.assertEqual(ai.cases(17), ai.cases(17))

    def test_truncated_and_oversized_text_cannot_qualify(self):
        truncated = ValueError("The model exhausted the response token limit. Try another model.")
        for outcome in [dict(side_effect=truncated), dict(return_value=("x" * 12001, None)),
                        dict(return_value=("", None)), dict(return_value=(None, None))]:
            qualify(self.library)
            with patch.object(native, "chat_request", **outcome), self.assertRaises(ValueError):
                self.library.request(dict(op="ai_test"))
            self.assertFalse(self.library.request(dict(op="ai_status"))["ready"])
            self.assertFalse(self.library.ai_lock.locked())

    def test_weak_model_and_failed_retest_revoke_qualification(self):
        qualify(self.library)
        with patch.object(native, "chat_request", return_value=("Hello!", None)):
            result = self.library.request(dict(op="ai_test"))
        self.assertFalse(result["passed"])
        self.assertEqual(result["score"], 0)
        self.assertFalse(self.library.request(dict(op="ai_status"))["ready"])
        qualify(self.library)
        for error in [native.AIConnectionError("AI connection failed"), ValueError("bounded response")]:
            with patch.object(native, "chat_request", side_effect=error), self.assertRaises(ValueError):
                self.library.request(dict(op="ai_test"))
            self.assertFalse(self.library.request(dict(op="ai_status"))["ready"])
            self.assertFalse(self.library.ai_lock.locked())

    def test_high_total_cannot_hide_critical_failure_or_bad_prose(self):
        tasks = ai.cases()
        def send(system, prompt):
            task = next(t for t in tasks if t[0] == json.loads(prompt)["task"])
            answer = task[2] | {task[3]: PROSE + " " + task[4]}
            if task[0] == "Period & evidence":
                answer["reward"] = 900
            return json.dumps(answer)
        with patch.object(ai, "cases", return_value=tasks):
            result = ai.run(send)
        self.assertGreater(result["score"], ai.MIN_SCORE)
        self.assertFalse(result["passed"], "A high total cannot excuse invented rewards")
        with patch.object(ai, "cases", return_value=tasks):
            result = ai.run(lambda system, prompt: json.dumps(next(t[2] for t in tasks if t[0] == json.loads(prompt)["task"])))
        self.assertFalse(result["passed"], "Structured guesses without prose cannot qualify")

    def test_benchmark_excludes_manuscripts_and_bounds_transport(self):
        qualify(self.library)
        slot = self.library.request(dict(op="create", mode="campaign", name="Privacy"))
        self.library.request(dict(op="document", slot=slot["id"], title="Private", text="PRIVATE MANUSCRIPT SENTINEL"))
        with patch.object(native, "chat_request", side_effect=provider_reply) as post:
            self.library.request(dict(op="ai_test"))
        self.assertNotIn("PRIVATE MANUSCRIPT SENTINEL", str(post.call_args_list))
        for call in post.call_args_list:
            self.assertEqual((call.kwargs["timeout"], call.kwargs["max_tokens"]), (ai.TIMEOUT, ai.MAX_TOKENS))
        for status in [401,404,429,500]:
            with patch.object(native.legacy.llm, "shared_service", return_value=failing_service(status)), \
                    self.assertRaises(ValueError) as caught:
                self.library.request(dict(op="ai_test"))
            self.assertNotIn("private", str(caught.exception))
            self.assertFalse(self.library.request(dict(op="ai_status"))["ready"])

    def test_chat_request_runs_on_the_shared_suite_and_maps_errors(self):
        service = MagicMock()
        service.generate_content.return_value = "A reply"
        service.last_usage = {"prompt_tokens": 7, "completion_tokens": 3}
        with patch.object(native.legacy.llm, "shared_service", return_value=service) as factory:
            answer = native.chat_request(url="https://api.example/v1/", key="private-key", model="m",
                                         system="rules", prompt="hi", max_tokens=450, timeout=25)
        self.assertEqual(answer, ("A reply", {"prompt_tokens": 7, "completion_tokens": 3}))
        provider, overrides = factory.call_args.args
        self.assertEqual(provider, "openrouter")
        self.assertEqual(overrides, {"base_url": "https://api.example/v1", "api_key": "private-key", "timeout": 25,
                                     "token_param": "max_tokens", "cap_is_ceiling": True, "headers": {}})
        keyless = MagicMock(**{"generate_content.return_value": "ok", "last_usage": None})
        with patch.object(native.legacy.llm, "shared_service", return_value=keyless) as factory:
            native.chat_request(url="http://localhost:11434/v1", key="", model="m", system="", prompt="hi",
                                max_tokens=450, timeout=25)
        self.assertEqual(factory.call_args.args[1]["api_key"], "")  # keyless: never another provider's key
        self.assertEqual(service.generate_content.call_args.kwargs,
                         dict(model="m", system="rules", max_completion_tokens=450, max_retries=1, wait_for_limits=False))
        messages = {401: "rejected the key", 404: "not found", 429: "quota", 503: "HTTP 503"}
        for status, text in messages.items():
            with patch.object(native.legacy.llm, "shared_service", return_value=failing_service(status)), \
                    self.assertRaisesRegex(ValueError, text) as caught:
                native.chat_request(url="https://api.example/v1", key="private-key", model="m",
                                    system="", prompt="hi", max_tokens=10, timeout=5)
            self.assertNotIn("private-key", str(caught.exception))
        timeout = MagicMock()
        timeout.generate_content.side_effect = TimeoutError("private-key timed out")
        with patch.object(native.legacy.llm, "shared_service", return_value=timeout), \
                self.assertRaises(native.AIConnectionError) as caught:
            native.chat_request(url="https://api.example/v1", key="private-key", model="m",
                                system="", prompt="hi", max_tokens=10, timeout=5)
        self.assertNotIn("private-key", str(caught.exception))

    def test_config_change_invalidates_and_router_rejected(self):
        qualify(self.library)
        config = dict(op="ai_config", url="http://localhost:11434/v1", model="different", key="private-test-key", enabled=True)
        self.library.request(config | dict(benchmark={"passed": True}, ready=True))
        self.assertFalse(self.library.request(dict(op="ai_status"))["ready"])
        self.assertNotIn("private-test-key", self.library.path.read_text())
        for model in ["openrouter/free", "openrouter/auto"]:
            with self.assertRaisesRegex(ValueError, "specific model"):
                self.library.request(config | dict(model=model))
        qualify(self.library)
        self.library.ai_lock.acquire()
        try:
            with self.assertRaisesRegex(ValueError, "Wait"):
                self.library.request(config)
        finally:
            self.library.ai_lock.release()

    def test_discussion_only_advances_after_real_response_and_tutorial_persists(self):
        qualify(self.library)
        slot = self.library.request(dict(op="create", mode="campaign", name="Circle"))
        def act(**data):
            return self.library.request(data | dict(slot=slot["id"]))
        act(op="campaign", action="study", book=-1)
        act(op="travel", destination="town")
        act(op="travel", destination="garden")
        before = copy.deepcopy(self.library.state)
        with patch.object(native, "chat_request", side_effect=native.AIConnectionError), self.assertRaises(ValueError):
            act(op="discuss", figure="galileo", topic="evidence")
        self.assertEqual(self.library.state, before)
        with patch.object(native, "chat_request", side_effect=provider_reply):
            result = act(op="discuss", figure="galileo", topic="evidence")
        self.assertIn("discussed", result["slot"]["journey"]["flags"])
        act(op="tutorial", lesson="map")
        act(op="tutorial", lesson="map")
        self.assertEqual(act(op="load")["tutorial"], ["map"])
        act(op="guidance", enabled=False)
        replay = act(op="tutorial", lesson="replay")
        self.assertEqual(replay["tutorial"], [])
        self.assertTrue(replay["guidance"])


if __name__ == "__main__":
    unittest.main()
