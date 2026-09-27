"""Test fixtures for mqtt-mediaplayer"""
import os
import sys

import pytest

# Make sure the project root (which contains custom_components/) is importable.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _purge_custom_components():
    for name in [n for n in sys.modules if n == "custom_components" or n.startswith("custom_components.")]:
        del sys.modules[name]


@pytest.fixture(autouse=True)
def _load_our_custom_components(enable_custom_integrations):
    """Drop phacc's cached custom_components so ours is imported."""
    _purge_custom_components()
    yield


@pytest.fixture(autouse=True)
def expected_lingering_timers():
    """The mocked MQTT component leaves its periodic misc timer running."""
    return True
