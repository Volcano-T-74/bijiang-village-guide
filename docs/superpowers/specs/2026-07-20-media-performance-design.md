# 前端媒体加载性能优化设计

## 范围

优化现有 Vue 导览站的图片和音频加载，不改变页面结构、路线逻辑、后台接口或二维码地址。

## 图片

将 `frontend/src/bijiang/assets` 中页面实际引用且超过 500 KB 的 PNG 转成 WebP。普通图片使用质量 82，村落地图使用质量 88；地图保持原尺寸，其他超过 1440 像素的图片按比例缩小到最长边 1440。代码和 CSS 改为引用 WebP，转换成功并完成引用检查后删除对应 PNG。

首页首屏地图使用 eager、`fetchpriority=high` 和异步解码。其余内容图片使用 `loading=lazy` 与 `decoding=async`。CSS 背景图继续按视图渲染，但引用压缩后的 WebP。

## 音频

音频文件格式本轮不改变，继续利用现有 HTTP Range 分段响应。`Audio` 对象只在用户点击当地声音后创建，显式设置 `preload=metadata`，不在页面进入时请求音频正文。

## 静态缓存

Django 仅从 Vite 的 `frontend/dist` 收集前端静态资源，避免同时收集 `public` 和源资产造成重复。匹配 Vite 内容哈希文件名的资源返回一年 immutable 缓存；未哈希音频返回一天缓存。部署仍由 Vite 重新构建生成内容哈希。

## 验证

对比优化前后的 `frontend/dist` 总体积、图片总体积和最大图片体积；运行 Vue 测试与构建、Django 检查与测试、静态资源收集，并在线验证 WebP、Cache-Control 和音频 Range 响应。
