# Review round 1 (2026-11-09)

Adversarial review of the published site as of commit 20cb727. No page was changed by this review. Line
numbers are source lines in the named file. "Scratch folder" means the folder HANDOFF.md names for the
9 Nov scripts and raw TSVs (not in git).

**Counts: 4 HIGH, 9 MEDIUM, 6 LOW.** Round 1 fix pass (9 Nov 2026): 18 fixed, 1 deferred (R1-5, the history rewrite), 0 rejected. No earlier REVIEW.md existed, so no previous fixes needed rechecking.

How it was checked: the repo has no test suite (static HTML), so the "main commands" are the scratch-folder
scripts. I ran them against a scratch copy of the pages. I re-derived figures from raw sources: the
Telluride tax page, NRCS SNOTEL, BC Hydro, NOAA CPC, Ikon's destination list and operator pages, plus four
Airbnb listings viewed in the browser pane at human pace. Government sources were fetched with an honest
project User-Agent, never a browser one.

---

## HIGH

### R1-1 · HIGH · Two of the three headline answers carry prices the 9 Nov data no longer supports

On the project's own 9 Nov data, neither the Europe answer nor the Japan answer fits $3,000 for two once the
brief's in-unit washer is required. Hakuba in January does not fit even without the washer.

**Evidence**
- **Engelberg.** `index.html:120`, `README.md:13` and `alps-extreme-ski-2027.html:89` still say $2,350–2,750
  "including lodging, pass and food", built on the $914 flat. That flat's washer is now "Paid washer – In
  building" (`alps:416-419`, `index.html:77`). The cheapest flat within 1.5 km with a washer in the flat is
  $1,571 (`index.html:75`); raw row in `eng_0109.tsv` is `1267557874578220140  1571.00  1.48 km`, with 19 cheaper
  results inside 1.5 km. Swapping $1,571 for $914 adds $657, which moves the range to about $3,007–3,407.
- **Hakuba.** `index.html:148,151`, `README.md:15` and `steep-and-town-2027.html:88,168` say $1,950–2,600
  including two $410 passes, "January or March". The 9 Nov raw search tells a different story:
  - **9–16 Jan:** `awk -F'\t' 'NR>1 && $5+0<2' hak_0109.tsv | sort -n | head -1` gives
    `2849.08  1.08 km  1725760259808478894`. The cheapest washer-filtered listing within 2 km of Happo/Echoland
    is $2,849 before tax, which is at least $3,669 with two passes. The first listing whose own page puts the
    washer in the unit is $5,605 (28161342).
  - **13–20 Mar:** the first stated in-unit washer is $2,618 (15857739, 1.33 km), at least $3,438 with
    passes. Only the filter-only result ($1,592, a bare "Washer") fits, and `index.html:268` calls that filter
    unreliable.
- No September Hakuba listing behind the range has a room ID on the page (`steep:336,379-382`), so none was
  rechecked (R1-8).

**Fix:** recompute both answers from 9 Nov listings that meet the brief (washer stated in the unit,
refundable), and show the arithmetic in the card: lodging + tax + two passes (+ food if kept). Then either
say plainly that Engelberg now lands at about $3,000–3,400 and that Hakuba in January is out of budget, or
replace those answers. Change these together: `README.md:13-15`, `index.html:120,148,151,238,240`, `alps:89`,
`steep:78-88,168`.

**Verify:** every headline range on the pages and in the README reproduces from a listed 9 Nov row plus the
stated pass and tax figures. `grep -n "2,350–2,750\|1,950–2,600\|1,950 incl" *.html README.md` should return
only lines that carry a date and a derivation.

Status: Fixed in f5c1aa9 (Zermatt floor price added in 62866e5). Every week-for-two figure now comes from data/costs.json through tools/costs.py, each part sourced in a cost table on the index; Engelberg $2,303–2,612 with a washer in the flat (food left out everywhere), Telluride $2,014–2,259 lodging and tax and $5,017–5,262 with tickets, Hakuba with no refundable week under budget. Test: R1_1_HeadlineCosts in tests/test_findings.py fails on 20cb727; tests/test_costs.py covers the arithmetic.

### R1-2 · HIGH · The public site gives out the travel windows, the party and an enquiry draft, and tells readers to book specific units

If the three-resort picks are booked as the page advises, anyone reading this public site can tell which
linked Airbnb unit the account owner will be in, and on which dates. CLAUDE.md says the repo is public and
holds no personal details, and this repo's rule is never to publish travel dates, bookings, addresses or
companions.

**Evidence**
- **Candidate weeks and party size:** `README.md:3`, `index.html:66`, `alps:65`, `steep:63` and
  `ski-rentals:68`. Second-person framing ("your four weeks", "your target windows") at `alps:72,102,281`.
