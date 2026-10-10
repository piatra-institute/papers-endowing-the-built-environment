# Renewal finance model

All economic and engineering inputs are illustrative assumptions in config.json.
No external price series, estimated hazard rates or legal permissions are silently
supplied. All amounts are constant purchasing-power euros.

## Reproduce

From this directory, with Python 3.12 and uv:

```sh
uv sync --frozen
MPLCONFIGDIR=.cache/matplotlib uv run --frozen python model.py
```

The runner executes twelve unit tests before all model cases. Tests alone:

```sh
uv run --frozen python -m unittest discover -v
```

protocol.md documents cash timing, component state, the rolling continuation
calculation, equal capital, stresses, rescue policies and the separate commercial
steward example. output/results.json contains summaries; output/annual.json
contains the full cash and physical ledgers. The figure is generated from these
same ledgers.

Negative balances mean unpaid obligations, not an available credit facility.
An overdue component is a service-risk proxy, not a predicted physical outage.
The matched_reserve control must be identical to the financial treatment in
every scenario. Portfolio return assumptions do not establish investment authority.

## Workspace evidence record

From the collection root:

```sh
MPLCONFIGDIR=.cache/matplotlib python3 tooling/papers.py run endowing-the-built-environment --id renewal --cwd simulation --artifact simulation/output/results.json --artifact simulation/output/annual.json --artifact paper/figures/renewal.pdf --execution-result simulation/output/execution.json -- .venv/bin/python model.py
```

The recorded initial run used uv run --frozen and the same lock-created
environment. Re-running regenerates the figure; rebuild and visually inspect the
manuscript afterwards. Financial results are conditional scenario calculations,
not observed building performance or estimates of success probability.
