# ski-rentals-2027 handoff

Rewritten **2026-11-21** (Claude Code). Read `CLAUDE.md` first for the rules.
**Rewrite this file at the end of every session, never append.** Under 150 lines.

## State

Published at https://samueljwebber.github.io/ski-rentals-2027/ : six pages, **public repo**. The pages are a
**snapshot of 9 November 2026 that nobody maintains**, and since 2026-11-21 every page says so in a line above its
title. Nothing has been rechecked since 9 November. The first refund cutoff the pages quote is 10 December 2026.

An independent review was filed on 2026-11-10 (`REVIEW.md`, top table; `reviews/fable-2026-11-10/`). On 2026-11-21
one finding was fixed (SKI-3, the Zermatt week with passes: from $3,069, not from $2,940) and the snapshot line was
added. The other seven are deferred, with the reason for each in `REVIEW.md` under "Status of each finding".

124 tests pass (`python -m unittest discover -s tests`) and `python tools/sitecheck.py` is clean (20 checks).

## Next, in order

1. **SKI-1 is the one that could change a recommendation.** Two cheaper Hakuba listings (rooms 678032453961510940
   and 1025746272456071125, 13-20 March) were dismissed for a washer their own pages say is in the unit. Read both
   by hand in the browser pane (total, cancellation line, washer wording), log them in `data/checks/<date>.tsv`,
   and correct the Hakuba card either way. No script may fetch Airbnb.
2. If the pages are ever to be current again, rerun the hand recheck of the listings that drive a recommendation
   and change the snapshot line's date. If not, leave them; the line says what they are.
3. The Zermatt month page still prices month passes at the pre-season CHF 1,118 (March bands: 1,270 to 1,422).
4. SKI-2, 4, 5, 6, 7, 8: one sentence or one figure each (`REVIEW.md`).

## Unverified

- The Zermatt band prices (CHF 384 / 436 / 488 for six days) come from the review's read of the operator's leaflet on
  10 Nov 2026. On 21 Nov the operator's ticket pages answered 404 to a plain fetch, so they were not re-read here.
- The pushed pages were not opened on the live site by this session until after the push; see the session report.

## How the pages are built now

- `data/costs.json` → `python tools/costs.py`: every week-for-two figure (lodging + tax + two 6-day passes, food
  left out) on the index cards, ranking table and cost table, the Europe verdict, the Hakuba card and the README.
  Figures sit in `data-cost` elements; edit the data and rerun, never the figure.
- `data/recheck/<date>.json` + `.tsv` (plus `zermatt-fresh-<date>.html` and `data/booking/<date>.tsv`) →
  `python tools/recheck.py`: the four recheck sections, header lines, nav links, the Zermatt banner and the dated
  status line on every listing a page cites. Each piece prints its own read date; blocks sit between markers.
- `data/checks/<date>.tsv`: listing pages read by hand (price, cancellation line). `data/readings.tsv`: dated
  snapshot of the CPC, SNOTEL and BC Hydro readings. `tools/listing_status.py`: the status rules.
- `python tools/sitecheck.py` (19 checks) and `python -m unittest discover -s tests` (68 tests), standard library,
  no network. Each finding's test also runs on the reviewed commit 20cb727 from git history and must fail there.
- `sh tools/install-hooks.sh` installs the pre-push hook (done in this clone): noreply emails only, no local
  paths or tokens, all checks green. When correcting a fact, add its old wording to `STALE_FACTS` in sitecheck.

## Recheck method from now on (review finding R1-13)

- **Only the listings that drive a recommendation**, each opened in the built-in browser pane at human pace on the
  listing page itself, dates in the address (`/rooms/<id>?check_in=...&check_out=...&adults=2`). With the pane
  hidden, take a screenshot before and between scrolls so lazy sections draw, then read the text. Log every read
  in `data/checks/<date>.tsv`.
- **No scripted scraping and no browser disguise.** Stop at the first HTTP 429, challenge or CAPTCHA, record it,
  and do not retry or route around it. Booking.com only in the browser pane, as an ordinary visitor.
- **The 9 Nov scripts are retired.** search.py, recheck.py, recheck2.py, verify.py and cheapest_inunit*.py sent a
  browser User-Agent while fetching hundreds of Airbnb pages over plain HTTP; they are not to be run again. They
  and the raw TSVs stay in `.codex-temp\ski-rentals-2027-2026-11-09\` under the machine's `code` folder.
- **Official sources** (CPC, NRCS, BC Hydro, municipal pages) are fetched with an honest project identifier,
  never a browser User-Agent.

## What is true now (9 Nov 2026)

- **Engelberg**, 9–16 Jan: $1,626–1,649 lodging and tourist tax, $2,303–2,612 with two 6-day passes, from a flat
  with the washer in the unit (1267557874578220140, $1,571, free cancellation before 4 Jan; no smoke or CO alarm).
- **Telluride**, 23–30 Jan: $2,014–2,259 lodging and 17.22% tax (29856063 at $1,718, 15395305 at $1,927, both free
  cancellation before 24 Dec); $5,017–5,262 with two 6-day tickets. Epic covers the lifts.
- **Hakuba**, 13–20 Mar: $2,742 lodging and tax (4721170, $2,697, washer in the unit, free cancellation before
  11 Feb), a 5-minute drive or a shuttle from the lifts; walk logged in data/walks. January from $5,605.
- **Zermatt**: a January week fits on lodging and tax ($1,992); with two passes it is from $3,069 (CHF 436 each,
  the January band's starting price). March from $3,817 to $3,945. Season pass CHF 1,850 from 1 Nov, 1,960 from 1 Dec.
- **Recheck**: 158 listing-weeks identified by room ID: 66 bookable, 88 not offered, 4 removed (3 listings). The
  steep page has 26 more priced listings without a room ID (every Japanese one), not rechecked. Of the 66 bookable,
  15 state a free washer in the unit and 29 a building or paid one (27 in the building, 2 paid in the unit).
- **Whistler**: the only September listing still offered is $3,144 with tax (9–16 Jan); not searched afresh.
- **Fernie has a gym**: Evolution Health & Fitness, 1192 8th Ave, day passes (its own site, read 9 Nov).

## Needs the user

- R1-5. **Decided 2026-11-22: no history rewrite** (the owner said "make the decision and do it"). 15 commits here
  carry a personal address, none since 2026-10-02; the repo has no forks. A rewrite would not remove the address
  from GitHub (old commits stay reachable by hash until GitHub Support purges them, and public push-event archives
  keep author addresses), and it would change every commit hash these review and handoff files cite and break every
  clone and the scheduled jobs' pushes. The leak is already stopped: every commit since uses the noreply address,
  held by the hook and tests. Reverse by running `git filter-repo --mailmap` and force-pushing; nothing done today
  prevents it. One account setting would also stop it at the source and is the owner's own: GitHub Settings, Emails,
  "Keep my email addresses private" and "Block command line pushes that expose my email".

## Rules that matter here

- Hand reading only for Airbnb and Booking.com, at human pace, in the browser pane. Stop at the first 429, challenge
  or CAPTCHA. The 9 Nov scripts are retired and must not be run.
- Every price carries its currency and the date it was quoted. Figures come from `data/costs.json` through
  `python tools/costs.py`; edit the data, never the figure. When a fact is corrected, add its old wording to
  `STALE_FACTS` in `tools/sitecheck.py`.
- The pre-push hook runs the checks and refuses commits with a non-noreply email, a local path or a token.
