# Headless CMS Migration & Enhancement Plan

Status: Draft
Owner: Platform Team
Last updated: 2025-08-07

## Objectives

Convert the current hybrid Wagtail setup into a robust headless platform consumed by the React SPA, while keeping Wagtail Admin for editors. Improve API consistency, preview, media handling, caching, search, and developer ergonomics. Optional enhancements include GraphQL, multi-site readiness, and CDN/media hardening.

## Scope (What we will deliver)

- Consistent, versioned JSON APIs for all Wagtail content with standardized pagination, absolute media URLs, and safe HTML.
- Headless preview flow for drafts with secure tokenization and SPA integration.
- Production-grade CORS/CSRF and security headers.
- Image rendition service in API responses.
- Cache strategy with ETag/Last-Modified and revalidation hooks.
- Navigation and sitemap endpoints for SPA.
- Unified search endpoint across Wagtail content.
- API schema and docs exposed in dev and prod.
- Redirect/slug history handling for headless routes.
- Optional: GraphQL (wagtail-grapple), multi-site/domain support, media via CDN with CORS.

## Success criteria

- SPA renders all Wagtail-driven pages (blog, courses, lessons, exercises, playground, homepage) exclusively from APIs.
- Editors can preview drafts in SPA via secure preview URLs.
- All images in SPA use rendition URLs with width/height and alt text.
- API responses cacheable and invalidated within 1 minute of publish/unpublish.
- Single, consistent pagination format for list endpoints.
- Search returns relevant mixed results (blog/tutorial/course/lesson) in <200 ms P95 (with cache warm).
- Swagger/Redoc available; endpoints covered by automated tests.

---

## Phasing & Milestones

### Phase 0 — Discovery & groundwork (0.5 week)
- Audit current endpoints under `/api/v1/wagtail/*` and `/api/v1/learning/*` in `apps/api/views.py`.
- Inventory StreamField block types in `apps/blog/models.py` and current serialization patterns.
- Decide production routing posture: keep hybrid (Wagtail catch‑all) vs SPA-only for public routes. Default: hybrid now, SPA-only later.
- Define SPA preview route pattern, e.g., `/preview/:contentType/:slug?token=...`.

Deliverables
- Signed architectural note in this doc; checklist of impacted endpoints.

### Phase 1 — API consistency & security baseline (1 week)
- Standardize DRF pagination for list endpoints (blog list, courses list, etc.) to DRF PageNumberPagination.
- Expose schema and docs:
  - `/api/schema/` (OpenAPI JSON)
  - `/api/docs/` (Swagger/Redoc)
- Harden production CORS/CSRF in `learning_community/settings/production.py`:
  - CORS_ALLOWED_ORIGINS, CORS_ALLOW_CREDENTIALS=True when needed
  - CSRF_TRUSTED_ORIGINS for SPA/admin domains
  - Explicit allowed headers/methods
- Add Content Security Policy (CSP) in prod settings.

Deliverables
- Consistent pagination envelope `{count, next, previous, results}`.
- OpenAPI served in dev/prod.
- CORS/CSRF/CSP verified in prod-like environment.

### Phase 2 — StreamField serialization & rich text safety (1 week)
- Create a reusable serialization module, e.g., `apps/api/serializers/streamfield.py`:
  - Map all known block types to JSON structures.
  - Convert RichText to sanitized HTML (bleach with allowlist) or plain text as needed.
  - Handle unknown blocks by logging and returning a safe fallback.
- Add utilities for absolute URLs using `request.build_absolute_uri()`.
- Refactor `apps/api/views.py` Wagtail endpoints to use the shared serializer.

Deliverables
- Unified serialization for BlogPage, CoursePage, LessonPage, ExercisePage, HomePage, CodePlaygroundPage.
- Unit tests for serializer coverage and safety.

### Phase 3 — Images & renditions (0.5–1 week)
- Add image rendition utility, e.g., `apps/api/serializers/images.py`:
  - Return `{src, width, height, alt}` for named renditions (e.g., `fill-640x360`, `max-1280x`), plus original URL.
  - Absolute URLs; include `srcset` where helpful.
- Integrate with BlogPage featured images, inline images, course images, etc.

Deliverables
- All image references in API include rendition metadata.

### Phase 4 — Headless preview (1 week)
- Add `wagtail-headless-preview` or custom token-based preview:
  - On preview, generate a signed, short-lived token bound to the specific draft revision and user.
  - Implement `/api/v1/preview/[<content_type>/]<id or slug>/` to return draft JSON when token is valid.
  - SPA preview route consumes this token and renders the content.
- Add `get_preview_url()` to page models to point editors to SPA preview URL.

Deliverables
- Editors can click “Preview” in Wagtail and see SPA preview with draft content.
- Tokens expire and are single-use or short-lived.

