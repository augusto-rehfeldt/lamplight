"""Optional UI smoke test with an installed Playwright browser; uses a temporary save.

Run: python check_game_browser.py. No model calls or game-save changes.
"""
import pathlib
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from playwright.sync_api import sync_playwright
from playwright.sync_api import expect

import game_server as server
import game_campaign as campaign


def check_reference(browser, evidence):
    """The M0 board is a local, offline reference, separate from player saves."""
    context = browser.new_context(offline=True, device_scale_factor=1.25,
                                  reduced_motion="reduce")
    try:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((server.WEB / "reference.html").as_uri())
        expect(page.locator("#selection")).to_contain_text("Arrival:")
        arrival = page.locator("#room").evaluate("canvas => canvas.toDataURL()")
        page.get_by_label("Opening choice").select_option("shared")
        expect(page.locator("#selection")).to_contain_text("public observation circle")
        shared = page.locator("#room").evaluate("canvas => canvas.toDataURL()")
        page.get_by_label("Opening choice").select_option("patron")
        expect(page.locator("#selection")).to_contain_text("access to the instruments")
        patron = page.locator("#room").evaluate("canvas => canvas.toDataURL()")
        assert len({arrival, shared, patron}) == 3, "Opening choices need distinct room art"
        for mode, label in (("free_play", "FREE PLAY"), ("modern", "MODERN")):
            page.get_by_label("Mode", exact=True).select_option(mode)
            expect(page.locator("#scene-label")).to_contain_text(label)
            expect(page.get_by_label("Opening choice")).to_be_hidden()
        page.get_by_label("Mode", exact=True).select_option("campaign")
        expect(page.get_by_label("Opening choice")).to_have_value("patron")
        page.get_by_label("Opening choice").select_option("arrival")
        page.get_by_label("Readable UI font").check()
        expect(page.locator("body")).to_have_class("readable")
        page.get_by_label("Readable UI font").uncheck()
        for width, height in ((1280, 720), (1920, 1080), (390, 844)):
            page.set_viewport_size(dict(width=width, height=height))
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(evidence / f"reference-{width}.png"), full_page=True)
        page.set_viewport_size(dict(width=1280, height=720))
        page.evaluate("document.body.style.zoom = '125%'")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        expect(page.get_by_label("Mode", exact=True)).to_be_visible()
        assert not errors, errors
    finally:
        context.close()


