# 集章寻迹点亮交互 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将九点模拟到达状态与“集章寻迹”邮章点亮状态打通，并在首次点亮时显示可关闭的祝贺弹层。

**Architecture:** 继续以 `state.visitedSlugs` 作为足迹和邮章的唯一持久化状态，不增加新的后台模型。新增 `state.unlockedStampSlug` 作为仅存在于当前页面内存的弹层状态；首次到达时设置，关闭或刷新后清除。现有单文件渲染方式保持不变，修改集中在 `site.js`、`site.css` 和现有 Vue 集成测试中。

**Tech Stack:** Vue 3、原生 DOM 事件委托、Vitest、Vue Test Utils、CSS。

---

### Task 1: 让集章页面由已访问状态驱动

**Files:**
- Modify: `frontend/src/App.test.js`
- Modify: `frontend/src/bijiang/site.js:200-228`

- [ ] **Step 1: 写集章初始状态失败测试**

在 `frontend/src/App.test.js` 的站点测试组中新增测试，打开 `#stamps` 后断言唯一测试景点默认锁定且进度为 `0 / 1`：

```js
it('starts every stamp locked and derives progress from visited places', async () => {
  history.replaceState({}, '', '/#stamps')
  const wrapper = mount(App, { attachTo: document.body })
  await flushPromises()

  expect(wrapper.text()).toContain('已点亮 0 / 1 个印章点')
  expect(wrapper.findAll('.stamp-card.is-locked')).toHaveLength(1)
  expect(wrapper.findAll('.stamp-card.is-lit')).toHaveLength(0)
})
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
$env:PATH="C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback;" + $env:PATH
pnpm test -- --run src/App.test.js
```

Expected: FAIL，页面仍显示硬编码的 `6`，第一枚邮章带有 `.is-lit`。

- [ ] **Step 3: 将邮章状态改为动态计算**

在 `renderStamps()` 中计算有效点亮集合和数量：

```js
const litPlaces = places.filter(place => state.visitedSlugs.has(place.slug));
const litCount = litPlaces.length;
```

渲染每个景点时使用：

```js
const isLit = state.visitedSlugs.has(place.slug);
```

顶部数字、进度圆点、卡片 class、`aria-label`、锁图标和“已点亮”印章都根据 `isLit` 生成，不再使用 `i < 6`。

- [ ] **Step 4: 运行测试并确认通过**

Run: `pnpm test -- --run src/App.test.js`

Expected: 新测试 PASS，原有前端测试继续通过。

- [ ] **Step 5: 提交动态集章状态**

```powershell
git add frontend/src/App.test.js frontend/src/bijiang/site.js
git commit -m "feat: derive stamps from simulated visits"
```

### Task 2: 首次到达显示并关闭祝贺邮章

**Files:**
- Modify: `frontend/src/App.test.js`
- Modify: `frontend/src/bijiang/site.js:85-105, 405-460, 961-1022, 1040-1070`
- Modify: `frontend/src/bijiang/site.css`

- [ ] **Step 1: 写首次点亮和关闭弹层失败测试**

新增测试，生成路线、选择村史馆并确认到达：

```js
it('shows a dismissible stamp celebration on the first simulated arrival', async () => {
  const wrapper = mount(App, { attachTo: document.body })
  await flushPromises()
  await wrapper.get('[data-route="interests"]').trigger('click')
  await wrapper.get('[data-action="generate-route"]').trigger('click')
  await flushPromises()

  await wrapper.get('[data-map-slug="village-history-museum"]').trigger('click')
  await wrapper.get('[data-action="confirm-arrival"]').trigger('click')
  await flushPromises()

  expect(wrapper.get('[role="dialog"]').text()).toContain('恭喜你已点亮')
  expect(wrapper.get('[role="dialog"]').text()).toContain('村史馆')
  await wrapper.get('[data-action="close-stamp-unlock"]').trigger('click')
  expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
})
```

- [ ] **Step 2: 写重复到达不重复祝贺失败测试**

在同一个测试或独立测试中，关闭弹层后再次选择村史馆并确认：

```js
await wrapper.get('[data-map-slug="village-history-museum"]').trigger('click')
await wrapper.get('[data-action="confirm-arrival"]').trigger('click')
await flushPromises()
expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
```

- [ ] **Step 3: 运行测试并确认失败**

Run: `pnpm test -- --run src/App.test.js`

Expected: FAIL，因为当前没有 `[role="dialog"]` 和关闭行为。

- [ ] **Step 4: 增加临时弹层状态和首次访问判断**

在 `state` 中加入：

```js
unlockedStampSlug: null,
```

在 `confirmSimulatedArrival()` 修改 `visitedSlugs` 前记录：

```js
const isFirstVisit = !state.visitedSlugs.has(slug);
state.visitedSlugs.add(slug);
if (isFirstVisit) state.unlockedStampSlug = slug;
```

