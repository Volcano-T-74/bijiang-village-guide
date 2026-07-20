# Local Voices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store five independent local-voice recordings in the backend and play them from a new “当地声音” section on the stories page.

**Architecture:** Add a `LocalVoice` Django model and idempotent import command, expose enabled records through a read-only REST endpoint, and load them independently from the existing bootstrap request. Keep exactly one active `Audio` instance per selected track generation; switching pauses and abandons the old instance so stale media events cannot affect the new recording.

**Tech Stack:** Django 5.2, Django REST Framework, SQLite/PostgreSQL, Vue 3 host component with DOM template renderer, HTMLAudioElement, Vitest

---

### Task 1: Add the independent local-voice model

**Files:**
- Modify: `main/models.py`
- Create: `main/migrations/0003_localvoice.py`
- Modify: `main/admin.py`
- Test: `main/tests/test_models.py`

- [ ] **Step 1: Write a failing model test**

Add a `LocalVoiceTests` test case that creates records and asserts ordering and string representation:

```python
class LocalVoiceTests(TestCase):
    def test_local_voice_is_independent_and_ordered(self):
        second = LocalVoice.objects.create(
            title="乡音记录二",
            original_file_name="two.m4a",
            file_url="/static/audio/two.m4a",
            duration_seconds=20,
            language="local",
            language_label="当地讲述",
            display_order=2,
        )
        first = LocalVoice.objects.create(
            title="乡音记录一",
            original_file_name="one.m4a",
            file_url="/static/audio/one.m4a",
            duration_seconds=10,
            language="local",
            language_label="当地讲述",
            display_order=1,
        )

        self.assertEqual(list(LocalVoice.objects.all()), [first, second])
        self.assertEqual(str(first), "乡音记录一")
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python manage.py test main.tests.test_models.LocalVoiceTests`

Expected: FAIL because `LocalVoice` cannot be imported.

- [ ] **Step 3: Add the model**

```python
class LocalVoice(models.Model):
    title = models.CharField("标题", max_length=100)
    original_file_name = models.CharField("原始文件名", max_length=100, unique=True)
    file_url = models.TextField("音频文件地址")
    duration_seconds = models.PositiveIntegerField("音频时长（秒）")
    language = models.CharField("语言代码", max_length=20, default="local")
    language_label = models.CharField("语言标签", max_length=20, default="当地讲述")
    display_order = models.PositiveSmallIntegerField("后台排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "local_voices"
        ordering = ("display_order", "id")
        verbose_name = "当地声音"
        verbose_name_plural = "当地声音"

    def __str__(self):
        return self.title
```

Run `python manage.py makemigrations main` to generate `0003_localvoice.py`.

- [ ] **Step 4: Register the model in admin**

Add `LocalVoice` to the model import, dashboard statistics, and admin:

```python
@admin.register(LocalVoice)
class LocalVoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "language_label", "duration_seconds",
        "display_order", "is_active", "file_link",
    )
    list_editable = ("display_order", "is_active")
    list_filter = ("language", "is_active")
    search_fields = ("title", "original_file_name")

    @admin.display(description="音频文件")
    def file_link(self, obj):
        return _external_link(obj.file_url, "打开音频")
```

- [ ] **Step 5: Run model tests and Django checks**

Run: `python manage.py test main.tests.test_models.LocalVoiceTests && python manage.py check`

Expected: PASS and no Django check issues.

### Task 2: Import the five audio files idempotently

**Files:**
- Create: `frontend/public/audio/20260719_223040.m4a`
- Create: `frontend/public/audio/20260719_223446.m4a`
- Create: `frontend/public/audio/中原路 4.m4a`
- Create: `frontend/public/audio/国语版 顺德碧江村介绍.m4a`
- Create: `frontend/public/audio/顺德碧江村介绍粤语版.m4a`
- Create: `main/management/commands/import_local_voices.py`
- Create: `main/tests/test_local_voice_import.py`
- Modify: `build.sh`
- Modify: `start.sh`

- [ ] **Step 1: Write a failing import-command test**

Use `call_command("import_local_voices")` twice and assert the exact five records exist once, including title, duration, language labels, and `/static/audio/` URLs.

