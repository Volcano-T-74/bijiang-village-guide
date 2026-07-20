# Django Admin AI Conversation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent, staff-only AI operations conversation workspace inside Django Admin with continuous follow-up context and structured DeepSeek answers.

**Architecture:** Store staff-owned conversations and question/answer turns in two Django models. A focused conversation service builds anonymous metrics, selects the last six completed turns, calls the existing DeepSeek client, and persists success or safe failure state. Custom admin-protected Django views expose the page and JSON actions; a Django template plus small static CSS/JavaScript layer provides the chat UI without changing Vue.

**Tech Stack:** Django 5.2, Django Admin/SimpleUI, Django ORM and migrations, Django forms, Python `urllib.request`, vanilla JavaScript, CSS, Django TestCase.

---

### Task 1: Persistent Conversation Models

**Files:**
- Modify: `main/models.py`
- Create: `main/migrations/0007_analyticsconversation_analyticsturn.py`
- Create: `main/tests/test_ai_conversation_models.py`

- [ ] **Step 1: Write failing ownership and turn-state tests**

Create tests that instantiate `AnalyticsConversation(owner, title, default_days)` and `AnalyticsTurn(conversation, question, status, answer, metrics_snapshot, model)`, assert chronological ordering and cascade deletion, and assert the day constraint rejects values outside 7/30/90 through model validation.

- [ ] **Step 2: Run the model tests and verify RED**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_ai_conversation_models`

Expected: import failure because both models do not exist.

- [ ] **Step 3: Implement the models**

Add `AnalyticsConversation` with `owner`, `title`, `default_days`, `created_at`, and `updated_at`. Add `AnalyticsTurn.Status` choices (`pending`, `completed`, `failed`) and fields `conversation`, `question`, `answer`, `metrics_snapshot`, `model`, `days`, `status`, `error_code`, `created_at`, and `answered_at`. Use `CheckConstraint` for allowed day values and indexes for owner/update and conversation/create ordering.

- [ ] **Step 4: Generate and inspect migration**

Run: `.\.venv\Scripts\python.exe manage.py makemigrations main`

Expected: `0007_analyticsconversation_analyticsturn.py` containing both tables, constraints, indexes, and the user dependency.

- [ ] **Step 5: Run model tests and migration check**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_ai_conversation_models`

Run: `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`

Expected: tests pass and `No changes detected`.

- [ ] **Step 6: Commit models**

```powershell
git add main/models.py main/migrations/0007_analyticsconversation_analyticsturn.py main/tests/test_ai_conversation_models.py
git commit -m "feat: persist staff AI conversations"
```

### Task 2: Continuous DeepSeek Context

**Files:**
- Modify: `main/services/deepseek_client.py`
- Modify: `main/tests/test_deepseek_client.py`

- [ ] **Step 1: Write a failing history payload test**

Call `analyze_visitor_metrics(question, metrics, history=[{"question": "第一名是谁？", "answer": ANALYSIS}])`, decode the mocked request, and assert messages appear in this order: system, prior user question, prior assistant JSON, current user metrics/question. Assert private identifiers are absent.

- [ ] **Step 2: Run the client tests and verify RED**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_deepseek_client`

Expected: `TypeError` because `history` is not accepted.

- [ ] **Step 3: Extend the client minimally**

Change the signature to `analyze_visitor_metrics(question, metrics, history=None)`. Build prior messages from `history or []`, serialize assistant answers with `ensure_ascii=False`, and retain current metrics only in the final user message. Do not change error mappings or required response fields.

- [ ] **Step 4: Run client tests**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_deepseek_client`

Expected: all client tests pass.

- [ ] **Step 5: Commit client context support**

```powershell
git add main/services/deepseek_client.py main/tests/test_deepseek_client.py
git commit -m "feat: add context to DeepSeek analytics"
```

### Task 3: Conversation Orchestration Service

**Files:**
- Create: `main/services/analytics_conversation.py`
- Create: `main/tests/test_analytics_conversation.py`

