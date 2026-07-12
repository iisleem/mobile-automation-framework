from __future__ import annotations

from base64 import b64decode
from pathlib import Path
import re
from typing import Any


def safe_artifact_name(nodeid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid).strip("_")


def attach_file(path: Path, name: str, attachment_type: Any = None, extension: str | None = None) -> None:
    try:
        import allure

        allure.attach.file(
            str(path),
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )
    except Exception:
        return


def capture_failure_artifacts(
    driver,
    project_root: Path,
    config: dict,
    test_name: str,
) -> list[Path]:
    artifacts: list[Path] = []
    artifacts.extend(_capture_screenshot(driver, project_root, config, test_name))
    artifacts.extend(_dump_page_source(driver, project_root, config, test_name))
    artifacts.extend(_capture_driver_logs(driver, project_root, config, test_name))
    return artifacts


def save_screen_recording(
    encoded_recording: str | None,
    project_root: Path,
    config: dict,
    test_name: str,
) -> Path | None:
    if not encoded_recording:
        return None

    extension = config.get("recording", {}).get("video_type", "mp4")
    recordings_dir = project_root / config["artifacts"]["recordings_dir"]
    recordings_dir.mkdir(parents=True, exist_ok=True)
    recording_path = recordings_dir / f"{test_name}.{extension}"
    recording_path.write_bytes(b64decode(encoded_recording))
    attach_file(recording_path, "failure screen recording", "video/mp4", extension)
    return recording_path


def _capture_screenshot(driver, project_root: Path, config: dict, test_name: str) -> list[Path]:
    screenshots_dir = project_root / config["artifacts"]["screenshots_dir"]
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshots_dir / f"{test_name}.png"
    try:
        driver.get_screenshot_as_file(str(screenshot_path))
        attach_file(screenshot_path, "failure screenshot", _allure_attachment_type("PNG"))
        return [screenshot_path]
    except Exception:
        return []


def _dump_page_source(driver, project_root: Path, config: dict, test_name: str) -> list[Path]:
    source_dir = project_root / config["artifacts"]["source_dumps_dir"]
    source_dir.mkdir(parents=True, exist_ok=True)
    source_path = source_dir / f"{test_name}.xml"
    try:
        source_path.write_text(driver.page_source, encoding="utf-8")
        attach_file(source_path, "failure page source", _allure_attachment_type("XML"), "xml")
        return [source_path]
    except Exception:
        return []


def _capture_driver_logs(driver, project_root: Path, config: dict, test_name: str) -> list[Path]:
    logs_dir = project_root / config["artifacts"]["logs_dir"]
    logs_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []
    try:
        available_logs = set(driver.log_types)
    except Exception:
        available_logs = set()

    for log_type in ("logcat", "syslog", "server", "driver", "client"):
        if log_type not in available_logs:
            continue
        log_path = logs_dir / f"{test_name}-{log_type}.log"
        try:
            entries = driver.get_log(log_type)
            log_path.write_text(_format_log_entries(entries), encoding="utf-8")
            attach_file(log_path, f"failure {log_type} log", _allure_attachment_type("TEXT"), "log")
            artifacts.append(log_path)
        except Exception:
            continue
    return artifacts


def _format_log_entries(entries: list[dict]) -> str:
    lines = []
    for entry in entries:
        timestamp = entry.get("timestamp", "")
        level = entry.get("level", "")
        message = entry.get("message", "")
        lines.append(f"{timestamp} {level} {message}".strip())
    return "\n".join(lines)


def _allure_attachment_type(name: str):
    try:
        import allure

        return getattr(allure.attachment_type, name)
    except Exception:
        return None
