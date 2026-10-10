"""Auditable real-cash renewal model; assumptions are not local underwriting."""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
import platform
import sys
import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config.json").read_text())
SCENARIOS = ("baseline", "return_before", "return_after", "rental_failure",
             "cost_growth", "fees", "approval", "combined")
SCHEMES = ("reserve", "rental", "financial", "matched_reserve")


def launch(c=CONFIG, annual_required=120000):
    n, p, d, f = c["units"], c["unit_sale_price"], c["development_cost"], c["opening_cash"]
    retained = c["retained_units"]
    q, profit = c["annual_net_rent_per_unit"], c["developer_cash_return"]
    if min(n, p, q) <= 0 or min(d, f, profit, annual_required) < 0:
        raise ValueError("Invalid launch assumptions")
    n_min = math.ceil(annual_required/q)
    n_max = min(n, math.floor((n*p-d-profit-f)/p))
    return {"sales": (n-retained)*p, "opening_cash": f,
            "retained_opportunity_value": retained*p, "dedicated_capital": retained*p+f,
            "developer_cash_surplus": (n-retained)*p-d-f,
            "net_rent": retained*q, "n_min": n_min, "n_max": n_max,
            "feasible": n_min <= n_max, "required_annual": annual_required,
            "total_surplus": n*p-d}


def parameters(c, scheme, scenario, year):
    growth = .03 if scenario in ("cost_growth", "combined") else c["real_construction_growth"]
    rate = c["real_financial_return"] if scheme in ("financial", "matched_reserve") else c["real_cash_return"]
    if scheme in ("financial", "matched_reserve") and (
        year == 19 and scenario in ("return_before", "combined")
        or year == 21 and scenario == "return_after"
    ):
        rate = -.35
    rent_factor = .5 if scenario in ("rental_failure", "combined") and 12 <= year <= 14 else 1
    fee = c["annual_steward_fee"] * (2 if scenario in ("fees", "combined") else 1)
    delay = 2 if scenario in ("approval", "combined") else 0
    return growth, rate, rent_factor, fee, delay


def continuation(c, scheme, scenario, year, ages, units):
    """Minimum current cash for a timely 20-year plan; future shocks unknown."""
    ages = list(ages)
    balance_pv, required, discount = 0., 0., 1.
    for offset in range(1, c["planning_horizon"]+1):
        t = year+offset
        growth, _, _, fee, _ = parameters(c, scheme, scenario, -1)
        rate = c["real_financial_return"] if scheme in ("financial", "matched_reserve") else c["real_cash_return"]
        discount *= 1+rate
        cost = c["routine_cost"]*(1+growth)**t+fee
        for i, comp in enumerate(c["components"]):
            ages[i] += 1
            if ages[i] >= comp["life"]:
                cost += comp["cost"]*(1+growth)**t
                ages[i] = 0
        income = units*c["annual_net_rent_per_unit"] if scheme == "rental" else 0
        balance_pv += (income-cost)/discount
        required = max(required, -balance_pv)
    return required


def simulate(c=CONFIG, scheme="reserve", scenario="baseline", calls=False, sales=False, extra_cash=0):
    if scheme not in SCHEMES or scenario not in SCENARIOS or extra_cash < 0:
        raise ValueError("Unknown treatment or invalid funding")
    cash = c["opening_cash"]+extra_cash
    units = c["retained_units"] if scheme == "rental" else 0
    if scheme != "rental":
        cash += c["retained_units"]*c["unit_sale_price"]
    initial = cash+units*c["unit_sale_price"]
    ages = [0]*len(c["components"])
    first_due = [None]*len(ages)
    rows, events = [], []
    for year in range(1, c["years"]+1):
        growth, rate, rent_factor, fee, delay = parameters(c, scheme, scenario, year)
        opening = cash
        returns = max(cash, 0)*rate
        rent = units*c["annual_net_rent_per_unit"]*rent_factor
        routine = c["routine_cost"]*(1+growth)**year
        cash += returns+rent-routine-fee
        call, proceeds, spent = 0., 0., 0.
        for i, comp in enumerate(c["components"]):
            ages[i] += 1
            if year == 12 and scenario in ("rental_failure", "combined") and comp["name"] == "roof":
                ages[i] = max(ages[i], comp["life"])
            if ages[i] >= comp["life"] and first_due[i] is None:
                first_due[i] = year

        def fund(amount):
            nonlocal cash, units, call, proceeds
            shortage = max(0., amount-cash)
            if shortage > 1e-7 and sales and units:
                sold = min(units, math.ceil(shortage/c["unit_sale_price"]))
                units -= sold
                received = sold*c["unit_sale_price"]
                proceeds += received
                cash += received
            if cash < amount and calls:
                injection = amount-cash
                call += injection
                cash += injection

        fund(0.)
        for i, comp in enumerate(c["components"]):
            if first_due[i] is None or year < first_due[i]+delay:
                continue
            cost = comp["cost"]*(1+growth)**year
            fund(cost)
            if cash+1e-7 >= cost:
                cash -= cost
                spent += cost
                events.append({"year": year, "component": comp["name"], "due": first_due[i], "cost": cost})
                ages[i], first_due[i] = 0, None
        overdue = sum(x is not None for x in first_due)
        requirement = continuation(c, scheme, scenario, year, ages, units)
        residual = cash-(opening+returns+rent-routine-fee-spent+call+proceeds)
        if abs(residual) > 1e-6:
            raise AssertionError("Cash reconciliation failed")
        rows.append({"year": year, "opening_cash": opening, "returns": returns,
                     "rent": rent, "routine": routine, "fee": fee, "renewal_spend": spent,
                     "owner_call": call, "sale_proceeds": proceeds, "cash": cash,
                     "rental_units": units, "overdue_components": overdue,
                     "ages": list(ages), "continuation_cash_required": requirement,
                     "planning_gap": max(0., requirement-cash), "accounting_residual": residual})
    terminal = rows[-1]
    summary = {
        "initial_dedicated_capital": initial, "terminal_cash": terminal["cash"],
        "terminal_property_value": units*c["unit_sale_price"],
        "terminal_continuation_required": terminal["continuation_cash_required"],
        "terminal_liquid_gap": terminal["planning_gap"],
        "overdue_component_years": sum(r["overdue_components"] for r in rows),
        "years_with_overdue_work": sum(r["overdue_components"] > 0 for r in rows),
        "maximum_cash_arrears": max(0., -min(r["cash"] for r in rows)),
        "owner_calls": sum(r["owner_call"] for r in rows),
        "owner_calls_pv": sum(r["owner_call"]/(1+c["real_cash_return"])**r["year"] for r in rows),
        "units_sold": c["retained_units"]-units if scheme == "rental" else 0,
        "fees_paid_or_accrued": sum(r["fee"] for r in rows),
        "renewal_spend": sum(r["renewal_spend"] for r in rows),
        "first_overdue_year": next((r["year"] for r in rows if r["overdue_components"]), None),
    }
    return {"summary": summary, "annual": rows, "interventions": events}


