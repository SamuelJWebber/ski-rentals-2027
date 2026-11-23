"""Tests for Round 2 Deliverable #2: closing the non-scraping Fable review findings (SKI-2, 4, 5, 6, 7, 8),
SKI-1 interim disclosure, Zermatt month-pass March band disclosure, and known-but-live slips (R2-10, 11, 13, 14).
Each check passes on the current tree and, where applicable, fails on the parent commit before this sprint."""
import csv
import json
import os
import re
import unittest

from helpers import REPO, export
import costs
import sitecheck

BEFORE = 'c39cd52'


class ZermattMonthPassBands(unittest.TestCase):
    def test_current_pages_disclose_march_bands_and_9415_9790(self):
        z = sitecheck.read(REPO, 'zermatt-month-stay-2026-27.html')
        for needle in ('CHF 1,270&ndash;1,422', 'from 1,270&ndash;1,422', '$9,415 to $9,790',
                       '$3,136 to $3,511', 'operator leaflet dated April 2026, read 10 Nov 2026'):
            self.assertIn(needle, z)
        self.assertEqual(sitecheck.check_propagated_corrections(REPO), [])
        self.assertEqual(sitecheck.check_recheck_blocks(REPO), [])

    def test_before_commit_fails_stale_month_pass_check(self):
        root = export(BEFORE)
        if root is None:
            self.skipTest('commit before sprint not in this clone')
        joined = '\n'.join(sitecheck.check_propagated_corrections(root))
        self.assertIn('zermatt-month-stay-2026-27.html: "$9,040"', joined)
        self.assertIn('zermatt-month-stay-2026-27.html: "from 1,118"', joined)


class SKI2_HakubaAccommodationTax(unittest.TestCase):
    def test_costs_json_and_walks_use_400_and_900_bands(self):
        model = costs.load()
        rows = {r['key']: r for r in model['rows']}
        self.assertEqual(rows['hakuba_mar']['tax']['amount'], [400, 400])
        self.assertEqual(rows['hakuba_jan']['tax']['amount'], [900, 900])
        vals = costs.values(model)
        self.assertEqual(vals[('hakuba_mar', 'tax')], '$36')
        self.assertEqual(vals[('hakuba_mar', 'lodging_tax')], '$2,733')
        self.assertEqual(vals[('hakuba_mar', 'total')], '$3,552')
        self.assertEqual(vals[('hakuba_jan', 'tax')], '$81')
        self.assertEqual(vals[('hakuba_jan', 'lodging_tax')], '$5,686')
        self.assertEqual(vals[('hakuba_jan', 'total')], '$6,505')
        walks = sitecheck.load_walks(REPO)
        self.assertEqual(walks['hakuba_mar']['tax_usd'], 36)
        self.assertEqual(walks['hakuba_jan']['tax_usd'], 81)

    def test_pages_disclose_consumption_tax_uncertainty_and_drop_old_totals(self):
        index = sitecheck.read(REPO, 'index.html')
        steep = sitecheck.read(REPO, 'steep-and-town-2027.html')
        readme = sitecheck.read(REPO, 'README.md')
        self.assertIn('data-cost="hakuba_mar:lodging_tax">$2,733</span>', index)
        self.assertIn('data-cost="hakuba_mar:total">$3,552</span>', index)
        self.assertIn('data-cost="hakuba_jan:lodging_tax">$5,686</span>', index)
        self.assertIn('data-cost="hakuba_jan:total">$6,505</span>', index)
        self.assertIn('data-cost="hakuba_mar:lodging_tax">$2,733</span>', steep)
        self.assertIn('$2,733', readme)
        self.assertIn('$3,552', readme)
        self.assertIn('4721170', index)
        self.assertIn('$3,003', index)
        self.assertIn('$3,003', steep)
        self.assertEqual(sitecheck.check_costs(REPO), [])
        self.assertEqual(sitecheck.check_propagated_corrections(REPO), [])

    def test_before_commit_fails_hakuba_tax_check(self):
        root = export(BEFORE)
        if root is None:
            self.skipTest('commit before sprint not in this clone')
        joined = '\n'.join(sitecheck.check_propagated_corrections(root))
        for old in ('$3,561', '$5,695', '$6,514', '¥500 per person per night', '¥1,000 per person per night'):
            self.assertIn(old, joined)


class SKI1_HakubaInterimDisclosure(unittest.TestCase):
    def test_unread_cheaper_candidates_are_disclosed_until_hand_read(self):
        for name in ('index.html', 'steep-and-town-2027.html'):
            txt = sitecheck.read(REPO, name)
            self.assertIn('$2,156', txt)
            self.assertIn('$2,231', txt)
            self.assertNotIn('the first listing within 2 km, in price order, with the washer', txt)
        self.assertEqual(sitecheck.check_walks(REPO), [])

    def test_before_commit_fails_first_in_price_order_check(self):
        root = export(BEFORE)
        if root is None:
            self.skipTest('commit before sprint not in this clone')
        joined = '\n'.join(sitecheck.check_propagated_corrections(root))
        self.assertIn('first listing within 2 km, in price order, with the washer', joined)


