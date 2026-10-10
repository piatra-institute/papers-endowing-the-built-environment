import copy
import unittest
from model import CONFIG, continuation, launch, simulate


class RenewalTests(unittest.TestCase):
    def test_launch_identity_and_opportunity_cost(self):
        r = launch()
        self.assertEqual(r["sales"], 12000000)
        self.assertEqual(r["developer_cash_surplus"], 1700000)
        self.assertEqual(r["dedicated_capital"]+r["developer_cash_surplus"], r["total_surplus"])

    def test_integer_feasibility(self):
        self.assertEqual((launch()["n_min"], launch()["n_max"]), (25,25))
        self.assertFalse(launch(annual_required=150000)["feasible"])
        self.assertEqual(launch(annual_required=150000)["n_min"], 32)

    def test_equal_starting_capital(self):
        capitals = [simulate(scheme=s)["summary"]["initial_dedicated_capital"]
                    for s in ("reserve", "rental", "financial", "matched_reserve")]
        self.assertEqual(capitals, [3300000]*4)

    def test_same_portfolio_same_result(self):
        for scenario in ("baseline", "combined", "approval"):
            self.assertEqual(simulate(scheme="financial", scenario=scenario),
                             simulate(scheme="matched_reserve", scenario=scenario))

    def test_cash_identity(self):
        for sale, call in ((False,False),(True,False),(False,True)):
            for r in simulate(scheme="rental", scenario="combined", sales=sale, calls=call)["annual"]:
                self.assertLess(abs(r["accounting_residual"]), 1e-6)

    def test_component_repeats_and_age_resets(self):
        r = simulate(extra_cash=20000000)
        years = [e["year"] for e in r["interventions"] if e["component"] == "lifts"]
        self.assertEqual(years, [20,40,60])

    def test_delay_is_visible_even_with_ample_money(self):
        r = simulate(scenario="approval", extra_cash=20000000)
        self.assertGreater(r["summary"]["overdue_component_years"], 0)
        self.assertEqual(r["interventions"][0]["year"], 22)

    def test_terminal_plan_sees_next_cycle(self):
        self.assertGreater(continuation(CONFIG, "reserve", "baseline", 60, [10,0,0,0], 0), 0)

    def test_unfunded_costs_are_not_erased(self):
        c = copy.deepcopy(CONFIG)
        c["opening_cash"] = c["retained_units"] = 0
        r = simulate(c)
        self.assertGreater(r["summary"]["maximum_cash_arrears"], 0)
        self.assertGreater(r["summary"]["overdue_component_years"], 0)

    def test_owner_calls_are_explicit(self):
        c = copy.deepcopy(CONFIG)
        c["opening_cash"] = c["retained_units"] = 0
        r = simulate(c, calls=True)["summary"]
        self.assertGreater(r["owner_calls"], 0)
        self.assertEqual(r["overdue_component_years"], 0)

    def test_sales_reduce_future_rental_income(self):
        c = copy.deepcopy(CONFIG)
        c["opening_cash"] = 0
        c["routine_cost"] = 150000
        r = simulate(c, scheme="rental", sales=True)
        self.assertGreater(r["summary"]["units_sold"], 0)
        self.assertLess(r["annual"][-1]["rent"], 120000)

    def test_cost_growth_applies_to_renewal(self):
        r = simulate(extra_cash=20000000)
        first = r["interventions"][0]
        self.assertAlmostEqual(first["cost"], 350000*1.01**20)


if __name__ == "__main__":
    unittest.main()
