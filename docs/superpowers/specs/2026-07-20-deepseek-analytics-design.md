# DeepSeek 景区运营分析接口设计

## 目标

新增一个只允许 Django 管理员调用的后端接口。接口自动汇总匿名游客行为数据，并调用 DeepSeek 回答景区运营问题，例如判断热门景点、推荐小摊类型和提出投放注意事项。游客前端不接入此接口。

## 接口

```text
POST /api/v1/analytics/deepseek/
```

请求体：

```json
{
  "question": "最近30天哪个景点最受欢迎，适合投放什么小摊？",
  "days": 30
}
```

- `question` 必填，去除首尾空白后长度为 1 至 1000 个字符。
- `days` 可选，默认 30，范围为 1 至 365。
- 使用 DRF `SessionAuthentication` 和 `IsAdminUser`，未登录返回 403，普通用户返回 403。

响应体：

```json
{
  "question": "最近30天哪个景点最受欢迎，适合投放什么小摊？",
  "period": {
    "days": 30,
    "start": "2026-06-21T00:00:00+08:00",
    "end": "2026-07-20T00:00:00+08:00"
  },
  "metrics": {
    "total_sessions": 120,
    "attractions": []
  },
  "analysis": {
    "summary": "总体结论",
    "popular_attractions": [],
    "business_recommendations": [],
    "evidence": [],
    "limitations": []
  },
  "model": "deepseek-chat"
}
```

## 数据汇总

后端在请求指定时间范围内按景点汇总以下匿名指标：

- `simulated_arrivals`：`VisitorEvent.event_type = simulated_arrival` 的次数。
- `footprints`：足迹打卡次数。
- `favorites`：收藏次数。
- `route_appearances`：景点出现在生成路线中的次数。
- `event_count`：该景点关联的所有游客事件数。

每个景点同时包含名称、slug 和区域。统计结果按模拟到达、足迹、收藏、路线出现次数的降序组合排序，供 DeepSeek 判断热门程度。接口返回原始聚合指标，使管理员可以核对 AI 结论。

不向 DeepSeek 发送游客 UUID、IP、真实 GPS、请求头、管理员信息或单条可识别记录。只发送按景点聚合后的数字和管理员问题。

## DeepSeek 调用

新增独立服务模块负责调用兼容 Chat Completions 的 DeepSeek API：

```text
POST https://api.deepseek.com/chat/completions
```

配置全部来自环境变量：

```env
DEEPSEEK_API_KEY=replace-with-a-rotated-secret
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_TIMEOUT_SECONDS=30
```

- API Key 不写入代码、数据库、日志、测试或 Git。
- 系统提示要求模型仅依据给定指标回答，输出中文 JSON，并明确数据不足和推断局限。
- 温度使用较低值，降低运营分析的随机性。
- DeepSeek 返回内容解析为 JSON；缺少约定字段或 JSON 无效时返回明确的上游响应错误。

## 错误处理

- 请求参数无效：`400`。
- 未登录或非管理员：`403`。
- 未配置 `DEEPSEEK_API_KEY`：`503`，提示后台尚未配置分析服务。
- DeepSeek 超时：`504`。
- DeepSeek 认证失败、限流或其他上游错误：`502`，不回传 Key、完整上游响应或敏感请求头。
- 数据库中没有行为数据时仍允许分析，但 `metrics` 明确为零，模型必须在 `limitations` 中说明数据不足。

## 代码边界

- `main/serializers.py`：请求参数校验。
- `main/services/visitor_analytics.py`：确定性聚合匿名游客数据。
- `main/services/deepseek_client.py`：DeepSeek HTTP 请求、超时和响应解析。
- `main/api_views.py`：管理员权限、编排聚合与模型调用、HTTP 错误映射。
- `main/api_urls.py`：注册管理员分析接口。
- `config/settings.py`：读取 DeepSeek 环境变量。
- `.env.example`：只添加变量示例，不添加真实密钥。

## 测试

- 未登录和普通用户无法调用接口。
- 管理员可以调用接口。
- `question` 和 `days` 校验返回明确错误。
- 模拟到达、足迹、收藏和路线出现次数聚合正确。
- 发给 DeepSeek 的内容不包含游客 UUID 或真实位置。
- 未配置 Key、超时、上游错误和无效 JSON 映射到正确状态码。
- 成功响应同时返回可核对的 `metrics` 和结构化 `analysis`。
- 测试全部 Mock 上游 HTTP，不使用真实 DeepSeek Key，不产生实际费用。

## 非目标

- 不修改游客 Vue 前端。
- 不自动执行摊位投放决策。
- 不保存 AI 报告历史。
- 不提供公开匿名调用或游客会话调用。
- 不把真实 GPS 或个人行为明细发送给 DeepSeek。
