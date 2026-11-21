"""2026-11-21: every page says it is a snapshot of 9 November 2026 that is not maintained, and the Zermatt week with
passes uses the January band price (independent review SKI-3). Each check must pass on the current tree and fail
on the pages as they were pushed on 2026-11-10 (3d136e3)."""
import json
import os
import unittest

from helpers import REPO, export
import sitecheck

BEFORE = '3d136e3'


class SnapshotNote(unittest.TestCase):
    def test_every_page_carries_the_line(self):
        self.assertEqual(sitecheck.check_snapshot_note(REPO), [])

    def test_the_pages_before_did_not(self):
        root = export(BEFORE)
        if root is None:
            self.skipTest('commit not in this clone')
        problems = sitecheck.check_snapshot_note(root)
        self.assertEqual(len(problems), len(sitecheck.PAGES), problems)


class ZermattJanuaryBand(unittest.TestCase):
    def rows(self):
        with open(os.path.join(REPO, 'data', 'costs.json'), encoding='utf-8') as f:
            d = json.load(f)
        return d, {r['key']: r for r in d['rows']}

    def test_week_with_two_passes_is_3069(self):
        d, rows = self.rows()
        z = rows['zermatt_jan']
        self.assertEqual(z['passes']['each'], [436, 436])
        chf = d['fx']['per_usd']['CHF']
        tax = z['tax']['amount'][0] * d['people'] * d['nights'] / chf
        total = z['lodging']['usd'][0] + tax + 2 * 436 / chf
        self.assertEqual(round(total), 3069)                      # 1,923 + 69 + 1,077
        self.assertEqual(rows['zermatt_mar']['passes']['each'], [436, 488])

    def test_pages_print_it_and_not_the_old_figure(self):
        index = sitecheck.read(REPO, 'index.html')
        self.assertIn('data-cost="zermatt_jan:total">from $3,069</span>', index)
        self.assertIn('from $3,817', index)
        self.assertNotIn('from $3,688', index)
        self.assertEqual(index.count('from $2,940'), 1)           # only where the page says what it used to print
        self.assertIn('Until 21 Nov 2026 this page said from $2,940', index)
        self.assertEqual(sitecheck.check_propagated_corrections(REPO), [])
        self.assertEqual(sitecheck.check_costs(REPO), [])


if __name__ == '__main__':
    unittest.main()