- **First-person enquiry email:** `zermatt-month-stay-2026-27.html:251-269` gives preferred month windows,
  party size and a budget, and is addressed to four agencies.
- **A plan rather than options:** `three-resorts-best-snow-2027.html:105` says "That leaves room to book all
  three now, watch the bases … and drop the weakest", beside one named, linked unit per week (`:151-180`).

**Fix:**
- Delete the enquiry-email block and keep it in a private note outside any repo.
- Replace party-size and second-person phrasing with neutral wording such as "priced for Saturday-to-Saturday
  weeks in January and March 2027". Keep the dates on price rows, because every price needs one.
- Reword `three-resorts:105` as options, not a plan.
- Add a CLAUDE.md hard line: a unit the user books is never identifiable on the public site. Remove or
  anonymise that row the day it is booked.

Whether to publish the candidate weeks at all is the user's decision, and git history keeps the old text
unless it is rewritten.

**Verify:** `grep -n "Email to send\|your four weeks\|your target\|book all three" *.html README.md` returns
nothing, and no page names the party size.

Status: Fixed in 5d162d5. Party size, candidate-week lists, second-person trip framing, the enquiry email and "book all three now" are gone; dates stay on price rows. The suggested CLAUDE.md hard line is not added, because an agent cannot authorize a CLAUDE.md change; the rule is in HANDOFF.md and the privacy check enforces the wording. Test: R1_2_Privacy fails on 20cb727.

### R1-3 · HIGH · The "Week for two" comparison mixes four different cost definitions

The ranking table and README make Telluride (≈$2,200) look cheaper than Engelberg ($2,350–2,750). But
Telluride's figure is lodging plus tax only, while Engelberg's includes two lift passes and food. Add
Telluride's own ticket price (regular 6-day $1,430 each, `steep:250`) and Telluride comes to about $5,060 for
two before food.

**Evidence:** every row below sits under a "Week for two" header (`index.html:236`, `README.md:11`).

| Resort | Figure | What it covers |
|---|---|---|
| Engelberg (`index.html:120`) | $2,350–2,750 | lodging + pass + food |
| Telluride (`index.html:136`, `README:14`) | ≈$2,200 | lodging + tax ($1,877 × 1.1722) |
| Hakuba (`index.html:151`) | $1,950–2,600 | lodging + two passes, no food |
| Whistler (`index.html:165`) | | lodging + 16% tax, no passes |
| Jackson (`index.html:243`) | ≈$1,949 | lodging + tax ($1,725 × 1.13) |
| Zermatt (`index.html:242`) | $1,750–2,900 | lodging $1,268–2,435 + **one** $480 pass |

`steep:74` puts the same Zermatt week for two people at $2,300–3,400.

**Fix:** use one definition everywhere: lodging + tax + two 6-day passes, with food either left out or
included everywhere. Show each component. Where passes come from Epic or Ikon, put the pass in its own
column rather than silently leaving it out. Count two passes for Zermatt.

**Verify:** every "Week for two" cell splits into the same parts, and a note under the table states the
definition.

Status: Fixed in f5c1aa9. One definition (lodging + tax + two 6-day passes, food left out), the parts in their own columns, and the definition stated under the ranking table and the README table. Test: R1_3_CostDefinitions fails on 20cb727.

### R1-4 · HIGH · The documented refresh crashes on the next real run, and would mis-date every price if it ran

HANDOFF "Next 3" tells the next session to rerun the pipeline:
`recheck.py → make_tight_spec.py → recheck2.py → gen_sections.py → insert_sections.py`. The scripts live in
the scratch folder.

**Evidence**
- **The crash.** `insert_sections.py:48` replaces `'Built 10 Sep 2026 · '` through `once()`, which asserts that
  the old string occurs exactly once. The first run removed that string, so any rerun whose Europe count
  differs from 23 of 44 fails. I reproduced it on a scratch copy of the four pages with stub snippets (Europe
  at 20 of 44): `python -I insert_sections.py <copy> <gen>` raised `AssertionError: Built 10 Sep 2026 ·` and
  exited 1 before writing any page. With the count left at 23, the same run succeeds.
- **Hard-coded dates.** `gen_sections.py:136-142` hard-codes "Rechecked 9 November 2026", "looked up again on
  9 Nov 2026" and the "9 Nov" column headers. `insert_sections.py:47,55,63,69,71` hard-codes "9 Nov 2026" and
  the Zermatt conclusion ("January no longer fits …"). A successful run in January would publish January
  prices under a 9 November label, which breaks CLAUDE.md's rule that every price carries the date it was
  quoted.
- **Stale hotel table.** The Booking.com table is a static snippet (`insert_sections.py:60`,
  `rentals_booking.html`), so a rerun would re-insert the 9 Nov hotel prices into the new section.

