# 优化执行计划 · Still Here（2026-10-28）

## 背景与目标

项目已从 `C:\Users\LEOVO\.zcode\workspace\default\my-website` 迁移到 `C:\Users\LEOVO\Desktop\vscode\test1`，但代码、脚本、快捷方式里仍有多处指向旧目录，**后端在新位置无法启动**。本次优化目标：

1. 让项目在当前目录完整可运行（不再依赖任何硬编码路径）
2. 修复审查中发现的确定性 bug
3. 消除 8 个页面间侧边栏导航的重复维护
4. 让文档与代码实际行为一致
5. 建立 git 版本管理基线，可随时回滚

## 范围外（本次不做，附原因）

- **图片 WebP 压缩**：本机磁盘加载无感知收益；将来上公网（GitHub Pages）时再做
- **待办 id 防同毫秒冲突**：人工表单提交不可能同毫秒，风险可忽略
- **style.css 清理孤儿规则**（如 `.side-contact`）：无功能影响，避免无谓 diff

## 阶段 A：版本管理基线

- `git init`（main 分支）+ 全量快照提交，后续重命名/重构可随时回滚
- 若无全局 git 身份，仅在本仓库设置本地 user.name / user.email

## 阶段 B：后端修复（main.py）

1. `MY_DIR` 硬编码旧目录 → `BASE_DIR = Path(__file__).resolve().parent`（项目放哪都能跑）
2. 删除 `get_news()` 末尾 `return` 之后的死代码（原 244-247 行）
3. `fetch_source` 的 `except: pass` → 打印一行失败原因（无窗口模式下写入 server.log，排障有线索）
4. 新增 lifespan 启动预热：服务启动即后台抓一次，消除重启后首次访问的长等待
5. 首页路由指向 `index.html`；新增 `/test1.html` → `/` 的 301 跳转，旧书签不失效
6. `__main__` 端口占用分支的 `input()` 加 EOFError 保护（无 stdin 场景不崩）

## 阶段 C：情报站修复（hub.html）

1. 删除重复引入两次的 `<script src="news-data.js">`
2. 补上 PROJECT_PLAN 宣称但从未实现的逻辑：响应带 `refreshing: true` 时 8 秒后自动再取

## 阶段 D：公共组件抽取与页面整改

- 新增 **`nav.js`**：侧边栏导航统一注入、当前页自动高亮；页面只留 `<aside class="site-side"></aside>`
  - 顺带移除指向 example.com 的占位邮箱链接（要恢复：在 nav.js 里加一行）
- 新增 **`favicon.svg`**（🏛），每页 head 加引用，消除控制台 404
- 重命名：`test1.html` → `index.html`；`about friends.html` → `about-friends.html`（URL 不再需要 %20 转义）
- 重建 `about-friends.html`：接入全站骨架（样式 + 侧边栏），修复未闭合标签、title 笔误、`width="100px"` 无效写法；**原文字内容一字不改**
- 其余 6 页（hub / philosophy / movies / books / mao / greek）：侧边栏换 nav.js + 加 favicon

## 阶段 E：启动体系

- 新增 **`launch.pyw`** 无窗口启动器：端口占用检测 → 后台拉起后端（日志写 `server.log`）→ 等端口就绪 → 开浏览器
  - 原快捷方式的 `pythonw main.py && start url` 写法本身无效（快捷方式不走 shell，`&&` 不生效，浏览器从未被打开过），一并修正
- `make_shortcut.py`：全部路径改为基于 `__file__` 定位，指向 `launch.pyw`，重新生成桌面快捷方式
- `start.bat`：地址改为 `http://127.0.0.1:8898/`
- 删除过时文件：`启动网站.bat`（cd 到旧目录）、项目内旧 `启动网站.lnk`（指向旧目录）
- `requirements.txt` 补 `pywin32`（仅 make_shortcut.py 需要，加注释说明）

## 阶段 F：文档同步

- `README.md`：页面表（index / about-friends）、启动方式、数据源数量（6 个）、文件清单、移除 `update_news.ps1` 表述
- `PROJECT_PLAN.md`：架构图、三层保障（补启动预热；"8 秒自动再取"改为真实现）、启动方式表、排查表（补 server.log）、文件清单、移除所有 `my-website` 引用

## 阶段 G：验证清单

- [ ] `uvicorn main:app --port 8899` 启动无异常（避开可能在运行的 8898）
- [ ] `/`、`/index.html`、7 个页面、`/nav.js`、`/favicon.svg` 全部返回 200
- [ ] `/test1.html` 301 跳转到 `/`
- [ ] `/api/news` 返回合法 JSON（数据源失败不影响结构，体现在 failed 字段）
- [ ] 全仓 grep：无 `my-website` 引用、无 `about friends.html` 链接、无残留 `test1.html` 链接（图片 `test1.jpg` 除外）
- [ ] 浏览器抽查 index / hub / about-friends：侧边栏注入正常、当前页高亮
- [ ] 桌面快捷方式重新生成且指向 launch.pyw
- [ ] git 提交完整、工作区干净

## 回滚方式

全部改动在 git 提交里：`git reset --hard <基线快照提交>` 即可完全回到优化前状态。

---

## 执行结果（2026-10-28 实测）

计划全部完成，另有 **两个执行中新发现并一并处理的问题**：

1. **philosophy.html 内混入情报站刷新脚本的完整副本**（拆页工具复制残留），引用了本页不存在的按钮，每次加载抛 TypeError——已整段删除。
2. **目录里原本就存在一个 index.html**（"李晓明 · 个人主页"，拆站前的第一版单页设计，无任何页面链接到它）——已改名为 `old-home.html` 保留（去留由作者决定，不需要可删除；基线提交里也有原始版本），把 `index.html` 名称让给现首页。

验证清单全部通过：

- [x] `uvicorn main:app --port 8899` 启动无异常，lifespan 预热生效
- [x] `/`、`/index.html`、7 个页面、`/old-home.html`、`/nav.js`、`/favicon.svg` 全部 200
- [x] `/test1.html` 301 跳转到 `/`
- [x] `/api/news` 返回合法 JSON：B 站 NBA 源被限流（412）时 ESPN 赛程兜底生效（`nba_is_schedule: true`，4 条），清华/CS:GO 板块抓到真实数据，`failed` 字段正确标记；二次调用走 10 分钟缓存
- [x] 抓取失败日志正常输出：`[fetch] nba 拉取失败: RuntimeError('rate-limited (412 / 52 bytes)')`
- [x] 浏览器实测 index / hub / about-friends / mao：侧边栏 8 个链接注入正常、当前页高亮正确、毛选页 40 篇章节目录完整保留（顺序：站点导航 → 章节目录）
- [x] 桌面快捷方式已重新生成，指向 `launch.pyw`
- [x] 全仓 grep 无 `my-website`、`about friends.html`、`test1.html` 残留引用（`test1.jpg` 图片除外）
