"""Checks on the commits about to be pushed, for a public repository.

Run by tools/hooks/pre-push (through tools/sitecheck.py --pre-push). For every outgoing commit:
  - author and committer emails must be GitHub noreply addresses;
  - the added lines must not contain a local Windows user path, an email address outside the allow-list,
    or a string shaped like a token or private key.
Standard library only.
"""
import os
import re
import subprocess
import sys

ZERO = '0' * 40
NOREPLY = re.compile(r'^[0-9]+\+[A-Za-z0-9-]+@users\.noreply\.github\.com$|^[A-Za-z0-9-]+@users\.noreply\.github\.com$')
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
EMAIL_ALLOW = {
    # businesses' own published contacts, quoted on the rentals page
    'reservations@nisade.com', 'enquiry@powderlife.com', 'enquiries@japanskiexperience.com',
    # the commit-trailer address required by the workflow
    'noreply@anthropic.com',
}
SECRET_PATTERNS = [
    (re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}'), 'a GitHub token'),
    (re.compile(r'\bgithub_pat_[A-Za-z0-9_]{30,}'), 'a GitHub token'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'an AWS access key'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'a private key'),
    (re.compile(r'\bsk-[A-Za-z0-9]{32,}'), 'an API key'),
]
LOCAL_PATH = re.compile(r'[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+', re.I)


def git(repo, *args):
    r = subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise RuntimeError(f'git {" ".join(args)}: {r.stderr.strip()}')
    return r.stdout


def outgoing(repo, updates=None):
    """Commits to be pushed. `updates` is the hook's stdin as (local_sha, remote_sha) pairs; without it,
    the commits on HEAD that no remote-tracking branch has."""
    if updates is None:
        out = git(repo, 'rev-list', 'HEAD', '--not', '--remotes')
        return [c for c in out.split() if c]
    commits = []
    for local, remote in updates:
        if local == ZERO:
            continue  # a deletion pushes no commits
        rng = [local, '--not', '--remotes'] if remote == ZERO else [f'{remote}..{local}']
        commits += [c for c in git(repo, 'rev-list', *rng).split() if c and c not in commits]
    return commits


def is_allowed_email(addr):
    a = addr.lower()
    return a in EMAIL_ALLOW or a.endswith('@users.noreply.github.com')


def check_commit(repo, sha):
    problems = []
    meta = git(repo, 'show', '-s', '--format=%ae%n%ce', sha).split('\n')
    for role, email in zip(('author', 'committer'), meta[:2]):
        if not NOREPLY.match(email.strip()):
            problems.append(f'{sha[:7]}: {role} email is not a GitHub noreply address')
    diff = git(repo, 'show', '--format=', '--unified=0', '--no-color', sha)
    for line in diff.split('\n'):
        if not line.startswith('+') or line.startswith('+++'):
            continue
        if LOCAL_PATH.search(line):
            problems.append(f'{sha[:7]}: adds a local Windows user path')
        for m in EMAIL.finditer(line):
            if not is_allowed_email(m.group(0)):
                problems.append(f'{sha[:7]}: adds an email address outside the allow-list')
        for pat, what in SECRET_PATTERNS:
            if pat.search(line):
                problems.append(f'{sha[:7]}: adds what looks like {what}')
    return sorted(set(problems))


def check_outgoing(repo, updates=None):
    problems = []
    for sha in outgoing(repo, updates):
        problems += check_commit(repo, sha)
    return problems


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    updates = []
    for line in sys.stdin.read().splitlines():
        parts = line.split()
        if len(parts) == 4:
            updates.append((parts[1], parts[3]))
    problems = check_outgoing(repo, updates or None)
    for p in problems:
        print('pre-push:', p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