**Fix:**
- Take the run date as an argument and build every date string from it.
- Replace the block between the markers by regex instead of asserting exact old strings.
- Generate the Europe header line and the Zermatt banner from `summary.json`.
- Drop the Booking.com snippet unless it was re-read that day.
- Keep the scripts in a versioned place (Bigger improvements 3).

**Verify:** run the pipeline twice on a scratch copy with different summaries and run dates. Both runs
succeed, and every heading shows its own run date.

Status: Fixed in d191655. tools/recheck.py renders all four pages from dated data in the repo, replaces marker blocks by regex, takes every date from the data, and dates the Booking.com and Zermatt pieces independently. On a copy of the reviewed pages the old insert_sections.py still exits 1 with AssertionError on a 20-of-44 rerun; tests/test_recheck.py runs two dated runs with different counts.

---

## MEDIUM

### R1-5 · MEDIUM · A personal email address and a local user path are in the public git history

**Evidence:** `git log --all --format='%ae%n%ce' | sort | uniq -c` shows that 15 commits (5bc2635 … 2eac02b)
carry a personal Gmail address as author and committer. The other 13 use the GitHub noreply address. The
same address appears under two different author names, which links those identities. 2eac02b, authored on
2 Oct, was pushed on 9 Nov with that address (HANDOFF "Choices made"). 868d81c added a full local Windows user
path to HANDOFF.md; 20cb727 removed it from the file but not from history
(`git log --all -p | grep -n 'C:\\Users'`).

**Why MEDIUM and not HIGH:** the address has been public since September, the global git identity is now the
noreply address, and the only complete fix rewrites published history.

**Fix:** the user decides whether to rewrite history (`git filter-repo` with a mailmap to the noreply address,
plus a scrub of 868d81c, then a force-push). That is destructive on a public repo, so it needs an explicit
go-ahead. Meanwhile, set a repo-local `user.email` to the noreply address and add a pre-push hook that
rejects any other author email.

**Verify:** after a rewrite, `git log --all --format='%ae%n%ce' | sort -u` lists only the noreply address.
Before that, the hook rejects a test commit made with another address.

Status: Deferred: rewriting the 15 published commits that carry the personal address, and 868d81c with the local path, needs git filter-repo plus a force-push to this public repo, a destructive change only the owner can approve; it also cannot recall existing clones or GitHub's cached commits. The preventive part is fixed in 0afff08: tools/prepush.py and the pre-push hook reject non-noreply author or committer emails, local user paths and token-shaped strings, and this clone's identity is pinned to the noreply address (tests/test_prepush.py).

### R1-6 · MEDIUM · The St Anton currency error survives on the Europe page, and the recheck measured price changes against it

**Evidence**
- `index.html:227` says the first St Anton pass "quoted the right numbers in the wrong currency", and `alps:428`
  says the September quotes were "as displayed in USD".
- Yet `alps:99,343,525-527` still read "€2,561–7,659 … ($2,971–8,884). It breaks the budget on accommodation
  alone", and `alps:340` says "priced out".
- The recheck used $2,971 as the September quote (`alps:409`; `sept.tsv` row
  `1455513831165257651 2027-01-09 2971`) and reports "−$512 (−17%)". Against the USD figure the change is
  −$102 (−4%), in line with most European rows.
- Corrections 4e16970 and f2c46f4 touched `index.html` only (`git show --stat`).
- The same pass labelled the Argentière rows (`alps:391-392`, "−19%" for both weeks) and Sadama in January
  (`alps:411`, "+10%") in euros. Those changes are probably wrong in the same way.

**Fix:** relabel the September St Anton, Argentière and Sadama quotes as USD. Drop "breaks the budget on
accommodation alone": per the index, the washer plus a €468 pass is what breaks it. Retitle rank 9, and
recompute those Change cells or mark them "September currency uncertain".

**Verify:** `grep -n "2,971\|€2,561\|priced out\|Cut from contention" alps-extreme-ski-2027.html` returns
nothing, and St Anton's Change cell reads −$102 (−4%).

Status: Fixed in cb1478c. The September St Anton, Argentière and Sadama figures are the US dollars Airbnb displayed; St Anton's change reads −$102 (−4%), Argentière −6%, and "priced out" is replaced by the washer finding. Test: R1_6_CurrencyLabels fails on 20cb727.

### R1-7 · MEDIUM · Corrections made on the index never reached the detailed pages

**Evidence:** each item is a correction the index made, or one on HANDOFF's "do not undo" list.