- [ ] **Step 1: Write failing success/context tests**

Seed a staff-owned conversation with seven completed turns and one failed turn. Mock `build_visitor_metrics` and `analyze_visitor_metrics`, call `ask_analytics_question(conversation, question, days)`, and assert only the latest six completed turns are passed in chronological order. Assert the new turn stores the answer, metrics snapshot, model, `completed`, and `answered_at`.

- [ ] **Step 2: Write failing safe-failure and retry tests**

For each existing DeepSeek exception, assert a turn remains stored with `failed`, an empty answer, and one of `configuration`, `timeout`, `upstream`, or `response`. Call `retry_analytics_turn(turn)` and assert it reuses the question but refreshes metrics and can transition the same turn to `completed`.

- [ ] **Step 3: Run service tests and verify RED**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_analytics_conversation`

Expected: module import failure.

- [ ] **Step 4: Implement orchestration**

Implement `ask_analytics_question(conversation, question, days)` and `retry_analytics_turn(turn)`. Create/save pending state before the external call, build history from `conversation.turns.filter(status="completed").order_by("-created_at")[:6]` reversed to chronological order, persist success fields atomically after the call, and map known exceptions to safe codes without storing exception text.

- [ ] **Step 5: Run service tests**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_analytics_conversation`

Expected: all service tests pass.

- [ ] **Step 6: Commit service**

```powershell
git add main/services/analytics_conversation.py main/tests/test_analytics_conversation.py
git commit -m "feat: orchestrate persistent AI analysis turns"
```

### Task 4: Staff-Only Admin Routes

**Files:**
- Create: `main/admin_ai_views.py`
- Create: `main/forms.py`
- Modify: `config/urls.py`
- Create: `main/tests/test_admin_ai_views.py`

- [ ] **Step 1: Write failing page and ownership tests**

Cover anonymous redirect to `admin:login`, staff access to `/admin/ai-analytics/`, ordinary-user rejection, own-conversation listing, and a 404 when reading another employee's conversation.

- [ ] **Step 2: Write failing action tests**

Cover conversation creation with days 7/30/90, validation failures for other values or blank/over-1000 questions, successful ask serialization, failed ask safe response, and retry ownership. Patch the orchestration service so endpoint tests never call DeepSeek.

- [ ] **Step 3: Run view tests and verify RED**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_admin_ai_views`

Expected: 404 because routes do not exist.

- [ ] **Step 4: Implement forms and views**

Add `AnalyticsConversationForm(default_days=ChoiceField(7,30,90))` and `AnalyticsQuestionForm(question=CharField(max_length=1000), days=ChoiceField(...))`. Implement page, create, detail, ask, and retry views. Every conversation/turn query must filter through `owner=request.user`; serialize only IDs, titles, dates, status, question, structured answer, days, and safe error code.

- [ ] **Step 5: Register protected routes**

Add named routes in `config/urls.py`, wrapping every view with `admin.site.admin_view`:

```python
path("admin/ai-analytics/", admin.site.admin_view(ai_analytics_page), name="admin_ai_analytics"),
path("admin/ai-analytics/conversations/", admin.site.admin_view(create_conversation), name="admin_ai_conversation_create"),
path("admin/ai-analytics/conversations/<int:conversation_id>/", admin.site.admin_view(conversation_detail), name="admin_ai_conversation_detail"),
path("admin/ai-analytics/conversations/<int:conversation_id>/ask/", admin.site.admin_view(ask_conversation), name="admin_ai_conversation_ask"),
path("admin/ai-analytics/turns/<int:turn_id>/retry/", admin.site.admin_view(retry_turn), name="admin_ai_turn_retry"),
```

- [ ] **Step 6: Run view tests**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_admin_ai_views`

Expected: all route, permission, validation, and serialization tests pass.

- [ ] **Step 7: Commit admin routes**

