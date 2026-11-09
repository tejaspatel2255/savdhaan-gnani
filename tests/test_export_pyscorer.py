"""Tests for export_pyscorer export and byte-identical integrity."""
from pathlib import Path
from scripts.export_pyscorer import export_pyscorer, verify_pyscorer_integrity

ROOT = Path(__file__).resolve().parent.parent


def test_pyscorer_copies_are_byte_identical():
    export_pyscorer()
    assert verify_pyscorer_integrity() is True, "pyscorer files must be byte-identical to source"
