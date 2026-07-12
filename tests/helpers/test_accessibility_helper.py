from __future__ import annotations

import pytest

from utils.helpers.accessibility import assert_no_unlabeled_controls, find_unlabeled_controls


pytestmark = pytest.mark.helpers


def test_android_accessibility_detects_unlabeled_clickable_controls():
    source = """<hierarchy>
      <node class="android.widget.Button" clickable="true" enabled="true" text="" content-desc="" resource-id="save"/>
    </hierarchy>"""
    missing = find_unlabeled_controls(source, platform="android")
    assert len(missing) == 1
    assert missing[0].resource_id == "save"


def test_android_accessibility_accepts_labeled_controls():
    source = """<hierarchy>
      <node class="android.widget.Button" clickable="true" enabled="true" text="Save" content-desc="" resource-id="save"/>
    </hierarchy>"""
    assert_no_unlabeled_controls(source, platform="android")


def test_accessibility_assertion_fails_with_details():
    source = """<AppiumAUT>
      <XCUIElementTypeButton enabled="true" label="" name="" value=""/>
    </AppiumAUT>"""
    with pytest.raises(AssertionError):
        assert_no_unlabeled_controls(source, platform="ios")