| Topic | Corrected statement | Uncorrected statement still published |
|---|---|---|
| Fernie gym | `index.html:247,277`: "no gym found"; no commercial gym in any directory | `steep:102,224,338,354` name "Evolution Health & Fitness, 1192 8th Ave — 10,000 sq ft". Commit 28cf0d1 touched `index.html` only. |
| Crested Butte | `index.html:143,246`: "Dropped" | `steep:172` "The March answer"; `steep:412` "the North American March answer". Commit 143871a touched `index.html` only. |
| Revelstoke bus | `three-resorts:239`: about every 30, then 45, minutes | `steep:171,227,364`: "only every 2 hours" |
| Jackson distance | `index.html:225`: "19 to 26 minutes … not 40" | `three-resorts:226`: "Jackson's 40 minutes" |
| Engelberg pass (the recommendation's weakest number) | `index.html:275`: CHF 274 | `alps:170,548,587`: CHF 365–390 estimated |

**Fix:** carry each correction to every page that states the fact (grep before closing a correction), and
add the consistency check in Bigger improvements 1.

**Verify:** `grep -n "Evolution\|March answer\|every 2 h\|40 minutes\|365–390" *.html` returns only lines that
carry the corrected statement.

Status: Fixed in 8b95077. Revelstoke bus, Crested Butte, Jackson distance, Engelberg pass and Fernie distance now read the same everywhere. The Fernie gym went the other way: its own site (read 9 Nov 2026) confirms Evolution Health & Fitness with day passes, so the index's "no gym found" is corrected rather than propagated. Test: R1_7_PropagatedCorrections fails on 20cb727.

### R1-8 · MEDIUM · The recheck says it looked up every September listing, but 26 were skipped and gone picks are still shown as picks

**Evidence**
- **The coverage claim.** `steep:275` says "Every Airbnb listing this page priced in September was looked up
  again". In fact 26 priced Airbnb listings on that page (about 31 listing-weeks) have no room ID and appear
  nowhere in its recheck: an ID-matching parse finds 34 rechecked IDs and 26 unidentified listings. They
  include every Hakuba, Niseko, Myoko, Furano and Rusutsu listing and both Zermatt benchmark units
  (`steep:336,337,348,351-359,364,368,373,379-393`). One of them, SeiSei, is rechecked under its ID on the
  rentals page.
- **What that means.** The "158 listing-weeks" (`index.html:73`) is a subset, and the Japan answer has had no
  9 Nov recheck.
- **Picks shown as current though gone:**
  - Rentals #1 Cascade Lodge, 6–13 Mar (`ski-rentals:81-84`): the recheck at `:157` says "Not offered", and
    on 9 Nov the listing page showed "Those dates are not available".
  - #5 Terrasses d'Eos (`:101`; `:153-154`) and #6 Le Kalinda (`:106`; `:152`): both not offered.
  - Jackson's "≈$1,949" (`index.html:243`, `steep:128,174,331`) rests on Slope Side at Snow King, which the
    recheck lists as "Listing removed" (`steep:307`).

**Fix:**
- Change the recheck wording to "every listing this page identified by room ID", and state how many could not
  be rechecked.
- Put a dated "not offered / removed on 9 Nov" note on each pick card and row the recheck found gone.
- Recompute Jackson or mark it superseded.

**Verify:** every pick whose 9 Nov status is "Not offered" or "Listing removed" carries a visible dated note,
and the recheck intro states the skipped count.

Status: Fixed in 15c16c8. Each recheck says it covers listings identified by room ID and the steep page states the 26 it could not recheck; every listing a page cites outside its recheck table carries a dated status line rendered from the run data (Cascade Lodge, Terrasses d'Eos, Le Kalinda, Slope Side and the rest). Test: R1_8_PickStatus fails on 20cb727.

### R1-9 · MEDIUM · Whistler's "more than six resorts combined" capacity claim is false by the page's own table

**Evidence:** `index.html:168` says Whistler moves "71,761 people an hour, more than Telluride, Hakuba,
Jackson, Crested Butte, Fernie and Revelstoke combined". The same page's table (`index.html:185-199`) gives
those six as 23,800 + 28,500 + 22,530 + 21,177 + 15,114 + 13,000.
`python -c "print(23800+28500+22530+21177+15114+13000)"` returns `124121`; the first three alone exceed
71,761. Row 1 also says "Nothing else comes close as a system", while row 3 (`index.html:187`) gives
St Anton/Arlberg 145,948. The claim has been there since 07f8f08.

**Fix:** replace it with a true comparison, for example "about three times Telluride's ~23,800". Either
explain that raw capacity is not the ranking key, or drop "nothing else comes close".

**Verify:** the sentence's arithmetic holds against the table on the same page.

Status: Fixed in 6717a85. Whistler moves about three times Telluride's ~23,800 and two and a half times Hakuba's 28,500; row 1 says raw capacity is not the ranking key. Test: R1_9_CapacityClaims fails on 20cb727 with the review's 124,121.

### R1-10 · MEDIUM · The Telluride 17.22% tax correction missed two figures

**Evidence**
- `steep:165`: the scorecard still says "Cheapest all-in $2,088 (Jan)". It is unchanged since 2b19b58, no
  listing on the page produces it, and the same page's verdict says $2,200–2,900.
- `steep:348`: "hot tub and deck near the gondola | $1,643 | ~$1,839" equals 1,643 × 1.119, the old 11.9%
  rate. At 17.22% it would be $1,926, and the row has no note like the Valley Floor row's (`steep:350`).
- `steep:149` says "the Telluride rows below are recomputed". The 17.22% rate itself is correct (see Checked
  and solid).

**Fix:** derive the scorecard cell from a listed row, which gives $2,200. Recompute `steep:348` at 17.22%, or
annotate it like `steep:350` if the unit is in Mountain Village.

**Verify:** every Telluride all-in on the page equals the quote × 1.1722, or carries a note saying why not.

Status: Fixed in 85cc978. $1,926 at 17.22% and a scorecard $2,200 from the listed row; tracing the column found seven more cells with no listed source, all now tied to listed all-ins. Test: R1_10_AllInArithmetic recomputes every North American all-in on the page and fails on 20cb727.

### R1-11 · MEDIUM · "February and March still fit" in Zermatt is true only if the 10k excludes skiing

**Evidence:** `index.html:78` and `zermatt:55,82` say February and March "still fit" through the studio
($7,452 and $7,779 on 9 Nov). The page's own method (`zermatt:59,192-205`: two month passes at $2,760, plus
$280–300 for tax and transport) gives $10,492 for February and about $10,845 for March. Both are over 10k
all-in. On that basis only Täsch in March fits ($4,927 + $2,760 + about $1,350 ≈ $9,040). The September text
showed both budget views; the 9 Nov wording dropped the qualifier.

**Fix:** say "fits on lodging alone; with two month passes, only Täsch in March fits (about $9,040)".

**Verify:** every "fits" on the Zermatt page and the index says which budget view it uses.

Status: Fixed in 7d54a6c. February and March fit on lodging alone; with two month passes only Täsch in March fits (about $9,040). 62866e5 adds that the operator charges the "from" pass prices only 1–27 Nov and 19 Apr–2 May, so totals with passes are lower bounds. Test: R1_11_FitQualifiers fails on 20cb727.

### R1-12 · MEDIUM · The recheck script turns a blank or blocked search page into "Not offered"

**Evidence:** in `recheck2.py`, `dated_price` handles a page without `data-deferred-state-0` like this:
`deferred()` returns None, `blocks` and `pag` stay empty, the loop ends after one page with `seen = 0`, and the
function returns `NOT_IN_DATED_SEARCH`. That status is published as "Not offered for these dates". HTTP errors
are handled correctly and become "Not determined"; a 200 response carrying a challenge page or changed markup
is not. Two published rows have `seen = 0`: the Zermatt rows for 1556537260452412398 (December) and
1295138371680887002 (January). In the browser on 9 Nov the first showed "Those dates are not available", so
these two rows are right, but the path is still unguarded for the next run.

**Fix:** when `deferred(html)` is None, or `paginationInfo` is missing on page 0, return an error status that
publishes as "Not determined".

**Verify:** given a saved non-Airbnb HTML page, the function returns an error status, not
`NOT_IN_DATED_SEARCH`.

Status: Fixed in 41ae8e0. tools/listing_status.py returns NOT_DETERMINED for any page it does not recognise, both for listing-page text read in the browser and for saved search pages; a copy of the old logic in tests/test_listing_status.py returns NOT_IN_DATED_SEARCH for a saved non-Airbnb page where the new code does not. The scratch recheck2.py is retired with the scrapers (R1-13) rather than patched outside the repo.

### R1-13 · MEDIUM · The data collection runs against site terms and the working rule on bot walls

**Evidence**
- Every Airbnb script (`search.py:10`, `recheck.py:14`, `recheck2.py:14`, `verify.py:9`,
  `cheapest_inunit*.py:11`) sends a spoofed desktop Chrome User-Agent while fetching hundreds of search and
  listing pages: 196 spec rows, up to 15 search pages each in the tight pass.
- Airbnb's Terms of Service forbid scrapers and other automated collection, and the browser disguise is what
  keeps the client from being identified. robots.txt itself allows the `/s/homes` and `/rooms/<id>` paths
  used; it disallows place-named searches (`/s/*/*`).
- HANDOFF records reading Booking.com in an agent-driven browser after plain HTTP met an AWS WAF challenge.
- `alps:587` records about a dozen attempts on titlis.ch after HTTP 429.
- All of these sit against the working rule never to bypass a bot wall or rate limit.

**Fix:** for future rechecks, read only the listings that drive a recommendation, in the browser pane at
human pace, with no User-Agent spoofing. Stop at the first 429 and record it. Write the changed method into
HANDOFF.

**Verify:** the next HANDOFF's method section names no spoofed User-Agent and no workaround for a WAF
challenge or a 429.

Status: Fixed in 54addcb. README and HANDOFF state the method (only the listings that drive a recommendation, browser pane, human pace, no disguise, stop at the first 429 or challenge) and mark the 9 Nov scripts retired; the 33 listing pages read this session followed it, and titlis.ch's 429 was not retried. Test: R1_13_Method fails on 20cb727 and rejects any browser User-Agent in the repo.

---

## LOW

### R1-14 · LOW · An Ikon correction now reads as if Furano, Shiga Kogen and Myoko are not on Ikon

**Evidence:** 9fc2bdf replaced "Niseko United, Kiroro, Rusutsu and Hakuba are all on Ikon" with "of these,
only Niseko United is on Ikon" (`ski-rentals:346`). "These" now refers to the Hoshino, Lime Resort Myoko, Shin
Furano Prince and Shiga Kogen Prince deals in the same sentence. `index.html:76` repeats it as "Of the
Japanese resorts on the rentals page, only Niseko United is on Ikon". Ikon's live destination list (read
9 Nov) includes Furano Ski Resort, Shiga Kogen Mountain Resort and Myoko Suginohara, and `steep:264` agrees.

