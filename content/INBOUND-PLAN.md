# Shared work plan: THEODORA inbound growth

**Purpose.** The shared work plan between Claude Code and Grok Bot for THEODORA inbound growth.

**How to use it.** Claude Code picks up tasks T1-T10 in dependency order, one branch and PR per task, never pushes to main, and Ron approves each PR. Record each update in the Status log at the bottom.

The handoff below is the task list. On 2026-10-24 Ron changed the CTA to email only: Write to Stav, no booking tool. Tasks T3, T5, T9 and T10 below match that decision.

---

# THEODORA site: Claude Code handoff plan (inbound growth, Week 1 and 2)

Prepared by Grok Bot on 2026-10-24 (ET) from a read-only clone of `Ronkimhi/stavtheodor` at `origin/main` **20ed7dd** ("Wave 1 reviews", 2026-10-24 00:59 ET). Source plan: the Page "THEODORA inbound growth plan". Grok Bot did not write to the repo. **Revised 2026-10-24 12:57 ET after Ron's decision: no photo upload, and the "send one photo of the wall" CTA is retired.** Re-checked against `origin/main` (still 20ed7dd) after a fresh fetch. **Revised again 2026-10-24 (ET): no Calendly or other booking tool. The CTA is email only.**

**The CTA system (use everywhere):**
- The only button: **Write to Stav** / **כתבו לסתיו**, exactly as the live hero and footer (`templates/home.html` line 52, `data-write`, opens the contact form; the mailto href stays the no-JavaScript fallback). No "Book a 15-minute call" button, no `BOOKING_URL`, and no booking link.
- Microline under the button: **Tell me about the space: the room, the walls, the timeline.** / **ספרו לי על החלל: החדר, הקירות, לוח הזמנים.** It matches the existing contact card headline `CONTACT_HEAD` ("Tell me about your space." / "ספרו לי על החלל שלכם.") and the form's message label.

## Rules for every agent (read first)

1. Read `AGENTS.md` in full before touching anything, as `CLAUDE.md` says. Follow its sync protocol: `git fetch origin && git status`, read the Work Log, never force-push, leave other agents' work alone.
2. **Pushing to `main` deploys the live site** (`.github/workflows/pages.yml`). So each task works on its **own branch off the latest `origin/main`**, named `growth-<task-id>-2026-10-24`. When it is done, **open a PR (or leave a local branch plus `git diff origin/main`) and stop. Do not merge, do not push to `main`, do not deploy without Ron's explicit OK.**
3. Edit sources only, never generated files (`index.html`, `guide/`, `advisory/`, `radar/`, the stubs, the sitemaps). Then run `python3 build.py` and finish only when it ends with `check_site: OK`. Also run `python3 tools/check_pages.py` when `content/pages/*.json` changes. Commit the built output with the source, per AGENTS.md.
4. Standing content rules that apply here: no em or en dashes anywhere (rule 2). Every visible string needs an English and Hebrew twin. Hebrew is drafted for Ron to edit. The FACT-TRACE RULE (rule 14) means no invented clients, prices, credentials or process steps. **No pricing figures or budget ranges anywhere on the site** (owner, 2026-10-24). Google review quotes follow rule 15. **Never send a test submission to Formspree**: Ron tests the live form himself.
5. Append one Work Log line to `AGENTS.md` in every commit, and say "awaiting Ron's OK, not pushed".

## Dependencies at a glance

| Task | Depends on | Can run in parallel with |
|---|---|---|
| T1 Form fields | Nothing: free Formspree plan, no upload, no cost | T3, T5, T6 (T10 touches the same form note: do T1 first or rebase) |
| T2 One form per page | Touches the same `site_chrome.py` form code as T1. **Do T1 first or rebase on it** | T5, T6 |
| T3 Write to Stav in the hero (already live) and on the four guides | Nothing | T1, T5, T6 |
| T4 Reviews | **Already live on main** (20ed7dd). Only a change when Ron confirms another reviewer | anything |
| T5 Titles and metas | Ron approves the six pairs. Each meta ends with Write to Stav. No booking link | T1, T3, T6 |
| T6 404 stubs | Ron approves the redirect map. The extra stubs wait on the Search Console 404 list | T1, T3, T5 |
| T7 Museum noindex | **Pending Ron's OK** on consolidation (nothing deleted) | T8 is the same decision |
| T8 Sitemap tightening | T7 decision | T7 |
| T9 Referral page | Grok Bot's copy (`content/REFERRAL-PAGE-COPY.md`) and Ron's OK | anything |
| T10 Retire the photo CTA strings | Ron's OK on the wording. Same files as T3 in `site_chrome.py` and `build-site-pages.py`: do T3 first or rebase | T5, T6 |

Suggested order: T6 (smallest), then T1, then T10, then T3 and T5 (either order; neither waits on a booking link), then T2. T7, T8 and T9 wait for their decisions.

---

## T1. Contact form: budget, timeline, Who referred you?, fewer required fields (no upload)

**Goal.** Capture timeline, an optional budget note and the referrer, and make the form shorter to finish. 5 of 8 form starts were abandoned. **No file upload and no Formspree plan change**: Ron decided against photo upload, so the form stays on the free plan at no cost.

