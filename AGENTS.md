# AGENTS.md: Rules for Every AI Working on stavtheodor.com

**Read this file in full BEFORE making any change to this repository. No exceptions.**

More than one AI assistant works on this site (different Claude/other-AI sessions, sometimes at the same time). This file is the single source of truth for how we work here, and the sync channel between us. The site owner set this up on 2026-07-01 after two sessions edited the repo simultaneously and collided on push.

---

## 1. Sync protocol (multi-AI coordination)

1. **Pull first.** Run `git fetch origin && git status` before touching anything. If `origin/main` is ahead, integrate it before you start. Assume another AI may have pushed since your context was built.
2. **Read the Work Log** (bottom of this file) to see what the other AI did recently and whether anything is in flight.
3. **Push promptly.** Do not sit on finished work; the longer you wait, the more likely a collision.
4. **Never force-push.** If push is rejected, fetch and rebase, resolve carefully, keep BOTH sides' content (a rejected push here almost always means the other AI added something real, like a new post).
5. **Leave other work alone.** If you find untracked files or changes you did not make (example: a work-in-progress directory), do NOT commit, delete, or "clean up" that work. It belongs to the other AI or to the site owner. Commit only the files you yourself changed.
6. **Append to the Work Log** (Section 7) in every commit that changes site content or tooling: one dated line, what you did, anything the other AI must know.
7. **Keep this file updated.** If the site owner gives you a new standing rule for this site, add it here in the same commit. This file is how the rule reaches the other AI.

---

## 2. Site facts

| Fact | Value |
|---|---|
| Live site | https://stavtheodor.com (www redirects to apex) |
| What it is | THEODORA, Stav Theodor-Kimhi's fine art curation practice + the Art Radar blog (exhibitions in NY / NJ / Tel Aviv) |
| Hosting | GitHub Pages, free tier, auto-deploys on push to `main` (no CI, no build step) |
| Repo | `Ronkimhi/stavtheodor`, remote `origin`, branch `main` |
| GitHub account | `Ronkimhi`. Verify with `gh auth status` before pushing. |
| Architecture | One hand-authored `index.html` + static assets. No framework, no npm. `build-post-pages.py` generates per-post pages and the sitemap. |
| Line endings | LF everywhere (normalized 2026-07-01). Do not reintroduce CRLF. |
| CDN cache | ~10 minutes (`max-age=600`). A push that "doesn't show up" is usually just cache. Bypass check: `curl -sk --resolve stavtheodor.com:443:185.199.108.153 https://stavtheodor.com/` |

---

## 3. Content rules (the site owner's standing rules, mandatory)

1. **Every post is bilingual.** Each Art Radar post carries TWO body blocks inside the same `<article>`:
   - Hebrew original: `<div class="post-body" lang="he" dir="rtl">`
   - Full English translation: `<div class="post-body post-body-en" lang="en" dir="ltr">`

   The English must be a complete, faithful translation of the Hebrew source. Not a summary, not a paraphrase, no added opinions. Keep the same paragraph structure, the same emojis, the same links and `<strong>` emphasis, and repeat every `<figure>`/video inside the English block. A site-wide toggle (Hebrew default, localStorage key `radarLang`) shows one language at a time; both stay in the HTML so search engines and LLMs index both. Rule set by the site owner 2026-07-01; it applies to every new post, forever.

2. **No em dashes (—) and no en dashes (–) in any English text you write.** Use commas, colons, periods, or parentheses. Hard rule from the site owner, applies to posts, metadata, llms.txt, agent.txt, this file, commit messages, everything.

3. **Per-post JSON-LD** uses `"inLanguage": ["he", "en"]`, real permalink URLs (`/radar/<slug>/`, never `#slug` anchors), and an `"about"` Event/ExhibitionEvent block when the post covers an exhibition with dates.

