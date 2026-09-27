# How to Add a Blog Post to stavtheodor.com

> **First read `AGENTS.md` in this directory.** It carries the multi-AI sync protocol (pull first, work log, collision rules) and the site owner's standing content rules. This guide is the detailed post-authoring reference; AGENTS.md is the law.

Self-contained instructions for an AI agent adding a new "Art Radar" post to Stav Theodor-Kimhi's THEODORA website. Read this whole file before touching anything. It assumes only that you have this repository checked out and shell access on the machine that owns it (`git` and `gh` authenticated as below); no other context is required.

---

## 0. What this site is

- **One file, one source of truth for posts:** `content/posts.html`. Every Art Radar post lives there, newest first. No framework, no npm: three small Python scripts render the site.
- **`index.html` is GENERATED.** The homepage is rendered by `build-home.py` from `templates/home.html` and the data in `content/`. Never add a post to `index.html`, never edit `index.html` by hand: the build overwrites it, and it refuses to run while a post `<article>` is in it.
- **Other generated files (do not hand-edit):** `radar/<slug>/index.html` (one standalone permalink page per post), `radar/index.html` (the archive of every post), `sitemap.xml`, and the advisory/projects/partner/guide pages. If you edit them by hand your changes will be silently overwritten next time someone runs the build.
- **Hand-maintained alongside the posts:** `llms.txt`, `agent.txt` and `answers.md` (curated, human/LLM-readable summaries, the build does NOT touch these, you must update them yourself, see Step 4).
- Live at **https://stavtheodor.com** (`www` redirects to the apex). Hosted free on **GitHub Pages**, auto-deploys on every push to `main`.

---

## 1. Repo and account facts (check these before doing anything)

| Fact | Value |
|---|---|
| Local path | the existing local checkout of this repo (do not clone a second copy on the same machine) |
| Canonical GitHub repo | `Ronkimhi/stavtheodor` |
| Git remote name | `origin` → `https://github.com/Ronkimhi/stavtheodor.git` |
| GitHub account that must be active | `Ronkimhi` |
| Branch | `main` |

**Before pushing, always verify:**

```bash
git remote -v          # origin must point to Ronkimhi/stavtheodor.git
gh auth status          # active account for github.com must be "Ronkimhi"
```

If `gh auth status` shows a different account active, switch before pushing:

```bash
gh auth switch -h github.com -u Ronkimhi
gh auth setup-git
```

There is also a deprecated backup remote called `old-backup` (points at an old, now-inert copy of this repo under a different account). **Never push to it.** It only exists as a historical fallback.

---

## 2. Step-by-step: add a new post

### Step 2.1: Write the post content

