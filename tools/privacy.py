"""What must never be published in this public repository: the patterns, in one place, for
tools/sitecheck.py (every tracked text file) and tools/prepush.py (every line an outgoing commit adds).

- Wording (review findings R1-2 and R2-8): the party, the candidate weeks as the user's, a first-person
  enquiry or plan, and any booking recorded in the first person or impersonally ("is booked for",
  "Booked:", "Reserved the", "booking confirmed", an Airbnb confirmation code). Booking state belongs in
  a private note outside every repository, never in HANDOFF.md. Code and tests (tools/, tests/) hold
  these patterns themselves, so wording is scanned in prose and data only; in review files, quoted
  examples ("..." and `...`) are the reviewer's evidence, not a booking.
- Local paths in every form this machine and others print: Windows (either slash), Git Bash
  (/<drive>/Users/<name>), WSL (/mnt/<drive>/), macOS (/Users/<name>/) and Linux (/home/<name>/).
- Email addresses outside the allow-list, and token- or key-shaped strings.
Standard library only.
"""
import re

I, CS = re.I, 0  # case-insensitive, case-sensitive
WORDING = [
    (r'Email to send', 'an enquiry email drafted for the user', False, I),
    (r'\bWe are looking for\b', 'a first-person enquiry', False, I),
    (r'\bbook all three\b', 'a booking plan rather than options', False, I),
    (r"\byour (?:four |two |target |chosen )?(?:weeks?|windows?|dates|trip)\b", 'second-person travel window', False, I),
    (r"\bafter you'd go\b", 'second-person travel window', False, I),
    (r'\b1 ?(?:to|–|-) ?3 people\b', 'party size', False, I),
    (r'\(possibly 3\)', 'party size', False, I),
    (r'\bweeks of 9 Jan, 16 Jan\b', 'the candidate travel weeks as a list', False, I),
    (r'\bTarget weeks\b', 'the candidate travel weeks as a list', False, I),
    (r'\b(?:I|we) (?:have |just )?(?:booked|reserved)\b', 'a first-person booking', False, I),
    (r'\b(?:our|my) (?:booking|reservation|stay)\b', 'a first-person booking', False, I),
    # a rule that forbids them ("no booking references") is not one
    (r'\b(?:booking|reservation|confirmation) (?:reference|number|code)\b', 'a booking reference', True, I),
    # R2-8: bookings recorded impersonally
    (r'\b(?:is|was|are|were|been|now|got)\s+(?:booked|reserved)\b', 'a stay recorded as booked', False, I),
    (r'^\s*(?:[-*]\s*)?(?:\*\*)?(?:Booked|Reserved|Booking|Reservation)(?:\*\*)?\s*:', 'a booking recorded as a label',
     False, re.M | re.I),
    (r'\b(?:Booked|Reserved)\s*:', 'a booking recorded as a label', False, CS),
    (r'\b(?:[Rr]eserved|[Bb]ooked)\s+(?:the|a|an|it|unit|room|listing|flat|apartment|studio|condo|chalet|cabin)\b',
     'a stay recorded as booked', False, CS),
    (r'\b(?:[Bb]ooking|[Rr]eservation)\s+(?:is\s+|was\s+)?confirmed\b|\bconfirmed\s+(?:booking|reservation)\b',
     'a confirmed booking', False, CS),
    (r'\bHM[A-Z0-9]{8}\b', 'an Airbnb confirmation code', False, CS),
    (r'\b(?:[Uu]ser|[Oo]wner|[Tt]hey|[Hh]e|[Ss]he)\s+(?:has\s+|have\s+|just\s+)?(?:booked|reserved)\b',
     'a stay recorded as booked', False, CS),
]
NEGATED = re.compile(r'\b(?:[Nn]o|[Nn]ever|[Nn]ot|[Ww]ithout)\s+(?:\w+\s+){0,2}$')

LOCAL_PATHS = [
    re.compile(r'\b[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+', re.I),       # Windows, either slash
    re.compile(r'(?<![\w.:/-])/[a-z]/Users/[A-Za-z0-9._-]+'),             # Git Bash: /<drive>/Users/<name>
    re.compile(r'(?<![\w.:/-])/mnt/[a-z]/'),                              # WSL: /mnt/<drive>/
    re.compile(r'(?<![\w.:/-])/Users/[A-Za-z0-9._-]+/'),                  # macOS: /Users/<name>/
    re.compile(r'(?<![\w.:/-])/home/[a-z_][a-z0-9_-]*/'),                 # Linux: /home/<name>/
]
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
EMAIL_ALLOW = {
    # businesses' own published contacts, quoted on the rentals page
    'reservations@nisade.com', 'enquiry@powderlife.com', 'enquiries@japanskiexperience.com',
    # the commit-trailer address required by the workflow
    'noreply@anthropic.com',
}
SECRETS = [
    (re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}'), 'a GitHub token'),
    (re.compile(r'\bgithub_pat_[A-Za-z0-9_]{30,}'), 'a GitHub token'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'an AWS access key'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'a private key'),
    (re.compile(r'\bsk-[A-Za-z0-9]{32,}'), 'an API key'),
]
TEXT_SUFFIXES = ('.html', '.md', '.json', '.tsv', '.txt', '.py', '.sh', '.yml', '.yaml', '.css', '.js', '.spec')


def is_text(path):
    base = path.replace('\\', '/').rsplit('/', 1)[-1]
    return base.endswith(TEXT_SUFFIXES) or base in ('pre-push', '.gitattributes', '.gitignore')


def wording_scope(path):
    """Prose and data are scanned for wording; code and tests hold the patterns themselves."""
    p = path.replace('\\', '/')
    return not (p.startswith(('tools/', 'tests/')) or p.endswith('.py'))


def unquote_review(path, text):
    """In a review file, quoted examples are evidence, not bookings: drop "..." and `...` spans."""
    if re.search(r'(?:^|/)REVIEW[^/]*\.md$', path.replace('\\', '/')):
        text = re.sub(r'`[^`]{0,300}`', ' ', text)  # an inline code span may wrap onto the next line
        text = re.sub(r'"[^"\n]*"|“[^”\n]*”', ' ', text)
    return text


def wording_problems(text):
    """(matched text, why) for every wording pattern the text matches."""
    out = []
    for pat, why, negatable, flags in WORDING:
        for m in re.finditer(pat, text, flags):
            if negatable and NEGATED.search(text[max(0, m.start() - 30):m.start()]):
                continue
            out.append((m.group(0).strip(), why))
    return out


def is_allowed_email(addr):
    a = addr.lower()
    return a in EMAIL_ALLOW or a.endswith('@users.noreply.github.com')


def other_problems(text):
    """(what, why) for local paths, stray email addresses and secrets in any text."""
    out = []
    for pat in LOCAL_PATHS:
        m = pat.search(text)
        if m:
            out.append((m.group(0), 'a local user path'))
    for m in EMAIL.finditer(text):
        if not is_allowed_email(m.group(0)):
            out.append((m.group(0), 'an email address outside the allow-list'))
    for pat, what in SECRETS:
        if pat.search(text):
            out.append(('', f'what looks like {what}'))
    return out