4. **LLM discoverability is a first-class feature.** The site is deliberately positioned so LLMs surface it for "art recommendations in New Jersey / New York" queries. Maintain: `robots.txt` (AI-crawler allowlist), `llms.txt` + `agent.txt` (curated maps, hand-updated per post), `sitemap.xml` (generated), FAQPage + Person/Organization/WebSite JSON-LD in `index.html`. When you add a post, update `llms.txt` and `agent.txt` in the same commit.

5. **Post titles are English; slugs are lowercase-hyphenated and never reused.** Images go in `images/` named `YYYY-MM-DD-slug.jpg`, web-optimized (~900px wide). Never embed images as base64 in the HTML.

---

## 4. Standard workflow for adding or editing a post

Full templates and step-by-step detail: `ADD-BLOG-POST-GUIDE.md` (same directory). Short version:

```
1. git fetch origin && git status        # sync check (Section 1)
2. Edit index.html: JSON-LD <script> + <article> pair at the TOP of <section id="posts">
   with BOTH language blocks (Hebrew + full English)
3. Add image(s) to images/
4. python3 build-post-pages.py           # regenerates radar/<slug>/ pages + sitemap.xml
5. Update llms.txt and agent.txt post lists (real /radar/<slug>/ URLs)
6. Append a line to the Work Log in AGENTS.md
7. git add <your files only> && git commit && git push origin main
8. Verify live (allow ~10 min CDN cache; bypass trick in Section 2)
```

---

## 5. Never do

- Never hand-edit `radar/<slug>/index.html` or `sitemap.xml` (generated; edit `index.html` and re-run `build-post-pages.py`).
- Never force-push, never push to the deprecated `old-backup` remote.
- Never touch DNS/GoDaddy, the GitHub Pages custom-domain config, or the Google Analytics tag (`G-4300MN0Q97`) as part of content work. If the domain itself seems broken, stop and flag it to the site owner.
- Never commit secrets, credentials, or any of the owners' private or business files. This is a PUBLIC repo serving a public site.
- Never delete or commit another AI's untracked work-in-progress.
- Never publish content that Stav or the site owner did not provide as source material. Translations must trace to a Hebrew source post.

---

## 6. Verify before you claim done

```
curl -s -o /dev/null -w "%{http_code}" https://stavtheodor.com/            # 200
curl -s https://stavtheodor.com/radar/<slug>/ | grep -c 'post-body-en'    # >= 1
curl -s https://stavtheodor.com/sitemap.xml | grep '<slug>'               # present
```

Report failures honestly. If a check fails after the cache window, say so; do not declare success.

---

## 7. Work Log (append-only, newest first, one line per change)

Format: `- YYYY-MM-DD HH:MM (TZ) | who | what changed | notes for the other AI`

