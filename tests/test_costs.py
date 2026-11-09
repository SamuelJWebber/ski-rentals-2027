"""The cost model's arithmetic, formatting and page check, on hand-made inputs."""
import os
import shutil
import tempfile
import unittest

from helpers import REPO
import costs

MODEL = {
    'people': 2, 'nights': 7,
    'fx': {'label': 'test', 'per_usd': {'USD': 1, 'CHF': 0.81, 'JPY': 156}},
    'definition': 'test', 'as_of': 'test',
    'rows': [
        {'key': 'pct', 'resort': 'A', 'region': 'X', 'week': '9–16 Jan 2027',
         'lodging': {'usd': [1877, 1877], 'quoted': 'd', 'basis': 'b', 'rooms': []},
         'tax': {'kind': 'percent', 'amount': [17.22, 17.22], 'basis': 'b'},
         'passes': {'each': [1430, 1430], 'currency': 'USD', 'ticket_tax': 5, 'basis': 'b', 'covered_by': 'c'},
         'refund': 'r', 'washer': 'w', 'fits': 'f'},
        {'key': 'ppn', 'resort': 'B', 'region': 'Y', 'week': '9–16 Jan 2027',
         'lodging': {'usd': [1571, 1571], 'quoted': 'd', 'basis': 'b', 'rooms': []},
         'tax': {'kind': 'per_person_night', 'amount': [3.2, 4.5], 'currency': 'CHF', 'basis': 'b'},
         'passes': {'each': [274, 390], 'currency': 'CHF', 'basis': 'b', 'covered_by': 'c'},
         'refund': 'r', 'washer': 'w', 'fits': 'f', 'readme_note': 'n'},
        {'key': 'gone', 'resort': 'C', 'region': 'Z', 'week': '6–13 Mar 2027',
         'lodging': {'usd': None, 'quoted': 'd', 'basis': 'b', 'rooms': []},
         'tax': {'kind': 'percent', 'amount': [13, 13], 'basis': 'b'},
         'passes': {'each': [100, 200], 'currency': 'USD', 'basis': 'b', 'covered_by': 'c'},
         'refund': 'r', 'washer': 'w', 'fits': 'f'},
    ],
}


class Arithmetic(unittest.TestCase):
    def test_percent_tax_and_ticket_tax(self):
        c = costs.compute(MODEL['rows'][0], MODEL)
        self.assertAlmostEqual(c['lodging_tax'][0], 1877 * 1.1722)       # 2200.2
        self.assertAlmostEqual(c['passes'][0], 2 * 1430 * 1.05)           # 3003
        self.assertEqual(costs.fmt(c['total']), '$5,203')

    def test_per_person_night_tax_converts_currency(self):
        c = costs.compute(MODEL['rows'][1], MODEL)
        self.assertAlmostEqual(c['tax'][0], 2 * 7 * 3.2 / 0.81)
        self.assertEqual(costs.fmt(c['lodging_tax']), '$1,626–1,649')
        self.assertEqual(costs.fmt(c['passes']), '$677–963')
        self.assertEqual(costs.fmt(c['total']), '$2,303–2,612')

    def test_unknown_lodging_leaves_totals_empty(self):
        c = costs.compute(MODEL['rows'][2], MODEL)
        self.assertIsNone(c['total'])
        self.assertEqual(costs.fmt(c['total']), '—')
        self.assertEqual(costs.fmt(c['passes']), '$200–400')

    def test_rounding_is_half_up(self):
        self.assertEqual(costs.fmt((2912.5, 2912.5)), '$2,913')
        self.assertEqual(costs.fmt((3447.4, 3447.4)), '$3,447')


class PageCheck(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        for f in costs.PAGES + ['README.md']:
            shutil.copy(os.path.join(REPO, f), self.dir)

    def tearDown(self):
        shutil.rmtree(self.dir, True)

    def test_repo_pages_match_the_data(self):
        self.assertEqual(costs.check(REPO), [])

    def test_a_hand_edited_figure_is_caught(self):
        p = os.path.join(self.dir, 'index.html')
        with open(p, encoding='utf-8') as f:
            s = f.read()
        s = s.replace('<span data-cost="engelberg:total">', '<span data-cost="engelberg:total">$1', 1)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(s)
        problems = costs.check(self.dir)
        self.assertTrue(any('engelberg:total shows' in x for x in problems), problems)

    def test_apply_repairs_the_pages(self):
        p = os.path.join(self.dir, 'index.html')
        with open(p, encoding='utf-8') as f:
            s = f.read()
        s = s.replace('<span data-cost="telluride:total">', '<span data-cost="telluride:total">9', 1)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(s)
        costs.apply(self.dir)
        self.assertEqual(costs.check(self.dir), [])


if __name__ == '__main__':
    unittest.main()
