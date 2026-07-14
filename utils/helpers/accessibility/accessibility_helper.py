from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class UnlabeledControl:
    tag: str
    resource_id: str | None
    class_name: str | None


def find_unlabeled_controls(page_source: str, platform: str = "android") -> list[UnlabeledControl]:
    root = ET.fromstring(page_source)
    platform_name = platform.lower()
    missing: list[UnlabeledControl] = []

    for node in root.iter():
        attrs = node.attrib
        if not _is_interactive(node.tag, attrs, platform_name):
            continue
        if _accessible_label(attrs, platform_name):
            continue
        missing.append(
            UnlabeledControl(
                tag=node.tag,
                resource_id=attrs.get("resource-id") or attrs.get("name"),
                class_name=attrs.get("class") or node.tag,
            )
        )
    return missing


def assert_no_unlabeled_controls(page_source: str, platform: str = "android") -> None:
    missing = find_unlabeled_controls(page_source, platform=platform)
    assert not missing, f"Found unlabeled interactive controls: {missing}"


def _is_interactive(tag: str, attrs: dict[str, str], platform: str) -> bool:
    normalized = f"{tag} {attrs.get('class', '')}".lower()
    if _is_layout_container(normalized) and attrs.get("clickable") != "true":
        return False
    if attrs.get("clickable") == "true":
        return True
    if (
        attrs.get("enabled") == "true"
        and attrs.get("focusable") == "true"
        and _looks_like_control(normalized, platform)
    ):
        return True
    if platform == "ios":
        return _looks_like_control(normalized, platform)
    return _looks_like_control(normalized, platform)


def _is_layout_container(normalized_class: str) -> bool:
    return any(
        token in normalized_class
        for token in (
            "framelayout",
            "linearlayout",
            "relativelayout",
            "scrollview",
            "viewgroup",
            "recyclerview",
            "collectionview",
            "table",
        )
    )


def _looks_like_control(normalized_class: str, platform: str) -> bool:
    if platform == "ios":
        return any(token in normalized_class for token in ("button", "textfield", "switch", "cell"))
    return any(token in normalized_class for token in ("button", "edittext", "checkbox", "switch", "imagebutton"))


def _accessible_label(attrs: dict[str, str], platform: str) -> str | None:
    if platform == "ios":
        return attrs.get("label") or attrs.get("name") or attrs.get("value")
    return attrs.get("content-desc") or attrs.get("text")
