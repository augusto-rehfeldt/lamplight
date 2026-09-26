"""The writing engine's router runs every completion on the shared ai-suite AIService.

Offline: the service factory is replaced by a fake; no provider, CLI or proxy is touched.
Run: python -B -m unittest -q test_engine_llm
"""
import os
import pathlib
import sys
import unittest
from unittest.mock import MagicMock, patch

import game_server as legacy

llm = legacy.llm


class FakeService:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate_content(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.saved = (llm.CHAIN[:], llm.PRO, llm.FLASH, dict(llm.PROVIDERS), llm.INTERACTIVE)
        llm.INTERACTIVE = False
        self.built = []
        self.services = {}

        def factory(provider, overrides):
            self.built.append((provider, dict(overrides)))
            return self.services[provider]
        patcher = patch.object(llm, "shared_service", side_effect=factory)
        patcher.start()
        self.addCleanup(patcher.stop)
        env = patch.dict(os.environ, {"AW_API_KEY": "hyper-key", "OPENCODE_API_KEY": "zen-key"})
        env.start()
        self.addCleanup(env.stop)

    def tearDown(self):
        chain, pro, flash, providers, interactive = self.saved
        llm.PROVIDERS.clear()
        llm.PROVIDERS.update(providers)
        llm.configure(chain, pro, flash)
        llm.INTERACTIVE = interactive

    def test_hyper_link_streams_through_the_shared_hyper_config(self):
        self.services["hyper"] = FakeService(["draft"])
        llm.configure(["hyper"], "qwen3.8-max", "deepseek-v4-pro-0813")
        self.assertEqual(llm.chat(llm.PRO, "write", "be exact", temperature=0.3, max_tokens=900), "draft")
        provider, overrides = self.built[0]
        self.assertEqual(provider, "hyper")
        self.assertEqual((overrides["base_url"], overrides["api_key"], overrides["stream"]),
                         (llm.PROVIDERS["hyper"]["base_url"], "hyper-key", True))
        self.assertEqual((overrides["token_param"], overrides["cap_is_ceiling"]), ("max_tokens", True))
        prompt, kwargs = self.services["hyper"].calls[0]
        self.assertEqual(prompt, "write")
        self.assertEqual(kwargs["model"], "qwen3.8-max")
        self.assertEqual((kwargs["system"], kwargs["temperature"], kwargs["max_completion_tokens"]),
                         ("be exact", 0.3, 900))
        self.assertFalse(kwargs["wait_for_limits"])

    def test_chain_falls_to_the_next_link_and_translates_the_role(self):
        self.services["hyper"] = FakeService([RuntimeError("503")])
        self.services["opencode-zen"] = FakeService(["from zen"])
        llm.configure(["hyper", "zen"], "qwen3.8-max", "deepseek-v4-pro-0813")
        self.assertEqual(llm.chat(llm.FLASH, "p"), "from zen")
        provider, overrides = self.built[-1]
        self.assertEqual((provider, overrides["api_key"]), ("opencode-zen", "zen-key"))
        self.assertEqual(self.services["opencode-zen"].calls[0][1]["model"], "deepseek-v4-pro")

    def test_claude_link_is_the_shared_cli_and_a_quota_notice_is_a_failure(self):
        self.services["claude"] = FakeService(["You've hit your session limit · resets 9:10am"])
        self.services["hyper"] = FakeService(["real text"])
        llm.configure(["claude", "hyper"], "opus", "sonnet")
        self.assertEqual(llm.chat("sonnet", "p"), "real text")
        provider, overrides = self.built[0]
        self.assertEqual(provider, "claude")
        self.assertFalse({"base_url", "api_key", "stream"} & set(overrides))

    def test_go_link_uses_the_shared_opencode_go_config(self):
        self.services["opencode-go"] = FakeService(["ok"])
        llm.configure(["go"], "qwen3.8-max", "deepseek-v4-pro-0813")
        llm.chat(llm.FLASH, "p")
        provider, overrides = self.built[0]
        self.assertEqual(provider, "opencode-go")
        self.assertNotIn("api_key", overrides)  # ai-suite reads opencode's own login
        self.assertEqual(self.services["opencode-go"].calls[0][1]["model"], "deepseek-v4-pro")

    def test_custom_provider_only_ever_gets_its_own_key(self):
        llm.PROVIDERS["mine"] = dict(label="mine", base_url="https://api.example/v1", key_env="MINE_KEY",
                                     pro="p1", flash="f1", models=["p1", "f1"], alias={}, exclusive=False,
                                     own_key_only=True)
        self.services["openrouter"] = FakeService(["x"])
        llm.configure(["mine"], "p1", "f1")
        with patch.dict(os.environ, {"MINE_KEY": "mine-key"}):
            llm.chat("p1", "p")
        provider, overrides = self.built[0]
        self.assertEqual((provider, overrides["base_url"], overrides["api_key"], overrides["headers"]),
                         ("openrouter", "https://api.example/v1", "mine-key", {}))
        with patch.dict(os.environ, {"MINE_KEY": ""}), self.assertRaisesRegex(RuntimeError, "MINE_KEY"):
            llm.chat("p1", "p")

    def test_chat_json_repairs_through_the_same_path(self):
        self.services["hyper"] = FakeService(["not json at all", '```json\n{"ok": true}\n```'])
        llm.configure(["hyper"], "qwen3.8-max", "deepseek-v4-pro-0813")
        self.assertEqual(llm.chat_json(llm.PRO, "give json"), {"ok": True})
        self.assertEqual(self.services["hyper"].calls[1][1]["temperature"], 0.0)

    def test_engine_has_no_provider_transport_of_its_own(self):
        source = (pathlib.Path(llm.__file__)).read_text(encoding="utf-8")
        for needle in ("from openai import", "OpenAI(", '"-p"', '"run", "-m"'):
            self.assertNotIn(needle, source)


class SharedServiceTests(unittest.TestCase):
    def test_builds_the_suites_service_once_per_setting(self):
        built = []
        suite = MagicMock()
        suite.AIService.side_effect = lambda **kw: built.append(kw) or object()
        suite.provider_config_path.side_effect = lambda name: f"/cfg/{name}.json"
        modules = {"ai_suite": suite}
        with patch.dict(sys.modules, modules), patch.object(sys, "path", list(sys.path)), \
                patch.dict(llm._services, clear=True):
            first = llm.shared_service("hyper", {"api_key": "k"})
            self.assertIs(llm.shared_service("hyper", {"api_key": "k"}), first)
            llm.shared_service("hyper", {"api_key": "other"})
            self.assertIn(str(llm.SUITE_PATH), sys.path)
        self.assertEqual(len(built), 2)
        self.assertEqual(built[0]["config_path"], "/cfg/hyper.json")
        self.assertEqual(built[0]["config_overrides"], {"api_key": "k"})
        self.assertFalse(built[0]["allow_auth_prompt"])


if __name__ == "__main__":
    unittest.main()
