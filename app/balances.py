"""Who owes what in the house.

Amounts are always in cents (integers), so we never get rounding
problems like 0.1 + 0.2 != 0.3.
"""


def split_amount(amount, n):
    """Split amount (cents) into n shares that add up exactly to amount.

    The leftover cents go to the first people, e.g. 1000 / 3 -> [334, 333, 333].
    """
    if n <= 0:
        raise ValueError("need at least one person to split with")
    base, rest = divmod(amount, n)
    return [base + 1 if i < rest else base for i in range(n)]


def compute_balances(people, expenses):
    """Return {person: balance}. Positive means the house owes them money,
    negative means they owe money to the house.

    expenses is a list of dicts with "amount", "paid_by" and "shared_by"
    (the list of people that split this expense).
    """
    balances = {p: 0 for p in people}
    for e in expenses:
        balances[e["paid_by"]] += e["amount"]
        shares = split_amount(e["amount"], len(e["shared_by"]))
        for person, share in zip(e["shared_by"], shares):
            balances[person] -= share
    return balances


def settle(balances):
    """Turn balances into a short list of payments (from, to, amount).

    Greedy: the person who owes the most pays the person who is owed the
    most, as much as possible, and we repeat. With n people this gives at
    most n - 1 payments. It is not always the smallest possible number,
    but finding that is a much harder problem and this is good enough
    for a house.
    """
    debtors = sorted((-b, p) for p, b in balances.items() if b < 0)
    creditors = sorted((b, p) for p, b in balances.items() if b > 0)
    payments = []
    while debtors and creditors:
        owes, debtor = debtors.pop()
        owed, creditor = creditors.pop()
        amount = min(owes, owed)
        payments.append((debtor, creditor, amount))
        if owes > amount:
            debtors.append((owes - amount, debtor))
            debtors.sort()
        if owed > amount:
            creditors.append((owed - amount, creditor))
            creditors.sort()
    return payments
