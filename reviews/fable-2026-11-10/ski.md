# ski: ski-rentals-2027, internal attack and outside comparison

Snapshot SHA 412d997497b9d5fc4cd4fcd12527cebaaa76fea9, reviewed 2026-11-10 (one reviewer, both jobs).

What I ran (everything is in `<review-scratch>/work\ski\`):
- Fetched the six live pages with curl and compared them with the snapshot: all six identical (`live/`, `text/`).
- `tools/sitecheck.py` (24 checks ok), `python -m unittest discover -s tests` (120 tests OK, 15.5 s),
  `costs.py --check`, `recheck.py --check` (no drift), all single-process in a copy (`repo_copy/`).
- `rebuild_costs.py`: my own rebuild of the cost table from the inputs in `data/costs.json`, at the ECB reference
  rates for 2026-11-10 (1 USD = 0.89174 EUR, 0.82067 CHF, 1.4136 CAD, 158.18 JPY, api.frankfurter.dev) with corrected
  taxes and pass prices. At the site's own rates it reproduces every published cell to the dollar.
- `linkcheck.py`: 73 external links outside Airbnb and Booking.com, one request each.
- `fetch_all.py` / `summarise_listings.py`: the 20 Airbnb listing pages that drive a recommendation, one plain
  request each, 10 s apart, with an honest identifier (robots.txt allows `/rooms/<id>` to generic agents).
  `fetch_walks.py` / `analyse_walks.py`: the 60 listings the logged "price walks" dismissed, same method, 8 s apart.
  In all, 82 plain page requests to Airbnb, every one answered 200 with no challenge. The project's own rule is
  that its rechecks are done by hand in a browser; I am flagging the count so the owner can judge it.
- NOAA CPC read with curl and a plain descriptive identifier (2 requests). Web reads through WebFetch.
- The shared web-search allowance ran out part-way, so several look-ups are listed under Not checked.

## Verdict

1. On its own definition (lodging plus tax) the headline holds: with corrected taxes and today's exchange rates
   every figure the site calls under $3,000 stays under. Engelberg $1,626-1,648, Telluride $2,014-2,259, Hakuba
   $2,732, three-resort picks $2,256 / $2,523 / $2,582. I am confident in the arithmetic and the tax rates.
2. The Hakuba answer is probably not the cheapest one: two cheaper listings the published walk dismissed state a
   free washer in the unit on their own pages today ($2,156 and $2,231 before tax). The "exists under $3,000"
   verdict stands; the $2,742 figure and the "first in price order" wording do not. Engelberg and Zermatt walks hold.
3. The Japanese-tax item runs the other way from how it is described: the cost model slightly overstates Hakuba's
   tax, and 13 rows on the North America and Japan page still add about 12% too much. Hakuba at $2,697 fails only
   if 10% consumption tax is charged on top of Airbnb's displayed total ($3,002); not seen at a price breakdown.
4. Also wrong or overstated: Zermatt "from $2,940 with passes" (the operator's January starting price makes it
   about $3,054); "Telluride is January only"; Jackson as the March substitute; a snow table that expert data
   contradict; no El Niño note for Japan; the rentals page still headlines Whistler.
5. Not verified today: prices, date availability and refund lines. Airbnb loads them by script and browser tools
   were off-limits. What a plain page read shows (listing exists, washer wording, rating) matches on 21 of 21.

## Findings

### SKI-1 [HIGH] [CONFIRMED on the washer wording; PLAUSIBLE on the price] [new] Two cheaper Hakuba listings that the published walk dismissed state "Free washer – In unit" on their own pages; the $2,742 answer is not "the first in price order"

- Where it shows: `index.html` "walking up in price order, the first whose own page puts the washer in the unit
  ($2,619) and the next two refund in full only for 24 hours, and the fourth, a chalet at $2,697"; Hakuba card
  "$2,742 ... the first listing within 2 km, in price order, with the washer in the unit and free cancellation";
  cost table and `data/costs.json:114` ("First listing within 2 km of Happo and Echoland, in the 9 Nov search's
  price order, whose own page puts the washer in the unit ..."); the same sentence on the steep page.
- Evidence: `data/walks/2026-11-09.json`, walk `hakuba_mar`, lists 29 cheaper listings as "washer: not stated in
  the unit", each with `washer_read: "amenity list, 9 Nov scripted read (retired; wording not kept)"`. I re-read
  all 29 pages on 2026-11-10 (`work/ski/airbnb_walks/`, `analyse_walks.py`). Two say otherwise in their own
  amenity lists, group "Bedroom and laundry", `available: true`:
  - room 678032453961510940, "Hakuba Private Cottage | BBQ & Nature", $2,156 in the walk, 1.98 km, 4.93 from 102
    reviews: "Free washer – In unit". Its page puts Hakuba47 three minutes and Goryu five minutes away by car and
    says there are no shuttle stops nearby.
  - room 1025746272456071125, "Pet-Friendly Forest Cabin w/ BBQ Near Echoland", $2,231 in the walk, 1.81 km, 4.76
    from 38 reviews: "Free washer – In unit". Its page describes a free snow shuttle from nearby stops.
  Neither has a row in `data/checks/2026-11-09.tsv`, so neither cancellation line was read. Five more whole
  houses or cabins at $2,232-2,567 say "Free washer – In building", which for a detached house is not the shared
  laundry the rule was written to exclude.
- What it would change: if either has a free-cancellation date, the Japan answer is about $2,191 or $2,266 for
  lodging and tax (5,600 yen of tax), not $2,742, and with two valley passes about $3,000 or $3,075, not $3,561.
  The current pick is itself "a 5-minute drive or a shuttle ride from the lifts", so neither is worse placed.
- Why it matters: this is the failure R2-1 described (a verdict resting on listings nobody opened), surviving in
  its fix: commit 94a1f58 walked on from the $2,619 listing but took every cheaper row's washer status from the
  retired scripted read, whose wording was never kept. The site's first rule is that only the listing page counts.
- How I tried to refute it: (a) parser error: I printed the raw amenity entries for both rooms; the title is
  "Free washer – In unit" and the only "Not included" laundry item is a dryer on the first. (b) Out of area: both
  distances are the walk's own and inside its 2 km. (c) The pages changed overnight: possible, cannot be excluded,
  but two hosts editing the same field in a day is unlikely, and no 9 Nov wording exists to compare. (d) The same
  re-read of the Engelberg walk (19 dismissed listings), Zermatt January (5) and March (7) and Hakuba January (5)
  found none stating "in unit", so the method is not simply over-reading.
- Fix: open those two listings (and the "in building" houses) by hand with the dates, log washer and cancellation
  lines in `data/checks`, and re-run the walk. Keep the amenity wording for every row a walk dismisses, and have
  sitecheck refuse a walk row whose washer status has no stored wording.

### SKI-2 [MEDIUM] [CONFIRMED] [known-but-live] Japanese tax (R2-4) and unconfirmed North American rates, quantified: no "under $3,000" answer crosses the line

- Known-but-live, one line: R2-4 is still open and still public: `steep-and-town-2027.html` adds about 12% to 13
  Japanese Airbnb totals (rows "~$1,790", "~$1,460", "~$1,230", scorecard cells Niseko $1,460, Myoko $1,230,
  Furano $1,460) and `ski-rentals-2027.html` gives Kutchan's tax as 2% in one place and 3% in another and calls
  consumption tax "a 10% accommodation tax".
- Where it shows: index cost table, Hakuba "¥500 per person per night ... $45 ... $2,742"; January "¥1,000 ...
  $5,695"; Niseko "2% ... $37 ... $1,865"; steep page tax note "Kutchan adds a 2% accommodation tax" and "Jackson
  looks closer to 11-12% ... Taos Ski Valley about 14.4% and Park City about 14.6%".
- Evidence, Japan:
  - Hakuba village accommodation tax from 1 Jun 2026, per person per night by room charge before tax: 6,000-19,999
    yen 200; 20,000-49,999 yen 400; 50,000-99,999 yen 900; 100,000+ yen 1,900, Nagano's share included.
    https://www.snownavi.com/en/topics/accommodation-tax-introduced-from-6-1-mon (dated 2 May 2026: "the Nagano
    Prefecture accommodation tax is included in the amounts above") and
    https://docs.roomboss.com/docs/general/financial-and-reporting-tools/price-component/hakuba-bed-tax (same
    table), both read 2026-11-10. Two independent secondary sources; the village ordinance itself was not found.
  - The $2,697 week is 30,472 yen per person per night (27,702 before 10% tax): the 400 yen band, not 500. The
    $5,605 January week is 63,328 yen (57,571 before tax): 900 yen, not 1,000.
  - Kutchan (Niseko Hirafu): "3% of the room rate", with the Hokkaido tax (in force since April 2026) "already
    included in that percentage": https://livejapan.com/en/in-hokkaido/in-pref-hokkaido/in-sapporo_chitose/article-a0005864/
    (updated 6 Apr 2026, secondary). The Niseko listing the cost table uses (room 766838246342060838) states in its
    own description "No Cleaning Fee or Accom Tax to Guests" (page read 2026-11-10), so nothing is added for it.
  - Consumption tax: hosts set a tax-inclusive price and Japan requires tax-inclusive consumer prices, so nothing
    is added to an Airbnb total for it. PLAUSIBLE, not CONFIRMED: Airbnb's help pages I could open do not say it
    in terms, and I could not open a price breakdown. One read of the breakdown popover on room 4721170 settles it.
- Evidence, North America (official pages read 2026-11-10):
  - Telluride 17.22%: https://www.telluride.gov/401/Taxes "The total tax to be collected on short-term rentals is
    17.22%."
  - Montana 4% + 4%: https://revenue.mt.gov/taxes/miscellaneous/lodging-facility ; with Big Sky's 4% resort tax, 12%.
  - British Columbia 8% PST plus up to 3% MRDT, and the taxable price includes cleaning and booking fees:
    https://www2.gov.bc.ca/gov/content/taxes/sales-taxes/pst/publications/accommodation ; with 5% GST, 16% is the
    ceiling. The per-town MRDT map (Whistler, Revelstoke, Fernie) was not opened.
  - Not confirmed on official pages today: Utah, Wyoming, New Mexico, Colorado outside Telluride, Quebec. The site's
    assumptions sit at or above the secondary figures it quotes, and the nearest rows to the line (Park City
    ≈$2,920 at 15%, Tremblant ≈$2,779 at 18.5%) need rates of about 18% and 28% to cross. Quebec's three taxes
    compound to about 19.0% (1.035 x 1.14975) rather than 18.5%; that is from the statutory rates as I know them,
    not re-read today.
  - The model multiplies the rate by Airbnb's whole displayed total, service fee included, so wherever the service
    fee is not taxable it overstates the tax. Every error of this kind is on the safe side.
- Rebuilt table (`rebuild_costs.out`; site figure, then rebuilt at 10 Nov rates and corrected tax):

  | Row | Site lodging + tax | Rebuilt | Site with two passes | Rebuilt | Crosses $3,000? |
  |---|---|---|---|---|---|
  | Engelberg 9-16 Jan | $1,626-1,649 | $1,626-1,648 | $2,303-2,612 | $2,293-2,598 | no |
  | Telluride 23-30 Jan | $2,014-2,259 | $2,014-2,259 | $5,017-5,262 | same | no |
  | Hakuba 13-20 Mar | $2,742 | $2,732 | $3,561 | $3,540 | no (see stress test; a cheaper listing may exist, SKI-1) |
  | Hakuba 9-16 Jan | $5,695 | $5,685 | $6,514 | $6,493 | already over |
  | Zermatt 9-16 Jan | $1,992 | $1,991 | from $2,940 | from $3,054 | with passes: yes (SKI-3) |
  | Zermatt 6-13 Mar | $2,740 | $2,739 | from $3,688 | from $3,802 | already over with passes |
  | Whistler | $3,144 | $3,144 | $4,926-5,361 | $4,884-5,308 | already over |
  | Chamonix | $1,038-1,103 | $1,038-1,100 | $2,199-2,264 | $2,157-2,220 | no |
  | Andermatt | $3,086 | $3,085 | $4,024 | $4,011 | already over |
  | Crested Butte | $1,564 | $1,564 | $3,692 | $3,692 | no |
  | Fernie | $1,414 | $1,414 | $3,023 | $2,984 | lodging no; total dips under on the weaker CAD |
  | Alagna | $954-1,019 | $954-1,016 | $1,815-1,880 | $1,784-1,846 | no |
  | St Anton | $2,540 | $2,537 | $3,629 | $3,587 | no |
  | Snowbird | $3,767 | $3,767 | $5,917-6,347 | same | already over |
  | Les Deux Alpes | $696-761 | $696-758 | $1,456-1,536 | $1,428-1,505 | no |
  | Niseko 13-20 Mar | $1,865 | $1,828 (host absorbs) to $1,883 (3%) | $2,802 | $2,752-2,807 | no |
  | Three-resort picks | $2,256 / $2,523 / $2,582 | same | n/a | n/a | no |

- Hakuba stress test on the $2,697 total: $2,732 with 5,600 yen of accommodation tax; $2,766 if 10% consumption tax
  on Airbnb's service fee is also added; $3,021 under the September +12% rule still used on the steep page; $3,002
  if 10% were charged on the whole displayed total. The margin under the last reading is nil.
- Why it matters: the Japan answer is the only one whose verdict depends on how the tax is read.
- Fix: one Japan tax table in data (Hakuba 200/400/900/1,900 yen bands, Kutchan 3% including Hokkaido, per-listing
  "host absorbs" flag); recompute the 13 steep-page rows without the 12%; read one price breakdown and record it.

### SKI-3 [MEDIUM] [CONFIRMED] [new] Zermatt "from $2,940 with passes" uses a pre-season price; the operator's own January starting price puts the week over $3,000, and the month page's pass line is $335-705 low

- Where it shows: index ranking table "from $2,940 Jan ... March from $3,688"; cost table "from $948 ... from
  $2,940"; `zermatt-month-stay-2026-27.html` "Lift pass, 1 month, adult, Zermatt only | from 1,118 | $1,380",
  "With two month passes ($2,760)", "only Täsch in March fits, at about $9,040"; HANDOFF.md:92 "only the floors
  are known".
- Evidence: the operator's winter 2026/27 leaflet (dated April 2026),
  https://www.matterhornparadise.ch/ZBAG/13-trade/01-downloads/03-prospekte-broschueren/starting-prices-ski-passes-winter-26-27.pdf
  (saved as `pdf/zermatt_prices.pdf`, text extracted with pypdf, 2026-11-10). Starting prices in CHF, Zermatt /
  International: Pre (1-27 Nov, 19 Apr-2 May) 6 days 384 / 432, 1 month 1,118 / 1,215; Basic (28 Nov-18 Dec, 4-24
  Jan, 8-26 Mar) 6 days 436 / 491, 1 month 1,270 / 1,381; Peak (19 Dec-3 Jan, 25 Jan-7 Mar, 27 Mar-18 Apr) 6 days
  488 / 550, 1 month 1,422 / 1,547. Season pass 1,850 from 1 Nov and 1,960 from 1 Dec (the site's figures match).
- Recomputed: 9-16 Jan with two 6-day passes is from $3,069 at the site's rate, $3,054 at today's; 6-13 Mar from
  $3,802-3,929. Two month passes are $3,095 (Basic) to $3,465 (Peak) today against the page's $2,760, so the
  Täsch March month is about $9,375-9,745 rather than $9,040. It still fits 10k; February and January do not get
  closer.
- Why it matters: the ranking table's "Week for two, with passes" column shows Zermatt under $3,000, and the
  correct floor is over. The page does say January "will cost more", and the budget test (lodging and tax, $1,992)
  is unaffected, which is why this is not HIGH.
- How I tried to refute it: checked whether the 9-16 Jan week falls in a cheaper band (it is Basic, 4-24 Jan) and
  whether the leaflet is superseded (it covers 1 Nov 2026-2 May 2027; its Pre-season and season-pass figures equal
  what the site read on the operator's page on 9 Nov).
- Fix: use 436 for January, 436-488 for 6-13 March and 1,270 / 1,422 for month passes; drop "only the floors are
  known".

### SKI-4 [MEDIUM] [CONFIRMED] [new] The index says Telluride is "January only"; the site's own three-resort page has a refundable week in late February in the same flat, and says the steep terrain is better covered then

- Where it shows: `index.html` "North America · January only", "Telluride is January only, since both March weeks
  are its declared peak", ranking verdict "The North American answer, January only".
- Evidence: `three-resorts-best-snow-2027.html`: "Telluride · 20-27 Feb 2027 ... $2,523 all-in (US$2,152 + 17.22%
  tax) ... Free cancellation before 21 Jan", room 29856063, the same studio the index prices for 23-30 Jan. Its
  snow table gives Telluride a 39 in base in January, 50 in February, 61 in March, and says Gold Hill and Palmyra
  are "rocky and stays closed or thin on a shallow base". Tony Crocker's Telluride entry,
  http://bestsnow.net/swconet.htm (read 2026-11-10): best time "March for maximum coverage, preservation, highest
  average snowfall". ZRankings' Telluride page (https://www.zrankings.com/ski-resorts/163-telluride-ski-resort,
  read 2026-11-10): the Gold Hill Chutes "may not open until February" and "March is the best month" for snow
  quality. The index names Gold Hill and Palmyra as the reason to go.
- How I tried to refute it: the index header says it priced January and March only, so "January only" can be read
  as "of those two months". On that reading it is incomplete rather than false, which is why this is MEDIUM.
- Why it matters: terrain is the site's first priority, and the North American answer's week was chosen on price
  between two months, with the better-snow week sitting unlinked on another page.
- Fix: "late January, or 20-27 February for deeper cover; March is over budget", with a link to the three-resort
  page.

### SKI-5 [MEDIUM] [CONFIRMED] [new] The snow table rests on a 13-season resort-reported series; long-run station data are 9-43% higher, rank the three resorts differently, and contradict "February is the snowiest month" at Telluride

- Where it shows: three-resort page "Revelstoke 257″/yr ... Telluride 206″/yr ... Big Sky 265″/yr", "February is
  the snowiest month", "Revelstoke: deepest snow".
- Evidence (all read 2026-11-10): OnTheSnow's Telluride page lists seasons 2012-13 to 2024-25 and an average of
  206 in (the site transcribed it correctly). Crocker's long-run averages: Revelstoke 368 in at 6,429 ft
  (http://bestsnow.net/crocnet.htm), Big Sky 289 in at 8,920 ft (http://bestsnow.net/nrocnet.htm), Telluride 273 in
  at 11,170 ft (http://bestsnow.net/swconet.htm). Ratios 1.43, 1.09 and 1.33. ZRankings' "true snow" agrees with
  Crocker: Revelstoke 367 in, Big Sky 286 in, Telluride 276 in (https://www.zrankings.com/ski-resorts/snow and the
  two resort pages).
- The page's table shows Big Sky snowier than Revelstoke while its heading calls Revelstoke the deepest; on
  Crocker's figures Revelstoke leads Big Sky by 27%, so the heading is right and the table is not.
- The choice of weeks survives: Crocker's best periods are January-February for Revelstoke and "Mid-January to
  mid-March for Lone Peak coverage" at Big Sky. For Telluride he says March, later than either week the site uses.
- Fix: put Crocker's averages beside OnTheSnow's, say what period each covers, and reword the February claim.

### SKI-6 [MEDIUM] [CONFIRMED for the precedent, PLAUSIBLE for 2026-27] [new] The El Niño note covers North America only; Japan's weather agency ties El Niño winters to warmth and below-normal snowfall on the Sea of Japan side, and the Japan answer is mid-March at a 760 m base

- Where it shows: index "A strong El Niño is forecast. NOAA's winter outlook leans dry for southwest Montana and
  near even for southwest Colorado ..." with no line for Japan or the Alps; the Hakuba card and the "Which week"
  section give price as the reason for March. The steep page does say "Hakuba carries the most March risk ... the
  base area gets rain and slush", without linking it to this winter.
- Evidence: NOAA CPC discussion of 8 Oct 2026, still the live text today: "Chances remain high for a historic event
  that would exceed the strength of previous El Niño events dating back to 1950" (`noaa/ensodisc_live.html`). JMA's
  outlook for the last El Niño winter, https://ds.data.jma.go.jp/tcc/tcc/library/EASCOF/2023/5-2.pdf pp. 12 and 14
  (`pdf/jma_eascof2023_5-2.pdf`): Sea of Japan side of eastern Japan 50% below-normal snowfall, 20% above;
  "Above-normal temperatures (60%) and below-normal snowfall amounts (50%) nationwide except for northern Japan."
  Hakuba gets its snow from the same winter monsoon as that zone (JMA's own region for Nagano is Kanto-Koshin, so
  the zone is an analogue, not Hakuba's label); Hokkaido is "northern Japan", where the tilt was weaker.
- What would confirm it for this winter: JMA's 2026-27 cold-season outlook, which I could not locate.
- Fix: add a Japan row to the outlook table; say that Hokkaido is the less exposed side in an El Niño winter and
  that a March week at a 760 m base is the more exposed choice, which pulls against the price argument.

### SKI-7 [MEDIUM] [CONFIRMED] [new] The rentals page still opens by saying Whistler has qualifying apartments at $1,400-2,500; its own 9 Nov recheck shows the top pick gone in March and $3,144 with tax in January

- Where it shows: `ski-rentals-2027.html` first paragraph: "Whistler, Park City's Canyons Village and the French
  Alps each have gym-and-washer apartments ... cancellable for free, at $1,400 to $2,500"; heading "North America:
  Whistler and Canyons Village win on price after tax"; pick 1 "Cascade Lodge ... $2,572 all-in, 6-13 Mar 2027".
- Evidence: the same card: "Rechecked 9 Nov 2026: bookable for 9-16 Jan at $2,710 ...; not offered for 6-13 Mar;
  not offered for 13-20 Mar". $2,710 x 1.16 = $3,144, which the index marks "No: over budget with tax". Of the
  seven top picks and two runners-up, four are "not offered" for every week listed or over budget (Cascade, Flaine,
  Tignes, Deer Luxe).
- Related to R1-8, which added the recheck notes but left the summary sentences.
- Fix: rewrite the lede and the North America heading from the 9 Nov rows; move gone picks out of "Top picks".

### SKI-8 [MEDIUM] [CONFIRMED] [new] Jackson is offered as the March substitute; both expert sources call it a January mountain that suffers in March sun and in El Niño winters

- Where it shows: index "March substitute: Jackson, not Crested Butte ... Jackson in March runs to 11 April and
  ranks second in the United States"; cost table row "Jackson town, 6-13 Mar 2027". The El Niño paragraph names
  Montana, Colorado and British Columbia, not Wyoming.
- Evidence (read 2026-11-10): Crocker, http://bestsnow.net/nrocnet.htm: best time "January/early February for
  snowfall and to avoid warm weather exposures". http://bestsnow.net/La_Nina.htm: Jackson 88% of normal in strong
  El Niño months, in the "strongly favoured by La Niña" group, and "At Snoqualmie, Jackson and Sunshine the top 6
  El Nino seasons through 2010 and 2023-24 were all below average." ZRankings,
  https://www.zrankings.com/ski-resorts/70-jackson-hole: best month January, snowfall about 11% lower in El Niño
  winters, and "Jackson is very unusual for a steep area in having more south than north exposure."
- Why it matters: the site applies this winter's outlook to the three-resort page but not to its own March
  alternative, which is the resort of the group that El Niño hurts most and whose steep faces handle March worst.
- Fix: present Jackson as the January alternative; for March point to Telluride's 20-27 February week or to Big
  Sky's high north-facing terrain, with the El Niño caveat.

### SKI-9 [LOW] [CONFIRMED] [new] Smaller mismatches found while checking

- Index "Snow King ... gets 150 to 200 inches against the big mountain's 458": 458 is the resort's claim; the
  steep page itself says "ZRankings' adjusted figure is 368", and Crocker has 367 in at 8,250 ft (nrocnet.htm).
- Les Deux Alpes row ($680): the listing says "Bed linen and towels are not included" (double set EUR 20, towels EUR 10
  a person) and "There is currently no Wi-Fi in the property"; neither is on the row (page read 2026-11-10).
- Exchange rates: every total is converted at "10 to 11 Sep 2026" rates beside lodging "priced 9 Nov 2026". The
  ECB had the yen at 154.0-154.2 on those days, not 156, and the dollar has since gained 2-4% on the euro, Canadian
  dollar and yen. Largest effect on any total: about $40-55 (Whistler with passes).
- The Hakuba listing says shuttle buses "run between the late December and March"; whether the stop outside is
  still served on 13-20 March was not checked by the site or by me.
- R2-6's expiry guard runs only when someone pushes: on 10 Dec the public cost table will still answer "Yes" for
  Zermatt and Chamonix until a re-read is published (`sitecheck.py --today 2026-12-10` fails as designed).

### Known-but-live, one line each (already in REVIEW.md, still public)

- R2-11: Zermatt page still says "Cancellation terms were not read for any of these."
- R2-10: Engelberg flat is "$906" in one index paragraph and "$907" in another.
- R2-13: `data/readings.tsv` says the live CPC page "was replaced by the 12 Nov 2026 discussion"; today it still
  shows the 8 Oct text.
- R2-14: README says "nineteen listing policies ... nine"; the page says seventeen and eight.
- Round 2 has no status lines in REVIEW.md, and HANDOFF.md still describes round 1 (19 checks and 68 tests; the
  repo now has 24 and 120).
- R1-5: the personal email in git history is still there (not quoted here).

## Listing verification, 2026-11-10

Method: one plain page request per listing with its dates in the address. Airbnb's page arrives with the listing,
amenity list, rating and description; the booking panel (price, availability, cancellation line) is marked
"NOT_COMPLETE" in the page data and filled in later by script, so those three are "could not reach" for every row.

| Listing (room) | Exists | Washer wording today | Site says | Rating today | Price, dates, refund |
|---|---|---|---|---|---|
| Engelberg 1267557874578220140 | yes | Washer – In unit | in unit | 4.57 (56), as published | could not reach |
| Engelberg Sunny 779567373113942720 | yes | Paid washer – In building | same | 4.86 (76) | could not reach |
| Telluride West Studio 29856063 | yes | Free washer – In unit | same | 4.83 (174), as published | could not reach |
| Telluride In-Town 1BR 15395305 | yes | Free washer – In unit | same | 4.87 (136) | could not reach |
| Hakuba chalet 4721170 | yes | Free washer – In unit | same | 4.96 (134) | could not reach |
| Hakuba $2,619 hut 15857739 | yes | Free washer – In unit | same | 4.93 (215) | could not reach |
| Hakuba January 28161342 | yes | Free washer – In unit | same | 4.5 (4) | could not reach |
| Zermatt Baccara 1005849900575274943 | yes | Free washer – In unit | same | 4.82 (57) | could not reach |
| Zermatt March 749164300750846312 | yes | Free washer – In unit | same | 4.93 (45) | could not reach |
| Whistler 1450123020779481422 | yes | Washer (no location) | same | 4.93 (59) | could not reach |
| Chamonix 1400536477616188823 | yes | Paid washer – In unit | same | 4.96 (50) | could not reach |
| Andermatt 999872551685699126 | yes | Free washer – In unit | in unit | 5.0 (6) | could not reach |
| Crested Butte 42225513 | yes | Free washer – In unit | in unit | 4.85 (246) | could not reach |
| Fernie 914666151815486819 | yes | Washer (no location) | same | 4.96 (28) | could not reach |
| Alagna 5416558 | yes | Washer (no location) | same | 4.67 (3) | could not reach |
| St Anton 1455513831165257651 | yes | Paid washer – In building | same | 5.0 (1) | could not reach |
| Snowbird 990789137087199196 | yes | Washer (no location) | same | 4.9 (10) | could not reach |
| Les Deux Alpes 29125805 | yes | Free washer – In unit | in unit | 4.76 (87) | could not reach; linen extra |
| Niseko 766838246342060838 | yes | Free washer – In unit | same | 5.0 (53) | could not reach; no accommodation tax to guests |
| Revelstoke pick 1521039495192820325 | yes | Washer (no location) | same | 5.0 (67), as published | could not reach |
| Big Sky pick 9624791 | yes | Washer (no location) | same | 4.48 (119), as published | could not reach |

Location wording matches too: the Hakuba chalet's page says "Ski resorts are 5 minutes away by car" with a
winter shuttle stop outside; the Chamonix flat "1 minute from the Grands Montets ski lift". No Swiss listing's
description states the tourist tax, so those amounts remain the site's assumption.

Booking.com rows (Niseko hotels) were not opened.

## Outside comparisons

**Tony Crocker, bestsnow.net** (tables "as of 2026", snowfall data through 2023; read 2026-11-10).
- Measures: long-run snowfall at a fixed mid-mountain site per resort, its variability, and how monthly and
  seasonal snowfall track the ENSO index, with percent of normal in strong El Niño and strong La Niña months.
- His numbers: Telluride is on the "indifferent" list at 104% of normal in strong El Niño months
  (http://bestsnow.net/Neutral_areas.htm); Big Sky "mildly favoured by La Niña", 91% in strong El Niño; Mt Fidelity
  in the Selkirks, the long record nearest Revelstoke, 89%, "strongly favoured by La Niña"; Fernie 84%, Whistler
  base 89%, Jackson 88% (http://bestsnow.net/La_Nina.htm). "El Nino strongly favors only Southern California,
  Arizona and southern New Mexico" (http://bestsnow.net/El_Nino.htm).
- Ours: "A strong El Niño tilts this winter toward Telluride"; Telluride "El Niño neutral to favourable", Big Sky
  "leaning below normal", Revelstoke "historically warmer with less snow".
- Definitions match (resort-level snowfall against ENSO). Verdict: ours is right in direction and in its relative
  form: Telluride near normal, the two northern resorts about 10% short. "Favourable" for Telluride is a little
  generous; "neutral" is the supported word. OnTheSnow's own series agrees: Telluride 241 in in 2015-16 and 237 in
  in 2023-24 against a 206 in average. On absolute snowfall Crocker is more correct than our table (SKI-5).
- Change: quote the 104 / 91 / 89 figures and say the effect is modest.

**ZRankings** (resort pages and snow ranking, read 2026-11-10).
- Measures: "true snow" per resort from long records, a snow-quality score adjusted for aspect, altitude and rain,
  and each resort's snowfall in El Niño winters.
- Theirs: Telluride 276 in, "El Niño winters bring about 4% more snow", best month March; Big Sky 286 in, 6% less
  snow in El Niño winters, best month February, experts "wait until mid-January or later"; Revelstoke 367 in,
  30th of North American resorts on total snow score, the only one of the three in the top 30.
- Ours: 206, 265 and 257 in; Telluride late February, Big Sky early March, Revelstoke late January.
- Verdict: they confirm our El Niño ordering and our Big Sky and Revelstoke weeks, and they are more correct than
  our table on how much snow each resort gets and on which of the three gets most.
- Overall ranking: Jackson Hole 1st in North America (99.0), Telluride 2nd (95.6), Big Sky 10th (86.9). That is the
  same pair our index lands on for North America (Telluride, with Jackson as the alternate), reached by a different
  method; theirs does not score walking distance or the town, ours does.

**NOAA Climate Prediction Center, ENSO diagnostic discussion, 8 Oct 2026** (live page read 2026-11-10 with a plain
identifier; next issue 12 Nov).
- Their words: "El Niño Advisory"; "a strong-to-very strong El Niño likely through January-March 2027 (remaining
  greater than an 83% chance)". Ours quotes this exactly. They add that a record-strength event is likelier than
  not for October-December (83%); our pages say "strong". Both are fair; ours could say how unusual the event is.

**Zermatt Bergbahnen, starting prices winter 2026/27** (operator leaflet, April 2026). See SKI-3. The operator is
right and our Zermatt pass figures are too low for January to March.

**Bank Cler and BAK Economics, Swiss ski-week cost study** (16 Dec 2025, reported by Keystone-SDA,
https://www.swissinfo.ch/eng/various/ski-holidays-cost-the-most-in-zermatt-and-st-moritz/90644405).
- Measures: a February holiday week in 14 Swiss resorts for families, couples and students: passes, ski school,
  hire and accommodation (four-star hotels for couples).
- Theirs: cheapest overall Airolo, Andermatt-Sedrun and Engelberg-Titlis; dearest for passes Zermatt, St Moritz,
  Laax; dearest hotels Verbier, Gstaad, Zermatt.
- Ours: Engelberg $1,626-1,649 against Zermatt $1,992 on lodging and tax, and Engelberg "roughly half the price"
  of Zermatt; Andermatt $3,086, "over budget".
- Agreement on Engelberg below Zermatt. Disagreement on Andermatt, where ours is one surviving September listing
  (its own note: "$910 in September") and theirs is a resort-wide survey: theirs is the better guide to
  Andermatt's price level, and our row should say it is a single listing, not a resort price. "Zermatt is more
  affordable than assumed" and their "most expensive" are both true on their definitions: ours is the cheapest
  washer flat in a low-season January week, theirs a four-star hotel in the February holidays.

**Post Office Travel Money Ski Resort Report 2026, with Crystal Ski Holidays** (reported by The Telegraph, 13 Dec
2025, https://www.yahoo.com/lifestyle/articles/revealed-europe-best-value-ski-060000563.html; the Post Office's own
page answered 403).
- Measures: one adult's week of lift pass, ski hire, lessons, lunch and drinks in 32 European resorts; no lodging.
- Theirs: cheapest Bardonecchia £601; dearest Wengen £1,372, Val d'Isère £1,313, St Anton £1,265, Saas-Fee £1,256.
- Ours, week for two with passes: Les Deux Alpes about $1,500, Alagna about $1,850, Chamonix about $2,200,
  Engelberg $2,303-2,612, St Anton $3,629.
- Definitions do not match (they leave out lodging, we leave out lessons, hire and food), but the ordering agrees:
  Italy and the smaller French resorts cheapest, Switzerland and the Arlberg dearest. Neither is "more correct";
  ours answers the self-catered question, theirs the on-slope one. No change needed.

**SnowBrains, 2026-27 peak day-ticket survey** (19 Aug 2026, https://snowbrains.com/2026-27-lift-ticket-prices/).
- Theirs, window price for 26 Dec 2026: Jackson Hole $339 ($255 online), Big Sky $289, Snowbird $238. Vail Resorts
  and Telluride prices were not out.
- Ours: Jackson $1,275-1,560 for five to six days ($255-260 a day), Snowbird $1,075-1,290, Telluride $1,430 for six.
- Consistent. Against the operator's Hakuba Valley page (6-day adult 63,900 yen, about $404), a North American
  week of tickets is three to four times a Japanese one, which is the gap our cost table shows.

## Where ours is better than the outside work

- It reads the cancellation line on each listing instead of the search badge; none of the price indices tests
  refundability at all.
- It checks where the washer is, and found the two search traps (building laundry passing the filter, US-dollar
  quotes on Canadian listings).
- Town-level tax: Telluride's 17.22% from the town's own page, where published comparisons use a state rate.
- It prices one definition (week for two, self-catered) across three continents; the outside indices each cover
  one region and one basket.
- It dates every figure and says which ones are estimates.

## Checked and found right

- Six live pages equal the snapshot. 24 site checks, 120 tests, both drift checks pass.
- All 48 cost-table cells reproduce from `data/costs.json` at the stated rates; the three-resort total is $7,361.
- NOAA: El Niño Advisory and the 83% sentence, verbatim, still the live text on 10 Nov.
- Telluride 17.22%; Montana 8% plus Big Sky 4%; BC PST 8% and MRDT up to 3%.
- Hakuba Valley 2026-27 adult passes on the operator's page: 1-day 11,100, 5-day 53,400, 6-day 63,900 yen
  (https://www.hakubavalley.com/en/ticket_en).
- Zermatt season pass 1,850 from 1 Nov and 1,960 from 1 Dec; 1,750 in October only.
- Season dates on the operators' pages: Telluride targeted opening 26 Nov 2026, closing 4 Apr 2027, gondola
  20 Nov-4 Apr, 6:30 am to midnight; Big Sky 25 Nov 2026-11 Apr 2027 plus 16-18 and 23-25 Apr; Revelstoke
  5 Dec 2026.
- Telluride on Epic for up to seven days, not on Epic Local (Epic's Telluride FAQ, via search result text).
- Environment Canada, Taylor (1998): the catalogue abstract carries both quoted phrases, "El Niño winters are
  generally warmer throughout most of British Columbia and Yukon" and less snowfall "especially in southern
  British Columbia" (https://publications.gc.ca/site/eng/9.893812/publication.html).
- Calendar, computed: Easter 28 Mar 2027, MLK Day 18 Jan, Presidents' Day 15 Feb, Coming of Age Day 11 Jan;
  every stay starts on a Saturday; every logged refund cutoff is 30, 5 or 1 days before arrival.
- OnTheSnow's Telluride figures are transcribed correctly (206 in, 45 snow days, monthly snowfall and base).
- Links: 70 of 73 external links return 200; two Pierre & Vacances pages answer 403 and VRBO 429 to a plain
  client. Every internal link and anchor resolves.
- Listings: 21 of 21 exist, with the washer wording and ratings the site reports.
- The Engelberg and Zermatt walks: none of the 19 cheaper Engelberg listings, the 5 cheaper Zermatt January ones
  or the 7 Zermatt March ones states a washer in the unit today (9 Engelberg rows are a bare "Washer", 10 "in
  building"). "Cheapest whose amenity list puts the washer in the flat" holds for both. Hakuba January's five
  cheaper rows are all a bare "Washer".

## Not checked

- Today's price, availability and cancellation line for every Airbnb row (script-loaded; browser tools off-limits),
  and all Booking.com rows. That includes the cancellation lines of the two Hakuba listings in SKI-1, which decide
  whether the Japan answer gets cheaper.
- Whether Airbnb adds any tax line at the price breakdown for a Japanese listing.
- Engelberg's six-day Titlis pass: titlis.ch answered 429 to one request (as it did for the site); not retried.
- Official tax pages for Utah, Wyoming, New Mexico, Colorado outside Telluride, Quebec, Kutchan, Zermatt,
  Engelberg, St Anton, Chamonix and Alagna. The shared web-search allowance ran out. Zermatt's CHF 4 agrees with
  one secondary source; Engelberg's CHF 3.20-4.50 has no official source either way.
- "Too low to trust in mid-March" for Engelberg's run-outs, and whether early January is reliably better there:
  no station record reached.
- Chamonix Grands Montets, Hakuba's new gondola, Fernie's new lifts, Engelberg's "second summit line", transfer
  times and bus fares, French and Swiss school-holiday dates, Ikon terms for Big Sky, Revelstoke, Jackson and the
  Japanese resorts, and the lift-audit capacity figures.
- JMA's outlook for this winter.
- Epic Pass price and sales deadline: epicpass.com sent the request to a waiting-room queue; not pursued. The
  pages say "an Epic Pass covers the lifts" without saying that Epic passes normally go off sale in early December,
  before either Telluride refund deadline. Worth one line once confirmed.
- Post Office report on its own page (403).
