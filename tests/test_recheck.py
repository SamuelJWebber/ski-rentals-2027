"""R1-4 and R2-3: the recheck sections render from dated readings. A full rerun relabels every row it
re-read and nothing else; a partial re-read (the method since 9 Nov re-reads only the listings that drive
a recommendation) keeps every row and every older date; and a run that cannot render changes no file."""
import csv
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from helpers import REPO, REVIEWED_R2, have_commit
import recheck

CHECKS_9NOV = os.path.join(REPO, 'data', 'checks', '2026-11-09.tsv')
TABLE_ROWS = {'alps': 44, 'steep': 36, 'rentals': 52, 'zermatt': 26}


def copy_site(dst):
    for f in list(recheck.PAGES.values()) + [recheck.INDEX]:
        shutil.copy(os.path.join(REPO, f), dst)


def base_rows():
    with open(os.path.join(recheck.RUNS, '2026-11-09.json'), encoding='utf-8') as f:
        src_meta = json.load(f)
    with open(os.path.join(recheck.RUNS, src_meta['rows']), encoding='utf-8', newline='') as f:
        return src_meta, list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))


def make_run(runs_dir, run_date, flip_alps=0, keep=None, checks=True):
    """Copy the 9 Nov run under a new date, turning `flip_alps` bookable Europe rows into not offered and,
    with `keep`, keeping only the rows for which keep(row) is true (a partial run)."""
    src_meta, rows = base_rows()
    flipped = 0
    for r in rows:
        if flipped < flip_alps and r['page'] == 'alps' and r['status'] == 'BOOKABLE':
            r['status'], r['quote_usd'] = 'NOT_OFFERED', ''
            flipped += 1
    if keep is not None:
        rows = [r for r in rows if keep(r)]
    meta = dict(src_meta, run_date=run_date, rows=f'{run_date}.tsv')
    # keep the pieces that were not re-read on their own dates, pointing at the real files
    meta['zermatt_fresh'] = dict(src_meta['zermatt_fresh'],
                                 fragment=os.path.join(recheck.RUNS, src_meta['zermatt_fresh']['fragment']))
    meta['booking'] = dict(src_meta['booking'], rows=os.path.join(recheck.RUNS, src_meta['booking']['rows']))
    meta.pop('checks', None)
    if checks:
        meta['checks'] = CHECKS_9NOV
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
    parts = re.findall(r'<!-- (recheck(?:-meta|-nav|-banner|-tally)?):start -->(.*?)<!-- \1:end -->', text, re.S)
    out = []
    for name, body in parts:
        if name == 'recheck-banner':
            continue
        body = re.sub(r'<h2 id="fresh">.*?(?=<h3>The September listings)', '', body, flags=re.S)
        body = re.sub(r'<h3>Japan hotels on Booking\.com.*?</table></div>\n', '', body, flags=re.S)
        # a correction note names the day the correction was made, which is not the run date
        body = re.sub(r'<i>[A-Z][a-z]+ \d{1,2} [A-Z][a-z]{2} \d{4}:</i>[^<]*', '', body)
        out.append(body)
    return '\n'.join(out)


def table_rows(text):
    m = re.search(r'<!-- recheck:start -->(.*?)<!-- recheck:end -->', text, re.S)
    body = re.sub(r'<h2 id="fresh">.*?(?=<h3>The September listings)', '', m.group(1), flags=re.S)
    body = re.sub(r'<h3>Japan hotels on Booking\.com.*?</table></div>\n', '', body, flags=re.S)
    return re.findall(r'<tr><td><a href="https://www\.airbnb\.com/rooms/.*?</tr>', body)


