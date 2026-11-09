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
    check = staticmethod(sitecheck.check_currency_labels)

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


if __name__ == '__main__':
    unittest.main()
