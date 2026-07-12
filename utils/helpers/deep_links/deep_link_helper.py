from __future__ import annotations


class DeepLinkHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def open_android_deep_link(self, url: str, package: str) -> None:
        self.driver.execute_script("mobile: deepLink", {"url": url, "package": package})

    def open_universal_link(self, url: str) -> None:
        self.driver.get(url)
