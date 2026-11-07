"""Tests for blind_status pure helper."""
from scripts.blind_status import blind_status


def test_blind_status_not_scored():
    assert blind_status({}) == "not_scored"
    assert blind_status({"splits": {}}) == "not_scored"
    assert blind_status({"splits": {"dev": {}}}) == "not_scored"


def test_blind_status_placeholder():
    assert blind_status({"splits": {"blind": {"n": 2}}}) == "placeholder"
    assert blind_status({"splits": {"blind": {"ceiling": {"n": 2}}}}) == "placeholder"
    assert blind_status({"splits": {"blind": {"n": 9}}}) == "placeholder"


def test_blind_status_scored():
    assert blind_status({"splits": {"blind": {"n": 10}}}) == "scored"
    assert blind_status({"splits": {"blind": {"n": 12}}}) == "scored"
    assert blind_status({"splits": {"blind": {"ceiling": {"n": 12}}}}) == "scored"
