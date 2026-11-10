# ski-V: verification of ski-rentals-2027

Given: `findings/ski.md` (1 HIGH, 7 MEDIUM, 1 LOW, plus known items). Snapshot SHA
412d997497b9d5fc4cd4fcd12527cebaaa76fea9. Verified 2026-11-10.

GitHub `main` is still 412d997 and all six live pages are byte-identical to the snapshot (curl + `cmp`,
2026-11-10), so nothing below was fixed after the snapshot.

No listing site was requested. Listing evidence is the first-line reviewer's saved copies in `work/ski/` and the
repo's own `data/`. Two WebFetch reads went to Airbnb help-centre articles (2710 and 436, not listings) because the
task named Airbnb's help pages as a source for the tax question; neither answered it. Everything I produced is in
`work/ski-V/` (scripts, downloaded PDFs in their own folders, extracted text).

## Verdict table

| Finding | Their severity | Verdict | My severity | Corrected one-line statement |
|---|---|---|---|---|
| SKI-1 | HIGH | WEAKENED (washer wording UPHELD; price consequence UNVERIFIABLE) | HIGH, narrowed | Two cheaper Hakuba listings ($2,156, $2,231) were dismissed as "not stated in the unit" and their pages say "Free washer – In unit"; their cancellation lines were never read, so "$2,742 is the first in price order" is unsupported, not shown wrong. |
| SKI-2 | MEDIUM | UPHELD on the accommodation-tax bands (primary sources); consumption-tax part UNVERIFIABLE | MEDIUM | Hakuba's tax this winter is ¥400 per person per night at this price (¥900 in January), not ¥500 / ¥1,000: $2,733, not $2,742. Whether Airbnb's displayed total already contains consumption tax was not confirmed by any page I could reach. |
| SKI-3 | MEDIUM | UPHELD | MEDIUM | With the operator's January band starting price (CHF 436) the Zermatt week with two passes is from $3,069 at the site's rate ($3,054 at 10 Nov ECB), not from $2,940; these are still "from" prices. |
| SKI-4 | MEDIUM | WEAKENED | MEDIUM (low end) | "January only" is accurate inside the index's stated January-and-March frame, and the index does link the three-resort page; what is missing is one line on the Telluride card that the same studio is refundable for 20–27 Feb at $2,523 with tax (priced 9 Nov 2026). |
| SKI-5 | MEDIUM | WEAKENED | MEDIUM (low end) | The gap is a property of the source (OnTheSnow resort-reported, 14 recent rows, operating-season window, visible reporting gaps), not a transcription error; Crocker and ZRankings are one dataset, not two; "February is the snowiest month" at Telluride rests on 50 in against 47 in. |
| SKI-6 | MEDIUM | WEAKENED | LOW | The index's El Niño note omits Japan (true), but JMA's own statistics list no significant snowfall signal for the Sea of Japan side in El Niño winters; the cited JMA document is a one-winter forecast for 2023-24 with other drivers. |
| SKI-7 | MEDIUM | UPHELD | MEDIUM | The rentals page's first sentence still says Whistler has qualifying flats at $1,400–2,500; every Whistler row in the 9 Nov recheck is "not offered" except one at $2,710 before tax ($3,144 with tax). Whistler was not searched afresh, so the sentence is unsupported rather than proven false. |
| SKI-8 | MEDIUM | UPHELD | MEDIUM (low end) | Crocker and ZRankings both put Jackson's best period in January and say its steep south-facing terrain suffers in March; Crocker has it at 88% of normal in strong El Niño months. The site's sentence is a lift comparison with Crested Butte and makes no snow claim, so this is an omitted caveat. |

Counts: UPHELD 4 (SKI-2, 3, 7, 8), WEAKENED 4 (SKI-1, 4, 5, 6), REFUTED 0 whole findings, two parts UNVERIFIABLE
(SKI-1 refundability, SKI-2 consumption tax). Sub-claims refuted: SKI-4 "unlinked on another page"; SKI-5 "two
outside sources"; SKI-6 "JMA ties El Niño winters to below-normal snowfall on the Sea of Japan side" as a general
rule; SKI-3's fix "drop 'only the floors are known'".

## Per finding

### SKI-1: WEAKENED (HIGH kept, narrowed)

- Claim: two cheaper listings the Hakuba walk dismissed state an in-unit washer on their own pages, so $2,742 is
  not "the first in price order".
- What would make it false: the saved pages not saying "in unit"; the walk recording a different ground for
  dismissal; the two listings being outside the walk's area; or a cancellation read showing both refund for 24
  hours only (which would leave the published answer standing).
