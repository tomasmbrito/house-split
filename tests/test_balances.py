import pytest

from app.balances import compute_balances, settle, split_amount


def test_split_even():
    assert split_amount(900, 3) == [300, 300, 300]


def test_split_leftover_cents_go_to_first_people():
    assert split_amount(1000, 3) == [334, 333, 333]
    assert sum(split_amount(1001, 4)) == 1001


def test_split_needs_someone():
    with pytest.raises(ValueError):
        split_amount(100, 0)


def test_one_person_pays_for_everyone():
    people = ["tomas", "henrique", "ana"]
    expenses = [{"amount": 3000, "paid_by": "tomas", "shared_by": people}]
    assert compute_balances(people, expenses) == {"tomas": 2000, "henrique": -1000, "ana": -1000}


def test_expense_only_shared_by_some():
    people = ["tomas", "henrique", "ana"]
    expenses = [{"amount": 1000, "paid_by": "ana", "shared_by": ["ana", "henrique"]}]
    assert compute_balances(people, expenses) == {"tomas": 0, "henrique": -500, "ana": 500}


def test_balances_always_add_up_to_zero():
    people = ["a", "b", "c"]
    expenses = [
        {"amount": 1000, "paid_by": "a", "shared_by": people},
        {"amount": 777, "paid_by": "b", "shared_by": ["b", "c"]},
        {"amount": 1, "paid_by": "c", "shared_by": people},
    ]
    assert sum(compute_balances(people, expenses).values()) == 0


def test_settle_simple():
    assert settle({"tomas": 2000, "henrique": -1000, "ana": -1000}) in (
        [("henrique", "tomas", 1000), ("ana", "tomas", 1000)],
        [("ana", "tomas", 1000), ("henrique", "tomas", 1000)],
    )


def test_settle_nothing_to_do():
    assert settle({"tomas": 0, "henrique": 0}) == []


def test_settle_leaves_everyone_at_zero():
    balances = {"a": 1500, "b": -700, "c": -300, "d": -500}
    left = dict(balances)
    for debtor, creditor, amount in settle(balances):
        left[debtor] += amount
        left[creditor] -= amount
    assert all(v == 0 for v in left.values())


def test_settle_uses_at_most_n_minus_one_payments():
    balances = {"a": 400, "b": 300, "c": -200, "d": -250, "e": -250}
    assert len(settle(balances)) <= len(balances) - 1
