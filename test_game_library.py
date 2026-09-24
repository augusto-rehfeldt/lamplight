"""English library integration checks: python -m unittest test_game_library -v.

Uses temporary saves and mocked model/book responses; never spends API quota.
"""
import copy
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import game_campaign as campaign
import game_server as server


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = server.read_json(server.WEB / "books.json", [])
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.settings = dict(chain=server.llm.CHAIN[:], pro=server.llm.PRO, flash=server.llm.FLASH,
            agent_model=server.llm.FLASH, agents={}, custom=[], language="en", monthly_calls=0)
        for name, value in dict(DATA=self.root, BOOKS=campaign.BOOKS | {b["id"]: b for b in self.catalog},
                                SETTINGS=self.settings, JOBS={}, USAGE=[]).items():
            context = patch.object(server, name, value)
            context.start()
            self.addCleanup(context.stop)

    def test_catalog_has_1200_english_public_domain_editions_and_all_shelves(self):
        self.assertGreaterEqual(len(self.catalog), 1200)
        self.assertEqual(len({b["id"] for b in self.catalog}), len(self.catalog))
        for b in self.catalog:
            self.assertIn("en", b["languages"])
            self.assertIs(b["copyright"], False)
            self.assertEqual(b["rights"], "Public domain in the USA")
            self.assertTrue(b["rights_source"].endswith(f"/pg{b['id']}.rdf"))
        for category in ("Science", "Philosophy", "Politics", "Religion", "Literature", "History"):
            self.assertGreaterEqual(sum(category in b["categories"] for b in self.catalog), 150)

    def test_fulltext_cache_and_campaign_isolation(self):
        selected = self.catalog[0]
        with self.assertRaises(ValueError):
            server.book_text(selected["id"])
        with self.assertRaises(ValueError):
            server.book_text(-1, "archive")
        text = "CHAPTER I\n\n" + "An English book, with original source notices. " * 100
        with patch.object(server.requests, "get") as get:
            response = get.return_value.__enter__.return_value
            response.status_code = 200
            response.iter_content.return_value = [text.encode()]
            self.assertEqual(server.book_text(selected["id"], "archive"), text)
            self.assertEqual(server.book_text(selected["id"], "archive"), text)
            self.assertEqual(get.call_count, 1)
        source = server.sources_for([selected["id"]], "archive")[0]
        self.assertEqual(source.fulltext, text)
        self.assertEqual(source.year, "")  # Gutenberg upload dates are not original publication years.
        self.assertEqual(source.origin, "gutenberg")
        self.assertEqual(server.campaign_state()["era"], 0)
        with self.assertRaises(ValueError):
            server.start_job(dict(kind="ideas", books=[selected["id"]], collection="campaign"))
        self.assertFalse(server.WORK.locked())

    def test_custom_provider_never_inherits_another_api_key(self):
        s = copy.deepcopy(self.settings)
        provider = dict(id="my-local", base_url="http://127.0.0.1:1234/v1",
                        key_env="MY_LOCAL_KEY", pro="custom-pro", flash="custom-flash")
        s.update(custom=[provider], chain=["my-local"], pro="custom-pro", flash="custom-flash")
        self.assertEqual(server.clean_settings(s)["chain"], ["my-local"])
        with patch.dict(server.os.environ, {"AW_API_KEY": "must-not-be-forwarded"}, clear=True):
            self.assertFalse(server.llm._key_for(provider | {"own_key_only": True}))
        s["custom"][0]["base_url"] = "http://remote.example/v1"
        with self.assertRaises(ValueError):
            server.clean_settings(s)

    def test_archive_generation_reuses_pipeline_and_keeps_guided_checkpoint(self):
        selected = self.catalog[0]
        data = dict(kind="generate", books=[selected["id"]], brief="A quiet argument",
                    format="corto", mode="guided", language="en", collection="archive")
        job = dict(id="a" * 32, kind="generate", status="running", logs=[], period_context="", collection="archive")
        topic = dict(titulo="A quiet argument", hipotesis="Read carefully", pregunta="What changes?")
        answers = []

        def approve(run, prompt, default=""):
            answers.append(prompt)
            return ""

        def pipeline(run, **kwargs):
            self.assertEqual(run.mode, "asistido")
            self.assertEqual(run.load("01_topic.json"), topic)
            sources = server.research.load_dossier(run.dir / "02_dossier.json")
            self.assertEqual(sources[0].fulltext, "Complete source text")
            self.assertIn("libros", run.load("02_estado.json"))
            path = run.dir / "05_final.md"
            path.write_text("# A quiet argument\n\nFinished draft.", encoding="utf-8")
            return path

        with patch.object(server, "ROOT", self.root), patch.object(server, "book_text", return_value="Complete source text"), \
             patch.object(server.llm, "chat_json", return_value=topic), \
             patch.object(server.LibraryRun, "ask", approve), patch.object(server.pipeline, "run_pipeline", pipeline):
            server.WORK.acquire()
            server.execute_job(job, data)
        self.assertEqual(job["status"], "complete", job)
        self.assertTrue(answers)
        self.assertIn("Finished draft", job["result"]["text"])
        self.assertFalse(server.WORK.locked())

    def test_usage_limit_blocks_a_call_before_the_provider(self):
        self.settings["monthly_calls"] = 1
        with patch.object(server, "_chat", return_value="Measured response") as model:
            server.measured_chat("test-model", "One question")
            with self.assertRaisesRegex(RuntimeError, "budget"):
                server.measured_chat("test-model", "Another question")
            self.assertEqual(model.call_count, 1)
        self.assertEqual(len(server.month_usage()), 1)
        self.assertTrue(server.month_usage()[0]["success"])


if __name__ == "__main__":
    unittest.main()