```python
class LocalVoiceImportTests(TestCase):
    def test_import_is_idempotent(self):
        call_command("import_local_voices", verbosity=0)
        call_command("import_local_voices", verbosity=0)

        self.assertEqual(LocalVoice.objects.count(), 5)
        mandarin = LocalVoice.objects.get(
            original_file_name="国语版 顺德碧江村介绍.m4a"
        )
        self.assertEqual(mandarin.title, "顺德碧江村介绍（普通话）")
        self.assertEqual(mandarin.duration_seconds, 88)
        self.assertEqual(mandarin.language, "zh-CN")
        self.assertEqual(
            mandarin.file_url,
            f"/static/audio/{quote('国语版 顺德碧江村介绍.m4a')}",
        )
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python manage.py test main.tests.test_local_voice_import`

Expected: FAIL because the command does not exist.

- [ ] **Step 3: Copy source recordings into public static assets**

Create `frontend/public/audio/` and copy the five files from `audio/` without deleting or modifying the originals.

- [ ] **Step 4: Implement the import command**

Define a fixed tuple with these records and use `update_or_create(original_file_name=..., defaults=...)`:

```python
LOCAL_VOICES = (
    ("国语版 顺德碧江村介绍.m4a", "顺德碧江村介绍（普通话）", 88, "zh-CN", "普通话"),
    ("顺德碧江村介绍粤语版.m4a", "顺德碧江村介绍（粤语）", 73, "yue", "粤语"),
    ("中原路 4.m4a", "中原路乡音", 118, "local", "当地讲述"),
    ("20260719_223040.m4a", "乡音记录一", 202, "local", "当地讲述"),
    ("20260719_223446.m4a", "乡音记录二", 198, "local", "当地讲述"),
)
```

Build each URL with `quote(file_name)` and preserve `/` using:

```python
file_url = f"/static/audio/{quote(file_name)}"
```

- [ ] **Step 5: Add import to deployment lifecycle**

Run `python manage.py import_local_voices` after migrations in both `build.sh` and `start.sh`. The command is idempotent, so repeated deploys remain safe.

- [ ] **Step 6: Verify the import command**

Run: `python manage.py test main.tests.test_local_voice_import`

Expected: PASS with five records after two imports.

### Task 3: Expose enabled local voices through the API

**Files:**
- Modify: `main/api_views.py`
- Modify: `main/api_urls.py`
- Modify: `main/tests/test_api.py`

- [ ] **Step 1: Write a failing API test**

```python
def test_local_voices_returns_only_active_records_in_display_order(self):
    call_command("import_local_voices", verbosity=0)
    LocalVoice.objects.filter(original_file_name="20260719_223446.m4a").update(
        is_active=False
    )

    response = self.client.get("/api/v1/local-voices/")

    self.assertEqual(response.status_code, 200)
    payload = response.json()
    self.assertEqual(len(payload), 4)
    self.assertEqual(payload[0]["title"], "顺德碧江村介绍（普通话）")
    self.assertNotIn("20260719_223446.m4a", [item["original_file_name"] for item in payload])
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python manage.py test main.tests.test_api.TourismApiTests.test_local_voices_returns_only_active_records_in_display_order`

Expected: FAIL with HTTP 404.

- [ ] **Step 3: Implement the read-only view and URL**

```python
class LocalVoiceListView(APIView):
    def get(self, request):
        voices = LocalVoice.objects.filter(is_active=True).order_by("display_order", "id")
        return Response([
            {
                "id": item.id,
                "title": item.title,
                "original_file_name": item.original_file_name,
                "file_url": item.file_url,
                "duration_seconds": item.duration_seconds,
                "language": item.language,
                "language_label": item.language_label,
            }
            for item in voices
        ])
```

Register `path("local-voices/", LocalVoiceListView.as_view(), name="api-local-voices")`.

- [ ] **Step 4: Verify the API test**

Run the focused test again.

Expected: PASS.

