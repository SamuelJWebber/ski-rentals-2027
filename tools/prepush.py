"""Checks on the commits about to be pushed, for a public repository.

Run by tools/hooks/pre-push (and by tools/sitecheck.py --pre-push). For every outgoing commit:
  - author and committer emails must be GitHub noreply addresses;
  - the added lines must not contain a local user path in any form (Windows, Git Bash, WSL, macOS,
    Linux), an email address outside the allow-list, or a string shaped like a token or private key;
  - added lines of prose and data must not record a booking in any wording, first person or impersonal,
    so a booking never reaches the public history even if a later commit removes it (review finding R2-8).
The patterns live in tools/privacy.py. Standard library only.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import privacy  # noqa: E402

ZERO = '0' * 40
NOREPLY = re.compile(r'^[0-9]+\+[A-Za-z0-9-]+@users\.noreply\.github\.com$|^[A-Za-z0-9-]+@users\.noreply\.github\.com$')
EMAIL_ALLOW = privacy.EMAIL_ALLOW


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
    return privacy.is_allowed_email(addr)


def added_lines(repo, sha):
    """{path: added text} for one commit."""
    diff = git(repo, 'show', '--format=', '--unified=0', '--no-color', sha)
    out, path = {}, None
    for line in diff.split('\n'):
        if line.startswith('+++ '):
            path = line[6:] if line.startswith('+++ b/') else None
            continue
        if path and line.startswith('+') and not line.startswith('+++'):
            out.setdefault(path, []).append(line[1:])
    return {p: '\n'.join(v) for p, v in out.items()}


def check_commit(repo, sha):
    problems = []
    meta = git(repo, 'show', '-s', '--format=%ae%n%ce', sha).split('\n')
    for role, email in zip(('author', 'committer'), meta[:2]):
        if not NOREPLY.match(email.strip()):
            problems.append(f'{sha[:7]}: {role} email is not a GitHub noreply address')
    for path, text in added_lines(repo, sha).items():
        for what, why in privacy.other_problems(text):
            if why == 'a local user path':
                problems.append(f'{sha[:7]}: adds a local user path ({path})')
            elif why.startswith('an email'):
                problems.append(f'{sha[:7]}: adds an email address outside the allow-list ({path})')
            else:
                problems.append(f'{sha[:7]}: adds {why} ({path})')
        if privacy.wording_scope(path):
            for what, why in privacy.wording_problems(privacy.unquote_review(path, text)):
                problems.append(f'{sha[:7]}: adds {why}: "{what}" ({path})')
    return sorted(set(problems))


def check_outgoing(repo, updates=None):
    problems = []
    for sha in outgoing(repo, updates):
        problems += check_commit(repo, sha)
    return problems


def main():
    repo = os.path.dirname(HERE)
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
