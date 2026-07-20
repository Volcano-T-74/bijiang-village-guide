# DeepSeek 景区运营分析接口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增一个管理员专用 Django API，聚合匿名游客行为并调用 DeepSeek 输出热门景点和经营投放建议。

**Architecture:** 数据聚合、DeepSeek HTTP 客户端和 API 编排分别放在独立模块。聚合模块只返回匿名指标；客户端只接收问题和聚合指标；DRF View 负责管理员权限、参数校验和错误状态映射。测试使用 Mock，不调用真实 DeepSeek。

**Tech Stack:** Django 5.2、Django REST Framework、Python `urllib.request`、Django ORM、Django TestCase。

---

### Task 1: 聚合匿名景点热度指标

**Files:**
- Create: `main/services/visitor_analytics.py`
- Create: `main/tests/test_visitor_analytics.py`

- [ ] **Step 1: 写聚合失败测试**

测试建立两个景点和指定时间范围内的模拟到达、足迹、收藏、路线数据，并断言：

```python
metrics = build_visitor_metrics(days=30, now=fixed_now)
museum = next(item for item in metrics["attractions"] if item["slug"] == "village-history-museum")
self.assertEqual(museum["simulated_arrivals"], 2)
self.assertEqual(museum["footprints"], 1)
self.assertEqual(museum["favorites"], 1)
self.assertEqual(museum["route_appearances"], 1)
self.assertEqual(museum["popularity_score"], 14)
```

同时断言 `metrics` 不包含游客 UUID、GPS 或单条事件 metadata。

- [ ] **Step 2: 运行测试确认失败**

Run: `\.venv\Scripts\python.exe manage.py test main.tests.test_visitor_analytics`

Expected: FAIL，`main.services.visitor_analytics` 尚不存在。

- [ ] **Step 3: 实现确定性聚合**

实现：

```python
def build_visitor_metrics(days, now=None):
    end = now or timezone.now()
    start = end - timedelta(days=days)
```

按景点汇总 `VisitorEvent`、`Footprint`、`Favorite`；遍历指定时间内 `Itinerary.attraction_sequence` 统计路线出现次数。热度分数使用：

```python
score = simulated_arrivals * 4 + footprints * 3 + favorites * 2 + route_appearances
```

返回 ISO 时间、会话总数、评分公式和全部启用景点指标，按 `popularity_score` 及各项计数降序排列。

- [ ] **Step 4: 运行测试确认通过**

Run: `\.venv\Scripts\python.exe manage.py test main.tests.test_visitor_analytics`

Expected: PASS。

- [ ] **Step 5: 提交聚合服务**

```powershell
git add main/services/visitor_analytics.py main/tests/test_visitor_analytics.py
git commit -m "feat: aggregate attraction popularity metrics"
```

### Task 2: DeepSeek HTTP 客户端

**Files:**
- Create: `main/services/deepseek_client.py`
- Create: `main/tests/test_deepseek_client.py`
- Modify: `config/settings.py`
- Modify: `.env.example`

- [ ] **Step 1: 写成功与错误失败测试**

使用 `override_settings` 和 `patch("main.services.deepseek_client.urlopen")` 覆盖：

```python
analysis = analyze_visitor_metrics("哪个景点最热门？", metrics)
self.assertEqual(analysis["summary"], "村史馆最热门")
```

并覆盖未配置 Key、超时、HTTP 401/429/500、无效 JSON、缺失必需字段。断言发送内容不包含测试会话 UUID。

- [ ] **Step 2: 运行测试确认失败**

Run: `\.venv\Scripts\python.exe manage.py test main.tests.test_deepseek_client`

Expected: FAIL，客户端模块尚不存在。

- [ ] **Step 3: 添加环境配置**

在 `config/settings.py` 读取：

```python
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_TIMEOUT_SECONDS = int(os.environ.get("DEEPSEEK_TIMEOUT_SECONDS", "30"))
```

在 `.env.example` 添加相同变量名和假值，不添加真实 Key。

- [ ] **Step 4: 实现客户端与异常类型**

定义：

```python
class DeepSeekConfigurationError(Exception): ...
class DeepSeekTimeoutError(Exception): ...
class DeepSeekUpstreamError(Exception): ...
class DeepSeekResponseError(Exception): ...
```