**Fix:** on both pages, write "Of Niseko United, Kiroro, Rusutsu and Hakuba, only Niseko United is on Ikon
for 2026-27; Furano, Shiga Kogen and Myoko Suginohara are also on Ikon".

**Verify:** the sentence names its resorts explicitly.

Status: Fixed in 06ed2dd. Both sentences now name Niseko United, Kiroro, Rusutsu and Hakuba, and say Furano, Shiga Kogen and Myoko Suginohara are on Ikon. Test: R1_14_IkonSentence fails on 20cb727.

### R1-15 · LOW · Refund deadlines read as inclusive dates, but Airbnb's cutoff falls before the date

**Evidence:** `three-resorts:105,153,164,174,263,276` and `index.html:75` write "to 21 Jan", "until
21 January" and "refundable to 4 Jan". On 9 Nov the listing pages themselves said "Free cancellation before
January 21" (West Telluride Studio) and "Free cancellation before January 4" (the Chamonix flat). The cutoff
runs in the listing's own time zone, which for Engelberg and Chamonix is Central European Time.

**Fix:** write "free cancellation before 21 Jan (listing's local time)", and in HANDOFF list the day before
each deadline as the action date.

**Verify:** `grep -n "Free cancellation to\|refundable to\|until 2[12] January" *.html` returns nothing.