- What I did and saw:
  - Ground of dismissal, from the repo: `data/walks/2026-11-09.json`, walk `hakuba_mar`. Rooms 678032453961510940
    ($2,156, 1.98 km) and 1025746272456071125 ($2,231, 1.81 km) both carry `"washer": "not stated in the unit"`,
    `"washer_read": "amenity list, 9 Nov scripted read (retired; wording not kept)"`. No refund field on either.
    28 of the 29 cheaper rows have that same note; one keeps wording ("9 Nov run: Washer").
  - The saved pages contradict that ground. My own raw scan, not the reviewer's parser
    (`work/ski-V/washer_scan.py`, output `washer_two.out`), of
    `work/ski/airbnb_walks/678032453961510940.html` and `...\1025746272456071125.html` (fetched 10 Nov by the
    reviewer): amenity group "Bedroom and laundry", `"available":true,"title":"Free washer – In unit"` on both. The
    first also carries a highlight "an in-unit washer for longer stays" and lists only "Dryer" as unavailable; the
    second has a "Laundry area" photo stop.
  - The retired script's own rule agrees. `code\.codex-temp\ski-rentals-2027-2026-11-09\tools\cheapest_inunit2.py`
    flags a listing IN-UNIT when a washer amenity title contains "In unit", and stops at the first one. Applied
    without network to the saved copies (`work/ski-V/retired_logic.py`): both rooms flag IN-UNIT, as do the $2,619
    hut and the published pick; five houses at $2,232–2,567 read "Free washer – In building". Had that script read
    today's wording over 0–2 km it would have stopped at $2,156. The raw 9 Nov search file
    (`...\results\hak_0313.tsv` lines 51 and 59) has both rooms priced for the dates. Why they were passed over on
    9 Nov cannot be recovered (no page cache was kept).
  - Refundability: unknown. In both saved pages the booking, policy and cancellation sections are
    `"sectionContentStatus":"NOT_COMPLETE"` with `cancellationPolicies: null`, `structuredDisplayPrice: null`,
    `available: null` (`work/ski-V/ctx.py`). Neither room is in `data/checks/2026-11-09.tsv`
    (`grep` finds them only in the walk file). For scale: of the four Hakuba March listings whose line was read
    on 9 Nov, three refund for 24 hours only and one has a date; across all 33 hand reads, 24 show a date.
  - Exact public wording: index "walking up in price order, the first whose own page puts the washer in the unit
    ($2,619)" and the card "the first listing within 2 km, in price order, with the washer in the unit and free
    cancellation". The first sentence is contradicted by the 10 Nov copies as it stands. The second depends on the
    two unread cancellation lines.
  - Location does not rule either out by the site's own standard (the pick is "a 5-minute drive or a shuttle
    ride"): the cottage's page says Hakuba 47 three minutes by car and "no nearby shuttle stops"; the cabin's page
    says a free ski shuttle stops in front of the house.
- Verdict and corrected statement: washer wording UPHELD independently; "the answer is wrong" UNVERIFIABLE.
  Correct statement: "Two cheaper candidates were dismissed on a ground their own pages contradict and need a hand
  read; the 'first in price order' wording is unsupported until then." If either shows a free-cancellation date,
  lodging and tax becomes about $2,192 or $2,267 (¥400 band, site rate 156), and about $3,011 or $3,086 with two
  valley passes, against the published $2,742 and $3,561. "Hakuba has a refundable week under $3,000" stands
  either way.
- For the owner to read by hand, each with `?check_in=2027-03-13&check_out=2027-03-20&adults=2`: rooms
  678032453961510940 and 1025746272456071125: the total for the dates, the cancellation line under the price (a
  date, or "24 hours"), and that the amenity list still says "Free washer – In unit". Optionally room 4003524
  ($2,232, a detached house, "Free washer – In building").
- The proposed fix keeps the dating rule provided each new read is logged in `data/checks/<date>.tsv` with its
  read date.

### SKI-2: UPHELD on the tax bands; consumption tax UNVERIFIABLE

- Claim: the cost model overstates Hakuba's accommodation tax (¥500 / ¥1,000 against ¥400 / ¥900), the steep page
  still adds about 12% to 13 Japanese rows, and nothing crosses $3,000 unless 10% consumption tax sits on top of
  Airbnb's displayed total.
- What would make it false: the village's rates being ¥500 / ¥1,000 this winter; the band falling elsewhere; or
  Airbnb adding consumption tax at checkout.
