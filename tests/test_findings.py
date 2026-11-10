"""One test class per review finding. Each check must pass on the current pages and, where the
finding was about page content, must fail on the pages as reviewed (commit 20cb727)."""
import unittest

from helpers import REPO, export
import sitecheck


class Base(unittest.TestCase):
    check = None

    def current(self):
        return type(self).check(REPO)

    def reviewed(self):
        root = export()
        if root is None:
            self.skipTest('reviewed commit not in this clone')
        return type(self).check(root)

    def assertPasses(self):
        problems = self.current()
        self.assertEqual(problems, [], '\n'.join(problems))

    def assertCaught(self, *needles):
        problems = self.reviewed()
        joined = '\n'.join(problems)
        for n in needles:
            self.assertIn(n, joined, f'check did not flag {n!r} on the reviewed pages')


class Anchors(Base):
    check = staticmethod(sitecheck.check_anchors)

    def test_current(self):
        self.assertPasses()


class R1_2_Privacy(Base):
    check = staticmethod(sitecheck.check_privacy)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('Email to send', 'We are looking for', 'book all three', 'your four weeks',
                          '1 to 3 people', 'weeks of 9 Jan, 16 Jan', '(possibly 3)')


class R1_1_HeadlineCosts(Base):
    check = staticmethod(sitecheck.check_headline_costs)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught("'2,350–2,750'", "'1,950–2,600'", "'1,950 incl'",
                          'the Engelberg answer price is not taken from the cost model')

    def test_model_figures_on_pages(self):
        problems = sitecheck.check_costs(REPO)
        self.assertEqual(problems, [], '\n'.join(problems))


class R1_3_CostDefinitions(Base):
    check = staticmethod(sitecheck.check_cost_definitions)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('"Telluride, CO" week-for-two cell is not a cost-model total',
                          'no note under the ranking table',
                          'README.md: the answers table does not split')


class R1_6_CurrencyLabels(Base):
    # the round-1 expectation is passed in, so a later recheck that moves St Anton's quote cannot break it (R2-7)
    check = staticmethod(lambda root: sitecheck.check_currency_labels(
        root, expect=None if root == REPO else '&minus;$102 (&minus;4%)'))

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught("'$2,971'", "'€2,561'", "'priced out'", "'Cut from contention'",
                          'euros converted to dollars: €682 ≈ $791', 'expected −$102, −4%')


class R1_7_PropagatedCorrections(Base):
    check = staticmethod(sitecheck.check_propagated_corrections)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('"10,000 sq ft"', '"The March answer"', '"North American March answer"',
                          '"every 2 h', '"Jackson', '"365–390"', '"5 km / 7"')


class R1_8_PickStatus(Base):
    check = staticmethod(sitecheck.check_pick_status)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('listing 1450123020779481422 is cited without its dated recheck status',   # Cascade Lodge pick
                          'listing 22627280 is cited without',                                      # Terrasses d'Eos
                          'listing 40328205 is cited without',                                      # Le Kalinda
                          'listing 2387164 is cited without',                                       # Slope Side, Jackson
                          '26 priced listings have no room ID',
                          'does not say it covers only listings identified by room ID')

    def test_skipped_count_matches_the_review(self):
        text = sitecheck.read(REPO, 'steep-and-town-2027.html')
        self.assertEqual(len(sitecheck._unidentified_priced_rows(text)), 26)


class R1_9_CapacityClaims(Base):
    check = staticmethod(sitecheck.check_capacity_claims)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('but they total 124,121', '"Nothing else comes close"')


class R1_10_AllInArithmetic(Base):
    check = staticmethod(sitecheck.check_all_in_arithmetic)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('$1,643 at 17.22% is $1,926, page says $1,839',
                          'scorecard Telluride CO cheapest all-in $2,088 matches no listed option',
                          'scorecard Fernie BC cheapest all-in $1,095')


class R1_11_FitQualifiers(Base):
    check = staticmethod(sitecheck.check_fit_qualifiers)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('February and March still fit, each through one studio for two',
                          'February and March still fit through one studio for two, but January does not')


