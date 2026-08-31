import json
from datetime import date
from pathlib import Path

from app.triage import build_pile, classify, extract_ask_deadline, make_cards, rank

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "emails.json").read_text())


def test_classifies_bill(): assert classify(FIXTURES[0]) == "bill_payment"
def test_classifies_approval(): assert classify(FIXTURES[1]) == "approval"
def test_classifies_newsletter(): assert classify(FIXTURES[2]) == "newsletter"
def test_classifies_notification(): assert classify(FIXTURES[3]) == "notification"


def test_extracts_payment_ask_and_deadline():
    ask, deadline = extract_ask_deadline(FIXTURES[0], date(2026, 9, 1))
    assert ask == "Pay ₹14,000 by Sep 15" and deadline.startswith("2026-09-15")


def test_extracts_approval_deadline():
    ask, deadline = extract_ask_deadline(FIXTURES[1], date(2026, 9, 1))
    assert ask == "Approve by Sep 10" and deadline.startswith("2026-09-10")


def test_bill_ranks_ahead_of_approval():
    assert [card["id"] for card in rank(make_cards(FIXTURES))][:2] == ["bill", "approval"]


def test_pile_groups_noise():
    pile = build_pile(FIXTURES)
    assert pile["newsletter"]["count"] == 1 and pile["notification"]["count"] == 1
