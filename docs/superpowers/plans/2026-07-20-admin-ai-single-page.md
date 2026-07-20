# Admin AI Single Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the persistent AI conversation workspace into the existing data overview page and expose actionable safe DeepSeek error categories.

**Architecture:** Reuse the existing conversation models, service, and JSON actions. Render a compact conversation panel from `data_overview.html`, adapt the vanilla JavaScript from sidebar buttons to a conversation select, redirect the old full-page route, and remove its SimpleUI menu entry. Extend the DeepSeek exception with a status code and map it to safe stored error categories.

**Tech Stack:** Django Admin/SimpleUI, Django ORM, Python urllib, vanilla JavaScript, CSS, Django TestCase.

---

### Task 1: Safe DeepSeek Upstream Diagnosis

**Files:**
- Modify: `main/services/deepseek_client.py`
- Modify: `main/services/analytics_conversation.py`
- Modify: `main/tests/test_deepseek_client.py`
- Modify: `main/tests/test_analytics_conversation.py`

- [ ] Write failing tests asserting HTTP 401/402/429/500 preserve only `status_code`, and orchestration maps them to `authentication`, `balance`, `rate_limit`, and `upstream`.
- [ ] Run both service test modules and confirm the new expectations fail.
- [ ] Add `status_code` to `DeepSeekUpstreamError` and a safe `_error_code()` mapper without storing exception text.
- [ ] Run both service test modules and confirm they pass.
- [ ] Commit with `fix: classify DeepSeek upstream failures`.

### Task 2: Embed Compact Chat in Data Overview

**Files:**
- Modify: `main/admin.py`
- Modify: `main/admin_ai_views.py`
- Modify: `main/templates/admin/data_overview.html`
- Delete: `main/templates/admin/ai_analytics.html`
- Modify: `main/static/main/admin_ai.css`
- Modify: `main/static/main/admin_ai.js`
- Modify: `config/settings.py`
- Modify: `main/tests/test_admin.py`
- Modify: `main/tests/test_admin_ai_views.py`

- [ ] Write failing tests asserting the data overview contains all compact chat controls, the menu omits the AI item, and the old URL redirects to data overview.
- [ ] Run admin test modules and verify the layout expectations fail.
- [ ] Add owned conversations to `data_overview`, redirect the old page view, remove the menu item, and embed the compact semantic markup after the stat grid.
- [ ] Adapt CSS to one bordered full-width panel with a fixed-height message region and responsive controls; remove sidebar-specific layout.
- [ ] Adapt JavaScript to a conversation `<select>` while preserving create, load, ask, retry, CSRF, `textContent` rendering, query-string restoration, loading and error states.
- [ ] Run admin tests and Node syntax check.
- [ ] Commit with `feat: embed AI chat in data overview`.

### Task 3: Verify and Deploy

**Files:**
- Modify only scoped defects found by verification.

- [ ] Run `manage.py check`, `manage.py test`, migration dry run, collectstatic, `git diff --check`, and a long-token secret scan.
- [ ] Preserve the user's local `.env.example` and `audio/` changes outside commits.
- [ ] Push `main`, wait for the new static asset to deploy, and verify data overview redirects/authentication and bootstrap health.