Posts are written primarily in **Hebrew** (the site's main audience), with **English** metadata (title, JSON-LD description, keywords) for SEO/LLM discoverability.

**MANDATORY (standing rule from the site owner, 2026-07-01): every post is bilingual.** Each post carries TWO body blocks inside the same `<article>`: the Hebrew original, then a **full English translation** in a `<div class="post-body post-body-en" lang="en" dir="ltr">` block. The English version must be a complete, faithful translation of the Hebrew source: not a summary, not a paraphrase. Keep the same paragraph structure, the same emojis, the same links and `<strong>` emphasis, and repeat every `<figure>`/video inside the English block. A site-wide switch shows one language at a time: **every page opens in English** (site owner's decision, 2026-09-26; before that, post pages opened in Hebrew), and a reader who picks עברית once gets Hebrew everywhere after that. Both blocks live in the HTML so search engines and LLMs index both. Do not use em dashes or en dashes anywhere in the English text.

### Step 2.2: Add the post block to `content/posts.html`

Open `content/posts.html`. Every post is **newest-first**, add your new block immediately after the `<!-- POST TEMPLATE -->` comment at the top of the file and before the first existing `<script type="application/ld+json">` / `<article>` pair. Do NOT touch `index.html` (it is generated; the homepage timeline picks up the six newest posts from this file when you build).

A post is always **two adjacent blocks**: a JSON-LD `<script>` tag, then the `<article>` tag. Do not separate them or add anything between them.

**Full post template (with image)**, copy this exactly and fill in every `{{...}}` placeholder:

```html
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "{{English headline, e.g. 'Giacometti at the Temple of Dendur, the Met'}}",
    "description": "{{1-3 sentence English summary, this is what search engines and LLMs read to describe the post}}",
    "datePublished": "{{YYYY-MM-DD}}",
    "dateModified": "{{YYYY-MM-DD, same as datePublished unless later edited}}",
    "inLanguage": ["he", "en"],
    "url": "https://stavtheodor.com/radar/{{slug}}/",
    "mainEntityOfPage": "https://stavtheodor.com/radar/{{slug}}/",
    "author": { "@id": "https://stavtheodor.com/#stav" },
    "publisher": { "@id": "https://stavtheodor.com/#org" },
    "isPartOf": { "@id": "https://stavtheodor.com/#site" },
    "keywords": "{{comma-separated English keywords}}"
  }
  </script>
  <article class="post" id="{{slug}}">
    <div class="post-date">{{Month D, YYYY}}</div>
    <h2 class="post-title">{{English headline, same as JSON-LD headline}}</h2>
    <div class="post-body" lang="he" dir="rtl">
      <p>{{Hebrew paragraph one}}</p>
      <p>{{Hebrew paragraph two, etc.}}</p>
      <p>📍 {{venue, in Hebrew}}<br>📅 {{dates, in Hebrew}}</p>
      <figure>
        <img src="images/{{YYYY-MM-DD-slug}}.jpg" alt="{{descriptive English alt text}}" loading="lazy">
        <figcaption>{{English caption}}</figcaption>
      </figure>
    </div>
    <div class="post-body post-body-en" lang="en" dir="ltr">
      <p>{{Full English translation of paragraph one, faithful to the Hebrew}}</p>
      <p>{{Full English translation of paragraph two, etc.}}</p>
      <p>📍 {{venue, in English}}<br>📅 {{dates, in English}}</p>
      <figure>
        <img src="images/{{YYYY-MM-DD-slug}}.jpg" alt="{{same English alt text}}" loading="lazy">
        <figcaption>{{same English caption}}</figcaption>
      </figure>
    </div>
  </article>
```

**Rules for `{{slug}}`:** lowercase, hyphen-separated, no spaces, must be a valid URL path segment and a valid HTML `id` attribute (e.g. `giacometti-dendur`, `fresh-paint-2026`). It becomes both the on-page anchor (`#slug`) and the real permalink path (`/radar/slug/`) once you run the build script in Step 3. **Never reuse an existing slug.**

**If the post has an exhibition/event** (dates, venue), add an `"about"` array to the JSON-LD, right after `"keywords"`:

```json
    "about": [
      {
        "@type": ["Event", "ExhibitionEvent"],
        "name": "{{exhibition name}}",
        "startDate": "{{YYYY-MM-DD, omit if unknown}}",
        "endDate": "{{YYYY-MM-DD}}",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {
          "@type": "Museum",
          "name": "{{venue name}}",
          "address": { "@type": "PostalAddress", "addressLocality": "{{city}}", "addressRegion": "{{state, US only}}", "addressCountry": "{{US or IL}}" }
        }
      }
    ]
```

Use `"@type": "Museum"` for museums, `"@type": "Place"` for galleries/other venues (see existing posts for both patterns).

**Short/note-style post (no image, one-off tip, e.g. a museum-pass tip)**, use `class="post note"` instead of `class="post"`, drop the `"about"` array and the `<figure>` block:

```html
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "{{headline}}",
    "description": "{{description}}",
    "datePublished": "{{YYYY-MM-DD}}",
    "dateModified": "{{YYYY-MM-DD}}",
    "inLanguage": ["he", "en"],
    "url": "https://stavtheodor.com/radar/{{slug}}/",
    "mainEntityOfPage": "https://stavtheodor.com/radar/{{slug}}/",
    "author": { "@id": "https://stavtheodor.com/#stav" },
    "publisher": { "@id": "https://stavtheodor.com/#org" },
    "isPartOf": { "@id": "https://stavtheodor.com/#site" },
    "keywords": "{{keywords}}"
  }
  </script>
  <article class="post note" id="{{slug}}">
    <div class="post-date">{{Month D, YYYY}}</div>
    <h2 class="post-title">{{headline}}</h2>
    <div class="post-body" lang="he" dir="rtl">
      <p>{{Hebrew paragraph}}</p>
    </div>
    <div class="post-body post-body-en" lang="en" dir="ltr">
      <p>{{Full English translation of the paragraph}}</p>
    </div>
  </article>
```

### Step 2.3: Add the image (if any)

Drop the image file into `images/`, named `YYYY-MM-DD-{{slug}}.jpg` (or `.png`), matching the date and slug of the post. Keep file size reasonable for the web (existing images are optimized to roughly 900px wide, JPEG quality ~72), resize/compress before adding if the source image is large. Reference it in the `<img src="images/...">` tag exactly as named.

---

## 3. Run the build script (do not skip this)

```bash
cd "$(git rev-parse --show-toplevel)"   # run from anywhere inside the checkout
python3 build.py
```

This regenerates, **for every post including the new one**:
- `radar/<slug>/index.html`, a standalone, indexable page for that post (title, meta tags, OpenGraph, JSON-LD, breadcrumb, the post content, and a "More from Art Radar" list)
- `radar/index.html`, the archive of every post
- `index.html`, the homepage: its Art Radar timeline shows the six newest posts and the post count
- `sitemap.xml`, completely rewritten from scratch with every page of the site
- the advisory, projects, partner and guide pages (unchanged unless their JSON changed)

It also rewrites, in `content/posts.html` itself:
- Each post's JSON-LD `url` / `mainEntityOfPage` from a same-page anchor (`#slug`) to the real permalink (`/radar/slug/`), if not already set

Then it runs the gates in `tools/check_site.py`: no em or en dashes in the chrome, no phone numbers anywhere, every page has matching English and Hebrew twins, every internal link resolves, every JSON-LD block parses, and every page opens in English (`<html lang="en">`, `<body class="lang-en">`, at least 90% of the visible words Latin). A failed gate prints what and where; fix it and run again. Before pushing, `node tools/check_render.js` repeats the language check in a real browser (headless Chromium through the global Playwright install) and proves the switch shows Hebrew and remembers it.

It does NOT add any visible "Permalink" link to the post cards. Those were removed by the site owner on 2026-07-02; never add one to a post.

**If the build stops with "STOP: index.html contains an Art Radar article"**, a post was pasted into `index.html`. Move its JSON-LD `<script>` + `<article>` pair to the top of `content/posts.html`, run `git checkout index.html`, and build again. **If it errors with "No posts found in content/posts.html"**, the pair you added doesn't match the exact structure above (usually a missing/extra blank line, or the `id="slug"` attribute missing on the `<article>` tag). Fix the structure to match the template exactly and re-run.

---

## 4. Update `llms.txt` and `agent.txt` (the build script does NOT do this)

These two files are curated, hand-maintained summaries that AI crawlers (ChatGPT, Claude, Perplexity, etc.) read to understand and cite the site. They must be updated manually for every new post, using the **real permalink** (not an anchor fragment):

**In `llms.txt`**, under `## Recent Posts (Art Radar Archive)`, add a new line at the top of the list:

```
- [{{English headline}}](https://stavtheodor.com/radar/{{slug}}/): {{Month D, YYYY}}. {{1-sentence English summary}}
```

**In `agent.txt`**, under the matching `## Recent Posts` month heading (add a new month heading if needed), add:

```
- {{English headline}} ({{1-sentence summary}}, {{key dates}}): https://stavtheodor.com/radar/{{slug}}/
```

Also bump the "Structured Data Available" / archive references if you added a new venue not already listed in `agent.txt`'s "Venues Covered" section.

**Do not use `stavtheodor.com/#slug` (anchor) URLs in these two files**, only the real `/radar/slug/` permalinks. That was a stale pattern from before the permalink system existed; keep it fixed going forward.

---

## 5. Commit and push

```bash
cd "$(git rev-parse --show-toplevel)"   # run from anywhere inside the checkout
git add -A
git commit -m "Add post: {{headline}}"
git push origin main
```

`git add -A` is safe here: the generated artifacts (`radar/<slug>/index.html`, `radar/index.html`, `index.html`, `sitemap.xml`) all belong in the commit, they are the live pages, not build scratch. Check `git status` first and leave any file you did not change and do not recognize alone (AGENTS.md Section 1.5).

GitHub Pages redeploys automatically within roughly a minute of the push. No manual deploy trigger, no build step on GitHub's side (the repo is served as-is).

---

## 6. Verify it went live

```bash
# Homepage timeline (six newest) and the archive show the new post
curl -s https://stavtheodor.com/ | grep -o '{{slug}}'
curl -s https://stavtheodor.com/radar/ | grep -o '{{slug}}'

# The standalone permalink page works
curl -s -o /dev/null -w "%{http_code}\n" https://stavtheodor.com/radar/{{slug}}/
curl -s https://stavtheodor.com/radar/{{slug}}/ | grep -oiE "<title>[^<]*</title>"

# Sitemap includes it
curl -s https://stavtheodor.com/sitemap.xml | grep '{{slug}}'
```

Expect `200` and the correct title. **GitHub's CDN caches responses for ~10 minutes** (`Cache-Control: max-age=600`). If a check doesn't show the update immediately, that's expected, wait a few minutes and retry before assuming something is wrong. To bypass the cache entirely for a fast check:

```bash
curl -sk --resolve stavtheodor.com:443:185.199.108.153 https://stavtheodor.com/radar/{{slug}}/
```

---

## 7. What NOT to do

- **Never hand-edit `index.html`, `radar/<slug>/index.html`, `radar/index.html` or `sitemap.xml`.** They're generated. Edit `content/posts.html` and run `python3 build.py` instead. A post pasted into `index.html` stops the build until it is moved.
- **Never push to `old-backup`** (a deprecated, inert copy of this repo). Always push to `origin`.
- **Never touch DNS, GoDaddy, or the domain/HTTPS setup** to add a blog post, none of that is relevant here, it's already configured and stable. If something about the *domain itself* seems broken (not the content), stop and flag it to the site owner rather than guessing.
- **Never modify the Google Analytics tag** (`G-4300MN0Q97` in `index.html`'s `<head>`). It's domain-agnostic and needs no changes, ever.
- **Never commit secrets.** This repo has none, and none should ever be added to it.
- **Don't force-push.** There's no scenario where adding a blog post requires it.

---

## 8. Quick reference (copy-paste checklist)

```
1. Add {JSON-LD <script> + <article>} pair to content/posts.html, right under the POST TEMPLATE comment
   - Hebrew body block AND full English translation block (post-body-en). Both. Always.
   - NEVER into index.html (generated; the build stops if a post is there)
2. Add image to images/ (if any), named YYYY-MM-DD-slug.jpg
3. python3 build.py
4. Update llms.txt, agent.txt and answers.md (real /radar/slug/ URL, not #slug anchor)
5. git remote -v  →  confirm origin = Ronkimhi/stavtheodor.git
6. gh auth status  →  confirm active account = Ronkimhi
7. git add -A && git commit -m "Add post: ..." && git push origin main
8. curl stavtheodor.com/radar/slug/  →  200, correct title (allow ~10 min CDN cache)
```
