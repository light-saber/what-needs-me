"""Browser regression checks for the read-only Today deck."""

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

playwright = pytest.importorskip("playwright.sync_api")
expect = playwright.expect
sync_playwright = playwright.sync_playwright
STATIC_DIR = Path(__file__).resolve().parents[1] / "app" / "static"


@contextmanager
def static_server():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(STATIC_DIR)))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        worker.join()
        server.server_close()


@pytest.fixture(scope="module")
def browser_env():
    with static_server() as base_url, sync_playwright() as runner:
        browser = runner.chromium.launch(headless=True)
        yield base_url, browser
        browser.close()


def card(category, ask, thread_id, **overrides):
    item = {
        "category": category, "ask": ask, "threadId": thread_id,
        "accountId": "personal", "sender": "Example <person@example.com>",
        "subject": f"Original subject {thread_id}", "snippet": "A useful preview",
        "date": "2026-10-28T12:00:00Z", "deadline_ts": None, "urgency": "medium",
    }
    item.update(overrides)
    return item


def open_deck(page, base_url, cards, pile=None):
    page.route("**/api/accounts", lambda route: route.fulfill(json=[
        {"id": "personal", "label": "Personal", "color": "#5b51e8"},
        {"id": "work", "label": "Work", "color": "#167568"},
    ]))
    page.route("**/api/today?*", lambda route: route.fulfill(json={
        "cards": cards, "pile": {"categories": pile or {}}, "date": "2026-10-29",
    }))
    page.goto(base_url)
    page.wait_for_load_state("networkidle")


def thread_response():
    return {
        "summary": "Budget review requested.",
        "changed_since_last_seen": "A new request arrived.",
        "messages": [{"from": "Person <person@example.com>", "subject": "Budget",
                      "snippet": "Please approve the budget.", "date": "2026-10-28T12:00:00Z"}],
    }


def test_tiers_source_order_cap_and_disclosure(browser_env):
    base_url, browser = browser_env
    page = browser.new_page()
    try:
        cards = [
            card("approval", "Approve the budget", "a", urgency="high", deadline_ts="2026-10-30T12:00:00Z"),
            card("personal", "Reply", "generic"),
            card("travel", "Review travel details", "travel"),
            card("approval", "Review contract", "b"),
            card("approval", "Sign off proposal", "c", accountId="work"),
            card("approval", "Confirm scope", "d", accountId="work"),
            card("approval", "Read and respond", "generic2"),
            card("approval", "Respond by Oct 30", "generic3", deadline_ts="2026-10-30T12:00:00Z"),
            card("notification", "Approve now", "robot", sender="no-reply@example.com"),
        ]
        open_deck(page, base_url, cards)
        assert page.locator(".tier-action .card").count() == 3
        assert page.locator(".tier-action .headline").all_inner_texts() == [
            "Approve the budget", "Review contract", "Sign off proposal"]
        assert page.locator(".rank").all_inner_texts() == ["PRIORITY 1 · URGENT", "PRIORITY 2", "PRIORITY 3"]
        assert page.locator(".deadline").first.inner_text().startswith("Due ·")
        assert "Example <person@example.com>" in page.locator(".tier-action .card").first.inner_text()
        assert "Original subject a" in page.locator(".tier-action .card").first.inner_text()
        assert page.locator(".tier-fyi .card").count() == 1
        assert page.locator(".tier-quiet .quiet-row").count() == 3
        expect(page.locator("#status")).to_have_text("5 need you · 3 shown, 2 more · 1 for your info · 3 also arrived")
        page.get_by_role("button", name="Show 2 more priorities").click()
        assert page.locator(".tier-action .headline").all_inner_texts()[-1] == "Respond by Oct 30"
        expect(page.locator("#status")).to_have_text("5 need you · 1 for your info · 3 also arrived")
        page.get_by_role("button", name="Split").click()
        expect(page.locator(".tier-action .card")).to_have_count(3)
        expect(page.locator("#status")).to_contain_text("3 shown, 2 more")
    finally:
        page.close()


def test_generic_response_with_deadline_stays_in_action_deck(browser_env):
    base_url, browser = browser_env
    page = browser.new_page()
    try:
        open_deck(page, base_url, [
            card("personal", "Reply by tomorrow", "dated-reply", deadline_ts="2026-10-30T12:00:00Z"),
            card("personal", "Reply", "undated-reply"),
        ])
        expect(page.locator(".tier-action .card")).to_have_count(1)
        expect(page.locator(".tier-action .headline")).to_have_text("Reply by tomorrow")
        expect(page.locator(".tier-action .deadline")).to_be_visible()
        expect(page.locator(".tier-quiet .quiet-row")).to_have_count(1)
        expect(page.locator("#status")).to_have_text("1 need you · 1 also arrived")
    finally:
        page.close()


