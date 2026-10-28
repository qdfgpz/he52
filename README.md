# Still Here · 个人网站

一个纯前端的个人网站 + FastAPI 后端的每日情报聚合服务。主题配色致敬金州勇士与克莱·汤普森（Klay Thompson #11）。

## 功能模块

| 页面 | 内容 |
|---|---|
| `index.html`（首页） | To do list（完成自动沉底、截止 24 小时后自动删除）+ 克莱名言每日一格 |
| `hub.html` | 每日情报站：AI 前沿 / NBA 战报 / 清华科研（工物·原子·核）/ CS:GO，四个板块实时抓取 |
| `philosophy.html` | 每日哲学：40 则东西方哲学详解（思考题 + 书籍出处），按日轮换 |
| `movies.html` | 电影片单：豆瓣高分每日推荐 + 个人观影记录 |
| `books.html` | 书单：高分书籍每日推荐 + 读书记录 |
| `mao.html` | 每日毛选：《毛泽东选集》40 篇逐篇详解，章节侧边栏 + 分页阅读 |
| `greek.html` | 古希腊文明：11 讲系统通史（思考题 + 参考答案），章节侧边栏 |
| `about-friends.html` | 关于我的朋友们 |
| `old-home.html` | 旧版单页主页（拆站前的第一版，保留备用，不在导航中） |

## 运行

```bash
pip install -r requirements.txt
python main.py
```

然后访问 `http://127.0.0.1:8898/`（旧地址 `/test1.html` 会自动跳转到首页）。

- 前端首页：`http://127.0.0.1:8898/`
- 唯一 API 接口：`GET /api/news` —— 服务端并发抓取 6 个源（量子位 RSS、B 站搜索 ×3、HLTV RSS、ESPN 热火赛程兜底），完成时效过滤与营销号过滤后返回 JSON
- 接口文档：`http://127.0.0.1:8898/docs`
- 日常使用：双击桌面"启动网站"快捷方式（无窗口后台启动 + 自动开浏览器，无窗口模式的运行日志写入 `server.log`）；想看实时日志用 `start.bat`

## 技术说明

- 前端：原生 HTML/CSS/JS；侧边栏导航由 `nav.js` 统一注入（加新页面只改 `nav.js` 一处）；数据持久化使用 localStorage；各模块按日期轮换（天数对齐本地午夜）
- 后端：FastAPI + httpx，抓取任务线程池并发，各源独立容错（单源失败不影响其他板块）；启动时后台预热缓存，重启后首次访问不用等全量抓取
- 缓存：内存缓存 10 分钟 + Stale-While-Revalidate（后端立即返回旧数据并标记 `refreshing`，前端 8 秒后自动再取）
- 兜底数据：`news-data.js` / `philosophy-data.js`（后端未启动时页面自动降级显示）

## 图片版权

- `klay.webp` / `klay-shot.webp`：Photo by [Keith Allison](https://www.flickr.com/people/27003603@N00) / Wikimedia Commons，CC BY-SA 2.0（原始 jpg 存于 git 历史）
- `klay-hold.webp` / `klay-run.webp`：网络图片，仅个人学习使用