**Files.** `site_chrome.py`: `FORM_ENDPOINT` (line ~48), `contact_form()` (~573, including the docstring line "The free plan takes no files, so the note asks for the photo by email" and the `form-note` at line ~617), `FOUND_VIA` (~653), `form_js()` (~667). Also `css/theme.css` (chip and field styles), `tools/check_site.py` (form gates, if any count fields), `content/glossary-he.json` (only if a Latin word needs whitelisting), and `AGENTS.md` (rule 12 describes the form field by field, and line ~81 says "the note asks for the wall photo by email": update both in the same commit).

**Steps.**
1. **No upload.** Do not add a file input, `enctype`, or any `FORM_UPLOADS` switch. Replace the form note at line ~617, `L('I reply by email. If you have a photo of the wall, reply to my email with it.', ...)`, with `L('I reply by email.', 'אני עונה במייל.')`. Do not append a booking line. Update the docstring to match.
2. Add an optional **Timeline** chip set (`timeline`, none checked): This month / In 1 to 3 months / In 3 to 6 months / Just exploring, each with a Hebrew twin (החודש / בעוד 1 עד 3 חודשים / בעוד 3 עד 6 חודשים / רק בודקים). No dashes: write "1 to 3".
3. Add an optional **Budget** free-text field (`budget`, single line, label "Budget, if you have one in mind" / "תקציב, אם יש לכם אחד בראש"). **No preset ranges, figures, placeholders with numbers or dollar signs in the markup**: the owner rule is no pricing on the site.
4. Add an optional **Who referred you?** text field (`referred_by`, label "Who referred you?" / "מי הפנה אתכם?"). Show and enable it only when the `found_via` chip "A friend or client" or "A designer or architect" is checked, mirroring the existing `ai_query` show/disable sync (on change, after reset, on pageshow), so hidden text is never posted.
5. **Fewer required fields.** Required: **name and email only.** Make `message` optional (drop `required` from the textarea; keep its label "Tell me about your space"). Every chip set, `timeline`, `budget` and `referred_by` stay optional. Keep the `_gotcha` honeypot, `page`, `_subject`, `client_type` default (Homeowner) and every existing chip unchanged.
6. Rebuild. Confirm the form renders the same on `/contact/`, the homepage `#contact`, the pop-up and the buyer variants.

**Acceptance criteria.**
- `python3 build.py` ends `check_site: OK`. No dashes, and every new label has twins.
- Built pages contain no `type="file"`, no `enctype="multipart`, and no "photo" in the form markup or form note.
- Only `name` and `email` carry `required`.
- `referred_by` and `ai_query` are disabled in the markup until their chips are checked (verify in headless Chromium with Formspree mocked, as in the 2026-10-10 log line).
- No digits or "$" inside the budget field's label or placeholder.
- No test submission is sent to Formspree.
- PR description lists the new field names (`timeline`, `budget`, `referred_by`) so Ron can see them in the Formspree dashboard.

**Ship.** Open a PR. Don't deploy without Ron's OK. No cost: stays on the free Formspree plan.

---

## T2. One form per page

**Goal.** The homepage serves two copies of the same form: the inline `#contact` form and the Write to Stav pop-up `<dialog id="write-modal">` from `write_ui()`. Pages with an inline form should have exactly one, so analytics, autofill and screen readers aren't split.

**Files.** `site_chrome.py`: `write_ui()` (~851), the `data-write` click handler (~841), `tail()`. `build-home.py` (homepage and buyer variants). `build-site-pages.py` (`/contact/`, `CONTACT`). `tools/check_site.py` (add a gate). `templates/home.html` (the `hero-write` button at line ~52 already has `href="#contact"`).

**Steps.**
1. Add a `tail(..., inline_form=False)` flag. On pages that render `contact_form()` inline (homepage, buyer variants, `/contact/`), omit the dialog's form, or the whole dialog.
2. On those pages, make `[data-write]` scroll to and focus the inline form (`#contact`) instead of opening the dialog. Keep the pop-up behaviour on every other page.
3. Add a `check_site.py` gate: every built page has at most one `action="https://formspree.io/f/`.

**Acceptance criteria.**
- `grep -c 'formspree.io/f/' index.html` is 1, and the same for `contact/index.html` and each variant page.
- The hero Write to Stav button scrolls to the form on the homepage and opens the pop-up on a guide page.
- GA4 `form_start` and `generate_lead` still fire once.
- `check_site: OK`.

**Depends on.** T1, since both touch the same form code. Branch after T1 merges, or rebase.

**Ship.** Open a PR. Don't deploy without Ron's OK.

---

## T3. Write to Stav in the hero (already live), and a Write to Stav button on the four guides

**Goal.** The CTA is email only (Ron, 2026-10-24: no Calendly or other booking tool). **Write to Stav** / **כתבו לסתיו** is the action everywhere, the existing hero and footer wording. It opens email to Stav or the contact form, whichever that button already uses (the live hero is `data-write`, which opens the pop-up, and the mailto href stays the fallback). No "Book a 15-minute call" button, no `BOOKING_URL`, and no booking link. Keep the microline **"Tell me about the space: the room, the walls, the timeline."** / **"ספרו לי על החלל: החדר, הקירות, לוח הזמנים."** The hero button is already live. This task adds the same Write to Stav button on the four guides.

