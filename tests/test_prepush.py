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
        with open(os.path.join(self.dir, name), 'w', encoding='utf-8') as f:
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
        self.assertTrue(any('local Windows user path' in p for p in problems), problems)

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


if __name__ == '__main__':
    unittest.main()
