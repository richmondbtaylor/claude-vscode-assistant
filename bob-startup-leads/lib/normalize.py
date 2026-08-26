"""Normalization and validation shared across every pipeline stage."""
import re

import tldextract

LEGAL_SUFFIXES = {
    "llc", "l.l.c", "inc", "incorporated", "corp", "corporation", "co",
    "ltd", "limited", "pllc", "pc", "pa", "lp", "llp", "plc", "company",
}
_APOSTROPHE = re.compile(r"['’]")
_PUNCT = re.compile(r"[^a-z0-9&\s]")
_WS = re.compile(r"\s+")

# Social and directory hosts are never a company's own domain.
NON_COMPANY_HOSTS = {
    "facebook", "instagram", "linkedin", "twitter", "x", "yelp", "google",
    "youtube", "tiktok", "nextdoor", "bbb", "angi", "homeadvisor", "thumbtack",
    "indeed", "glassdoor", "mapquest", "yellowpages", "manta", "bizapedia",
}


def norm_name(s: str) -> str:
    """Lowercase, drop punctuation and legal suffixes, collapse whitespace."""
    if not s:
        return ""
    out = s.lower().replace("&", " and ")
    out = _APOSTROPHE.sub("", out)
    out = _PUNCT.sub(" ", out)
    tokens = [t for t in _WS.sub(" ", out).strip().split(" ") if t]
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def norm_phone(s: str | None) -> str | None:
    """Return a US number as E.164, or None if it is not a plausible US number."""
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    if digits[0] in "01" or digits[3] in "01":
        return None
    return "+1" + digits


def registrable_domain(url: str | None) -> str | None:
    """Registrable domain for a company site, or None for social and directory hosts."""
    if not url:
        return None
    candidate = url if "//" in url else "https://" + url
    ext = tldextract.extract(candidate)
    if not ext.domain or not ext.suffix:
        return None
    if ext.domain.lower() in NON_COMPANY_HOSTS:
        return None
    return f"{ext.domain}.{ext.suffix}".lower()


# A person name is two to four capitalized tokens, no company or CTA words.
# A capital letter is permitted immediately after a hyphen or apostrophe
# (O'Brien, Jean-Luc) but nowhere else inside the token.
_NAME_TOKEN = r"[A-Z][a-z]*(?:['’-][A-Za-z]+)*"
_NAME_RE = re.compile(rf"^{_NAME_TOKEN}(?:\s+(?:[A-Z]\.|{_NAME_TOKEN})){{1,3}}$")

NAME_STOPWORDS = {
    "contact", "team", "about", "our", "us", "free", "estimate", "learn",
    "more", "read", "get", "call", "now", "click", "here", "home", "services",
    "service", "quote", "schedule", "book", "menu", "view", "see", "start",
    "welcome", "meet", "the", "your", "we", "why", "how", "beach", "city",
    "county", "fort", "north", "south", "east", "west", "saint", "lake",
}


def is_valid_person_name(s: str) -> bool:
    """True only for something that really looks like a person's name."""
    if not s or not _NAME_RE.match(s.strip()):
        return False
    tokens = [t.lower().strip(".") for t in s.split()]
    if any(t in NAME_STOPWORDS for t in tokens):
        return False
    if any(t in LEGAL_SUFFIXES for t in tokens):
        return False
    return True
