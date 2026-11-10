"""R1-5: the pre-push check rejects a personal author email, a local user path and token-shaped
strings in outgoing commits. Offending strings are assembled at run time so this file never trips
the scan it tests."""
import os
import shutil
import subprocess
import tempfile
import unittest

from helpers import REPO
import prepush

NOREPLY = '70870645+SamuelJWebber' + '@users.noreply.github.com'
PERSONAL = 'someone' + '@' + 'example.com'
LOCAL_PATH = 'C:' + '\\' + 'Users' + '\\' + 'bob' + '\\notes.txt'
TOKEN = 'gh' + 'p_' + 'A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8'


def git(repo, *args, env=None):
    subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True, env=env)


class Repo:
    def __init__(self, email):
        self.dir = tempfile.mkdtemp()
        git(self.dir, 'init', '-q')
        git(self.dir, 'config', 'user.email', email)
        git(self.dir, 'config', 'user.name', 'Test')
        git(self.dir, 'config', 'commit.gpgsign', 'false')

    def commit(self, name, text):
        path = os.path.join(self.dir, *name.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        git(self.dir, 'add', name)
        git(self.dir, 'commit', '-q', '-m', 'test')

    def close(self):
        shutil.rmtree(self.dir, True)


class R1_5_PrePush(unittest.TestCase):
    def run_check(self, email, text):
        r = Repo(email)
        try:
            r.commit('page.html', text)
            return prepush.check_outgoing(r.dir)
        finally:
            r.close()

    def test_noreply_and_clean_diff_pass(self):
        self.assertEqual(self.run_check(NOREPLY, '<p>A price, $1,571, read 9 Nov 2026.</p>\n'), [])

    def test_personal_author_email_is_rejected(self):
        problems = self.run_check(PERSONAL, '<p>ok</p>\n')
        self.assertTrue(any('author email is not a GitHub noreply address' in p for p in problems), problems)
        self.assertTrue(any('committer email' in p for p in problems), problems)

    def test_local_user_path_is_rejected(self):
        problems = self.run_check(NOREPLY, f'<p>{LOCAL_PATH}</p>\n')
        self.assertTrue(any('local user path' in p for p in problems), problems)

    def test_stray_email_and_token_are_rejected(self):
        problems = self.run_check(NOREPLY, f'<p>{PERSONAL}</p>\n<p>{TOKEN}</p>\n')
        self.assertTrue(any('email address outside the allow-list' in p for p in problems), problems)
        self.assertTrue(any('GitHub token' in p for p in problems), problems)

    def test_business_contacts_on_the_pages_are_allowed(self):
        self.assertEqual(self.run_check(NOREPLY, '<p>Enquire at reservations@nisade.com.</p>\n'), [])

    def test_hook_stdin_ranges(self):
        r = Repo(NOREPLY)
        try:
            r.commit('a.txt', 'one\n')
            base = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=r.dir, capture_output=True, text=True).stdout.strip()
            git(r.dir, 'config', 'user.email', PERSONAL)
            r.commit('b.txt', 'two\n')
            head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=r.dir, capture_output=True, text=True).stdout.strip()
            problems = prepush.check_outgoing(r.dir, [(head, base)])
            self.assertTrue(problems and all(p.startswith(head[:7]) for p in problems), problems)
        finally:
            r.close()

    def test_hook_script_is_versioned(self):
        self.assertTrue(os.path.exists(os.path.join(REPO, 'tools', 'hooks', 'pre-push')))


def _s(*parts):
    """Assemble an offending string at run time, so this file never contains it."""
    return ''.join(parts)


# R2-8: the review's five placeholder phrasings of a booking, and the path forms the scans missed
BOOKINGS = [
    _s('UNIT is book', 'ed for DATES'),
    _s('Book', 'ed: UNIT, DATES'),
    _s('Reser', 'ved the UNIT for DATES'),
    _s('Booking confir', 'med for DATES, code H', 'M', '4KX2QZ7P'),
    _s('User book', 'ed the UNIT for DATES'),
]
PATHS = [_s('/c', '/Us', 'ers/bob/notes.txt'), _s('C:', '/Us', 'ers/bob/notes.txt'), _s('/mnt', '/c/work/notes.txt'),
         _s('/Us', 'ers', '/bob/notes.txt'), _s('/home', '/bob/notes.txt')]


