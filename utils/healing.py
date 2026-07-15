from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import os
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET

from appium.webdriver.common.appiumby import AppiumBy
from automation_core.healing import (
    CandidateDescriptor,
    HealingConfig,
    HealingDecision,
    HealingResult,
    LocatorDescriptor,
    append_healing_event,
    evaluate_healing,
)


DEFAULT_AUDIT_PATH = Path("reports") / "healing" / "events.jsonl"
SUPPORTED_MODES = {"disabled", "suggest", "apply"}
WEB_CONTEXT_PREFIXES = ("WEBVIEW", "CHROMIUM")
ACTION_FIND = "find"


@dataclass(frozen=True)
class MobileHealingCandidate:
    descriptor: CandidateDescriptor
    by: str
    value: str


def runtime_healing_enabled(settings: dict[str, Any]) -> bool:
    return healing_config_from_settings(settings).mode != "disabled"


def healing_config_from_settings(settings: dict[str, Any]) -> HealingConfig:
    raw = settings.get("runtime_healing", {})
    if not isinstance(raw, dict):
        raw = {}
    mode = str(raw.get("mode", "disabled")).strip().lower()
    if mode not in SUPPORTED_MODES:
        mode = "disabled"
    return HealingConfig(
        mode=mode,
        min_score=float(raw.get("min_score", 0.78)),
        ambiguity_delta=float(raw.get("ambiguity_delta", 0.05)),
        max_candidates=int(raw.get("max_candidates", 10)),
        allowed_actions=_string_tuple(raw.get("allowed_actions", ())),
        allow_patterns=_string_tuple(raw.get("allow_patterns", ())),
        deny_patterns=_string_tuple(raw.get("deny_patterns", ())),
        signal_weights=_dict_value(raw.get("signal_weights", {})),
    )


def healing_audit_path(project_root: Path, settings: dict[str, Any]) -> Path:
    raw = settings.get("runtime_healing", {})
    configured = raw.get("audit_path", DEFAULT_AUDIT_PATH) if isinstance(raw, dict) else DEFAULT_AUDIT_PATH
    path = Path(configured)
    return path if path.is_absolute() else project_root / path


def current_test_id() -> str:
    raw = os.getenv("PYTEST_CURRENT_TEST", "")
    return raw.split(" (", 1)[0]


def original_descriptor(locator, action: str, metadata: dict[str, Any] | None = None) -> LocatorDescriptor:
    return LocatorDescriptor(
        strategy=str(locator.by),
        value=str(locator.value),
        action=action,
        label=str(locator.description),
        metadata=metadata or {},
    )


def discover_mobile_candidates(
    driver, original, *, action: str, max_candidates: int = 10
) -> list[MobileHealingCandidate]:
    context = _current_context(driver)
    source = _page_source(driver)
    if not source:
        return []
    if _is_web_context(context):
        return _discover_web_candidates(source, original, action=action, context=context, max_candidates=max_candidates)
    return _discover_native_candidates(source, original, action=action, context=context, max_candidates=max_candidates)