- 2026-07-02 12:25 (ET) | Claude (main session) | Museum default theme is now LIGHT for first-time visitors. Changed the inline `<head>` theme bootstrap in all 89 museum HTML pages plus the `THEME_SNIPPET` in `museum/tools/build_artist_pages.py` from `localStorage.getItem('museumTheme') || (prefers-color-scheme dark ? 'dark' : 'light')` to `localStorage.getItem('museumTheme') || 'light'`. Stored preference still wins; the ☾ toggle and its persistence are unchanged. | The generator is now the source of truth for the artist-page theme default, so regenerating (`python3 museum/tools/build_artist_pages.py`) preserves light-default. Do not reintroduce the prefers-color-scheme fallback unless the site owner asks for system-follow again.
- 2026-07-02 00:55 (ET) | Claude (GEO session, Windows) | Published post: What to See in July 2026 (monthly curator's guide, bilingual, JSON-LD with 4 ExhibitionEvents; Stav approved publication in session, WhatsApp send still pending on her side). Created answers.md: AI-facing direct-answers file (14 Q&As, each linking to a real post), referenced from llms.txt, agent.txt, robots.txt | New standing pattern per Stav: answers.md is the AGENTS.md-style invisible answer layer; update it in the same commit as every new post, same as llms.txt/agent.txt. Facts sourced from the verified July must-see list (Loki, verified 2026-06-25).
- 2026-07-02 00:15 (ET) | Claude (GEO session, Windows) | Added /our-team-1/ and /our-team/ redirect stubs (same pattern as /about/): both old Squarespace URLs still rank in search for Stav's name but were 404ing | Rebased on the museum commit first; no conflicts. Old Squarespace URL cleanup so far: /about, /our-team-1, /our-team. IndexNow pinged for recrawl.
- 2026-07-01 23:20 (ET) | Claude (GEO session, Windows) | Added /about/index.html (redirect to /#about, noindex) and a branded 404.html | Search engines still hold old Squarespace URLs (found www.stavtheodor.com/about ranking for Stav's name with STALE "Israel-based" description); /about was 404ing. The redirect reclaims that equity and points crawlers at current content. If other old Squarespace paths show up in searches (services, contact, etc.), add the same kind of redirect stub.
- 2026-07-01 23:05 (ET) | Claude (GEO session, Windows) | Added IndexNow key file (eefe194362154568b0f48928e541282d.txt) and submitted all 18 site URLs to api.indexnow.org (202 Accepted) | After publishing any new post, POST the new /radar/<slug>/ URL to https://api.indexnow.org/indexnow with host stavtheodor.com, this key, and keyLocation https://stavtheodor.com/eefe194362154568b0f48928e541282d.txt. This feeds Bing, which feeds ChatGPT search and Perplexity. The key file is public by design; never delete it.
- 2026-07-01 22:36 (ET) | Claude (GEO session, Windows) | Added visible FAQ section (#faq) mirroring the FAQPage JSON-LD word for word, plus nav link and .faq-item CSS; fixed Person schema address to Tenafly NJ (was New York NY, inconsistent with footer and FAQ); added email, telephone, and Tenafly address to ProfessionalService; areaServed New Jersey corrected from City to State; llms.txt and agent.txt now point to the FAQ | Keep the visible #faq text and the FAQPage JSON-LD in sync when editing either. NAP data (Tenafly NJ, stavtheodor85@gmail.com, +1-551-246-6416) is now the canonical set for all external directory listings.
- 2026-07-01 19:05 (ET) | Claude (main session) | Privacy scrub of public md files: removed local filesystem paths, personal account details, and machine references from AGENTS.md / CLAUDE.md / ADD-BLOG-POST-GUIDE.md; renamed the deprecated backup remote to `old-backup` (local git config too); em dash sweep | This repo is public: never reintroduce local paths, personal names beyond what the site itself publishes, or account details into committed files.
- 2026-07-01 18:45 (ET) | Claude (main session) | Added AGENTS.md (this file) + CLAUDE.md pointer | New standing rule: read this file before any change, append here after every change.
- 2026-07-01 18:20 (ET) | Claude (main session) | Full English layer: faithful EN translation on all 16 posts, HE/EN toggle (Hebrew default), inLanguage [he,en], dateModified bump, NJ/NY FAQ schema entry, llms.txt/agent.txt rewritten for bilingual + NJ/NY positioning, Duchamp base64 image extracted to images/, LF normalization, toggle added to build-post-pages.py template | Every future post MUST include the English block (Section 3.1). Resolved a push collision with the Orientalism commit by rebasing and translating that post too.
- 2026-07-01 14:27 (ET) | Other AI session | Added post: Orientalism: Between Fact and Fantasy, at the Met (+2 images) | Was Hebrew-only; English block added by the other session at 18:20.
- 2026-07-01 12:20 (ET) | Claude (main session) | Fixed build-post-pages.py idempotency, corrected llms.txt/agent.txt permalinks, added ADD-BLOG-POST-GUIDE.md | Per-post permalink pages + sitemap now generated for all posts.
- 2026-06-30 → 2026-07-01 | Claude (main session) | Migrated site Squarespace/Netlify → GitHub Pages, DNS via GoDaddy API, HTTPS, robots.txt/llms.txt/agent.txt, GA kept | Hosting is now free and stable; domain/DNS is hands-off (Section 5).

Note: an untracked `museum/` directory (three.js experiment) exists in the local checkout as of 2026-07-01 evening; it belongs to another session and is intentionally not committed.
