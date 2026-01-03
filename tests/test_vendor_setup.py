from __future__ import annotations

import importlib
import sys

import vendor_setup


def test_ensure_vendor_path_adds_directory(monkeypatch):
    vendor_dir = vendor_setup.ensure_vendor_path()

    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != vendor_dir])
    assert vendor_dir not in sys.path

    restored_dir = vendor_setup.ensure_vendor_path()
    assert restored_dir == vendor_dir
    assert sys.path[0] == vendor_dir


def test_bundled_tts_imports_edge_tts(monkeypatch):
    vendor_dir = vendor_setup.ensure_vendor_path()

    monkeypatch.delitem(sys.modules, "edge_tts", raising=False)
    monkeypatch.delitem(sys.modules, "bundled_tts", raising=False)
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != vendor_dir])

    reloaded_module = importlib.import_module("bundled_tts")
    assert reloaded_module.edge_tts is not None
    assert vendor_dir in sys.path