def read_cells(rows):
    return [re.findall(r'<td class="num">(\d{1,2} [A-Z][a-z]{2})(?: <span class="small">\(listing page\)</span>)?</td>', r)[0]
            for r in rows]


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
            # a refund line keeps the date it was read, which here is older than the run
            gen = re.sub(r' <span class="small">\(read 9 Nov\)</span>', '', gen)
            self.assertNotRegex(gen, r'9 Nov|November 2026', f'{name}: a generated block still carries the old run date')
            self.assertRegex(gen, r'5 Jan', f'{name}: no generated block carries the new run date')

    def test_older_readings_keep_their_own_dates(self):
        recheck.apply(self.site, '2027-01-05', self.runs)
        rentals = read(self.site, recheck.PAGES['rentals'])
        self.assertIn('<h3>Japan hotels on Booking.com, rechecked 9 November 2026</h3>', rentals)
        zermatt = read(self.site, recheck.PAGES['zermatt'])
        self.assertIn('<strong>Rechecked 9 Nov 2026.</strong>', zermatt)
        self.assertIn('The September listings, rechecked 5 January 2027', zermatt)
        alps = read(self.site, recheck.PAGES['alps'])
        self.assertIn('free cancellation before 4 Jan <span class="small">(read 9 Nov)</span>', alps)

    def test_rerun_is_idempotent_and_reversible(self):
        recheck.apply(self.site, '2026-11-09', self.runs)
        first = {n: read(self.site, n) for n in list(recheck.PAGES.values()) + [recheck.INDEX]}
        changed, _ = recheck.apply(self.site, '2026-11-09', self.runs)
        self.assertEqual(changed, [])
        recheck.apply(self.site, '2027-01-05', self.runs)
        recheck.apply(self.site, '2026-11-09', self.runs)
        self.assertEqual({n: read(self.site, n) for n in first}, first)

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


def covered_by_checks():
    """The rows the review's simulation re-read: those the hand-read log covered at the reviewed commit."""
    text = None
    if have_commit(REVIEWED_R2):
        text = subprocess.run(['git', 'show', f'{REVIEWED_R2}:data/checks/2026-11-09.tsv'], cwd=REPO,
                              capture_output=True, text=True, encoding='utf-8').stdout
    if not text:
        with open(CHECKS_9NOV, encoding='utf-8', newline='') as f:
            text = f.read()
    keys = {(r['room_id'], r['check_in']) for r in csv.DictReader(io.StringIO(text), delimiter='\t', quoting=csv.QUOTE_NONE)}
    return lambda r: (r['room_id'], r['check_in']) in keys