### Phase 5 — Caching & revalidation (1 week)
- Add ETag/Last-Modified to read endpoints; honor Conditional GET.
- Add Cache-Control for public endpoints (short TTL, e.g., 60s) + CDN-friendly headers.
- Wire Wagtail signals (`page_published`, `page_unpublished`, `page_moved`) to:
  - Purge CDN keys / call `/api/v1/revalidate/` (protected) per affected slugs.
  - Invalidate server-side cache keys.

Deliverables
- Revalidation flow documented; automated tests for cache headers and invalidation.

### Phase 6 — Navigation & sitemap (0.5 week)
- Create Menu snippet (main, footer) with order and URL/slug targets.
- Endpoints:
  - `/api/v1/navigation/main/`
  - `/api/v1/navigation/footer/`
- Add sitemap endpoints:
  - XML: `/sitemap.xml` covering SPA routes
  - JSON: `/api/v1/sitemap/` (optional) for client-side prefetch.

Deliverables
- SPA consumes nav endpoints; sitemap verified by search engines.

### Phase 7 — Unified search (0.5–1 week)
- Implement `/api/v1/search/` that searches BlogPage, TutorialPage, CoursePage, LessonPage using Wagtail search.
- Return typed results with `type`, `title`, `slug`, `excerpt`, `image`.
- Optional: field boosting and filters (content type, level, category).

Deliverables
- Search endpoint with tests and pagination.

### Phase 8 — Routing posture in production (decision + 0.5 week)
- Option A (Hybrid): keep `include('wagtail.urls')` but ensure SPA owns public marketing/learning routes.
- Option B (Headless-only): remove catch‑all in prod via env flag; serve only admin, docs, images, documents from Wagtail.
- Implement ENV toggle, update `learning_community/urls.py` accordingly.

Deliverables
- Clear routing policy with env toggle and tests.

### Phase 9 — Redirects & slug history (0.5 week)
- Ensure `wagtail.contrib.redirects` is active (already installed).
- For API consumers, consider exposing an endpoint to check historical slugs or let edge handle 301s.
- Add guidance for editors on slug changes and automated redirect rules.

Deliverables
- Verified 301 behavior after slug changes; SPA gracefully handles redirects.

### Phase 10 — API documentation & SDKs (0.5 week)
- Finalize OpenAPI with `drf-spectacular` extensions/annotations.
- Publish Swagger/Redoc endpoints and generate client stubs if useful.

Deliverables
- API docs live; optional TS client for SPA.

### Phase 11 — Optional: GraphQL (wagtail-grapple) (1–2 weeks)
- Add `wagtail-grapple` to expose typed GraphQL schema.
- Define types for BlogPage, CoursePage, LessonPage, ExercisePage, HomePage.
- Add image rendition fields and rich text handling.
- Keep REST for backwards compatibility; add feature flag to SPA to test GraphQL.

Deliverables
- GraphQL endpoint with authentication and pagination; example queries; SPA POC.

### Phase 12 — Optional: Multi-site & CDN media (0.5–1 week)
- Multi-site awareness: use `Site` in serializers and absolute URLs; per-site CORS/CSRF.
- Media via CDN (e.g., S3+CloudFront): configure storage backend; set media CORS and signed URLs if needed.
- Ensure rendition URLs are cache-friendly; add `Vary` headers if auth-based.

Deliverables
- Multi-site doc; CDN-backed media with correct CORS and caching.

### Phase 13 — Preview UX polish (0.5 week)
- Add “Preview in SPA” button in Wagtail admin via `get_preview_url()` or admin hook.
- Show revision info and badges in SPA (Draft/Unpublished).
- Auto-refresh/notification when revision is updated (optional).

Deliverables
- Editor-friendly preview experience end-to-end.

---

## Implementation details (by area)

### Files and modules to add
- `apps/api/serializers/streamfield.py` — canonical StreamField → JSON serializer
- `apps/api/serializers/images.py` — rendition utilities (absolute URLs)
- `apps/api/serializers/common.py` — helpers (rich text sanitize, absolute URL builder)
- `apps/api/navigation.py` — menu endpoints
- `apps/api/search.py` — unified search endpoint
- `apps/api/preview.py` — headless preview endpoints/token validation
- `apps/api/revalidate.py` — protected revalidation endpoint (CDN purge/webhook)
- `apps/api/sitemap.py` — JSON sitemap (optional)
- `apps/blog/admin_hooks.py` — preview URL integration (if needed)

### Settings & config
- `learning_community/settings/production.py`
  - CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, CORS_ALLOW_CREDENTIALS
  - CSP headers; SecurityMiddleware config
- `learning_community/urls.py` — add schema/docs routes; add env‑guarded wagtail catch‑all
- `requirements.txt` — add bleach, wagtail-headless-preview, wagtail-grapple (optional)

### API behavior standards
- Pagination: DRF PageNumberPagination everywhere for lists
- Dates: ISO 8601 strings with timezone
- Images: `{src, width, height, alt, srcset?}`
- Rich text: sanitized HTML under `html`, plus optional `text` excerpt
- Caching: ETag + Last-Modified + Cache-Control (public, max-age=60) on read endpoints
- Errors: consistent JSON error envelope

