from __future__ import annotations

import argparse

import pytest

import framework
from scripts import run_device_matrix


pytestmark = pytest.mark.helpers


def _run_args(**overrides) -> argparse.Namespace:
    values = {
        "profile": None,
        "appium_server": None,
        "device_name": None,
        "platform_version": None,
        "udid": None,
        "app": None,
        "no_reset": False,
        "full_reset": False,
        "parallel": None,
        "reruns": None,
        "reruns_delay": None,
        "no_open_report": False,
        "no_generate_report": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_framework_cli_applies_default_test_retries_from_settings(monkeypatch):
    monkeypatch.setattr(
        framework,
        "_retry_setting",
        lambda name, default: {"default": 2, "delay_seconds": 0.5}.get(name, default),
    )
    command: list[str] = []

    framework._append_common_pytest_options(
        command,
        _run_args(),
        marker_expression=None,
        extra_pytest_args=[],
    )

    assert command == ["--reruns", "2", "--reruns-delay", "0.5"]


def test_framework_cli_keeps_explicit_rerun_options(monkeypatch):
    monkeypatch.setattr(
        framework,
        "_retry_setting",
        lambda name, default: {"default": 2, "delay_seconds": 0.5}.get(name, default),
    )
    command: list[str] = []

    framework._append_common_pytest_options(
        command,
        _run_args(reruns="4", reruns_delay="1.5"),
        marker_expression=None,
        extra_pytest_args=[],
    )

    assert command == ["--reruns", "4", "--reruns-delay", "1.5"]


def test_framework_cli_can_skip_profile_append_for_single_profile_runs(monkeypatch):
    monkeypatch.setattr(framework, "_retry_setting", lambda name, default: 0)
    command = ["--profile", "android_the_app"]

    framework._append_common_pytest_options(
        command,
        _run_args(profile="android_the_app"),
        marker_expression=None,
        extra_pytest_args=[],
        include_profile=False,
    )

    assert command == ["--profile", "android_the_app"]


def test_device_matrix_applies_default_test_retries_from_settings(monkeypatch, tmp_path):
    captured_commands: list[list[str]] = []

    class Completed:
        returncode = 0

    def fake_run(command, **kwargs):
        captured_commands.append(command)
        return Completed()

    args = argparse.Namespace(
        env="qa",
        appium_server=None,
        device_name=None,
        platform_version=None,
        udid=None,
        app=None,
        no_reset=False,
        full_reset=False,
        markers=None,
        parallel_workers=None,
        reruns=None,
        reruns_delay=None,
    )
    monkeypatch.setattr(
        run_device_matrix,
        "_retry_setting",
        lambda name, default: {"default": 2, "delay_seconds": 0.5}.get(name, default),
    )
    monkeypatch.setattr(run_device_matrix.subprocess, "run", fake_run)

    result = run_device_matrix._run_pytest_for_profile(
        "android_the_app",
        args,
        [],
        tmp_path / "results",
        tmp_path / "logs" / "android_the_app.log",
    )

    command = captured_commands[0]
    assert result["exit_code"] == 0
    assert command[command.index("--reruns") + 1] == "2"
    assert command[command.index("--reruns-delay") + 1] == "0.5"
