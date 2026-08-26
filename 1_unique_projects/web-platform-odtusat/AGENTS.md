# Project Rules and Constraints

## Stack
- **Static site generator:** Hugo
- **CMS:** Decap CMS (`static/admin/`)
- **Hosting:** Cloudflare Pages (Firebase is not used)

## Must-follow constraints
- **Hugo Asset Paths**: DO NOT add leading spaces inside the quote of a Hugo `relURL` or `relLangURL` call.
  - **Correct**: `{{ "assets/images/logo.png" | relURL }}`
  - **Incorrect**: `{{ " assets/images/logo.png" | relURL }}`
  - Leading spaces cause Hugo to generate URLs with `%20` encoded spaces (e.g., `/%20assets/...`), which breaks image and link rendering.
- Do not introduce Node.js, bundlers (Webpack/Vite), or package managers (`npm`/`yarn`) — Hugo handles all builds natively.
- The site is bilingual (TR/EN) using Hugo's built-in i18n support (`i18n/`). Any structural or content change in a Turkish page (`content/tr/`) **MUST** be manually replicated in its English counterpart (`content/en/`).

## Repo-specific conventions
- Base language is Turkish. English content lives under `content/en/`. Check `hugo.toml` for language and URL configuration before adding or renaming pages.
- Hugo outputs to `public/`. Do not manually edit files inside `public/` — they are generated artifacts.
- Decap CMS config lives at `static/admin/config.yml`. Keep collection definitions in sync with the actual content structure.

## Validation before finishing
- If adding, moving, or removing pages, ensure matching TR and EN content files exist and Hugo generates correct URLs for both.
- After structural changes, run `hugo` locally and verify `public/sitemap.xml` contains both TR and EN URLs.
- Verify internal links in `/en/` content point to `/en/...` paths, not their Turkish counterparts.

## Deployment
- Build command: `hugo`
- Output directory: `public`
- Deployed via Cloudflare Pages — do not run any Firebase commands.

## Known gotchas
- The homepage layout in `layouts/index.html` relies on specific class names like `.hero-bg`, `.adopt-bg`, and `.mission-bg` for background images.
- The blog grid is currently set to show only the latest 3 posts.
- **SEO / Indexing:** Search engine indexing is currently disabled via `robots.txt` (`Disallow: /`) and `<meta name="robots" content="noindex, nofollow">` in `layouts/partials/head.html`. **IMPORTANT:** These must be removed/reverted to allow indexing when the site is publicly available.