不要把 `unlockedStampSlug` 加入 `persistDemoState()`，确保刷新后不重复弹出。

- [ ] **Step 5: 在路线页渲染语义化祝贺弹层**

在 `renderRoute()` 中找到当前待展示景点：

```js
const unlockedStamp = places.find(place => place.slug === state.unlockedStampSlug);
```

在页面末尾按需渲染：

```html
<div class="stamp-unlock-backdrop" data-dismiss-stamp-unlock>
  <section class="stamp-unlock-dialog" role="dialog" aria-modal="true" aria-labelledby="stamp-unlock-title">
    <button class="stamp-unlock-close" data-action="close-stamp-unlock" aria-label="关闭邮章提示">&times;</button>
    <div class="stamp-unlock-art"><img src="对应景点图" alt="对应景点名称邮章" /><span>已点亮</span></div>
    <small>集章寻迹</small>
    <h2 id="stamp-unlock-title">恭喜你已点亮</h2>
    <strong>「对应景点名称」邮章</strong>
    <p>这枚邮章已收入你的集章册。</p>
  </section>
</div>
```

景点图使用 `placeImgUrls[slug] || cover_image_url`，所有景点名称经过现有 `escapeHtml()` 处理。

- [ ] **Step 6: 增加关闭按钮和遮罩关闭事件**

在按钮事件分支增加：

```js
if (button.dataset.action === "close-stamp-unlock") {
  state.unlockedStampSlug = null;
  transition(render);
  return;
}
```

在查找普通按钮之前处理仅点击遮罩本身的关闭：

```js
const stampBackdrop = event.target.closest('[data-dismiss-stamp-unlock]');
if (stampBackdrop && event.target === stampBackdrop) {
  state.unlockedStampSlug = null;
  transition(render);
  return;
}
```

- [ ] **Step 7: 增加响应式弹层样式**

在 `site.css` 增加固定遮罩、最大宽度 420px 的弹层、44px 关闭按钮、圆形邮章图、点亮印记和 180-220ms 状态动画。桌面居中，`max-width: 600px` 时底部贴近安全区；在 `prefers-reduced-motion: reduce` 下移除位移动画。弹层层级高于 `.bottom-nav`，不得出现横向溢出。

- [ ] **Step 8: 运行测试并确认通过**

Run: `pnpm test -- --run src/App.test.js`

Expected: 首次祝贺、关闭和重复到达测试 PASS，全部前端测试通过。

- [ ] **Step 9: 提交祝贺弹层**

```powershell
git add frontend/src/App.test.js frontend/src/bijiang/site.js frontend/src/bijiang/site.css
git commit -m "feat: celebrate newly unlocked stamps"
```

### Task 3: 验证刷新恢复、移动端布局和生产构建

**Files:**
- Modify if needed: `frontend/src/App.test.js`
- Modify if needed: `frontend/src/bijiang/site.css`

- [ ] **Step 1: 增加刷新后只恢复点亮、不恢复弹层的测试**

写入带版本号的 Demo 状态并打开集章页：

```js
localStorage.setItem('bijiang_indoor_demo_state', JSON.stringify({
  version: 2,
  interests: ['岭南建筑'],
  duration: 60,
  mode: 'relaxed',
  route,
  currentSimulatedSlug: 'village-history-museum',
  visitedSlugs: ['village-history-museum'],
}))
history.replaceState({}, '', '/#stamps')
```

断言 `.stamp-card.is-lit` 数量为 1，进度为 `1 / 1`，且不存在 `[role="dialog"]`。

- [ ] **Step 2: 运行测试并确认通过**

Run: `pnpm test -- --run src/App.test.js`

Expected: PASS。若失败，只修复恢复逻辑，不持久化临时弹层状态。

- [ ] **Step 3: 运行完整项目验证**

Backend:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Frontend:

```powershell
$env:PATH="C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback;" + $env:PATH
pnpm test
pnpm build
```

Expected: Django 48 项测试通过，Vue 测试总数增加且全部通过，Vite 生产构建成功。

- [ ] **Step 4: 启动本地服务并做移动端浏览器检查**

在现有 QA 数据库/服务上打开 390px 宽视口，完成一次村史馆模拟到达并截图。检查弹层不溢出、关闭按钮可见、背景不可误操作；关闭后打开“集章寻迹”，确认仅村史馆邮章点亮且进度为 `1 / 9`。

- [ ] **Step 5: 检查差异并提交最终调整**

```powershell
git diff --check
git status --short
git add frontend/src/App.test.js frontend/src/bijiang/site.js frontend/src/bijiang/site.css
git commit -m "test: cover stamp unlock persistence"
```

- [ ] **Step 6: 推送并验证 Render**

```powershell
git push origin main
```

等待 Render 新资源指纹上线，在手机宽度验证首次模拟到达弹层、关闭行为、集章页点亮状态和刷新恢复。
