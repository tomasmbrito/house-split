# House Split

A small web app for housemates to keep track of shared expenses: who paid what,
and who owes whom.

We are two housemates in Stockholm, and this is the app we use for our DevOps
project in DD2482 at KTH.

## How it works

- Add the housemates.
- Add an expense: what it was, the amount, who paid and who shares it
  (if nobody is ticked, it is shared by the whole house).
- The app shows each person's balance and a short list of payments that settles
  everything. Amounts are stored in cents to avoid rounding errors.

The settling logic is in `app/balances.py`: the person who owes the most pays the
person who is owed the most, and this repeats until everyone is at zero. With n
people this needs at most n - 1 payments.

## Run it locally

Needs Python 3.10 or newer.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
flask --app app.main run
```

Then open http://localhost:5000. The data is saved in `data/house.db`
(set `DB_PATH` to use another file).

## Tests and lint

```
pytest
ruff check .
```

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/` | the page |
| POST | `/people` | add a housemate |
| POST | `/expenses` | add an expense |
| POST | `/expenses/<id>/delete` | delete an expense |
| GET | `/api/summary` | everything as JSON |
| GET | `/health` | health check |
