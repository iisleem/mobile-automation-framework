from __future__ import annotations


class ClipboardHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def set_text(self, text: str) -> None:
        self.driver.set_clipboard_text(text)

    def get_text(self) -> str:
        return self.driver.get_clipboard_text()