Status: Fixed in 1be078a. Cutoffs read "before" with the listing's local time, and HANDOFF lists the day before each as the last safe day. Test: R1_15_RefundCutoffs fails on 20cb727.

### R1-16 · LOW · Several dated readings cite links that will soon show different data

**Evidence:** the CPC links at `three-resorts:286` are rolling products. `ensodisc.shtml` is replaced on
12 Nov, and the `lead02` images are replaced on 19 Nov, after which they show the January–March outlook, not
December–February. The SNOTEL link at `:294` is a "last 7 days" window (`/-7,0/`), and BC Hydro's `mtr.txt` is
a rolling file. I could re-derive the 9 Nov values only by building fixed-date queries.

**Fix:** cite fixed-date sources, for example
`https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/590:MT:SNTL%7Cid=%22%22%7Cname/2026-11-09,2026-11-09/SNWD::value`,
and CPC's archived pages. Alternatively, add "the linked page updates; value read 9 Nov".

**Verify:** after 19 Nov each link still shows the cited number, or the text says that it will not.

Status: Fixed in 77577ae. Fixed-date SNOTEL queries (re-fetched 9 Nov: 2, 4 and 3 in) and CPC's archived October discussion replace the rolling links; the CPC images and BC Hydro file are labelled as updating, and data/readings.tsv keeps each value, URL and read date. Test: R1_16_RollingCitations fails on 20cb727.

### R1-17 · LOW · The Telluride gondola's "2am on Friday and Saturday" has no source

**Evidence:** `index.html:139` and `steep:221` say "(2am Fri/Sat)". The cited page (telluride.com, read 9 Nov)
says "Seven days a week - 6:30 a.m. to midnight. Extended Friday and Saturday hours during peak seasons"
with no closing time given. CLAUDE.md requires an unsourceable claim to be cut or marked.

**Fix:** write "6:30am to midnight, with extended Friday and Saturday hours in peak periods (times not
published)".

**Verify:** no unsourced "2am" remains.

Status: Fixed in 06ed2dd. Both pages say extended Friday and Saturday hours in peak periods, times not published. Test: R1_17_GondolaHours fails on 20cb727.

### R1-18 · LOW · Stale dates and expired advice surround the refreshed content

**Evidence**
- `index.html:66` ("Researched 10 to 11 September 2026 … Every price was a live quote on the date researched")
  and `:301` ("Built 11 September 2026") sit on a page that now carries 9 Nov prices.