class R2_3_PartialRecheck(unittest.TestCase):
    """The review's simulation: a run holding only the rows data/checks covers, dated 5 Dec 2026."""

    def setUp(self):
        self.site = tempfile.mkdtemp()
        self.runs = tempfile.mkdtemp()
        copy_site(self.site)
        make_run(self.runs, '2026-11-09')
        self.covered = covered_by_checks()
        make_run(self.runs, '2026-12-05', keep=self.covered, checks=False)
        _, rows = base_rows()
        self.n_partial = sum(1 for r in rows if self.covered(r))

    def tearDown(self):
        shutil.rmtree(self.site, True)
        shutil.rmtree(self.runs, True)

    def test_the_partial_run_is_the_reviewed_size(self):
        self.assertEqual(self.n_partial, 23)

    def test_every_row_survives_and_only_the_reread_rows_take_the_new_date(self):
        changed, problems = recheck.apply(self.site, None, self.runs)
        self.assertEqual(problems, [])
        new_dates = 0
        for tag, name in recheck.PAGES.items():
            rows = table_rows(read(self.site, name))
            self.assertEqual(len(rows), TABLE_ROWS[tag], f'{name}: the table lost rows')
            cells = read_cells(rows)
            self.assertTrue(set(cells) <= {'9 Nov', '5 Dec'}, cells)
            new_dates += cells.count('5 Dec')
        self.assertEqual(new_dates, self.n_partial)

    def test_headings_split_the_count_by_read_date(self):
        recheck.apply(self.site, None, self.runs)
        alps = read(self.site, recheck.PAGES['alps'])
        m = re.search(r'<h2 id="recheck">(.*?)</h2>', alps)
        self.assertRegex(m.group(1), r'^Rechecked 9 Nov 2026 and 5 Dec 2026: \d+ of 44 listing-weeks bookable as last read '
                                     r'\(\d+ read 5 Dec 2026; \d+ as read 9 Nov 2026\)$')
        self.assertIn('the Read column gives the date each row was last read', alps)

    def test_notes_for_rows_nobody_reread_keep_their_date(self):
        recheck.apply(self.site, None, self.runs)
        steep = read(self.site, recheck.PAGES['steep'])
        # Plunge E (617410023719291310) is not among the 23 re-read rows
        self.assertRegex(steep, r'data-room="617410023719291310">Rechecked 9 Nov 2026: not offered for 9&ndash;16 Jan\.')
        # the Cascade Lodge row (1450123020779481422, 9-16 Jan) was re-read on 5 Dec
        rentals = read(self.site, recheck.PAGES['rentals'])
        self.assertRegex(rentals, r'data-room="1450123020779481422"[^>]*>[^<]*\(read 5 Dec 2026\)')

    def test_browser_readings_alone_update_the_rows_they_read(self):
        checks = tempfile.mkdtemp()
        try:
            with open(CHECKS_9NOV, encoding='utf-8', newline='') as f:
                head = f.readline()
            with open(os.path.join(checks, '2026-12-05.tsv'), 'w', encoding='utf-8', newline='') as f:
                f.write(head)
                cols = head.rstrip('\n').split('\t')
                row = dict.fromkeys(cols, '')
                row.update(read_date='2026-12-05', room_id='1400536477616188823', check_in='2027-01-09',
                           check_out='2027-01-16', status='NOT_OFFERED')
                if 'adults' in row:
                    row['adults'] = '2'
                if 'evidence' in row:
                    row['evidence'] = 'Those dates are not available'
                if 'source' in row:
                    row['source'] = 'pasted'
                f.write('\t'.join(row[c] for c in cols) + '\n')
            shutil.rmtree(self.runs, True)
            self.runs = tempfile.mkdtemp()
            make_run(self.runs, '2026-11-09', checks=False)
            changed, problems = recheck.apply(self.site, None, self.runs, checks)
            self.assertEqual(problems, [])
            alps = read(self.site, recheck.PAGES['alps'])
            rows = [r for r in table_rows(alps) if 'rooms/1400536477616188823?check_in=2027-01-09' in r]
            self.assertEqual(len(rows), 1)
            self.assertIn('5 Dec <span class="small">(listing page)</span>', rows[0])
            self.assertIn('Not offered for these dates', rows[0])
            self.assertEqual(len(table_rows(alps)), TABLE_ROWS['alps'])
        finally:
            shutil.rmtree(checks, True)

    def test_a_run_that_cannot_render_changes_no_file(self):
        only_partial = tempfile.mkdtemp()
        try:
            make_run(only_partial, "2026-12-05", keep=self.covered, checks=False)
            before = {n: read(self.site, n) for n in list(recheck.PAGES.values()) + [recheck.INDEX]}
            changed, problems = recheck.apply(self.site, None, only_partial, os.path.join(only_partial, 'none'))
            self.assertEqual(changed, [])
            self.assertTrue(any('is cited in a recheck note, but no run or browser reading has it' in p for p in problems),
                            problems[:3])
            self.assertFalse(any('marker' in p for p in problems), 'a missing room is not a missing marker')
            self.assertEqual({n: read(self.site, n) for n in before}, before)
        finally:
            shutil.rmtree(only_partial, True)

    def test_the_reviewed_renderer_loses_rows_on_the_same_run(self):
        """The defect itself: the renderer at the reviewed commit, given the same partial run, shrinks the
        tables and writes the pages before it reports the missing rooms."""
        if not have_commit(REVIEWED_R2):
            self.skipTest('reviewed commit not in this clone')
        src = subprocess.run(['git', 'show', f'{REVIEWED_R2}:tools/recheck.py'], cwd=REPO, capture_output=True,
                             text=True, encoding='utf-8').stdout
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, 'recheck_reviewed.py')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(src)
            spec = importlib.util.spec_from_file_location('recheck_reviewed', path)
            old = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(old)
            alps_before = read(self.site, recheck.PAGES['alps'])
            changed, problems = old.apply(self.site, '2026-12-05', self.runs)
            self.assertTrue(problems)                          # it reported missing rooms ...
            self.assertIn(recheck.PAGES['alps'], changed)      # ... after writing the page anyway
            self.assertNotEqual(read(self.site, recheck.PAGES['alps']), alps_before)
            self.assertLess(len(table_rows(read(self.site, recheck.PAGES['alps']))), TABLE_ROWS['alps'])
        finally:
            shutil.rmtree(d, True)


if __name__ == '__main__':
    unittest.main()
