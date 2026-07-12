from __future__ import annotations


class PermissionHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def grant_android_permission(self, package: str, permission: str) -> None:
        self.driver.execute_script(
            "mobile: shell",
            {"command": "pm", "args": ["grant", package, permission]},
        )

    def revoke_android_permission(self, package: str, permission: str) -> None:
        self.driver.execute_script(
            "mobile: shell",
            {"command": "pm", "args": ["revoke", package, permission]},
        )

    def accept_alert_if_present(self) -> bool:
        try:
            self.driver.switch_to.alert.accept()
            return True
        except Exception:
            return False

    def dismiss_alert_if_present(self) -> bool:
        try:
            self.driver.switch_to.alert.dismiss()
            return True
        except Exception:
            return False