def main():
    settings = dict(chain=server.llm.CHAIN[:], pro=server.llm.PRO, flash=server.llm.FLASH,
                    agent_model=server.llm.FLASH, agents={}, custom=[], language="en", monthly_calls=0)
    catalog = {b["id"]: b for b in server.read_json(server.WEB / "books.json", [])}
    with tempfile.TemporaryDirectory() as directory, patch.object(server, "DATA", pathlib.Path(directory)), patch.object(server, "BOOKS", campaign.BOOKS | catalog), patch.object(server, "SETTINGS", settings), patch.object(server, "JOBS", {}):
        cache = pathlib.Path(directory) / "books"
        cache.mkdir()
        # A long deterministic text exercises pagination/search without external downloads.
        (cache / "1342.txt").write_text("CHAPTER I\n\n" + ("An English reading fixture. " * 100 + "\n\n") * 6 + "CHAPTER II\n\nThe hidden amber bookmark.", encoding="utf-8")
        http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        worker = threading.Thread(target=http.serve_forever, daemon=True)
        worker.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1365, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{http.server_port}")
                expect(page.locator("#book-total")).to_have_text("1,200")
                evidence = server.ROOT / "output" / "lamplight-ui-check"
                evidence.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(evidence / "library-desktop.png"))
                for width, height in ((1280, 720), (1920, 1080), (390, 844)):
                    page.set_viewport_size(dict(width=width, height=height))
                    page.screenshot(path=str(evidence / f"baseline-{width}.png"), full_page=True)
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.set_viewport_size(dict(width=1365, height=1000))
                canvas = page.locator("#world")
                size = canvas.bounding_box()
                canvas.click(position={"x": size["width"] * 730 / 960, "y": size["height"] * 308 / 560})
                expect(page.get_by_role("heading", name="A small machine. Endless possibilities.")).to_be_visible(timeout=15000)
                page.get_by_role("button", name="Close panel", exact=True).click()
                page.get_by_role("button", name="Open the time machine").click()
                page.get_by_role("button", name="Study · 1 day").first.click()
                page.get_by_role("button", name="Studied", exact=True).wait_for()
                page.get_by_role("button", name="Take to desk").first.click()
                page.get_by_role("button", name="Return", exact=True).wait_for()
                page.locator("#letter-text").fill("Can one observation establish that the lights revolve around Jupiter?")
                page.get_by_role("button", name="Send letter").click()
                page.get_by_text("Galileo Galilei · 1630 · Arrives day 6", exact=True).wait_for()
                assert page.locator(".agent-response").count() == 0
                for day in range(3, 7):
                    page.get_by_role("button", name="Wait one day", exact=True).click()
                    page.get_by_text(f"Day {day}", exact=True).wait_for()
                page.get_by_text("Galileo Galilei · 1630 · Delivered", exact=True).click()
                assert "Jupiter" in page.locator(".agent-response").inner_text()
                assert page.get_by_role("button", name="Español", exact=True).count() == 0
                page.locator("#letter-parent").select_option(index=1)
                page.locator("#letter-text").fill("How could another observer check these movements using a different telescope?")
                page.get_by_role("button", name="Send letter").click()
                page.get_by_text("Galileo Galilei · 1630 · Arrives day 10", exact=True).wait_for()
                page.get_by_role("button", name="Add source notes to manuscript").click()
                assert "Jupiter" in page.get_by_role("textbox", name="Manuscript", exact=True).input_value()
                page.get_by_role("button", name="Save", exact=True).click()
                page.get_by_role("button", name="Close panel", exact=True).click()
                page.get_by_role("button", name="Time machine and post desk", exact=True).click()
                page.screenshot(path=str(evidence / "campaign-desktop.png"))
                page.set_viewport_size({"width": 390, "height": 844})
                page.screenshot(path=str(evidence / "campaign-mobile.png"))
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.get_by_role("button", name="Close panel", exact=True).click()
                page.set_viewport_size({"width": 1365, "height": 1000})
                page.locator('[data-view="archive"]').first.click()
                expect(page.get_by_role("heading", name="A thousand doors to somewhere.")).to_be_visible()
                expect(page.locator("#book-language")).to_have_value("en")
                page.screenshot(path=str(evidence / "english-catalog.png"))
                page.get_by_role("searchbox", name="Search books", exact=True).fill("pride prejudice")
                expect(page.locator('.book-cover[data-id="1342"]')).to_be_visible()
                page.locator('.book-card [data-action="bag"][data-id="1342"]').click()
                page.locator('.book-cover[data-id="1342"]').click()
                expect(page.locator("#reading-text")).to_contain_text("CHAPTER I")
                page.get_by_role("searchbox", name="Find in book", exact=True).fill("hidden amber")
                page.get_by_role("button", name="Find next", exact=True).click()
                expect(page.locator("#reading-text mark")).to_have_text("hidden amber")
                assert int(page.locator("#page-number").input_value()) > 1
                page.locator("#reader-font").select_option("sans")
                page.locator("#reader-size").select_option("22")
                expect(page.locator("#reading-text mark")).to_be_in_viewport()
                page.screenshot(path=str(evidence / "reader.png"))
                page.get_by_role("button", name="Close panel", exact=True).click()
                page.locator('[data-view="computer"]').first.click()
                expect(page.locator("#panel-body .notice").first).to_contain_text("English library")
                page.locator("#mode").select_option("manual")
                page.get_by_role("button", name="Open the blank page").click()
                page.locator("#draft-title").fill("English library smoke check")
                page.locator("#manuscript").fill("A quiet English manuscript.\n\n<script>alert('must stay text')</script>")
                page.get_by_role("button", name="Preview", exact=True).click()
                expect(page.locator(".preview")).to_contain_text("<script>")
                page.get_by_role("button", name="Edit", exact=True).click()
                page.get_by_role("button", name="Save", exact=True).click()
                expect(page.locator("#save-state")).to_have_text("Saved to your library")
                page.reload()
                page.locator('[data-view="writer"]').first.click()
                expect(page.locator("#manuscript")).to_contain_text("A quiet English manuscript.")
                page.get_by_role("button", name="Close panel", exact=True).click()
                page.locator('[data-view="settings"]').first.click()
                page.locator("#setting-agent").fill("shared-test-model")
                page.locator('[data-agent-model="editor"]').fill("editor-test-model")
                page.get_by_role("button", name="Save settings", exact=True).click()
                expect(page.locator("#settings-status")).to_have_text("Saved. The computer is ready.")
                page.get_by_role("button", name="Close panel", exact=True).click()
                page.locator('[data-view="residents"]').first.click()
                expect(page.locator(".resident-card").first).to_contain_text("editor-test-model")
                page.set_viewport_size({"width": 390, "height": 844})
                page.screenshot(path=str(evidence / "residents-mobile.png"))
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.get_by_role("button", name="Close panel", exact=True).click()
                page.locator('[data-view="archive"]').first.click()
                page.screenshot(path=str(evidence / "catalog-mobile.png"))
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.get_by_role("button", name="Close panel", exact=True).click()
                page.get_by_role("button", name="A little help").click()
                page.get_by_role("button", name="Coffee break", exact=True).click()
                page.get_by_role("button", name="Start pouring", exact=True).click()
                deadline = time.monotonic() + 4
                while time.monotonic() < deadline:
                    position = float(page.locator("#coffee-needle").get_attribute("style").split(":")[1].strip(" ;%"))
                    if 45 <= position <= 50:
                        break
                    time.sleep(.025)
                else:
                    raise AssertionError("Coffee marker did not move into the target")
                page.get_by_role("button", name="Stop pouring", exact=True).click()
                expect(page.locator("#coffee-result")).to_contain_text("+1 lovely cup")
                assert not errors, errors
                check_reference(browser, evidence)
                browser.close()
                print("PASS: campaign, English catalog, trolley, full-book search, typography, manual writer, safe preview, persistence, resident models, desktop/mobile; M0 offline reference, choices, modes and scaling; no browser errors")
        finally:
            http.shutdown()
            http.server_close()
            worker.join(timeout=3)


if __name__ == "__main__":
    main()
