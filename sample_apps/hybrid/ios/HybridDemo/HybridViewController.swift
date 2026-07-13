import UIKit
import WebKit

final class HybridViewController: UIViewController {
    private let webView = WKWebView(frame: .zero, configuration: WKWebViewConfiguration())

    override func loadView() {
        webView.accessibilityIdentifier = "hybridWebView"
        webView.isInspectable = true
        view = webView
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        webView.loadHTMLString(Self.html, baseURL: URL(string: "https://hybrid.demo.local/"))
    }

    private static let html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Hybrid Demo</title>
        <style>
          body { font-family: -apple-system, sans-serif; margin: 24px; background: #f7f8fb; color: #172033; }
          label, input, button, #status { display: block; margin-top: 16px; font-size: 18px; }
          input, button { min-height: 44px; width: 100%; box-sizing: border-box; }
          button { background: #1457a8; color: white; border: 0; border-radius: 6px; }
        </style>
      </head>
      <body>
        <h1>Hybrid Demo</h1>
        <p id="mode">Running inside a native WKWebView</p>
        <label for="name">Name</label>
        <input id="name" autocomplete="off">
        <button id="greet" type="button">Greet</button>
        <p id="status" role="status">Waiting</p>
        <script>
          document.getElementById("greet").addEventListener("click", function () {
            const name = document.getElementById("name").value || "hybrid tester";
            document.getElementById("status").textContent = `Hello, ${name}`;
          });
        </script>
      </body>
    </html>
    """
}