class R2_8_PrePush(unittest.TestCase):
    def run_check(self, name, text):
        r = Repo(NOREPLY)
        try:
            r.commit(name, text)
            return prepush.check_outgoing(r.dir)
        finally:
            r.close()

    def test_each_booking_phrasing_is_rejected(self):
        for b in BOOKINGS:
            problems = self.run_check('HANDOFF.md', f'- {b}\n')
            self.assertTrue(any('adds a ' in p and 'HANDOFF.md' in p for p in problems), (b, problems))

    def test_each_path_form_is_rejected(self):
        for path in PATHS:
            problems = self.run_check('notes.md', f'The raw files are in {path}\n')
            self.assertTrue(any('adds a local user path' in p for p in problems), (path, problems))

    def test_a_url_is_not_a_path(self):
        self.assertEqual(self.run_check('page.html', '<a href="https://example.org/Users/guide/">guide</a>\n'), [])

    def test_code_and_tests_may_hold_the_patterns(self):
        self.assertEqual(self.run_check('tests/test_x.py', f"PHRASE = '{BOOKINGS[0]}'\n"), [])

    def test_a_reviews_quoted_examples_are_evidence(self):
        self.assertEqual(self.run_check('REVIEW.md', f'The scan passes `{BOOKINGS[0]}` and "{BOOKINGS[2]}".\n'), [])
        self.assertTrue(self.run_check('REVIEW.md', f'{BOOKINGS[0]}.\n'))

    def test_the_site_check_rejects_them_too(self):
        import sitecheck
        d = tempfile.mkdtemp()
        try:
            for f in sitecheck.PAGES + ['README.md']:
                shutil.copy(os.path.join(REPO, f), d)
            with open(os.path.join(d, 'HANDOFF.md'), 'w', encoding='utf-8') as fh:
                fh.write('\n'.join(f'- {b}' for b in BOOKINGS) + '\n' + PATHS[0] + '\n')
            problems = [p for p in sitecheck.check_privacy(d) if p.startswith('HANDOFF.md')]
            for want in ('a stay recorded as booked', 'a booking recorded as a label', 'a confirmed booking',
                         'an Airbnb confirmation code', 'a local user path'):
                self.assertTrue(any(want in p for p in problems), (want, problems))
        finally:
            shutil.rmtree(d, True)


class R2_15_HookFindsAWorkingPython(unittest.TestCase):
    def test_a_failing_interpreter_stub_is_skipped(self):
        sh = shutil.which('sh')
        if not sh:
            self.skipTest('no sh on this machine')
        stub_dir = tempfile.mkdtemp()
        try:
            for name in ('python', 'python3'):  # stand-ins for the Microsoft Store alias, which fails
                p = os.path.join(stub_dir, name)
                with open(p, 'w', newline='\n') as f:
                    f.write('#!/bin/sh\nexit 9009\n')
                os.chmod(p, 0o755)
            env = dict(os.environ, PREPUSH_PRINT_PYTHON='1',
                       PATH=stub_dir + os.pathsep + os.environ.get('PATH', ''))
            r = subprocess.run([sh, os.path.join(REPO, 'tools', 'hooks', 'pre-push')], cwd=REPO, env=env,
                               capture_output=True, text=True)
            chosen = r.stdout.strip()
            if r.returncode != 0:
                self.assertIn('no working Python 3 found', r.stderr)
            else:
                self.assertTrue(chosen)
                self.assertNotEqual(shutil.which(chosen, path=env['PATH']), os.path.join(stub_dir, chosen))
        finally:
            shutil.rmtree(stub_dir, True)


if __name__ == '__main__':
    unittest.main()
