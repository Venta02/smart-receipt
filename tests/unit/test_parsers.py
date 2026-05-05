"""Unit tests for amount and date parsers."""

from datetime import date

from src.services.extraction.parsers import parse_amount, parse_date


def test_parse_amount_us_format():
    assert parse_amount("50,000.50") == 50000.50


def test_parse_amount_indonesian_thousand():
    assert parse_amount("50.000") == 50000.0


def test_parse_amount_indonesian_decimal():
    assert parse_amount("50.000,50") == 50000.50


def test_parse_amount_with_currency():
    assert parse_amount("Rp 13,875") == 13875.0


def test_parse_amount_invalid():
    assert parse_amount("") is None
    assert parse_amount("abc") is None


def test_parse_date_iso():
    assert parse_date("2026-05-04") == date(2026, 5, 4)


def test_parse_date_indonesian():
    assert parse_date("04/05/2026") == date(2026, 5, 4)


def test_parse_date_indonesian_month():
    result = parse_date("4 Mei 2026")
    assert result == date(2026, 5, 4)


def test_parse_date_invalid():
    assert parse_date("not a date") is None
    assert parse_date("") is None
