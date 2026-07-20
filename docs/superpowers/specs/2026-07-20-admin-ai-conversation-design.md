# Django Admin AI 运营对话设计

## 目标

在现有 SimpleUI Django Admin 中增加“AI 运营分析”页面。所有 `is_staff=True` 的后台员工都可以创建自己的对话、连续追问，并在刷新或重新登录后继续查看历史。游客 Vue 前端不做任何修改。

AI 只分析匿名聚合的景点行为指标，不接收游客 UUID、GPS、请求头、单条事件 metadata 或其他个人信息。

## 页面与交互

后台左侧菜单新增“AI 运营分析”，链接到 `/admin/ai-analytics/`。页面沿用 SimpleUI 的导航、颜色和字体，主体采用两栏工作区：

- 左栏显示当前员工的历史会话，支持新建会话和切换会话。
- 右栏顶部显示会话标题和统计周期选择（7、30、90 天）。
- 中部按时间展示管理员问题和 AI 回答。
- 底部提供多行问题输入框和“发送”按钮。

AI 回答不是纯文本气泡，而是紧凑的运营分析结果，依次显示：总结、热门景点、经营建议、关键证据和局限性。加载时禁用重复发送并显示骨架状态；空会话提供可直接点击的示例问题；失败时保留管理员的问题并显示安全错误信息与“重试”操作。

页面不显示完整九景点指标表，只显示 DeepSeek 返回的简要证据。所有布局在窄屏下改为上下排列，避免横向溢出。

## 数据模型

新增 `AnalyticsConversation`：

- `owner`：关联 Django 用户，限制为后台员工。
- `title`：由第一条问题截取生成，员工可通过后续功能扩展修改，本轮不提供重命名控件。
- `default_days`：当前统计周期，只允许 7、30、90。
- `created_at`、`updated_at`。

新增 `AnalyticsTurn`，一条记录代表一次问题和对应回答：

- `conversation`：所属会话。
- `question`：管理员输入的问题。
- `answer`：DeepSeek 的结构化 JSON 回答，失败或处理中为空对象。
- `metrics_snapshot`：本次调用使用的匿名聚合指标，保证历史结果可审计。
- `model`：本次使用的模型名称。
- `days`：本次统计周期快照。
- `status`：`pending`、`completed` 或 `failed`。
- `error_code`：仅保存安全的内部错误类别，不保存密钥或上游响应正文。
- `created_at`、`answered_at`。

删除会话时级联删除其轮次。数据库索引覆盖 `owner + updated_at` 和 `conversation + created_at`。

## 连续上下文与 DeepSeek 调用

每次提问执行以下流程：

1. 验证当前员工拥有目标会话，验证问题长度和统计周期。
2. 立即创建 `pending` 轮次，确保请求失败时问题仍保留。
3. 生成本次最新匿名聚合指标。
4. 读取同一会话最近 6 个已完成轮次，按时间顺序作为上下文。
5. 将系统约束、历史问题和结构化回答、当前问题、最新聚合指标发送给 DeepSeek。
6. 成功时保存结构化回答、指标快照、模型和完成时间；失败时标记 `failed` 并保存安全错误代码。

最多携带最近 6 个已完成轮次，避免对话无限增长导致成本和延迟失控。历史回答只用于理解“第二名呢”等追问；当前结论必须以本次最新指标为准。失败轮次不进入后续上下文，点击重试会重新使用最新指标调用。

## 权限与安全

- 页面和所有相关 JSON 路由均使用 `admin.site.admin_view`，要求后台登录。
- 服务层和查询层都按 `owner=request.user` 过滤，员工无法读取或操作其他员工的会话。
- 继续保留现有 `/api/v1/analytics/deepseek/` 管理员单次分析接口，避免破坏已有调用。
- 所有写操作要求 POST 与 CSRF，问题按纯文本处理，回答通过模板转义或 DOM `textContent` 渲染。
- DeepSeek Key 继续只从 `DEEPSEEK_API_KEY` 环境变量读取，不进入数据库、页面、日志或响应。
- 不记录 DeepSeek 上游响应正文；页面只展示配置缺失、超时、上游失败、响应无效等安全分类。

## 后台路由

- `GET /admin/ai-analytics/`：渲染对话页面和当前员工会话摘要。
- `POST /admin/ai-analytics/conversations/`：新建会话。
- `GET /admin/ai-analytics/conversations/<id>/`：读取本人会话和轮次。
- `POST /admin/ai-analytics/conversations/<id>/ask/`：保存问题并调用 DeepSeek。
- `POST /admin/ai-analytics/turns/<id>/retry/`：重试本人的失败轮次。

返回 JSON 的路由使用稳定的 `status`、`data` 和安全错误字段，前端据此更新页面状态。

## 测试与验收

Django 测试覆盖：

- 匿名用户被重定向到管理员登录页，非员工不可访问。
- 员工只能看到和操作自己的会话。
- 创建会话、发送问题、保存成功回答和统计快照。
- 连续追问只携带最近 6 个已完成轮次，且不携带失败轮次。
- 配置缺失、超时、上游失败和无效回答会保存失败状态并返回安全错误。
- 重试失败轮次后可以转为完成状态。
- 菜单包含“AI 运营分析”且指向真实后台路由。
- 页面包含周期选择、问题输入、发送、加载、空状态和重试所需的可访问控件。

最终运行 `python manage.py check`、`python manage.py test`，并在本地登录后台验证页面和 JSON 路由。生产部署后，用员工账号完成新建会话、首次提问、连续追问和刷新恢复四项验收。