### Security
- Preview tokens: signed, short-lived, audience scoped (content type + id), single-use optional
- Sanitize all rich text and raw HTML blocks; keep allowlist narrow
- CSP configured (script-src, img-src, connect-src for API/CDN)
- CORS in prod restricted to known SPA domains

### Editor-safe sanitization strategy (CodeMirror 6 friendly)
- Never sanitize or transform code-bearing fields; treat them as plain text (not HTML):
  - Fields: `code`, `starter_code`, `solution_code`, `template` (with `{{BLANK_N}}`), `choices`, `question_data`, `alternative_solutions`, `ai_hints`.
  - Transport as strings/JSON; do not render via `dangerouslySetInnerHTML`.
- For RichText fields (display content only), sanitize server-side with a minimal allowlist:
  - Tags: `p, ul, ol, li, br, strong, em, blockquote, h2, h3, h4, code, pre, table, thead, tbody, tr, th, td, a`.
  - Attributes: `a[href|title|target]` (auto-add `rel="nofollow noopener noreferrer"`), `code[class]` (optional), no `on*` handlers.
  - Protocols: `http, https, mailto`.
- Embed/raw HTML blocks: avoid passing raw HTML. Prefer oEmbed/URL-based blocks or whitelist known providers and render SPA-side via sandboxed `iframe` with strict attributes.
- Frontend rendering rules:
  - CodeMirror components receive plain strings only (never sanitized HTML).
  - Any HTML display uses sanitized `html` from API; avoid `dangerouslySetInnerHTML` for code blocks.
  - Escape when showing code outside editors (render inside `<pre><code>` with textContent).
- Contract by block type:
  - `code_example`, `runnable_code_example`, `interactive_exercise`, `fill_blank_code`, `multiple_choice_code`: keep code/templates as opaque strings; sanitize only descriptive RichText subfields.
  - Blog `body` RichText: keep `paragraph/heading/callout/quote` as sanitized HTML; surface `code` as `{language, code}` object for editor rendering if needed.

### CSP allowances for editors
- Ensure CSP supports editors without weakening security:
  - `script-src 'self'` (avoid inline; use hashes if needed for critical inline),
  - `style-src 'self' 'unsafe-inline'` (if Tailwind/dev injects styles),
  - `connect-src 'self' https://api-hosts ...` (API, code execution service),
  - `img-src 'self' data: https://cdn-hosts ...`,
  - `worker-src 'self' blob:` (for web workers used by some CM6 addons),
  - `frame-src` limited to approved providers (YouTube, CodePen) if embeds present.

---

## Testing & QA

- Unit tests for serializers (blocks, images, rich text)
- API tests for list/detail endpoints with pagination and caching headers
- Preview flow tests: token issuance, expiry, invalid token
- Navigation and sitemap tests
- Search endpoint tests (filters, boosting, pagination)
- E2E: SPA consumes endpoints for blog/course/lesson/exercise; image rendering verified
- Performance: cache warm latency P95 < 200 ms for read endpoints
- Editor safety: tests assert that code-bearing fields are returned unchanged and that `{{BLANK_N}}` markers are preserved.

---

## Rollout plan

- Ship Phase 1–3 to a staging environment; update SPA to consume new envelopes (pagination/images).
- Gate preview (Phase 4) behind feature flag; pilot with editors.
- Enable caching and revalidation (Phase 5) with staging CDN; monitor.
- Proceed with navigation, search, routing decision in production window.
- Optional enhancements scheduled after core is stable.

---

## Risks & mitigations

- Serialization regressions → Feature-flag and dual-run old/new serializers temporarily.
- Preview token misuse → Short TTL, signature, scope, audit logging.
- CORS/CSRF misconfig → Staged validation, automated integration tests.
- Cache staleness → Revalidation on publish/unpublish signals; manual purge endpoint.
- Image rendition load → Pre-generate common sizes; CDN caching.

---

## Task checklist (condensed)

- [ ] DRF pagination standardized across all list endpoints
- [ ] OpenAPI schema + docs routes
- [ ] Production CORS/CSRF/CSP hardened
- [ ] Shared StreamField serializer
- [ ] RichText sanitization
- [ ] Image renditions with absolute URLs
- [ ] Headless preview (tokens, endpoint, SPA route)
- [ ] Cache headers + revalidation endpoint + Wagtail signal hooks
- [ ] Navigation endpoints + Menu snippet
- [ ] Sitemap (XML + optional JSON)
- [ ] Unified search endpoint
- [ ] Routing env toggle (hybrid vs headless-only)
- [ ] Redirects/slug history validation
- [ ] API docs finalized
- [ ] Optional: GraphQL endpoint
- [ ] Optional: Multi-site & CDN media
- [ ] Optional: Preview UX polish in admin + SPA

---

## Estimates (rough)

- Core (Phases 1–8, 10): ~4–5 weeks including tests and staging
- Optional GraphQL: 1–2 weeks
- Multi-site + CDN: 0.5–1 week
- Preview UX polish: 0.5 week

