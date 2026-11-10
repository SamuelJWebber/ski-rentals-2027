"""Review round 2 (REVIEW.md): one test class per finding. Where a finding is about the published pages
or data, its check must pass on the current tree and fail on the commit the review examined (d46aeed,
whose pages and data are those of e3866e3)."""
import unittest

from helpers import REPO, REVIEWED_R2, export
import sitecheck


class Base(unittest.TestCase):
    check = None

    def current(self):
        return type(self).check(REPO)

    def reviewed(self):
        root = export(REVIEWED_R2)
        if root is None:
            self.skipTest('reviewed commit not in this clone')
        return type(self).check(root)

    def assertPasses(self):
        problems = self.current()
        self.assertEqual(problems, [], '\n'.join(problems))

    def assertCaught(self, *needles):
        joined = '\n'.join(self.reviewed())
        for n in needles:
            self.assertIn(n, joined, f'check did not flag {n!r} on the reviewed pages')


class R2_2_AllInMeansLodgingAndTax(Base):
    check = staticmethod(sitecheck.check_all_in_figures)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_pages_fail(self):
        self.assertCaught('$3,400 is called all-in but is not one of the page\'s lodging-plus-tax totals')

    def test_the_old_verdict_wording_is_superseded(self):
        self.assertEqual(sitecheck.check_superseded(REPO, {'R2-2'}), [])
        root = export(REVIEWED_R2)
        if root is None:
            self.skipTest('reviewed commit not in this clone')
        self.assertTrue(sitecheck.check_superseded(root, {'R2-2'}))

    def test_zermatt_note_takes_its_figures_from_the_cost_model(self):
        text = sitecheck.read(REPO, 'steep-and-town-2027.html')
        for key in ('zermatt_jan:lodging_tax', 'telluride:lodging_tax', 'zermatt_jan:total', 'telluride:total'):
            self.assertIn(f'data-cost="{key}"', text)

    def test_a_passes_figure_called_all_in_is_caught(self):
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
            s = s.replace('<span data-cost="zermatt_jan:total">from $2,940</span> and',
                          '<span data-cost="zermatt_jan:total">from $2,940</span> all-in and', 1)
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(s)
            self.assertTrue(any('a total figure, which includes lift passes, is called all-in' in x
                                for x in sitecheck.check_all_in_figures(d)))
        finally:
            shutil.rmtree(d, True)


if __name__ == '__main__':
    unittest.main()