def test_empty_and_pile_states(browser_env):
    base_url, browser = browser_env
    page = browser.new_page()
    try:
        open_deck(page, base_url, [])
        expect(page.locator("#lanes .empty")).to_have_text("Clear for now. Nothing needs you.")
        assert page.locator("#pile").is_hidden()
        page.reload()
        open_deck(page, base_url, [card("approval", "Approve budget", "a")])
        expect(page.locator("#pile-empty")).to_have_text("Nothing else came in.")
        assert page.locator("#pile-toggle").is_hidden()
        page.route("**/api/today?*", lambda route: route.fulfill(json={
            "cards": [card("approval", "Approve budget", "a")],
            "pile": {"categories": {"newsletter": {"count": 2, "latest": "2026-10-28T12:00:00Z"}}},
        }))
        page.reload()
        page.locator("#pile-toggle").click()
        expect(page.locator("#pile-toggle")).to_have_attribute("aria-expanded", "true")
        expect(page.locator(".pile-row")).to_contain_text("2 newsletter")
    finally:
        page.close()


def test_initial_error_and_retry(browser_env):
    base_url, browser = browser_env
    page = browser.new_page()
    calls = {"today": 0}

    def today(route):
        calls["today"] += 1
        if calls["today"] == 1:
            route.fulfill(status=503, json={"detail": "unavailable"})
        else:
            route.fulfill(json={"cards": [card("approval", "Approve budget", "a")], "pile": {"categories": {}}})

    try:
        page.route("**/api/accounts", lambda route: route.fulfill(json=[]))
        page.route("**/api/today?*", today)
        page.goto(base_url)
        expect(page.locator("#load-error")).to_be_visible()
        expect(page.locator("#status")).to_have_text("Could not load your priorities")
        page.get_by_role("button", name="Retry", exact=True).click()
        expect(page.locator(".tier-action .card")).to_have_count(1)
        assert page.locator("#load-error").is_hidden()
        assert calls["today"] == 2
    finally:
        page.close()


def test_thread_error_retry_focus_cycle_and_restore(browser_env):
    base_url, browser = browser_env
    page = browser.new_page()
    calls = {"thread": 0}

    def thread(route):
        calls["thread"] += 1
        if calls["thread"] == 1:
            route.fulfill(status=503, json={"detail": "unavailable"})
        else:
            route.fulfill(json=thread_response())

    try:
        page.route("**/api/thread/a", thread)
        open_deck(page, base_url, [card("approval", "Approve budget", "a")])
        trigger = page.locator(".tier-action .card")
        trigger.click()
        dialog = page.get_by_role("dialog", name="Thread unavailable")
        expect(dialog).to_be_visible()
        expect(page.locator("#thread-error")).to_be_visible()
        assert page.locator("main").evaluate("el => el.inert")
        expect(dialog).to_have_attribute("aria-modal", "true")
        expect(page.locator("#close-drawer")).to_be_focused()
        page.keyboard.press("Tab")
        assert page.locator("#retry-thread").evaluate("el => el === document.activeElement")
        page.keyboard.press("Tab")
        expect(page.locator("#close-drawer")).to_be_focused()
        page.keyboard.press("Shift+Tab")
        assert page.locator("#retry-thread").evaluate("el => el === document.activeElement")
        page.locator("#retry-thread").click()
        expect(page.locator("#thread-summary")).to_have_text("Budget review requested.")
        assert page.locator("#thread-error").is_hidden()
        assert calls["thread"] == 2
        page.keyboard.press("Escape")
        expect(page.locator("#drawer")).to_have_attribute("aria-hidden", "true")
        assert not page.locator("main").evaluate("el => el.inert")
        assert trigger.evaluate("el => el === document.activeElement")
        trigger.click()
        page.locator("#close-drawer").click()
        assert trigger.evaluate("el => el === document.activeElement")
    finally:
        page.close()


@pytest.mark.parametrize("width", [1440, 768, 390])
def test_viewports_controls_and_drawer_no_overflow(browser_env, width):
    base_url, browser = browser_env
    page = browser.new_page(viewport={"width": width, "height": 844})
    try:
        page.route("**/api/thread/a", lambda route: route.fulfill(json=thread_response()))
        open_deck(page, base_url, [card("approval", "Approve budget", "a")])
        for selector in ("[data-mode=fused]", "[data-mode=split]", "#density"):
            assert page.locator(selector).bounding_box()["height"] >= 44
        for density in ("zen", "compact", "dense"):
            page.locator("#density").select_option(density)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator(".tier-action .card").click()
        expect(page.locator("#thread-summary")).to_have_text("Budget review requested.")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator("#close-drawer").click()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    finally:
        page.close()