### Task 4: Add the frontend API client and loading state

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/api.test.js`
- Modify: `frontend/src/bijiang/site.js`

- [ ] **Step 1: Write a failing API-client test**

Import `getLocalVoices`, call it, and assert a GET request to `/api/v1/local-voices/` returns the JSON list.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `pnpm test -- -t "loads local voices"`

Expected: FAIL because `getLocalVoices` is not exported.

- [ ] **Step 3: Add the API function**

```javascript
export function getLocalVoices() {
  return request('/local-voices/')
}
```

- [ ] **Step 4: Load voices independently**

Add these state fields:

```javascript
localVoices: [],
localVoicesLoading: true,
localVoicesError: "",
activeLocalVoiceId: null,
localVoicePlaying: false,
localVoiceCurrentTime: 0,
```

Call `getLocalVoices()` separately from bootstrap initialization so a voice API failure does not replace themes and attractions with fallback data. On success set the list; on failure set `localVoicesError = "当地声音暂时无法加载"`; in both cases clear loading and rerender only when the current view is `stories`.

- [ ] **Step 5: Verify the API-client test**

Run the focused test again.

Expected: PASS.

### Task 5: Render and control the stories-page player

**Files:**
- Modify: `frontend/src/bijiang/site.js`
- Modify: `frontend/src/bijiang/site.css`
- Modify carefully: `frontend/src/App.test.js` (preserve existing uncommitted route-test edits)

- [ ] **Step 1: Add failing UI tests**

Extend the default fetch mock with `/api/v1/local-voices/`. Add tests asserting:

```javascript
expect(wrapper.text()).toContain('当地声音')
expect(wrapper.text()).toContain('顺德碧江村介绍（普通话）')
expect(wrapper.get('[data-local-voice-id="1"]').attributes('aria-label')).toContain('播放')
```

Mock `Audio` and assert selecting a second voice calls `pause()` before changing `src` and calling `play()`. Add a rejected `play()` case and assert the toast contains `播放失败`.

- [ ] **Step 2: Run the UI tests and verify RED**

Run: `pnpm test -- -t "local voices"`

Expected: FAIL because no local-voice section or playback actions exist.

- [ ] **Step 3: Render loading, error, empty, and populated states**

Append an unframed `local-voices-section` to `renderStories()`. Each list row contains one play/pause icon button, title, language label, formatted duration, and a progress range only for the active recording. Do not nest cards or add a new navigation item.

- [ ] **Step 4: Implement one-player behavior**

Create one active `Audio` instance per selected track generation inside `createBijiangSite`; at most one is live at a time. On `[data-local-voice-id]` click:

1. Pause the current recording when switching IDs.
2. Set `src` to the selected record URL and reset current time.
3. Toggle pause when the active recording is already playing, without rebinding media listeners.
4. Call `play()` and handle its rejected promise with `showToast("播放失败，请稍后重试")`.
5. On `timeupdate`, update only the active row's current-time label and range.
6. On `ended`, reset playing state and rerender.
7. On range input, set `currentTime` from the selected voice duration.
8. Pause and reset when leaving `stories` or destroying the site.

- [ ] **Step 5: Add responsive styles**

Use existing tokens and stable tracks:

```css
.local-voices-section { margin: 38px 0; }
.local-voice-list { border-block: 1px solid var(--line); }
.local-voice-item { display: grid; grid-template-columns: 48px minmax(0, 1fr) auto; gap: 16px; align-items: center; padding: 18px 4px; }
.local-voice-item + .local-voice-item { border-top: 1px solid var(--line); }
.local-voice-play { display: grid; place-items: center; width: 44px; height: 44px; color: var(--blue); border: 1px solid currentColor; border-radius: 50%; background: transparent; cursor: pointer; }
.local-voice-copy strong, .local-voice-copy small { display: block; }
.local-voice-copy small { margin-top: 4px; color: var(--muted); }
.local-voice-duration { color: var(--muted); font-variant-numeric: tabular-nums; }
.local-voice-progress { grid-column: 2 / -1; width: 100%; accent-color: var(--blue); }
```

At `max-width: 480px`, keep the same three-column structure with a `44px` button and allow title text to wrap.

- [ ] **Step 6: Run frontend tests**

Run: `pnpm test`

Expected: all frontend tests pass.

### Task 6: Apply data and verify end to end

**Files:**
- Modify: `db.sqlite3` through migrations/import (ignored by Git)
- Verify all files above

- [ ] **Step 1: Apply migration and import locally**

Run:

```powershell
python manage.py migrate
python manage.py import_local_voices
```

Expected: five enabled `LocalVoice` records.

- [ ] **Step 2: Verify backend**

Run:

```powershell
python manage.py check
python manage.py test
```

Expected: all backend checks and tests pass.

- [ ] **Step 3: Verify frontend**

Run:

```powershell
pnpm test
pnpm build
```

Expected: all frontend tests pass and Vite build succeeds with five `.m4a` assets in `dist/audio/`.

- [ ] **Step 4: Verify HTTP and browser behavior**

Check `GET /api/v1/local-voices/`, request each returned `file_url`, and verify HTTP 200. In desktop and mobile Playwright viewports, open `#stories`, confirm no overlap, play one recording, switch to another, seek, pause, and confirm audio stops after navigating away.

- [ ] **Step 5: Commit only scoped work**

Review `git diff` carefully, preserve unrelated user changes, and commit the model, migration, admin, importer, audio files, API, frontend player, tests, deployment scripts, and this plan.