def minimum_extra_cash(c, scheme):
    def funded(extra):
        s = simulate(c, scheme, extra_cash=extra)["summary"]
        return s["overdue_component_years"] == 0 and s["terminal_liquid_gap"] <= .01 and s["maximum_cash_arrears"] == 0
    if funded(0):
        return 0.
    low, high = 0., 1000000.
    while not funded(high):
        high *= 2
        if high > 1e9:
            raise ValueError("Funding search did not bracket a solution")
    for _ in range(32):
        mid = (low+high)/2
        if funded(mid): high = mid
        else: low = mid
    return high


def main():
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py")
    test_result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not test_result.wasSuccessful():
        raise SystemExit(1)
    cases, annual = {}, {}
    for scenario in SCENARIOS:
        cases[scenario], annual[scenario] = {}, {}
        for scheme in SCHEMES:
            result = simulate(scheme=scheme, scenario=scenario)
            cases[scenario][scheme] = result["summary"]
            annual[scenario][scheme] = result
    policies = {key: simulate(scheme="rental", scenario="combined", **options)
                for key, options in {"calls": {"calls": True}, "sales": {"sales": True}}.items()}
    sensitivity = {}
    for rate in (0., .02, .04):
        c = copy.deepcopy(CONFIG)
        c["real_financial_return"] = rate
        sensitivity[str(rate)] = simulate(c, "financial")["summary"]
    minimum = {scheme: minimum_extra_cash(CONFIG, scheme) for scheme in SCHEMES[:3]}
    business = CONFIG["steward_business"]
    margin = business["annual_fee"]-business["direct_cost_per_client"]
    results = {"launch": launch(), "launch_150k": launch(annual_required=150000),
               "scenarios": cases, "policies": {k: v["summary"] for k,v in policies.items()},
               "return_sensitivity": sensitivity, "minimum_additional_cash": minimum,
               "steward": {"contribution_per_client": margin,
                           "break_even_clients": math.ceil(business["central_cost"]/margin)},
               "interpretation": "Conditional illustrations; no estimated probabilities or market calibration"}
    output = HERE / "output"
    output.mkdir(exist_ok=True)
    (output / "results.json").write_text(json.dumps(results, indent=2)+"\n")
    (output / "annual.json").write_text(json.dumps({"cases": annual, "policies": policies}, indent=2)+"\n")
    figures = HERE.parent / "paper/figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 150})
    fig, axes = plt.subplots(2, 1, figsize=(6.6, 5.0), sharex=True)
    for scheme, label, color in zip(SCHEMES[:3], ("Liquid reserve (2%)", "Rental endowment", "Financial fund (4%)"),
                                    ("#687942", "#b56638", "#1c5268")):
        rows = annual["baseline"][scheme]["annual"]
        axes[0].plot([r["year"] for r in rows], [r["cash"]/1e6 for r in rows], label=label, color=color)
        axes[1].plot([r["year"] for r in rows], [r["overdue_components"] for r in rows], color=color)
    axes[0].set_ylabel("Liquid balance (EUR million)")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].set(xlabel="Year", ylabel="Overdue components", yticks=[0,1,2,3,4])
    fig.tight_layout()
    fig.savefig(figures / "renewal.pdf")
    plt.close(fig)
    (output / "execution.json").write_text(json.dumps({
        "execution": {"status": "PASS", "exit_code": 0},
        "runtime": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "matplotlib": matplotlib.__version__},
        "unit_tests": test_result.testsRun,
        "experiments": [{"name": name, "required": True, "execution": {"status": "PASS", "exit_code": 0}}
                        for name in ("unit-tests", "launch", "all-scenarios", "calls-and-sales", "return-sensitivity", "continuation-funding-search", "steward-costs")]
    }, indent=2)+"\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
