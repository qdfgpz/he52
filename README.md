# Still Here · 个人网站

一个纯前端的个人网站 + FastAPI 后端的每日情报聚合服务。主题配色致敬金州勇士与克莱·汤普森（Klay Thompson #11）。

## 功能模块

| 页面 | 内容 |
|---|---|
| `test1.html`（首页） | To do list（完成自动沉底、截止 24 小时后自动删除）+ 克莱名言每日一格 |
| `hub.html` | 每日情报站：AI 前沿 / NBA 战报 / 清华科研（工物·原子·核）/ CS:GO，四个板块实时抓取 |
| `philosophy.html` | 每日哲学：40 则东西方哲学详解（思考题 + 书籍出处），按日轮换 |
| `movies.html` | 电影片单：豆瓣高分每日推荐 + 个人观影记录 |
| `books.html` | 书单：高分书籍每日推荐 + 读书记录 |
| `mao.html` | 每日毛选：《毛泽东选集》40 篇逐篇详解，章节侧边栏 + 分页阅读 |
| `greek.html` | 古希腊文明：11 讲系统通史（思考题 + 参考答案），章节侧边栏 |
| `about friends.html` | 关于我的朋友们 |

## 运行

```bash
pip install fastapi uvicorn httpx
python main.py
```

然后访问 `http://127.0.0.1:8898/test1.html`（Windows 下也可双击 `start.bat`）。

- 前端首页：`http://127.0.0.1:8898/test1.html`
- 唯一 API 接口：`GET /api/news` —— 服务端并发抓取量子位 RSS、B 站接口、HLTV RSS，完成时效过滤与营销号过滤后返回 JSON
- 接口文档：`http://127.0.0.1:8898/docs`

## 技术说明

- 前端：原生 HTML/CSS/JS，数据持久化使用 localStorage；各模块按日期轮换（天数对齐本地午夜）
- 后端：FastAPI + httpx，五个抓取任务线程池并发，各源独立容错（单源失败不影响其他板块）
- 兜底数据：`news-data.js` / `philosophy-data.js`（可由 `update_news.ps1` 定时生成）

## 图片版权

- `klay.jpg` / `klay-shot.jpg`：Photo by [Keith Allison](https://www.flickr.com/people/27003603@N00) / Wikimedia Commons，CC BY-SA 2.0
- `klay.png` / `klay-run.png`：网络图片，仅个人学习使用
