from __future__ import annotations


class AppHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def install_app(self, app_path: str) -> None:
        self.driver.install_app(app_path)

    def remove_app(self, app_id: str) -> None:
        self.driver.remove_app(app_id)

    def is_installed(self, app_id: str) -> bool:
        return self.driver.is_app_installed(app_id)

    def activate(self, app_id: str) -> None:
        self.driver.activate_app(app_id)

    def terminate(self, app_id: str) -> bool:
        return bool(self.driver.terminate_app(app_id))

    def state(self, app_id: str):
        return self.driver.query_app_state(app_id)