**Files.** `templates/home.html` line 52 (the `hero-write` link inside the homepage-only `hero_write` region: confirm it, do not turn it into a booking button). `site_chrome.py`: `CTA_MICRO = ('Tell me about the space: the room, the walls, the timeline.', 'ספרו לי על החלל: החדר, הקירות, לוח הזמנים.')` under the button where this task places one. Do not add `BOOKING_URL` or a `click_booking` event. `build-site-pages.py` `cta_html()` only as needed to place the guide button. `content/pages/{restaurant-wall-decor,hotel-artwork,art-sourcing-for-interior-designers,dental-office-decor}.json`. `build-home.py` (`HOME_ONLY` stays as is).

**Steps.**
1. Do not add a booking URL, a booking button, Calendly, Cal.com, or any "Book a 15-minute call" / "קביעת שיחה" string.
2. Confirm the homepage hero **Write to Stav** / **כתבו לסתיו** button is present, with the live wording, `data-write`, and `data-loc="hero"`. Leave that control as the site already ships it.
3. If the hero button has no microline yet, add `CTA_MICRO` under it (homepage only).
4. On each of the four guides, add a **Write to Stav** / **כתבו לסתיו** button after the lead and again before the FAQ, the same `data-write` control as the hero. Put the microline under each of those buttons. In `cta_html()`, a page's own `cta_sub_en`/`cta_sub_he` still wins over `CTA_MICRO` when present (T10 rewrites the ones that ask for a photo).

**Acceptance criteria.**
- No built page contains "Book a 15-minute call", "קביעת שיחה", `BOOKING_URL`, or a booking host (Calendly, Cal.com).
- The hero Write to Stav wording and `data-loc="hero"` are unchanged.
- Each of the 4 guides has a Write to Stav button with `data-write`, and the microline in both languages.
- `check_site: OK`, and `check_pages.py` passes.

**Depends on.** Nothing.

**Ship.** Open a PR. Don't deploy without Ron's OK.

---

## T4. Reviews strip (status: already live)

`site_chrome.REVIEWS` and `reviews_block()` went live in 20ed7dd (2026-10-24 00:59 ET). Four exact quotes (Rotem, Hadas, Alina, Gonny, October 2026) appear on the homepage (`home_above_contact`, homepage only) and on `/contact/` (`CONTACT_AFTER_CARD`). **No code task now.**

When Ron confirms another reviewer is a real client (the quote/photo question to Stav is pending), paste that review's exact span into `REVIEWS` with its first name, month and labelled Hebrew translation, following rule 15. Never paraphrase, never invent, and add no stars, counts or schema. Open a PR. Don't deploy without Ron's OK.

---

## T5. Six title and meta description rewrites

**Goal.** Lift click-through on pages Google already shows (1,061 impressions and 9 clicks across the 5 guide and advisory pages). The drafts are approved in the plan Page's Search section once Ron says OK.

**Files and exact values** (`head_title` gets " · THEODORA" appended by the build; `check_pages.py` enforces 60 characters with the suffix and 160 for the meta):

