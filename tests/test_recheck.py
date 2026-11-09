"""R1-4: the refresh renders from dated data, survives a rerun with different counts, and never
relabels an older reading with a newer date."""
import csv
import io
import json
import os
import re
import shutil
import tempfile
import unittest

from helpers import REPO
import recheck


def copy_site(dst):
    for f in recheck.PAGES.values():
        shutil.copy(os.path.join(REPO, f), dst)


def make_run(runs_dir, run_date, flip_alps=0):
    """Copy the 9 Nov run under a new date, turning `flip_alps` bookable Europe rows into not offered."""
    with open(os.path.join(recheck.RUNS, '2026-11-09.json'), encoding='utf-8') as f:
        src_meta = json.load(f)
    with open(os.path.join(recheck.RUNS, src_meta['rows']), encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))
    flipped = 0
    for r in rows:
        if flipped < flip_alps and r['page'] == 'alps' and r['status'] == 'BOOKABLE':
            r['status'], r['quote_usd'] = 'NOT_OFFERED', ''
            flipped += 1
    meta = dict(src_meta, run_date=run_date, rows=f'{run_date}.tsv')
    # keep the pieces that were not re-read on their own dates, pointing at the real files
    meta['zermatt_fresh'] = dict(src_meta['zermatt_fresh'],
                                 fragment=os.path.join(recheck.RUNS, src_meta['zermatt_fresh']['fragment']))
    meta['booking'] = dict(src_meta['booking'], rows=os.path.join(recheck.RUNS, src_meta['booking']['rows']))
    if 'checks' in src_meta:
        meta['checks'] = os.path.join(recheck.RUNS, src_meta['checks'])
    with open(os.path.join(runs_dir, f'{run_date}.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f)
    fields = list(rows[0])
    with open(os.path.join(runs_dir, f'{run_date}.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(fields) + '\n')
        for r in rows:
            f.write('\t'.join(r[k] for k in fields) + '\n')


def read(d, name):
    with io.open(os.path.join(d, name), encoding='utf-8', newline='') as f:
        return f.read()


def generated(text):
    """The text inside every generated marker, excluding the parts that carry their own read date."""
    parts = re.findall(r'<!-- (recheck(?:-meta|-nav|-banner)?):start -->(.*?)<!-- \1:end -->', text, re.S)
    out = []
    for name, body in parts:
        if name == 'recheck-banner':
            continue
        body = re.sub(r'<h2 id="fresh">.*?(?=<h3>The September listings)', '', body, flags=re.S)
        body = re.sub(r'<h3>Japan hotels on Booking\.com.*?</table></div>\n', '', body, flags=re.S)
        # a correction note names the day the correction was made, which is not the run date
        body = re.sub(r'<i>Corrected \d{1,2} [A-Z][a-z]{2} \d{4}:</i>[^<]*', '', body)
        out.append(body)
    return '\n'.join(out)


class R1_4_Rerun(unittest.TestCase):
    def setUp(self):
        self.site = tempfile.mkdtemp()
        self.runs = tempfile.mkdtemp()
        copy_site(self.site)
        make_run(self.runs, '2026-11-09')
        make_run(self.runs, '2027-01-05', flip_alps=3)

    def tearDown(self):
        shutil.rmtree(self.site, True)
        shutil.rmtree(self.runs, True)

    def test_two_runs_with_different_dates_and_counts(self):
        changed, problems = recheck.apply(self.site, '2026-11-09', self.runs)
        self.assertEqual(problems, [])
        changed, problems = recheck.apply(self.site, '2027-01-05', self.runs)
        self.assertEqual(problems, [])
        alps = read(self.site, recheck.PAGES['alps'])
        self.assertIn('Rechecked 5 January 2027: 20 of 44 listing-weeks still bookable', alps)
        self.assertIn('listings rechecked 5 Jan 2027, 20 of 44 listing-weeks still bookable', alps)
        for tag, name in recheck.PAGES.items():
            gen = generated(read(self.site, name))
            self.assertNotRegex(gen, r'9 Nov|November 2026', f'{name}: a generated block still carries the old run date')
            self.assertRegex(gen, r'5 Jan', f'{name}: no generated block carries the new run date')

    def test_older_readings_keep_their_own_dates(self):
        recheck.apply(self.site, '2027-01-05', self.runs)
        rentals = read(self.site, recheck.PAGES['rentals'])
        self.assertIn('<h3>Japan hotels on Booking.com, rechecked 9 November 2026</h3>', rentals)
        zermatt = read(self.site, recheck.PAGES['zermatt'])
        self.assertIn('<strong>Rechecked 9 Nov 2026.</strong>', zermatt)
        self.assertIn('The September listings, rechecked 5 January 2027', zermatt)

    def test_rerun_is_idempotent_and_reversible(self):
        recheck.apply(self.site, '2026-11-09', self.runs)
        first = {n: read(self.site, n) for n in recheck.PAGES.values()}
        changed, _ = recheck.apply(self.site, '2026-11-09', self.runs)
        self.assertEqual(changed, [])
        recheck.apply(self.site, '2027-01-05', self.runs)
        recheck.apply(self.site, '2026-11-09', self.runs)
        self.assertEqual({n: read(self.site, n) for n in recheck.PAGES.values()}, first)

    def test_published_pages_match_the_data(self):
        self.assertEqual(recheck.check(REPO), [])

    def test_renderer_has_no_hard_coded_dates(self):
        with open(os.path.join(REPO, 'tools', 'recheck.py'), encoding='utf-8') as f:
            src = f.read()
        code = re.sub(r'"""(.*?)"""', '', src, flags=re.S)
        self.assertNotRegex(code, r'\b\d{1,2} (?:Nov|November|Sep|September|Jan|January)\b')
        self.assertNotRegex(code, r'20\d\d-\d\d-\d\d')

    def test_change_column_matches_the_published_quotes(self):
        self.assertEqual(recheck.change_cell('3365', '3264'), '&minus;$101 (&minus;3%)')
        self.assertEqual(recheck.change_cell('2561', '2459'), '&minus;$102 (&minus;4%)')
        self.assertEqual(recheck.change_cell('', '900'), '&mdash;')


if __name__ == '__main__':
    unittest.main()