- `README.md:32` still says prices are from 10–11 September "except the three-resort report".
- `ski-rentals:362` says "re-shop in October" and `:373` says "book Winter Park by 29 Sep".
- `zermatt:182` gives the season pass "from 1,750". The operator's page on 9 Nov lists CHF 1,850 from 1 Nov
  and CHF 1,960 from 1 Dec.

**Fix:** date-stamp both research rounds in the headers, footers and README. Mark expired offers "expired".
Update the season-pass line or date it.

**Verify:** no "live quote" sentence is undated, and no deadline in the past is presented as an action.

Status: Fixed in 62866e5. Both research rounds are dated in the index header and footer and the README, expired offers are marked, and the Zermatt season pass reads CHF 1,850 from 1 Nov and CHF 1,960 from 1 Dec (operator page re-read 9 Nov). Test: R1_18_DatesStamped fails on 20cb727.

### R1-19 · LOW · Small count and arithmetic slips

**Evidence**
- `index.html:73` says "4 listings had been removed", but that is 4 removed listing-weeks from 3 listings: the
  Maison Poluc suite is counted twice.
- HANDOFF says "27 list a building or paid washer". The tables give 27 in the building plus 2 "Paid washer –
  In unit", which makes 29.
- `three-resorts:193-194` show $3,448 and $2,912, but 2,941 × 1.1722 = 3,447.4 and 2,485 × 1.1722 = 2,912.9.
  The $8,286 total inherits the first.
- `ski-rentals:146` shows "−$102", but 3,264 − 3,365 = −101.
- `index.html:142` says "Ranks 6th of 9 here", but the page's own tables put Telluride 10th of 16
  (`:194,239`).
- `three-resorts:111` mentions "a Telluride/Big Sky tie", but Telluride's snowfall peaks in February and Big
  Sky ties December with March.
- `ski-rentals:203` says "then convert CAD at 1.38", which contradicts `:69`. The numbers themselves follow
  `:69`.
- `ski-rentals:270` says "Airbnb totals are all-in", against the 9 Nov finding at `steep:421` that they are
  "total before taxes".
- `steep:63` uses 0.80 CHF per USD; the index and rentals page use 0.81.

**Fix:** correct each in place.

**Verify:** redo each calculation and grep each phrase.

Status: Fixed in 06ed2dd (with d191655 for −$101, 5d162d5 for 0.81 CHF, 15c16c8 for 4 listing-weeks from 3 listings; HANDOFF now says 29). Test: R1_19_SmallSlips fails on 20cb727, including $3,447 and $2,913 from the three-resort arithmetic check.

---

## Bigger improvements (ranked)

1. **An in-repo check script, run before every push.** Stdlib Python with no network access, checking that:
   - every internal anchor resolves;
   - every all-in equals the quote × (1 + the stated rate), within $1;
   - each tax breakdown sums to its stated total;
   - each key fact keeps one canonical value on every page that states it (answers, pass prices,
     capacities, bus frequency, gym verdicts);
   - every dollar figure has a date in the same block.

   This alone would have caught R1-6, R1-7, R1-9, R1-10 and R1-19.
   Status: Done across this round: tools/sitecheck.py (anchors, all-in arithmetic on the steep and three-resort pages, tallies, superseded facts, privacy, dates, rolling citations) plus 68 unittest cases, and a tax-breakdown check that sums each stated total's parts; tools/hooks/pre-push runs it.

2. **One cost model, rendered from one data file.** Each resort gets lodging, tax, passes and optional food as
   separate fields, and the cards, tables and README read from that file. A corrected input then reaches
   every page, which fixes R1-1 and R1-3 for good.
   Status: Done in f5c1aa9: data/costs.json and tools/costs.py feed the answer cards, ranking table, cost table, the Europe verdict, the Hakuba card and the README.

3. **A private, versioned home for the scrapers, specs and raw TSVs**, such as a private companion
   repository, instead of the never-committed scratch folder. Take the run date as a parameter and write each
   run to a dated folder. Today nothing versioned can reproduce the 9 Nov numbers, and one machine clean-up
   loses the method.
   Status: Partly done. Rendering, status rules and the 9 Nov data are versioned in the repo (tools/recheck.py, tools/listing_status.py, data/); the scrapers are retired rather than moved. A private companion repository was not created: this round worked inside this repository only.

4. **Pick status driven by recheck output.** Each pick card would show bookable / not offered / removed, the
   date checked and the cancellation line read, so a stale pick cannot stay on a card.
   Status: Done in 15c16c8: every cited listing carries a dated status line, and the recheck tables have a refund column from data/checks/.

