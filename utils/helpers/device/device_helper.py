from __future__ import annotations


class DeviceHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def rotate_portrait(self) -> None:
        self.driver.orientation = "PORTRAIT"

    def rotate_landscape(self) -> None:
        self.driver.orientation = "LANDSCAPE"

    def background_app(self, seconds: int = 2) -> None:
        self.driver.background_app(seconds)

    def lock(self, seconds: int | None = None) -> None:
        if seconds is None:
            self.driver.lock()
        else:
            self.driver.lock(seconds)

    def unlock(self) -> None:
        self.driver.unlock()

    def battery_info(self) -> dict:
        return self.driver.execute_script("mobile: batteryInfo")

    def current_activity(self) -> str | None:
        return getattr(self.driver, "current_activity", None)

    def current_package(self) -> str | None:
        return getattr(self.driver, "current_package", None)
