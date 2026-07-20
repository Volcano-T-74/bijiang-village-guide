# Static Route Attraction Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the route page's attraction introduction cards display-only while leaving every other page control unchanged.

**Architecture:** Change only the route-stop renderer from interactive buttons to semantic articles and adjust its CSS from a three-column interactive layout to a two-column static layout. Preserve the existing attraction detail renderer and global click handler because removing unrelated dormant code is outside scope.

**Tech Stack:** Vue 3, DOM template strings, CSS, Vitest, Vue Test Utils

---

### Task 1: Lock the route-card behavior with a test

**Files:**
- Modify: `frontend/src/App.test.js:84`
- Test: `frontend/src/App.test.js`

- [ ] **Step 1: Replace the story-opening test with a failing static-card test**

```javascript
it('renders route attraction introductions without detail links', async () => {
  const wrapper = mount(App, { attachTo: document.body })
  await flushPromises()

  await wrapper.get('[data-route="interests"]').trigger('click')
  expect(wrapper.text()).toContain('岭南建筑')
  expect(wrapper.text()).toContain('自然水岸')

  await wrapper.get('[data-action="generate-route"]').trigger('click')
  await flushPromises()

  expect(wrapper.text()).toContain('村史馆')
  expect(wrapper.text()).toContain('匹配兴趣：岭南建筑')
  expect(wrapper.find('.route-stop').element.tagName).toBe('ARTICLE')
  expect(wrapper.find('[data-attraction-slug]').exists()).toBe(false)
  expect(wrapper.find('.route-stop .card-arrow').exists()).toBe(false)
})
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `pnpm test -- -t "renders route attraction introductions without detail links"`

Expected: FAIL because `.route-stop` is currently a `BUTTON` with `data-attraction-slug` and `.card-arrow`.

### Task 2: Make only the route attraction cards static

**Files:**
- Modify: `frontend/src/bijiang/site.js:451`
- Modify: `frontend/src/bijiang/site.css:469`
- Test: `frontend/src/App.test.js`

- [ ] **Step 1: Replace the interactive card markup with static markup**

```javascript
<section class="route-stop-list reveal">
  ${route.stops.map((stop, index) => `<article class="route-stop"><span>${index + 1}</span><div><strong>${stop.name}</strong><small>${stop.zone.name} · ${stop.visit_minutes}分钟</small><p>${stop.recommendation}</p></div></article>${route.legs[index] ? `<p class="route-bridge">${route.legs[index].narrative_bridge}</p>` : ""}`).join("")}
</section>
```

- [ ] **Step 2: Remove interactive-only layout and cursor styling**

```css
.route-stop { display: grid; grid-template-columns: 42px minmax(0, 1fr); gap: 14px; align-items: center; width: 100%; padding: 16px 18px; text-align: left; border: 1px solid var(--line); border-radius: 8px; background: #fffaf3; }
```

Delete the now-unused mobile rule:

```css
.route-stop .card-arrow { display: none; }
```

- [ ] **Step 3: Run the focused test to verify it passes**

Run: `pnpm test -- -t "renders route attraction introductions without detail links"`

Expected: PASS.

- [ ] **Step 4: Run the complete frontend test suite**

Run: `pnpm test`

Expected: all tests pass.

- [ ] **Step 5: Build the frontend**

Run: `pnpm build`

Expected: Vite production build completes successfully.

- [ ] **Step 6: Verify the running route page**

Open `http://127.0.0.1:5173/static/#route` with stored/generated route data and confirm the attraction introductions have no arrow, pointer cursor, or navigation action, while map markers and the back button still work.

- [ ] **Step 7: Commit the implementation**

```powershell
git add frontend/src/App.test.js frontend/src/bijiang/site.js frontend/src/bijiang/site.css docs/superpowers/plans/2026-07-20-static-route-attraction-cards.md
git commit -m "fix: make route attraction cards static"
```