```powershell
git add main/admin_ai_views.py main/forms.py config/urls.py main/tests/test_admin_ai_views.py
git commit -m "feat: add staff AI conversation routes"
```

### Task 5: Admin Conversation Interface

**Files:**
- Create: `main/templates/admin/ai_analytics.html`
- Create: `main/static/main/admin_ai.css`
- Create: `main/static/main/admin_ai.js`
- Modify: `config/settings.py`
- Modify: `main/tests/test_admin.py`
- Modify: `main/tests/test_admin_ai_views.py`

- [ ] **Step 1: Write failing menu and markup tests**

Assert `SIMPLEUI_CONFIG["menus"]` includes an “AI 运营分析” item pointing to `/admin/ai-analytics/`. Assert the rendered page contains accessible labels for conversation selection, 7/30/90 day options, question input, send button, new conversation button, live result region, example prompts, and static CSS/JS references.

- [ ] **Step 2: Run admin tests and verify RED**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_admin main.tests.test_admin_ai_views`

Expected: missing menu item/template assertions fail.

- [ ] **Step 3: Implement the template**

Extend `admin/base_site.html`; keep SimpleUI breadcrumbs and content width. Render a left conversation rail and right chat work area. Use semantic buttons, `<label>`, `<select>`, `<textarea>`, an `aria-live="polite"` status region, and data attributes containing named route templates and CSRF token. Render no unescaped user or AI HTML.

- [ ] **Step 4: Implement restrained admin styling**

Use existing blue accent, white surfaces, 6px radii, fixed 14–16px UI type, visible keyboard focus, stable control heights, compact structured answer sections, responsive single-column layout below 860px, and reduced-motion handling. Do not add nested decorative cards, gradients, custom icons, or unrelated animation.

- [ ] **Step 5: Implement browser behavior**

In `admin_ai.js`, implement conversation creation/switching, question POST, loading/disabled state, structured answer rendering via `textContent`, error/retry state, example prompt insertion, and automatic selection of the newest conversation. Never use `innerHTML` with server data. Preserve the current conversation on refresh via the query string `?conversation=<id>`.

- [ ] **Step 6: Add the SimpleUI menu entry**

Add a top-level “AI 运营分析” menu item with `fas fa-comments` and `/admin/ai-analytics/`, adjacent to “数据概览”. Update the exact menu-set test accordingly.

- [ ] **Step 7: Run admin tests**

Run: `.\.venv\Scripts\python.exe manage.py test main.tests.test_admin main.tests.test_admin_ai_views`

Expected: menu and rendered-page tests pass.

- [ ] **Step 8: Commit interface**

```powershell
git add main/templates/admin/ai_analytics.html main/static/main/admin_ai.css main/static/main/admin_ai.js config/settings.py main/tests/test_admin.py main/tests/test_admin_ai_views.py
git commit -m "feat: add admin AI conversation workspace"
```

### Task 6: Full Verification and Deployment

**Files:**
- Modify only scoped defects revealed by verification.

- [ ] **Step 1: Run Django verification**

Run: `.\.venv\Scripts\python.exe manage.py check`

Run: `.\.venv\Scripts\python.exe manage.py test`

Expected: no system-check issues and all tests pass without a real DeepSeek call.

- [ ] **Step 2: Verify migration and static collection**

Run: `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`

Run: `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`

Expected: no model changes and static files collect successfully.

- [ ] **Step 3: Run security and diff checks**

```powershell
git diff --check
git grep -n -I -E "sk-[A-Za-z0-9]{20,}" -- . ':!docs/superpowers/'
git status --short
```

Expected: no secret token; only task files are staged/tracked and the user's `audio/` remains untouched.

- [ ] **Step 4: Push and production acceptance**

Push `main`, wait for Render migration/deploy, then verify `/admin/ai-analytics/` with a staff account. Create a conversation, ask one question, ask “那第二名呢？”, refresh the page, and confirm both turns remain visible. Confirm a slow or failed DeepSeek request leaves the admin responsive and produces a retryable safe error.
