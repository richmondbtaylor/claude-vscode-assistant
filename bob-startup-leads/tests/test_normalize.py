import pytest
from lib.normalize import norm_name, norm_phone, registrable_domain, is_valid_person_name


@pytest.mark.parametrize("raw,expected", [
    ("Sumter Coatings, Inc.", "sumter coatings"),
    ("AMERIPRO CONSTRUCTION SERVICES, INC.", "ameripro construction services"),
    ("Castillo Smart Services LLC", "castillo smart services"),
    ("Bob's Plumbing & Heating Co.", "bobs plumbing and heating"),
    ("  Acme   PLLC  ", "acme"),
])
def test_norm_name_strips_suffixes_and_punctuation(raw, expected):
    assert norm_name(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("(786) 395-8578", "+17863958578"),
    ("786-395-8578", "+17863958578"),
    ("+1 786 395 8578", "+17863958578"),
    ("17863958578", "+17863958578"),
    ("555", None),
    (None, None),
    ("", None),
])
def test_norm_phone_to_e164(raw, expected):
    assert norm_phone(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("https://www.acmeplumbing.com/contact", "acmeplumbing.com"),
    ("http://acmeplumbing.com", "acmeplumbing.com"),
    ("https://shop.acmeplumbing.co.uk/x", "acmeplumbing.co.uk"),
    ("acmeplumbing.com", "acmeplumbing.com"),
    ("https://facebook.com/acme", None),
    (None, None),
])
def test_registrable_domain(raw, expected):
    assert registrable_domain(raw) == expected


@pytest.mark.parametrize("raw", [
    "Maria Gonzalez", "John O'Brien", "Jean-Luc Picard", "Ann Lee",
])
def test_valid_person_names_accepted(raw):
    assert is_valid_person_name(raw) is True


@pytest.mark.parametrize("raw", [
    "Get Ah", "Fort Lauderdale", "Contact Us", "Our Team", "Free Estimate",
    "X", "", "ACME PLUMBING LLC", "Learn More", "Read More", "Miami Beach",
])
def test_junk_names_rejected(raw):
    assert is_valid_person_name(raw) is False