class SKI4_TellurideFebruaryOption(unittest.TestCase):
    def test_telluride_cards_and_tables_include_february_option(self):
        index = sitecheck.read(REPO, 'index.html')
        steep = sitecheck.read(REPO, 'steep-and-town-2027.html')
        readme = sitecheck.read(REPO, 'README.md')
        for txt in (index, steep, readme):
            self.assertIn('20', txt)
            self.assertIn('$2,523', txt)
            self.assertIn('21 Jan', txt)
        self.assertIn('three-resorts-best-snow-2027.html#tel', index)
        self.assertIn('three-resorts-best-snow-2027.html#tel', steep)
        self.assertEqual(sitecheck.check_propagated_corrections(REPO), [])

    def test_before_commit_fails_january_only_check(self):
        root = export(BEFORE)
        if root is None:
            self.skipTest('commit before sprint not in this clone')
        joined = '\n'.join(sitecheck.check_propagated_corrections(root))
        self.assertIn('index.html: "North America · January only"', joined)
        self.assertIn('steep-and-town-2027.html: "Best fit, January only"', joined)


class SKI5_SnowSourceAndRankings(unittest.TestCase):
    def test_crocker_series_and_march_first_caveat_present(self):
        txt = sitecheck.read(REPO, 'three-resorts-best-snow-2027.html')
        for needle in ('368&Prime;/yr', '273&Prime;/yr', '289&Prime;/yr', '6,429 ft', '11,170 ft', '8,920 ft',
                       'OnTheSnow&rsquo;s 2012&ndash;26 series', 'bestsnow.net/crocnet.htm'):
            self.assertIn(needle, txt)
        self.assertNotIn('February is the snowiest month', txt)
        self.assertNotIn('El Ni&ntilde;o neutral to favourable', txt)

    def test_before_commit_fails_snowiest_month_check(self):
        root = export(BEFORE)
        if root is None:
            self.skipTest('commit before sprint not in this clone')
        joined = '\n'.join(sitecheck.check_propagated_corrections(root))
        self.assertIn('three-resorts-best-snow-2027.html: "February is the snowiest month"', joined)


class SKI6_JapanElNinoCaveat(unittest.TestCase):
    def test_jma_statistics_and_2026_pointer_without_unsupported_hokkaido_rule(self):
        index = sitecheck.read(REPO, 'index.html')
        self.assertIn('1947/48&ndash;2020/21', index)
        self.assertIn('No. 152', index)
        self.assertIn('22 Oct 2026', index)
        self.assertIn('jma.go.jp', index)
        self.assertNotIn('less exposed side in an El Niño winter', index)


class SKI7_RentalsWhistlerRewrite(unittest.TestCase):
    def test_lede_na_heading_and_top_picks_reflect_9_nov(self):
        txt = sitecheck.read(REPO, 'ski-rentals-2027.html')
        self.assertIn('As of 9 Nov 2026', txt)
        self.assertIn('Whistler was not searched afresh', txt)
        self.assertIn('Canyons Village holds on 9 Nov; September Whistler picks are gone or over budget', txt)
        picks_sec = re.search(r'<section id="picks">(.*?)</section>', txt, re.S).group(1)
        cards = re.findall(r'<div class="card">.*?</div>\s*</div>', picks_sec, re.S)
        cards_text = '\n'.join(cards)
        for gone in ('Cascade Lodge', 'Terrasses d', 'Le Kalinda', 'Deer Luxe'):
            self.assertNotIn(gone, cards_text)
        self.assertIn('Silverado Lodge', cards_text)
        self.assertEqual(sitecheck.check_pick_status(REPO), [])

    def test_before_commit_fails_whistler_lede_and_heading(self):
        root = export(BEFORE)
        if root is None:
            self.skipTest('commit before sprint not in this clone')
        joined = '\n'.join(sitecheck.check_propagated_corrections(root))
        self.assertIn('ski-rentals-2027.html: "Whistler, Park City\'s Canyons Village', joined)
        self.assertIn('ski-rentals-2027.html: "Whistler and Canyons Village win on price"', joined)


class SKI8_JacksonMarchAndElNino(unittest.TestCase):
    def test_jackson_exposure_and_el_nino_caveats_present(self):
        index = sitecheck.read(REPO, 'index.html')
        steep = sitecheck.read(REPO, 'steep-and-town-2027.html')
        self.assertIn('88% of normal snowfall in strong El Ni&ntilde;o months', index)
        self.assertIn('60% east and 30% south', index)
        self.assertIn('367&ndash;368 inches', index)
        self.assertIn('88% of normal', steep)
        self.assertIn('30% south / 60% east', steep)


class KnownSlipsClosed(unittest.TestCase):
    def test_r2_10_11_13_14_closed(self):
        index = sitecheck.read(REPO, 'index.html')
        self.assertNotIn('all four weeks searched at $906', index)
        z_fresh = sitecheck.read(REPO, os.path.join('data', 'recheck', 'zermatt-fresh-2026-11-09.html'))
        self.assertNotIn('Cancellation terms were not read for any of these', z_fresh)
        self.assertIn('free cancellation before 10 Dec', z_fresh)
        with open(os.path.join(REPO, 'data', 'readings.tsv'), encoding='utf-8') as f:
            rows = list(csv.DictReader(f, delimiter='\t'))
        self.assertIn('From 12 Nov 2026 the live page shows', rows[0]['note'])
        readme = sitecheck.read(REPO, 'README.md')
        self.assertIn('seventeen listing policies', readme)
        self.assertIn('eight refunded in full', readme)


if __name__ == '__main__':
    unittest.main()