class R1_13_Method(Base):
    check = staticmethod(sitecheck.check_method)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught("README.md: does not state the recheck method ('human pace' missing)",
                          'HANDOFF.md: describes scripted fetching as the method')

    def test_a_browser_user_agent_is_caught(self):
        import os
        import shutil
        import tempfile
        d = tempfile.mkdtemp()
        try:
            for f in ('README.md', 'HANDOFF.md'):
                shutil.copy(os.path.join(REPO, f), d)
            with open(os.path.join(d, 'fetch.py'), 'w', encoding='utf-8') as fh:
                fh.write("UA = '" + 'Mozil' + "la/5.0 (Windows NT 10.0; Win64; x64)'\n")
            self.assertTrue(any('fetch.py: carries a browser User-Agent' in p for p in sitecheck.check_method(d)))
        finally:
            shutil.rmtree(d, True)


def superseded(fid):
    return staticmethod(lambda root: sitecheck.check_superseded(root, {fid}))


class R1_14_IkonSentence(Base):
    check = superseded('R1-14')

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('of these, only Niseko United', 'Of the Japanese resorts on the rentals page, only Niseko')


class R1_15_RefundCutoffs(Base):
    check = superseded('R1-15')

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('Free cancellation to', 'refundable to', 'Free to 2', 'until 21 January',
                          'refund in full only until')


class R1_16_RollingCitations(Base):
    check = staticmethod(sitecheck.check_rolling_citations)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('enso_advisory/ensodisc.shtml', 'lead02/off02_prcp.gif', '/-7,0/', 'bchydro.com')


class R1_17_GondolaHours(Base):
    check = superseded('R1-17')

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('index.html: "2am"', 'steep-and-town-2027.html: "2am"')


class R1_18_DatesStamped(Base):
    # the round-1 recheck date is passed in for the reviewed pages; the current pages use the data's (R2-7)
    check = staticmethod(lambda root: sitecheck.check_dates_stamped(
        root, latest=None if root == REPO else '2026-11-09'))

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('index.html footer: does not date both research rounds',
                          'README.md: does not date both research rounds',
                          're-shop in October', 'book Winter Park by 29 Sep', 'season pass quoted "from 1,750"')


class R1_19_SmallSlips(Base):
    check = superseded('R1-19')

    def test_current(self):
        self.assertPasses()
        problems = sitecheck.check_three_resorts_arithmetic(REPO)
        self.assertEqual(problems, [], '\n'.join(problems))

    def test_reviewed_pages_fail(self):
        self.assertCaught('Ranks 6th of 9', 'Telluride/Big Sky tie', 'convert CAD at 1.38', 'Airbnb totals are all-in',
                          '4 listings had been removed', '0.80 CHF')
        root = export()
        joined = '\n'.join(sitecheck.check_three_resorts_arithmetic(root))
        self.assertIn('$2,941 + 17.22% = $3,447, page says $3,448', joined)
        self.assertIn('$2,485 + 17.22% = $2,913, page says $2,912', joined)


class TaxBreakdowns(Base):
    """Review, bigger improvement 1: each tax breakdown sums to its stated total."""
    check = staticmethod(sitecheck.check_tax_breakdowns)

    def test_current(self):
        self.assertPasses()

    def test_a_wrong_component_is_caught(self):
        import os
        import shutil
        import tempfile
        d = tempfile.mkdtemp()
        try:
            for f in sitecheck.PAGES:
                shutil.copy(os.path.join(REPO, f), d)
            p = os.path.join(d, 'steep-and-town-2027.html')
            with open(p, encoding='utf-8') as fh:
                s = fh.read()
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(s.replace("1.25% transit lodgers'", "1.35% transit lodgers'", 1))
            problems = sitecheck.check_tax_breakdowns(d)
            self.assertTrue(any('17.22% is stated, the listed parts sum to 17.32%' in x for x in problems), problems)
        finally:
            shutil.rmtree(d, True)


if __name__ == '__main__':
    unittest.main()
