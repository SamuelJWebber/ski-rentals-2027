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


if __name__ == '__main__':
    unittest.main()