- What I did and saw:
  - Primary source for Hakuba: Ministry of Internal Affairs and Communications consent notice dated 30 Sep 2025,
    https://www.soumu.go.jp/main_content/001033236.pdf (saved `work/ski-V/dl_soumu/`, text
    `soumu_001033236.txt`, read 2026-11-10). Village rate per person per night by room charge: ¥6,000–19,999
    ¥150 (¥100 for the first three years); ¥20,000–49,999 ¥350 (¥300); ¥50,000–99,999 ¥850 (¥800); ¥100,000+
    ¥1,850 (¥1,800); under ¥6,000 exempt; in force 1 Jun 2026; covers licensed inns and registered home-sharing.
  - Primary source for Nagano: prefecture council paper,
    https://www.pref.nagano.lg.jp/kankoki/kensei/soshiki/shingikai/ichiran/kanko/documents/sanko4.pdf (saved
    `dl_nagano/`, text `nagano_sanko4.txt`): ¥300, ¥200 for three years from 1 Jun 2026; exemption below ¥6,000
    "素泊まり、税抜き" (room only, before tax); halved in Hakuba and three other municipalities to ¥150, ¥100 while
    the rate is ¥200.
  - So until 31 May 2029 the combined Hakuba figures are ¥200 / ¥400 / ¥900 / ¥1,900, which is the reviewer's
    table, and the site's ¥500 / ¥1,000 are the rates from June 2029. Both secondary sources the reviewer cited
    (snownavi, roomboss) say the same when read directly.
  - Band check (`work/ski-V/recompute.py`): $2,697 at 156 is ¥30,052 per person per night, ¥27,320 before 10%
    tax: the ¥20,000–49,999 band whether or not fees are stripped. $5,605 is ¥56,778 before tax: the ¥900 band.
  - Recomputed Hakuba, lodging priced 9 Nov 2026: ¥5,600 of tax = $36 at the site's 156, giving **$2,733**
    (published $2,742), and $3,552 with two valley passes (published $3,561). At the 10 Nov ECB rate (158.18):
    $2,732 and $3,540. January: $5,686 (published $5,695).
  - Consumption tax: Japan's National Tax Agency, Tax Answer No. 6902 (law as of 1 Apr 2026,
    https://www.nta.go.jp/taxes/shiraberu/taxanswer/shohi/6902.htm) requires a business showing prices to
    consumers to show the tax-inclusive price. That makes a tax-inclusive host price the expected case; it is not
    a statement about Airbnb's checkout. Airbnb help articles 2710 and 436 do not address it. The repo's hand
    reads record only "$2,697 for 7 nights", not a breakdown. If 10% were added to the whole displayed total the
    week would be $2,967 + $36 = $3,003.
  - Known-but-live part confirmed on the steep page: $1,592 → "~$1,790", $1,303 → "~$1,460", $1,089 → "~$1,230"
    (12.0–12.9%), with a tax note that states no Japanese rate. The index adds no consumption tax; the steep page
    adds about 12%. The two pages cannot both be right; every affected row is far below $3,000 either way.
  - Telluride's 17.22% re-read on https://www.telluride.gov/401/Taxes: confirmed.
  - Not re-verified by me: Kutchan 3%, the other North American rates.
- Verdict and corrected statement: UPHELD for the bands and the arithmetic, from primary sources. The size is $9
  on the Hakuba answer. The one question that could move the Japan verdict (is consumption tax inside the
  displayed total) is UNVERIFIABLE without one hand read of the price breakdown on room 4721170.
- On the fix: do not strip the 12% from the 13 steep-page rows before that breakdown is read; those rows are
  September quotes without room IDs and must keep their September date. Any rebuilt table that uses 10 Nov
  exchange rates on 9 Nov lodging quotes has to print both dates.

### SKI-3: UPHELD