5. **A privacy split.** The research stays public; the shortlist being acted on, enquiry drafts and anything
   booked live in a private document. Back it with a CLAUDE.md rule and a pre-push grep for first-person
   enquiries, "booked" and non-noreply author emails.
   Status: Partly done in 5d162d5, 0afff08 and e6ed699: the privacy check and pre-push hook reject the review's patterns, first-person booking text and non-noreply emails. The CLAUDE.md rule needs the owner, and a private document for the acted-on shortlist was not created.

6. **Fixed-date citations with a small dated snapshot** (value, URL, read date) for each live reading
   (SNOTEL, BC Hydro, CPC, snow reports), so a reader can still audit a figure after its source rolls over.
   Status: Done in 77577ae: fixed-date URLs where they exist and data/readings.tsv for the rest.

7. **A lighter recheck that respects site terms.** Browser-pane reads of the 10–20 listings that drive a
   recommendation, logging date, price, availability and cancellation line, instead of mass searches.
   Status: Done in 54addcb and 41ae8e0: the method is written down, the status rules are tested, and 33 listing pages were read this way on 9 Nov (data/checks/2026-11-09.tsv).

---

## Checked and solid

- **Recheck tallies.** An independent parse of the four recheck tables gives 158 rows: 66 Bookable,
  87 Not offered, 4 Listing removed and 1 Not determined. 15 of the 66 say "Free washer – In unit". A portable
  check reproduces it:
  `sed -n '/recheck:start/,/recheck:end/p' alps-extreme-ski-2027.html steep-and-town-2027.html ski-rentals-2027.html zermatt-month-stay-2026-27.html | grep -oE '>(Bookable|Not offered for these dates|Listing removed|Not determined)<' | sort | uniq -c`
  gives 66 / 4 / 1 / 87. The Change column matches the two quotes in 65 of 66 rows (one $1 slip, R1-19).
- **Telluride 17.22%.** The town tax page (read 9 Nov) lists SMART 1.07, State 2.90, County 1.00, Town 4.50,
  food-and-lodging excise 2.00, short-term-rental excise 2.50, Town lodgers' 2.00 and SMART lodgers' 1.25,
  which sum to 17.22. It also notes the town has no agreement with rental platforms to collect local tax.
- **Snow on 9 Nov, from raw station data via fixed-date queries.** NRCS Lone Mountain 2″, Lizard Head Pass 4″,
  Idarado 3″; BC Hydro Mt Revelstoke 17–18 cm. All match `three-resorts:248-250`.
- **NOAA CPC.**
  - 8 Oct 2026 discussion: El Niño Advisory, "strong-to-very strong … through January-March 2027 (remaining
    greater than an 83% chance)".
  - December–February outlook made 15 Oct: Western Colorado 33.6 above / 33.6 near / 32.7 below;
    South-central Montana 24.0 above / 43.2 below.
  - Next ENSO discussion 12 Nov.

  All match `three-resorts:98-106`.
- **Three-resort arithmetic.** Every all-in equals quote × (1 + rate) to the dollar apart from two $1 slips,
  and the totals of $7,361, $8,286 and $7,750 add up.
- **Live spot checks in the browser pane on 9 Nov.**
  - West Telluride Studio, 20–27 Feb: $2,152, "Free cancellation before January 21", in-unit washer and
    dryer. This matches the pick.
  - Cascade Lodge 6–13 Mar, the two-room Chamonix flat 9–16 Jan and the Täsch "Panoramic Views" unit for
    5 Dec–5 Jan all showed "Those dates are not available", agreeing with "Not offered".
- **Official facts that match the pages:**
  - Big Sky resort tax 4% (resorttax.org).
  - The USFS project page reads "Pre NEPA", decision expected 4/2026, and the CARA notice of a draft decision
    to approve replacing Lifts 7 and 8 is live.
  - Telluride gondola 20 Nov 2026–4 Apr 2027, 6:30am to midnight.
  - Zermatt 6-day pass from CHF 384 and month pass from CHF 1,118.
- **Calendar.** 9 Jan 2027 is a Saturday; MLK Day falls on 18 Jan, Presidents' Day on 15 Feb and Easter on
  28 Mar 2027. Every pick's refund date follows Airbnb's 30-day, 5-day or 1-day tier.
- **Links.**
  - Every internal anchor on the six pages resolves.
  - 71 of the 72 external links outside Airbnb and Booking.com return 200; VRBO returns 429, which
    `zermatt:249` already discloses.
  - The USFS link now redirects (68020 → 301822) to the right project.
- **Publication.** The latest Pages build is "built" at 20cb727. All six live URLs return 200 and match the
  committed files apart from line endings.
- **Secrets.** No version contains API keys, tokens, passwords, cookies or booking codes. The email addresses
  in the page text are businesses' public contacts.
- **Error routing in `recheck2.py`.** HTTP errors become "Not determined", not "Not offered" (but see R1-12
  for the blank-page path).