| Source | Field | New value |
|---|---|---|
| `content/pages/restaurant-wall-decor.json` | `head_title` | `Restaurant Wall Decor Ideas That Last` |
| same | `meta_description` | `Restaurant wall decor ideas that survive steam, light and a full service, from a curator with 15+ years in art and hospitality. Write to Stav about the space.` (158 characters) |
| `content/pages/hotel-artwork.json` | `head_title` | `Hotel Artwork Guidelines, Lobby to Room` |
| same | `meta_description` | `Hotel artwork guidelines, zone by zone: lobby, corridors, rooms, budget per key, by a curator whose work includes Waldorf Astoria. Write to Stav about rooms.` (157 characters) |
| `content/pages/art-sourcing-for-interior-designers.json` | `head_title` | `Art Sourcing for Interior Designers` |
| same | `meta_description` | `Art sourcing for designers: trade, galleries, commissions or a curator, and the client stays yours. 15+ years in the art world. Write to Stav about the space.` (158 characters) |
| `content/pages/dental-office-decor.json` | `head_title` | `Dental Office Decor Ideas: Waiting Room to Chair` (59 with the suffix) |
| same | `meta_description` | `Dental office decor for the waiting room, chair view and kids' rooms, in art you can clean. By a curator with an M.A. in art history. Write to Stav by email.` (157 characters) |
| `build-site-pages.py` `HUBS["advisory"]` / `render_hub()` | new title | `<title>` becomes `Art Advisor in NYC & NJ: Cost and Process · THEODORA`. **Keep the h1 "Art advisory, answered plainly"**: add an optional head-title element to the HUBS tuple, or a `HUB_HEAD_TITLE` dict, used only in `sc.head()` |
| same | meta | `What an art advisor in NYC and New Jersey does, what it costs and how a piece gets to your wall, from curator Stav Theodor (15+ years). Write to Stav.` (150 characters) Replace the `strip_tags(lead_en)[:158]` truncation (today it cuts mid-word at "buil") with an explicit `HUB_DESC` |
| `build-home.py` line 43 | `TITLE` | `Stav Theodor · THEODORA Art Advisor, New Jersey & NYC` (keeps "art advisor New Jersey" per Ron's 2026-09-29 brief P1.4, and leads with the brand name for the "theodora" query) |
| `build-home.py` line 44 | `DESCRIPTION` | `Stav Theodor, art advisor in Tenafly, NJ: art for new homes in Bergen County and Manhattan, chosen, framed and hung. 15+ years in art. Write to Stav by email.` (158 characters) |

**Steps.**
1. Edit the values. Bump `date_modified` on the four guide JSONs only if the PAGE-SPEC requires it for head-only edits (otherwise leave it).
2. "Dental Office Decor Ideas: Waiting Room to Chair" is 48 characters, or 59 with the suffix, so it passes. If any gate complains, shorten it rather than dropping the suffix.
3. The six metas end with an email offer (Write to Stav), not a photo ask and not a call (Ron, 2026-10-24). T5 does not wait on T3 or on a booking link.
4. Rebuild. Credentials trace to BRIEF.md and the live site: 15+ years, M.A. in art history, and the Waldorf Astoria Chengdu project.

**Acceptance criteria.**
- `check_pages.py` and `check_site: OK` pass.
- Each built page's `<title>` and `<meta name="description">` match the table exactly.
- The `/advisory/` h1 is unchanged.
- `MERGED_PATHS['services']` still points at `/advisory/`.

**Ship.** Open a PR. Don't deploy without Ron's OK. After it goes live, request indexing for these 6 URLs in Search Console (Ron).

---

## T6. /press and the other 404 redirect stubs

**Goal.** Clear the Search Console "Not found (404)" list.

**Files.** `build-home.py` `OLD_PATHS` (~585) and `MERGED_PATHS` (~596). `site_chrome.redirect_stub()` is reused unchanged.

**Steps.**
1. Add `'press': (SITE + '/about/', 'About THEODORA | Art Advisor Stav Theodor, Tenafly NJ')` to `OLD_PATHS` (noindex stub, as `/blog/` has). GitHub Pages then answers `/press` with a 301 to `/press/`, and the stub forwards to `/about/`.
2. Add these **only if Ron supplies them from the Search Console Pages report** (Not found (404) examples). They are candidates that 404 today:
   - `about-us` and `team` → `/about/`
   - `contact-us` → `/contact/`
   - `gallery` → `/projects/`
   - `faq` → `/#faq`
3. Already handled, no change: `/our-team/`, `/our-team-1/` and `/designers/` (`MERGED_PATHS`, canonical plus instant refresh, no noindex), and `/blog/`, `/services/` and `/portfolio/` (`OLD_PATHS`).

**Acceptance criteria.**
- `press/index.html` is built with canonical `https://stavtheodor.com/about/`, a meta refresh and `noindex`.
- It is not in any sitemap.
- `check_site: OK`.

**Ship.** Open a PR. Don't deploy without Ron's OK.

---

## T7. Noindex the thinnest /museum/ artist pages (pending Ron's OK)

**Goal.** Stop thin pages from competing for crawl budget (145 pages are "Discovered, not indexed"). **Nothing is deleted.** Pages stay live and linked inside `/museum/`.

**Files.** `museum/tools/build_artist_pages.py` (artist page head) and `tools/build_sitemap.py` (`sitemap-museum.xml`). The `noindex` gate lives in `tools/check_site.py`.

**Candidates** (English word count of the built page, measured from the repo on 2026-10-24; museum median is 1,505 words):
- Lee Krasner (120)
- Jean-Michel Basquiat (137)
- Willem de Kooning (151)
- Mark Rothko (171)
- David Hockney (186)
- René Magritte (200)
- Georges Braque (206)
- Max Ernst (211)
- Jackson Pollock (213)
- Yayoi Kusama (221)
- Frida Kahlo (249)

`/museum/` itself has 48 words of static text because it is JS-driven, but keep it indexed.

**Steps.**
1. Add a `NOINDEX_ARTISTS` set to `build_artist_pages.py`. Emit `<meta name="robots" content="noindex, follow">` on those pages.
2. `build_sitemap.py` skips any page carrying noindex.
3. Alternatively, expand these 11 pages past about 400 words with sourced text. That is Ron's choice.

**Acceptance criteria.**
- The 11 pages carry noindex and are absent from `sitemap-museum.xml`.
- `check_site: OK`, and the museum gate still passes (no main-site page links `/museum/`).

**Ship.** **Do not open this PR until Ron says OK to consolidation.** Then open a PR. Don't deploy without Ron's OK.

---

## T8. Tighten the sitemap index to money pages (pending Ron's OK, same decision as T7)

**Goal.** The sitemap index should point Google at pages that can produce clients: home, hubs, advisory, guides, local pages, partner and service pages, projects, `/contact/` and `/about/`.

**Files.** `tools/build_sitemap.py`, `sitemap.xml` (generated).

**Steps.**
1. Keep `sitemap-pages.xml` and `sitemap-radar.xml` in the index.
2. Either drop `sitemap-museum.xml` from the index (keeping the file and pages live), or keep it with only the indexable museum pages after T7.
3. Don't touch `robots.txt`.

**Acceptance criteria.**
- `sitemap.xml` lists the agreed children.
- Every URL in them returns 200 and is indexable.
- `check_site: OK`.

**Ship.** Open a PR after Ron's OK. Don't deploy without it.

---

## T9. Referral page a client can forward (after Grok Bot's copy)

**Goal.** A short indexable page, for example `/refer/`, that a past client or designer forwards to a friend. It explains the first step (write to Stav about the space) and carries the T3 CTA: the Write to Stav button and the microline. No booking button. No photo ask.

**Files.** A new `content/pages/refer.json` following `content/PAGE-SPEC.md` (English and Hebrew), rendered by `build-site-pages.py` like the partner pages. Add it to `sitemap-pages.xml` (automatic). Link it from no main nav, only from the referral messages.

**Depends on.** Grok Bot's referral-page copy (`content/REFERRAL-PAGE-COPY.md`) and Ron's OK. **No referral-fee figures on the page**: `for-designers.json` already says referral terms are agreed studio by studio. The designer referral fee goes only in the private partner sheet, never in the repo.

**Acceptance criteria.** `check_pages.py` and `check_site: OK` pass, twins are complete, and there are no dashes and no prices.

**Ship.** Open a PR. Don't deploy without Ron's OK.

---

## T10. Retire every "send one photo / one wall photo" CTA string

**Goal.** Ron dropped photo upload and the photo CTA (2026-10-24). Every visitor-facing ask to send a photo becomes an ask to tell Stav about the space (or, through T3, to write to Stav). Found in a fresh clone at `origin/main` 20ed7dd by searching English and Hebrew phrasings ("one photo", "a photo of the wall", "photos of the walls", "תמונה אחת של", "תמונה של הקיר", "תצלומים של", "צרפו תמונה"). Every "Find" below was verified to exist in that commit.

**Files (34).** `site_chrome.py`, `build-site-pages.py`, `llms.txt`, 25 files in `content/pages/`, 6 in `content/variants/`. Plus docs in the same commit: `AGENTS.md` line ~81 (form note described as asking for the wall photo) and `content/BRIEF.md` line 28 (quotes "send me a photo of your first wall" as a site CTA). `llms-full.txt` is generated by `tools/build_llms_full.py` from the pages: never edit it by hand; the rebuild clears its 29 matches.

**Steps.**
1. Branch `growth-T10-2026-10-24` off the latest `origin/main` (after T1 and T3 if they merged; otherwise rebase later, since rows 1 to 8 touch the same lines).
2. Apply each row of the table. JSON rows are the decoded field value: edit inside the JSON string and keep its existing escaping (`\"` around attributes). Keep the surrounding sentence and links unchanged.
3. Leave these alone, they describe how Stav works or are about photographs as art, not asks: `how-the-art-advisory-process-works.json` ("on a call with photos and plans"), `art-for-a-home-in-israel-from-abroad.json` ("I work from the plans, the designer's material, and photos of the site"; the "what to have ready" list; faq 3), `art-for-a-new-condo-nyc.json`, `moved-to-nyc-empty-walls-art.json`, `art-for-an-office-or-business.json` faq 4, `for-designers.json` "What you hand over" ("A drawing set or a few photos"), and every "photograph" as an artwork or listing photo.
4. Optional gate in `tools/check_site.py`: fail when built HTML (excluding `/museum/`) contains "photo of the wall", "one photo", "wall photo", "photo of one wall", "תמונה אחת של הקיר", "תמונה של הקיר" or "תמונה של קיר אחד".
5. Rebuild; run `python3 tools/check_pages.py` and `python3 tools/check_variants.py`.

**Find and replace (85 rows).**

| File | Field | Find | Replace |
|---|---|---|---|
| `site_chrome.py` | `FOOTER_CTA[0]` | Send me one photo of the wall and a line about the space. I’ll tell you what I see. | Tell me about the space: the room, the walls, the timeline. I’ll tell you what I see. |
| `site_chrome.py` | `FOOTER_CTA[1]` | שלחו לי תמונה אחת של הקיר ושורה על החלל. אספר לכם מה אני רואה. | ספרו לי על החלל: החדר, הקירות, לוח הזמנים. אספר לכם מה אני רואה. |
| `site_chrome.py` | `NEXT_STEPS[0]` | ('You send a photo of the wall and a line about the space.', 'אתם שולחים תמונה של הקיר ושורה על החלל.') | ('You tell me about the space: the room, the walls, the timeline.', 'אתם מספרים לי על החלל: החדר, הקירות, לוח הזמנים.') |
| `site_chrome.py` | `CONTACT_LINES[0]` | ('One photo of the wall and a line about the space is enough.', 'תמונה אחת של הקיר ושורה על החלל מספיקות.') | ('A few lines about the room, the walls and the timeline are enough.', 'כמה שורות על החדר, הקירות ולוח הזמנים מספיקות.') |
| `site_chrome.py` | `contact_form() form-note` | L('I reply by email. If you have a photo of the wall, reply to my email with it.', 'אני עונה במייל. אם יש לכם תמונה של הקיר, שלחו אותה בתשובה למייל שלי.') | L('I reply by email.', 'אני עונה במייל.') |
| `build-site-pages.py` | `CTA_EN` | Send me one photo of the wall, and a line about the space. I will tell you what I see. | Tell me about the space: the room, the walls, the timeline. I will tell you what I see. |
| `build-site-pages.py` | `CTA_HE` | שלחו לי תמונה אחת של הקיר ושורה על החלל. אספר לכם מה אני רואה. | ספרו לי על החלל: החדר, הקירות, לוח הזמנים. אספר לכם מה אני רואה. |
| `build-site-pages.py` | `CONTACT description (line ~763)` | Send one photo of the wall and a line about the space. | Tell me about the space: the room, the walls, the timeline. |
| `llms.txt` | `Contact line (line 14)` | Send one photo of the wall and a line about the space. | Tell me about the space: the room, the walls, the timeline. |
| `content/pages/art-above-couch.json` | `body_en` | Send me a photo of the wall through <a href="/contact/">the contact page</a>. | Tell me about the wall through <a href="/contact/">the contact page</a>. |
| `content/pages/art-above-couch.json` | `body_he` | שלחו לי תמונה של הקיר דרך | ספרו לי על הקיר דרך |
| `content/pages/gallery-wall-ideas.json` | `body_en` | Send me a photo of the wall through <a href="/contact/">the contact page</a>. | Tell me about the wall through <a href="/contact/">the contact page</a>. |
| `content/pages/gallery-wall-ideas.json` | `body_he` | שלחו לי תמונה של הקיר דרך | ספרו לי על הקיר דרך |
| `content/pages/art-advisor-bergen-county.json` | `body_en` | send me the plans or one photo of the space: | send me the plans or tell me about the space: |
| `content/pages/art-advisor-bergen-county.json` | `body_he` | שלחו לי את התוכניות או תמונה אחת של החלל: | שלחו לי את התוכניות או ספרו לי על החלל: |
| `content/pages/art-advisor-bergen-county.json` | `faq[5].a_en` | Send one photo of the wall and a line about the space. | Tell me about the space: the room, the walls, the timeline. |
| `content/pages/art-advisor-bergen-county.json` | `faq[5].a_he` | שלחו תמונה אחת של הקיר ושורה על החלל. | ספרו לי על החלל: החדר, הקירות, לוח הזמנים. |
| `content/pages/art-advisor-bergen-county.json` | `cta_sub_en` | Send one photo and a line about the space. | Tell me about the space: the room, the walls, the timeline. |
| `content/pages/art-advisor-bergen-county.json` | `cta_sub_he` | שלחו תמונה אחת ושורה על החלל. | ספרו לי על החלל: החדר, הקירות, לוח הזמנים. |
| `content/pages/art-consultant-tenafly-nj.json` | `body_en` | send me one photo of the wall and a line about the space, and I will tell you what I see. | tell me about the space, the walls and the timeline, and I will tell you what I see. |
| `content/pages/art-consultant-tenafly-nj.json` | `body_he` | שלחו לי תמונה אחת של הקיר ושורה על החלל, ואספר | ספרו לי על החלל, הקירות ולוח הזמנים, ואספר |
| `content/pages/art-consultant-tenafly-nj.json` | `faq[5].a_en` | Send one photo of the wall and a line about the space. | Tell me about the space: the room, the walls, the timeline. |
| `content/pages/art-consultant-tenafly-nj.json` | `faq[5].a_he` | שלחו תמונה אחת של הקיר ושורה על החלל. | ספרו לי על החלל: החדר, הקירות, לוח הזמנים. |
| `content/pages/art-consultant-tenafly-nj.json` | `cta_sub_en` | Send one photo and a line about the space. | Tell me about the space: the room, the walls, the timeline. |
| `content/pages/art-consultant-tenafly-nj.json` | `cta_sub_he` | שלחו תמונה אחת ושורה על החלל. | ספרו לי על החלל: החדר, הקירות, לוח הזמנים. |
| `content/pages/art-advisor-manhattan-apartment.json` | `body_en` | Send me one photo of the wall and a line about the room, at | Tell me about the room, the walls and the timeline, at |
| `content/pages/art-advisor-manhattan-apartment.json` | `body_he` | שלחו לי תמונה אחת של הקיר ושורה על החדר, לכתובת | ספרו לי על החדר, הקירות ולוח הזמנים, בכתובת |
| `content/pages/art-curator-new-york.json` | `body_en` | Send me one photo of the wall and a line about the room, at | Tell me about the room, the walls and the timeline, at |
| `content/pages/art-curator-new-york.json` | `body_he` | שלחו לי תמונה אחת של הקיר ושורה על החדר, לכתובת | ספרו לי על החדר, הקירות ולוח הזמנים, בכתובת |
| `content/pages/art-curator-new-york.json` | `faq[0].a_en` | Write to stav@stavtheodor.com with one photo of a wall. | Write to stav@stavtheodor.com about the room, the walls and the timeline. |
| `content/pages/art-curator-new-york.json` | `faq[0].a_he` | כתבו ל-stav@stavtheodor.com עם תמונה אחת של קיר. | כתבו ל-stav@stavtheodor.com על החדר, הקירות ולוח הזמנים. |
| `content/pages/art-curator-new-jersey.json` | `body_en` | Send me one photo of the wall and a line about the home, at | Tell me about the home, the walls and the timeline, at |
| `content/pages/art-curator-new-jersey.json` | `body_he` | שלחו לי תמונה אחת של הקיר ושורה על הבית, לכתובת | ספרו לי על הבית, הקירות ולוח הזמנים, בכתובת |
| `content/pages/art-curator-new-jersey.json` | `faq[0].a_en` | Write to stav@stavtheodor.com with one photo of a wall. | Write to stav@stavtheodor.com about the room, the walls and the timeline. |
| `content/pages/art-curator-new-jersey.json` | `faq[0].a_he` | כתבו ל-stav@stavtheodor.com עם תמונה אחת של קיר. | כתבו ל-stav@stavtheodor.com על החדר, הקירות ולוח הזמנים. |
| `content/pages/art-advisor-westchester-ny.json` | `cta_sub_en` | Or one photo of the wall you want to start with, and a line about what you want to feel there. | Or a line about the room you want to start with, and what you want to feel there. |
| `content/pages/art-advisor-westchester-ny.json` | `cta_sub_he` | או תמונה אחת של הקיר שממנו תרצו להתחיל, ושורה על מה שתרצו להרגיש שם. | או שורה על החדר שממנו תרצו להתחיל, ועל מה שתרצו להרגיש שם. |
| `content/pages/art-for-a-home-in-israel-from-abroad.json` | `body_en` | and send one photo of the wall you think about most. | and tell me about the wall you think about most. |
| `content/pages/art-for-a-home-in-israel-from-abroad.json` | `body_he` | ושלחו תמונה אחת של הקיר שאתם הכי חושבים עליו. | וספרו לי על הקיר שאתם הכי חושבים עליו. |
| `content/pages/art-for-a-new-build-in-bergen-county.json` | `faq[4].a_en` | Send a photo of the wall or the floor plans to stav@stavtheodor.com and I will tell you what I see. | Send the floor plans to stav@stavtheodor.com, or tell me about the walls and the timeline, and I will tell you what I see. |
| `content/pages/art-for-a-new-build-in-bergen-county.json` | `faq[4].a_he` | שלחו תמונה של הקיר או את תוכניות הבית לכתובת stav@stavtheodor.com ואספר לכם מה אני רואה. | שלחו את תוכניות הבית לכתובת stav@stavtheodor.com, או ספרו לי על הקירות ועל לוח הזמנים, ואספר לכם מה אני רואה. |
| `content/pages/art-for-an-office-or-business.json` | `body_en` | with photos of the space and a sentence about what you do. | with a sentence about the space, what you do and your timeline. |
| `content/pages/art-for-an-office-or-business.json` | `body_he` | עם תמונות של החלל ומשפט על מה שאתם עושים | עם משפט על החלל, על מה שאתם עושים ועל לוח הזמנים |
| `content/pages/art-sourcing-for-interior-designers.json` | `body_en` | Send me the plans, or a photo of one wall, and a line about the client | Send me the plans and a line about the client |
| `content/pages/art-sourcing-for-interior-designers.json` | `body_he` | שלחו לי את התוכניות, או תמונה של קיר אחד, ושורה על הלקוח, | שלחו לי את התוכניות ושורה על הלקוח, |
| `content/pages/for-designers.json` | `body_en` | Send me the plans, or even a photo of one wall, and a line about the client. | Send me the plans and a line about the client. |
| `content/pages/for-designers.json` | `body_he` | שלחו לי את התוכניות, או אפילו תמונה של קיר אחד, ושורה על הלקוח. | שלחו לי את התוכניות ושורה על הלקוח. |
| `content/pages/dining-room-art.json` | `body_en` | or send me a photo of your dining wall through | or tell me about your dining wall through |
| `content/pages/dining-room-art.json` | `body_he` | או שלחו לי תמונה של קיר פינת האוכל דרך | או ספרו לי על קיר פינת האוכל דרך |
| `content/pages/financial-advisor-office-art.json` | `body_en` | send me one photo of the space where you meet clients through | tell me about the space where you meet clients through |
| `content/pages/financial-advisor-office-art.json` | `body_he` | שלחו לי תמונה אחת של החלל שבו אתם פוגשים לקוחות דרך | ספרו לי על החלל שבו אתם פוגשים לקוחות דרך |
| `content/pages/framing-and-installing-large-scale-art.json` | `body_en` | with the dimensions and a photo of the space. | with the dimensions and a line about the space. |
| `content/pages/framing-and-installing-large-scale-art.json` | `body_he` | עם המידות ותמונה של החלל. | עם המידות ושורה על החלל. |
| `content/pages/help-choosing-art-for-my-home-nyc.json` | `body_en` | Write to me with a line about the home and, if you can, a photo of the wall you look at most. | Write to me with a line about the home and the wall you look at most. |
| `content/pages/help-choosing-art-for-my-home-nyc.json` | `body_he` | כתבו לי שורה על הבית, ואם אפשר, צרפו תמונה של הקיר שאתם מסתכלים עליו הכי הרבה. | כתבו לי שורה על הבית ועל הקיר שאתם מסתכלים עליו הכי הרבה. |
| `content/pages/how-to-buy-from-a-gallery-without-overpaying.json` | `body_en` | a photo of the wall it is meant for, and the price | a line about the wall it is meant for, and the price |
| `content/pages/how-to-buy-from-a-gallery-without-overpaying.json` | `body_he` | תמונה של הקיר שהיא מיועדת לו, והמחיר | שורה על הקיר שהיא מיועדת לו, והמחיר |
| `content/pages/how-to-buy-from-a-gallery-without-overpaying.json` | `faq[4].a_en` | a photo of the wall it is meant for and the price | a line about the wall it is meant for and the price |
| `content/pages/how-to-buy-from-a-gallery-without-overpaying.json` | `faq[4].a_he` | תמונה של הקיר שהיא מיועדת לו והמחיר | שורה על הקיר שהיא מיועדת לו והמחיר |
| `content/pages/law-office-art.json` | `body_en` | send me the floor plan, photos of the walls clients see first, and the date. | send me the floor plan, a line about the walls clients see first, and the date. |
| `content/pages/law-office-art.json` | `body_he` | שלחו לי את תוכנית הקומה, תצלומים של הקירות שהלקוחות רואים ראשונים, ואת התאריך. | שלחו לי את תוכנית הקומה, שורה על הקירות שהלקוחות רואים ראשונים, ואת התאריך. |
| `content/pages/office-wall-art.json` | `body_en` | send me photos of the walls your clients see and your move date. | tell me about the walls your clients see and your move date. |
| `content/pages/office-wall-art.json` | `body_he` | שלחו לי תצלומים של הקירות שהלקוחות שלכם רואים ואת מועד המעבר. | ספרו לי על הקירות שהלקוחות שלכם רואים ועל מועד המעבר. |
| `content/pages/medical-office-wall-art.json` | `body_en` | send me your floor plan and a photo of the waiting area through | send me your floor plan and a line about the waiting area through |
| `content/pages/medical-office-wall-art.json` | `body_he` | שלחו לי את תוכנית הקומה ותמונה של אזור ההמתנה דרך | שלחו לי את תוכנית הקומה ושורה על אזור ההמתנה דרך |
| `content/pages/tel-aviv-bauhaus-residence.json` | `body_en` | Send me a photo of the wall</a> | Tell me about the wall</a> |
| `content/pages/tel-aviv-bauhaus-residence.json` | `body_he` | שלחו לי תמונה של הקיר</a> | ספרו לי על הקיר</a> |
| `content/pages/tel-aviv-renovated-bauhaus-home.json` | `body_en` | send me one photo of the wall</a> | tell me about the wall</a> |
| `content/pages/tel-aviv-renovated-bauhaus-home.json` | `body_he` | שלחו לי תמונה אחת של הקיר</a> | ספרו לי על הקיר</a> |
| `content/pages/what-does-an-art-advisor-cost.json` | `body_en` | with a photo of the space and a line about what you have in mind | with a line about the space and what you have in mind |
| `content/pages/what-does-an-art-advisor-cost.json` | `body_he` | עם תמונה של החלל ושורה על מה שיש לכם בראש | עם שורה על החלל ועל מה שיש לכם בראש |
| `content/pages/starting-an-art-collection.json` | `body_en` | Send a few photos of what you own and what you have been drawn to. | Tell me what you own and what you have been drawn to. |
| `content/pages/starting-an-art-collection.json` | `body_he` | שלחו כמה תמונות של מה שיש לכם ושל מה שמשך אתכם. | ספרו לי מה יש לכם ומה משך אתכם. |
| `content/variants/hotels.json` | `cta_en` | Send me the plans and the opening date, or one photo of the lobby. | Tell me about the property and the opening date. |
| `content/variants/hotels.json` | `cta_he` | שלחו לי את התוכניות ואת תאריך הפתיחה, או תמונה אחת של הלובי. | ספרו לי על המלון ועל תאריך הפתיחה. |
| `content/variants/investment-firms.json` | `cta_en` | Send me one photo of your reception and your move month. | Tell me about your reception and your move month. |
| `content/variants/investment-firms.json` | `cta_he` | שלחו לי תמונה אחת של הקבלה שלכם ואת חודש המעבר. | ספרו לי על הקבלה שלכם ועל חודש המעבר. |
| `content/variants/law-firms.json` | `cta_en` | Send me one photo of your reception and your move date. | Tell me about your reception and your move date. |
| `content/variants/law-firms.json` | `cta_he` | שלחו לי תמונה אחת של הקבלה שלכם ואת מועד המעבר. | ספרו לי על הקבלה שלכם ועל מועד המעבר. |
| `content/variants/medical-practices.json` | `cta_en` | Send me one photo of your reception. | Tell me about your reception. |
| `content/variants/medical-practices.json` | `cta_he` | שלחו לי תמונה אחת של הקבלה שלכם. | ספרו לי על הקבלה שלכם. |
| `content/variants/restaurants.json` | `cta_en` | Send me one photo of the dining room and a line about the menu. | Tell me about the dining room and the menu. |
| `content/variants/restaurants.json` | `cta_he` | שלחו לי תמונה אחת של חדר האוכל ושורה על התפריט. | ספרו לי על חדר האוכל ועל התפריט. |
| `content/variants/wealth-managers.json` | `cta_en` | Send me one photo of the space where you meet clients. | Tell me about the space where you meet clients. |
| `content/variants/wealth-managers.json` | `cta_he` | שלחו לי תמונה אחת של החלל שבו אתם פוגשים לקוחות. | ספרו לי על החלל שבו אתם פוגשים לקוחות. |

**Acceptance criteria.**
- `rg -i "one photo|photo of the wall|wall photo|photo of one wall|photos of the walls" --glob '!museum/**' --glob '!.git'` returns only the kept descriptive lines listed in step 3 (none in built HTML CTAs).
- The Hebrew search for "תמונה אחת של|תמונה של הקיר|תצלומים של הקירות|צרפו תמונה" returns nothing outside `/museum/`.
- `check_site: OK`, `check_pages.py` and `check_variants.py` pass; no dashes; every changed string keeps its twin.
- The PR description lists the 34 files.

**Ship.** Open a PR. Don't deploy without Ron's OK.

---

## Status log

Each agent appends a dated line (ET): task, status (picked up / PR open / merged / blocked), PR link, and notes or questions for Grok Bot or Ron.

2026-10-24 (ET) | Grok Bot | Plan added. T4 reviews strip already live. T7/T8 wait for Ron's OK. T9 copy is in content/REFERRAL-PAGE-COPY.md.
2026-10-24 (ET) | Grok Bot | Plan file | PR open | https://github.com/Ronkimhi/stavtheodor/pull/1 | Docs only. Not merged.
2026-10-24 (ET) | Grok Bot | CTA changed to email only (Write to Stav); no booking tool. T3 and T5 unblocked.
