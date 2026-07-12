from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import quote

import pytest

from screens.mobile_web import MobileBrowserScreen


pytestmark = [pytest.mark.mobile_web, pytest.mark.smoke]


def test_mobile_browser_runs_self_contained_example(mobile_driver, mobile_web_example_url):
    browser = MobileBrowserScreen(mobile_driver)
    browser.open_url(mobile_web_example_url)
    browser.assert_title_contains("Appium Mobile Web Example")
    browser.enter_name("Mobile QA")
    browser.submit_greeting()
    browser.assert_status_contains("Hello, Mobile QA")


@pytest.fixture
def mobile_web_example_url(mobile_driver, tmp_path_factory):
    platform_name = str(mobile_driver.capabilities.get("platformName", "")).lower()
    if platform_name == "android":
        yield "data:text/html;charset=utf-8," + quote(_example_page_html())
        return

    root = tmp_path_factory.mktemp("mobile-web-example")
    (root / "index.html").write_text(_example_page_html(), encoding="utf-8")

    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://127.0.0.1:{server.server_port}/index.html"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _example_page_html() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Appium Mobile Web Example</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 24px; }
      label, input, button, #status { display: block; margin-top: 16px; font-size: 18px; }
      input, button { min-height: 44px; width: 100%; box-sizing: border-box; }
    </style>
  </head>
  <body>
    <h1>Appium Mobile Web Example</h1>
    <label for="name">Name</label>
    <input id="name" autocomplete="off">
    <button id="greet" type="button">Greet</button>
    <p id="status" role="status">Waiting</p>
    <script>
      document.getElementById("greet").addEventListener("click", function () {
        const name = document.getElementById("name").value || "mobile tester";
        document.getElementById("status").textContent = `Hello, ${name}`;
      });
    </script>
  </body>
</html>"""
