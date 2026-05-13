"""Ensure __version__ and package metadata stay in sync."""
import importlib.metadata
import nmtcapp


def test_version_sync():
    assert nmtcapp.__version__ == importlib.metadata.version("nmtc-application-builder")