- Claim: "from $2,940 with passes" uses the pre-season pass price; the January starting price puts it over $3,000.
- What would make it false: the leaflet showing CHF 384 for 4–24 Jan, or a different exchange rate.
- What I did and saw: fetched the operator's leaflet myself (`work/ski-V/dl_zermatt/`, text
  `zermatt_start_prices.txt`; "April 2026", valid 1 Nov 2026–2 May 2027). Six days, Zermatt: Pre 384 (1–27 Nov,
  19 Apr–2 May), Basic 436 (28 Nov–18 Dec, 4–24 Jan, 8–26 Mar), Peak 488 (19 Dec–3 Jan, 25 Jan–7 Mar, 27 Mar–18
  Apr). One month: 1,118 / 1,270 / 1,422. Season pass 1,850 from 1 Nov, 1,960 from 1 Dec. All marked "ab / from",
  with the day's price left to the operator's calculator. ECB rates from api.frankfurter.dev: 0.82067 CHF on
  10 Nov; 0.812–0.815 on 10–11 Sep against the site's 0.81.
  Arithmetic (`recompute.out`): 9–16 Jan $1,923 + $69 tax + 2 × 436 = **$3,069** at 0.81, **$3,054** at 0.82067;
  published $2,940 reproduces with 384. 6–13 Mar (7 Mar is Peak, 8–12 Mar Basic): $3,817–3,945 at 0.81 against the
  published "from $3,688". Two month passes $3,136–3,511 at 0.81 against the published $2,760, so Täsch in March is
  about $9,415–9,790, still inside 10k.
- Exact wording matters here: the index already says the figure "uses the CHF 384 floor price ... so a January
  week with passes will cost more", and the month page says "every total here with passes is a lower bound". The
  ranking-table cell "from $2,940 Jan" carries no such note. The budget test (lodging and tax, $1,992) is untouched.
- Verdict: UPHELD, MEDIUM. Corrected: "from about $3,069 with two 6-day passes at the January band's starting
  price (operator leaflet dated April 2026, read 10 Nov 2026)".
- On the fix: "drop 'only the floors are known'" is wrong as written. 436 and 488 are also starting prices; say
  the band floors are known and the day's price is not, and date the leaflet.

### SKI-4: WEAKENED

- Claim: the index says Telluride is January only while the site's own page has a refundable late-February week.
- What would make it false: the index framing itself as January and March only; the February week not being
  refundable or under budget; the index pointing to it.
