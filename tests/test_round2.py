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


def _tmp_root_with_checks(rows, fields=None):
    """A temp root holding one data/checks file with these rows (dicts)."""
    import os
    import tempfile
    import log_read
    fields = fields or log_read.FIELDS
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'data', 'checks'))
    with open(os.path.join(d, 'data', 'checks', '2026-12-05.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(fields) + '\n')
        for r in rows:
            f.write('\t'.join(r.get(k, '') for k in fields) + '\n')
    return d


def _fixture(name):
    import os
    with open(os.path.join(REPO, 'tests', 'fixtures', name), encoding='utf-8') as f:
        return f.read()


class R2_9_EveryLoggedStatusHasItsLine(Base):
    check = staticmethod(sitecheck.check_reading_evidence)

    def test_current(self):
        self.assertPasses()

    def test_reviewed_log_fails(self):
        self.assertCaught('columns are not those tools/log_read.py writes')

    def test_log_read_classifies_the_pasted_page(self):
        import log_read
        r = log_read.classify('1267557874578220140', '2027-01-09', '2027-01-16', _fixture('listing_bookable.txt'),
                              read_date='2026-12-05')
        self.assertEqual((r['status'], r['total_usd'], r['originally_usd']), ('BOOKABLE', '1571', '1857'))
        self.assertEqual(r['evidence'], '$1,571 for 7 nights, originally $1,857')
        self.assertTrue(r['cancellation'].startswith('Free cancellation before January 4.'))
        self.assertEqual(r['source'], 'pasted')
        r = log_read.classify('1267557874578220140', '2027-01-09', '2027-01-16', _fixture('listing_not_offered.txt'))
        self.assertEqual((r['status'], r['evidence']), ('NOT_OFFERED', 'Those dates are not available'))

    def test_a_challenge_is_refused_not_logged_as_not_offered(self):
        import log_read
        with self.assertRaises(ValueError):
            log_read.classify('1267557874578220140', '2027-01-09', '2027-01-16', _fixture('challenge.txt'))
        r = log_read.classify('1267557874578220140', '2027-01-09', '2027-01-16', _fixture('challenge.txt'),
                              allow_undetermined=True)
        self.assertEqual(r['status'], 'NOT_DETERMINED')

    def test_a_logged_file_passes_and_a_hand_edit_is_caught(self):
        import os
        import shutil
        import tempfile
        import log_read
        d = tempfile.mkdtemp()
        try:
            rows = [log_read.classify('1267557874578220140', '2027-01-09', '2027-01-16', _fixture(n),
                                      read_date='2026-12-05') for n in ('listing_bookable.txt', 'listing_not_offered.txt')]
            log_read.append(rows, os.path.join(d, 'data', 'checks'))
            self.assertEqual(sitecheck.check_reading_evidence(d), [])
            p = os.path.join(d, 'data', 'checks', '2026-12-05.tsv')
            with open(p, encoding='utf-8') as f:
                s = f.read()
            with open(p, 'w', encoding='utf-8') as f:
                f.write(s.replace('\tBOOKABLE\t1571\t', '\tNOT_OFFERED\t1571\t', 1))
            problems = sitecheck.check_reading_evidence(d)
            self.assertTrue(any('the stored line supports BOOKABLE, the row says NOT_OFFERED' in p for p in problems), problems)
        finally:
            shutil.rmtree(d, True)

    def test_a_typed_not_available_without_the_pages_line_is_caught(self):
        import shutil
        d = _tmp_root_with_checks([dict(read_date='2026-12-05', room_id='36729825', check_in='2027-01-09',
                                        check_out='2027-01-16', adults='2', status='NOT_OFFERED',
                                        evidence='not available', source='typed')])
        try:
            problems = sitecheck.check_reading_evidence(d)
            self.assertTrue(any('the stored line supports NOT_DETERMINED, the row says NOT_OFFERED' in p for p in problems),
                            problems)
        finally:
            shutil.rmtree(d, True)

    def test_the_status_rules_are_now_called(self):
        import os
        for f in ('log_read.py', 'sitecheck.py'):
            with open(os.path.join(REPO, 'tools', f), encoding='utf-8') as fh:
                self.assertRegex(fh.read(), r'import listing_status')


class R2_12_ZermattMonthsReadOnTheirPages(unittest.TestCase):
    def test_both_rows_have_a_listing_page_reading(self):
        import recheck
        meta, rows = recheck.load()
        for room, cin, adults in (('1556537260452412398', '2026-12-05', '2'), ('1295138371680887002', '2027-01-05', '3')):
            got = [c for c in meta['_readings'] if (c['room_id'], c['check_in'], c['adults']) == (room, cin, adults)]
            self.assertTrue(got, f'{room} has no data/checks reading')
            self.assertEqual(got[-1]['evidence'], 'Those dates are not available')
            row = [r for r in rows if r['room_id'] == room and r['check_in'] == cin][0]
            self.assertEqual((row['status'], row['source']), ('NOT_OFFERED', 'browser'))


if __name__ == '__main__':
    unittest.main()