def evaluate_mobile_healing(
    *,
    driver,
    original,
    settings: dict[str, Any],
    project_root: Path,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> tuple[HealingResult, list[MobileHealingCandidate]]:
    config = healing_config_from_settings(settings)
    descriptor = original_descriptor(original, action, metadata)
    candidates = discover_mobile_candidates(driver, original, action=action, max_candidates=config.max_candidates)
    result = evaluate_healing(
        descriptor,
        [candidate.descriptor for candidate in candidates],
        config,
        action=action,
        test_id=current_test_id(),
        metadata={**(metadata or {}), "source": "mobile-appium"},
    )
    append_healing_event(healing_audit_path(project_root, settings), result)
    return result, candidates


def selected_mobile_candidate(
    result: HealingResult,
    candidates: list[MobileHealingCandidate],
) -> MobileHealingCandidate | None:
    if result.decision != HealingDecision.APPLIED or not result.selected:
        return None
    selected = result.selected.candidate
    for candidate in candidates:
        if candidate.descriptor.strategy == selected.strategy and candidate.descriptor.value == selected.value:
            return candidate
    return None


def mobile_locator_from_candidate(candidate: MobileHealingCandidate, description: str):
    from screens.base_screen import MobileLocator

    return MobileLocator(by=candidate.by, value=candidate.value, description=description)


def _discover_native_candidates(
    source: str,
    original,
    *,
    action: str,
    context: str,
    max_candidates: int,
) -> list[MobileHealingCandidate]:
    try:
        root = ET.fromstring(source)
    except ET.ParseError:
        return []
    candidates: list[MobileHealingCandidate] = []
    seen: dict[tuple[str, str], int] = {}
    nodes = list(root.iter())
    for node in nodes:
        attributes = {str(key): str(value) for key, value in node.attrib.items() if value not in ("", "false", "False")}
        tag = _node_type(node, attributes)
        label = _best_label(attributes)
        raw_candidates = _native_locator_values(attributes)
        for by, value, strategy, signal_name in raw_candidates:
            key = (by, value)
            seen[key] = seen.get(key, 0) + 1
            metadata = {
                "by": by,
                "context": context or "NATIVE_APP",
                "node_type": tag,
                "resource_id": attributes.get("resource-id", ""),
                "text": attributes.get("text", ""),
                "content_desc": attributes.get("content-desc", ""),
                "name": attributes.get("name", ""),
                "label": attributes.get("label", ""),
            }
            candidates.append(
                MobileHealingCandidate(
                    descriptor=CandidateDescriptor(
                        strategy=strategy,
                        value=value,
                        label=label or value,
                        source="native-page-source",
                        signals=_candidate_signals(original, value, label, tag, signal_name, context),
                        metadata=_without_empty(metadata),
                    ),
                    by=by,
                    value=value,
                )
            )
    unique_candidates = _mark_uniqueness(candidates, seen)
    return _dedupe_candidates(unique_candidates)[:max_candidates]


def _discover_web_candidates(
    source: str,
    original,
    *,
    action: str,
    context: str,
    max_candidates: int,
) -> list[MobileHealingCandidate]:
    try:
        root = ET.fromstring(source)
    except ET.ParseError:
        return []
    candidates: list[MobileHealingCandidate] = []
    seen: dict[tuple[str, str], int] = {}
    for node in root.iter():
        attributes = {str(key): str(value) for key, value in node.attrib.items() if value}
        tag = _node_type(node, attributes)
        label = _best_label(attributes)
        raw_candidates = _web_locator_values(attributes)
        for by, value, strategy, signal_name in raw_candidates:
            key = (by, value)
            seen[key] = seen.get(key, 0) + 1
            candidates.append(
                MobileHealingCandidate(
                    descriptor=CandidateDescriptor(
                        strategy=strategy,
                        value=value,
                        label=label or value,
                        source="webview-page-source",
                        signals=_candidate_signals(original, value, label, tag, signal_name, context),
                        metadata=_without_empty({"by": by, "context": context, "node_type": tag}),
                    ),
                    by=by,
                    value=value,
                )
            )
    return _dedupe_candidates(_mark_uniqueness(candidates, seen))[:max_candidates]


def _native_locator_values(attributes: dict[str, str]) -> list[tuple[str, str, str, str]]:
    values: list[tuple[str, str, str, str]] = []
    for key in ("content-desc", "name", "label"):
        if attributes.get(key):
            values.append((AppiumBy.ACCESSIBILITY_ID, attributes[key], AppiumBy.ACCESSIBILITY_ID, "accessibility"))
    resource_id = attributes.get("resource-id")
    if resource_id:
        values.append((AppiumBy.ID, resource_id, AppiumBy.ID, "stable_id"))
    text = attributes.get("text") or attributes.get("value")
    if text:
        escaped = text.replace('"', '\\"')
        values.append((AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{escaped}")', "text", "text"))
    return values


def _web_locator_values(attributes: dict[str, str]) -> list[tuple[str, str, str, str]]:
    values: list[tuple[str, str, str, str]] = []
    element_id = attributes.get("id")
    if element_id:
        values.append((AppiumBy.CSS_SELECTOR, f"#{_css_escape(element_id)}", "css selector", "stable_id"))
    for key in ("name", "aria-label"):
        if attributes.get(key):
            values.append((AppiumBy.CSS_SELECTOR, f'[{key}="{attributes[key]}"]', "css selector", "accessibility"))
    return values


def _candidate_signals(
    original, value: str, label: str, node_type: str, signal_name: str, context: str
) -> dict[str, float]:
    original_text = f"{original.value} {original.description}".strip()
    comparable = f"{value} {label}".strip()
    similarity = _similarity(original_text, comparable)
    signals = {
        "score": max(similarity, 0.0),
        signal_name: 1.0,
        "context": 1.0 if context else 0.0,
        "type": _similarity(original.description, node_type),
    }
    if value == original.value:
        signals["exact"] = 1.0
    return signals


def _mark_uniqueness(
    candidates: list[MobileHealingCandidate],
    seen: dict[tuple[str, str], int],
) -> list[MobileHealingCandidate]:
    marked: list[MobileHealingCandidate] = []
    for candidate in candidates:
        unique = seen.get((candidate.by, candidate.value), 0) == 1
        descriptor = CandidateDescriptor(
            strategy=candidate.descriptor.strategy,
            value=candidate.descriptor.value,
            category=candidate.descriptor.category,
            label=candidate.descriptor.label,
            source=candidate.descriptor.source,
            signals=candidate.descriptor.signals,
            metadata=candidate.descriptor.metadata,
            unique=unique,
        )
        marked.append(MobileHealingCandidate(descriptor=descriptor, by=candidate.by, value=candidate.value))
    return marked


def _dedupe_candidates(candidates: list[MobileHealingCandidate]) -> list[MobileHealingCandidate]:
    deduped: list[MobileHealingCandidate] = []
    seen: set[tuple[str, str]] = set()
    for candidate in sorted(candidates, key=lambda item: item.descriptor.signals.get("score", 0), reverse=True):
        key = (candidate.by, candidate.value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _current_context(driver) -> str:
    try:
        return str(getattr(driver, "current_context", "") or "")
    except Exception:
        return ""


def _page_source(driver) -> str:
    try:
        return str(driver.page_source or "")
    except Exception:
        return ""


def _is_web_context(context: str) -> bool:
    normalized = context.upper()
    return any(normalized.startswith(prefix) for prefix in WEB_CONTEXT_PREFIXES)


def _node_type(node: ET.Element, attributes: dict[str, str]) -> str:
    return attributes.get("class") or attributes.get("type") or node.tag


def _best_label(attributes: dict[str, str]) -> str:
    for key in ("content-desc", "label", "name", "text", "value", "resource-id", "id"):
        if attributes.get(key):
            return attributes[key]
    return ""


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _css_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("#", "\\#")


def _string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value if str(item))
    return ()


def _dict_value(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    return {str(key): float(item) for key, item in value.items()}


def _without_empty(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value not in ("", None)}