- What I saw: index header, "Priced for two sharing, Saturday to Saturday, in January and March 2027", and the
  sentence sits under "Which week": "Telluride is January only, since both March weeks are its declared peak".
  Inside that frame it is accurate. The index does link the three-resort page (`index.html:84`, "refundable picks
  for Revelstoke, Telluride and Big Sky"), so "unlinked" is wrong; the Telluride card itself does not mention it.
  Three-resort page: "Telluride · 20–27 Feb 2027 ... $2,523 all-in (US$2,152 + 17.22% tax) ... Free cancellation
  before 21 Jan", priced 9 Nov 2026, and its own text says the Gold Hill chutes and Palmyra stay "closed or thin
  on a shallow base". Outside support read directly: Crocker, "March for maximum coverage, preservation, highest
  average snowfall" (bestsnow.net/swconet.htm); ZRankings, the Gold Hill Chutes "may not open until February".
- Verdict: WEAKENED to an omission. The fix must carry the price and its date: "or 20–27 Feb, $2,523 with tax,
  priced 9 Nov 2026, free cancellation before 21 Jan".

### SKI-5: WEAKENED

- Claim: the snow table's averages run 9–43% below two outside sources, mis-rank two resorts and contradict
  "February is the snowiest month".
- What would make it false: the site mis-transcribing its source; the outside figures measuring something else.
- What I saw (all read 2026-11-10):
  - OnTheSnow read directly: Telluride 206 in, Revelstoke 257 in, Big Sky 265 in. The site transcribed correctly
    and labels them "OnTheSnow resort-reported historical averages ... not town weather-station numbers" with read
    dates. Each series has 14 rows from 2012-13. It is erratic: Big Sky shows 72 in for 2019-20 and 466 in for
    2013-14; April and November are thin because reporting follows the operating season.
  - Crocker's tables downloaded and parsed (`work/ski-V/web/`, `tabletext.py`): Telluride 273 at 11,170 ft, Big
    Sky 289 at 8,920 ft, Revelstoke 368 at 6,429 ft, Jackson 367 at 8,250 ft, season totals at a named
    mid-mountain site, 37–59 seasons where the ENSO page gives a count.
  - ZRankings' snow page gives Revelstoke 367 "measured at 6,429'" and Jackson 368 at 8,250': the same sites and
    values as Crocker. Treat them as one dataset.
  - Telluride by month on OnTheSnow: February 50 in, March 47 in.
- Verdict: the gap is definitional and a matter of source quality (window, period, reporting gaps), not an error
  in the site's handling. It still matters to a reader, because the cards show Big Sky above Revelstoke while the
  page's own heading says "Revelstoke: deepest snow", and the long record has Revelstoke 27% ahead. No sentence on
  the page ranks the resorts by these numbers, and the choice of weeks survives. "February is the snowiest month"
  should read "February and March are about level in OnTheSnow's 2012–26 series; a longer record puts March first".

### SKI-6: WEAKENED

- Claim: the El Niño note omits Japan, and JMA ties El Niño winters to warmth and less snow on the Sea of Japan side.
- What would make it false: JMA's statistics showing no such signal; the cited document being about one winter.
- What I saw:
  - NOAA CPC live discussion, curl with a plain descriptive identifier, one request (`work/ski-V/noaa/`): "El Niño
    Advisory"; "a strong-to-very strong El Niño likely through January-March 2027 (remaining greater than an 83%
    chance)"; still the 8 Oct text, next issue 12 Nov. The site quotes it exactly. (`data/readings.tsv` saying the
    live page "was replaced by the 12 Nov 2026 discussion" is ahead of the facts, as R2-13 says.)
  - JMA's statistical page on El Niño winters, 1947/48–2020/21
    (https://www.data.jma.go.jp/cpd/data/elnino/learning/tenkou/nihon1.html, `web/jma_nihon1.html`): the
    significant winter tendencies are temperature normal-or-high in western Japan, more precipitation on the
    Pacific side of eastern Japan, less sunshine on the Pacific side. Nothing significant for the Sea of Japan
    side, and snowfall is not an element it reports.
  - The reviewer's quotes from the EASCOF 2023 PDF are accurate, but it is JMA's forecast for winter 2023-24 and
    names El Niño, a positive Indian Ocean Dipole pattern and the warming trend together.
  - This winter: JMA Tokyo Climate Center monthly discussion No. 152, 22 Oct 2026 (`dl_jma/`): El Niño "strongest
    intensity on record since this September", "virtually certain (100%) to continue until boreal winter"; for
    Dec–Feb the model has warm 850-hPa anomalies over nearly the whole hemisphere and the Aleutian Low weaker in
    its western part. That leans warm with a weaker winter monsoon, but the paper says it is not an official
    forecast for any country. JMA's own cold-season outlook for Japan is script-rendered and I could not read it.
- Verdict: the omission is real and small; the general rule the reviewer attached to it is not what JMA's
  statistics say. The proposed line "Hokkaido is the less exposed side in an El Niño winter" should not be
  published on this evidence. A dated pointer to JMA's 2026-27 outlook is the supportable fix.

### SKI-7: UPHELD

- Claim: the rentals page's lede still says Whistler has qualifying flats at $1,400–2,500.
- What would make it false: another Whistler listing in the 9 Nov recheck still bookable under budget.
- What I saw: lede and heading as quoted by the reviewer. `data/recheck/2026-11-09.tsv`: every Whistler row is
  NOT_OFFERED except Cascade Lodge 9–16 Jan at $2,710, which is $3,144 at 16%. The page is headed "Researched
  10 Sep 2026 (listings rechecked 9 Nov 2026)" and each card carries its dated recheck line, so the contradiction
  is between the page's first sentence and its own cards. Whistler was not searched afresh (HANDOFF says so).
- Verdict: UPHELD, MEDIUM. The rewritten lede must say "as of 9 Nov 2026" and that Whistler was not re-searched.

### SKI-8: UPHELD

- Claim: Jackson is offered as the March substitute; outside records call it a January mountain hurt by El Niño.
- What would make it false: the sources not saying so, or the site making a different claim.
- What I saw: Crocker (`web/nrocnet.htm`): "January/early February for snowfall and to avoid warm weather
  exposures"; "In March steep ungroomed runs like the south-facing Hobacks will turn into cement"; exposure 10%
  north, 60% east, 30% south. `web/La_Nina.htm`: Jackson 88% of normal in strong El Niño months over 59 seasons,
  listed under "Strongly favored by La Nina"; the Snoqualmie, Jackson and Sunshine sentence is as quoted.
  ZRankings Jackson page: "January is the best month", "-11% snow in El Niño winters", "By March the exposure is a
  serious issue". The two sources share data, so this is one line of evidence, well documented.
  Site wording: "March substitute: Jackson, not Crested Butte ... Jackson in March runs to 11 April and ranks
  second in the United States". It is an argument about lifts and queues against Crested Butte and says nothing
  about snow. The Jackson cost row has no current listing ("removed from Airbnb by 9 Nov; Jackson was not
  searched afresh").
- Verdict: UPHELD as an omitted caveat. On the fix: "present Jackson as the January alternative" cannot carry a
  price, because the site has no dated Jackson quote; and Big Sky, the suggested March pointer, is itself 91% in
  strong El Niño months on the same table.

### SKI-9 (LOW), one check only

- The site labels its rates "10 to 11 Sep 2026". ECB for those days: JPY 154.18 and 154.04 against the site's 156;
  CHF, EUR and CAD agree to two figures. Confirmed, LOW, correctly graded.

## Us against the outside work

| Question | Ours | Theirs (who) | Do definitions match | Who is more correct, and why |
|---|---|---|---|---|
| Hakuba accommodation tax, winter 2026-27 | ¥500 / ¥1,000 per person per night, "from hotel notices" | ¥400 / ¥900 at these price bands (MIC consent notice 30 Sep 2025 plus Nagano prefecture paper) | Yes | Theirs. Ours are the rates that start in June 2029. Effect: $9 on the answer. |
| Zermatt 6-day pass, 9–16 Jan | from CHF 384 | from CHF 436 (operator leaflet, April 2026) | Yes | Theirs. 384 applies 1–27 Nov and 19 Apr–2 May only, which our page says in words while still printing $2,940. |
| Annual snowfall, three resorts | 257 / 206 / 265 in (OnTheSnow, 2012–26, resort-reported) | 368 / 273 / 289 in (Crocker; ZRankings repeats it) | No: different window, period and measuring site | Crocker for "how much snow and who gets most": longer record at a fixed site. Ours is a fair copy of a weaker source. |
| Telluride's snowiest month | February | March (Crocker) | Partly: 14 recent rows against a long record | Neither firmly; OnTheSnow has 50 in against 47 in. |
| Telluride in El Niño | "neutral to favourable" | 104% of normal in strong El Niño months (Crocker); +4% (ZRankings) | Yes | Agree; "neutral" is the better word. |
| Jackson in March of an El Niño winter | "March substitute" on lift grounds | Best in January; 88% in strong El Niño months; south-facing steeps suffer in March (Crocker, ZRankings) | Different questions: lifts against snow | Theirs on snow. Ours is not wrong on lifts but leaves this out. |
| ENSO state | El Niño Advisory, strong to very strong, over 83% through Jan–Mar | Same text (NOAA CPC, 8 Oct 2026, live 10 Nov) | Yes | Agree, verbatim. |
| Japan in an El Niño winter | silent on the index | No significant Sea of Japan signal in JMA's 1948–2021 statistics; this winter's model guidance leans warm | n/a | No basis yet for a strong statement either way. |

## Fix first

1. Read rooms 678032453961510940 and 1025746272456071125 by hand for 13–20 March (total, cancellation line, washer
   wording), log them with the date, and until then change "the first listing in price order" to wording that
   says two cheaper in-unit candidates are unread.
2. Read the price breakdown on room 4721170 once to settle whether any tax is added to Airbnb's displayed total in
   Japan, then set Hakuba's tax to ¥400 (¥900 in January) with the ministry notice as the dated source and make
   the steep page and the index use one treatment.
3. Replace "from $2,940" for the Zermatt January week with the January band's starting price (about $3,069, leaflet
   dated April 2026), and rewrite the rentals page's first sentence and North America heading from the 9 Nov rows.

## What the published work gets right

- "Hakuba has a refundable week under $3,000 on lodging and tax" survives every tax reading except 10% added to
  the whole displayed total, where it lands at $3,003.
- Every cost-table figure I recomputed from the site's inputs reproduces to the dollar (Hakuba $2,742 and $3,561,
  Zermatt $1,992, $2,940 and $3,688, month passes $2,760).
- Telluride's 17.22% matches the town's page; the NOAA sentence is quoted verbatim and is still the live text.
- OnTheSnow's figures are transcribed correctly, labelled as resort-reported and dated.
- The Zermatt pass floor is disclosed as a floor, with the dates it applies, in the index text and the cost table.
- The published pick (4721170) and the $2,619 hut both read "Free washer – In unit" in the saved copies, and the
  pick's refund line was pasted from the page into `data/checks`.

## Not checked

- Anything that needs a live listing page: prices, availability and cancellation lines, including the two in SKI-1.
- Kutchan's 3%, and the Utah, Wyoming, New Mexico, Quebec and British Columbia town rates.
- JMA's official cold-season outlook for Japan (script-rendered).
- ZRankings' Big Sky and Revelstoke resort pages (the snow page and Crocker's tables were enough).
- The Engelberg and Zermatt walks beyond what the reviewer reported.