`analyze_visitor_metrics(question, metrics)` 向 `${DEEPSEEK_BASE_URL}/chat/completions` POST JSON，携带 Bearer Key、`deepseek-chat`、低温度、JSON 输出要求。解析 `choices[0].message.content`，验证以下字段存在且类型正确：

```python
summary: str
popular_attractions: list
business_recommendations: list
evidence: list
limitations: list
```

捕获 `socket.timeout`/`TimeoutError`、`HTTPError`、`URLError` 和 JSON/字段错误，不记录响应正文或 Key。

- [ ] **Step 5: 运行测试确认通过**

Run: `\.venv\Scripts\python.exe manage.py test main.tests.test_deepseek_client`

Expected: PASS。

- [ ] **Step 6: 提交客户端**

```powershell
git add main/services/deepseek_client.py main/tests/test_deepseek_client.py config/settings.py .env.example
git commit -m "feat: add DeepSeek analytics client"
```

### Task 3: 管理员分析 API

**Files:**
- Modify: `main/serializers.py`
- Modify: `main/api_views.py`
- Modify: `main/api_urls.py`
- Create: `main/tests/test_deepseek_analytics_api.py`

- [ ] **Step 1: 写权限、校验和成功失败测试**

测试：

```python
response = self.client.post("/api/v1/analytics/deepseek/", ...)
self.assertEqual(response.status_code, 403)
```

普通用户同样返回 403；`force_login(superuser)` 后 Mock 聚合器和客户端，断言成功返回 `question`、`period`、`metrics`、`analysis` 和 `model`。覆盖空问题、超过 1000 字、`days=0/366`。

- [ ] **Step 2: 写上游错误映射失败测试**

依次让 Mock 抛出四种客户端异常，断言：

```text
DeepSeekConfigurationError -> 503
DeepSeekTimeoutError -> 504
DeepSeekUpstreamError -> 502
DeepSeekResponseError -> 502
```

响应只包含安全中文错误信息。

- [ ] **Step 3: 运行测试确认失败**

Run: `\.venv\Scripts\python.exe manage.py test main.tests.test_deepseek_analytics_api`

Expected: FAIL，路由返回 404。

- [ ] **Step 4: 实现 Serializer 和 View**

Serializer：

```python
class DeepSeekAnalyticsSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000, trim_whitespace=True)
    days = serializers.IntegerField(min_value=1, max_value=365, default=30)
```

View：

```python
class DeepSeekAnalyticsView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]
```

管理员请求通过后调用聚合器和 DeepSeek 客户端，并按异常类型返回 503/504/502。

- [ ] **Step 5: 注册路由并运行测试**

在 `main/api_urls.py` 注册：

```python
path("analytics/deepseek/", DeepSeekAnalyticsView.as_view(), name="api-deepseek-analytics")
```

Run: `\.venv\Scripts\python.exe manage.py test main.tests.test_deepseek_analytics_api`

Expected: PASS。

- [ ] **Step 6: 提交管理员 API**

```powershell
git add main/serializers.py main/api_views.py main/api_urls.py main/tests/test_deepseek_analytics_api.py
git commit -m "feat: expose admin DeepSeek analytics API"
```

### Task 4: 完整验证和生产交付

**Files:**
- No new production files unless verification reveals a scoped defect.

- [ ] **Step 1: 运行后端完整验证**

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Expected: 所有测试通过，不发出真实 DeepSeek 网络请求。

- [ ] **Step 2: 检查敏感信息和差异**

```powershell
git diff --check
git grep -n "sk-" -- . ':!docs/superpowers/'
git status --short
```

Expected: 项目文件中不存在真实 Key；只暂存本任务文件，保留用户的音频等并行改动。

- [ ] **Step 3: 推送并设置 Render 环境变量**

推送 `main`。在 Render 手工添加轮换后的 `DEEPSEEK_API_KEY`，以及可选的 model/base URL/timeout。不要将聊天中暴露的 Key 复制到项目文件。

- [ ] **Step 4: 生产验收**

先验证未登录 POST 返回 403。管理员登录后调用接口，确认返回聚合 metrics 和 DeepSeek 分析；若 Render 尚未配置 Key，应返回预期的 503 配置提示。
