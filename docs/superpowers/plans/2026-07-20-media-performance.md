# Media Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and test-driven-development for behavioral changes.

**Goal:** Reduce image payloads, defer noncritical media, and configure durable static caching without changing site behavior.

**Architecture:** Convert referenced large PNG assets to WebP at build-source level, update JS/CSS references and image loading attributes, preserve click-triggered audio with metadata preload, and configure WhiteNoise for Vite hashes plus one-day fallback caching.

**Tech Stack:** Vue/Vite, Pillow WebP encoder, Django/WhiteNoise, Vitest, Django TestCase.

---

### Task 1: Media Loading Behavior

- Add failing frontend assertions for eager first-map loading, lazy content images, and click-created audio metadata preload.
- Update `frontend/src/bijiang/site.js` minimally and run `pnpm test`.

### Task 2: WebP Asset Conversion

- Identify referenced PNG files over 500 KB from JS and CSS.
- Convert with quality 82, using quality 88 for `village-map.png`; resize only non-map images above 1440 pixels.
- Update JS/CSS references, delete replaced PNGs, build, and verify no missing imports.
- Compare before/after image and dist sizes.

### Task 3: WhiteNoise Cache Policy

- Add failing settings tests for a single Vite dist static directory, one-day fallback cache, and Vite hash immutable regex.
- Update `config/settings.py`, run Django tests and collectstatic, and inspect response headers locally/production.

### Task 4: Full Verification And Deployment

- Run `pnpm test`, `pnpm build`, Django checks/tests, migration check, collectstatic, diff check, and secret scan.
- Commit only task files, preserve unrelated working-tree changes, push, and verify production WebP/cache/audio Range behavior.
