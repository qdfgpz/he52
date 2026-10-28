# -*- coding: utf-8 -*-
"""把 test1.html 拆分为多页文档站：style.css + 7 个页面"""
import os

SRC = r'C:\Users\LEOVO\.zcode\workspace\default\my-website\test1.html'
OUT = r'C:\Users\LEOVO\.zcode\workspace\default\my-website'

s = open(SRC, encoding='utf-8').read()

# ---------- 1. 提取样式 ----------
i1 = s.index('<style>'); i2 = s.index('</style>')
style_css = s[i1 + len('<style>'):i2].strip()

extra_css = '''
/* ===== 多页文档站布局 ===== */
.page-wrap { max-width: 1210px; margin: 24px auto 0; display: flex; gap: 18px; align-items: flex-start; padding: 0 16px; }
.site-side {
  flex: 0 0 250px; position: sticky; top: 12px; align-self: flex-start;
  background: #fff; border-radius: 14px; border-top: 5px solid #ffc72c;
  box-shadow: 0 6px 24px rgba(0, 0, 0, .08);
  padding: 16px 12px; max-height: 680px; overflow-y: auto;
}
.site-brand { font-size: 17px; font-weight: 800; color: #1d428a; margin: 0 6px 12px; letter-spacing: 1px; }
.site-nav { list-style: none; margin: 0; padding: 0; }
.site-nav li { margin: 3px 0; }
.site-nav a { display: block; padding: 8px 10px; border-radius: 8px; color: #444; text-decoration: none; font-size: 14px; }
.site-nav a:hover { background: #fdf6e3; }
.site-nav a.cur { background: #ffc72c; color: #1d428a; font-weight: 700; }
.side-toc-title { font-size: 13px; color: #999; margin: 14px 6px 8px; border-top: 1px solid #eee; padding-top: 12px; }
#maoToc, #gkToc { list-style: none; margin: 0; padding: 0; }
#maoToc li, #gkToc li { margin: 3px 0; }
#maoToc button, #gkToc button {
  display: block; width: 100%; text-align: left;
  border: none; background: none; padding: 6px 8px; border-radius: 8px;
  cursor: pointer; font-size: 12.5px; color: #555; line-height: 1.45;
}
#maoToc button:hover, #gkToc button:hover { background: #fdf6e3; }
#maoToc button.active, #gkToc button.active { background: #1d428a; color: #fff; font-weight: 600; }
.side-contact {
  display: block; margin: 14px 6px 4px; padding: 9px 12px;
  background: #00897b; color: #fff !important; border-radius: 10px;
  text-align: center; font-size: 14px; font-weight: 600; text-decoration: none;
}
.side-contact:hover { background: #00695c; }
main.site-main { flex: 1 1 auto; min-width: 0; }
main.site-main .klay-banner { margin-top: 0; }
@media (max-width: 960px) {
  .page-wrap { flex-direction: column; }
  .site-side { position: static; max-height: none; flex: none; width: 100%; box-sizing: border-box; }
}
'''
style_css = style_css + '\n' + extra_css
open(os.path.join(OUT, 'style.css'), 'w', encoding='utf-8').write(style_css)

# ---------- 2. 切出各内容块 ----------
marks = {
    'intro': '<!-- ===== 网站开场白 ===== -->',
    'klay': '<!-- ===== 克莱·汤普森名言横幅（每日一格） ===== -->',
    'todo': '<!-- ===== 模块一：To do list ===== -->',
    'hub': '<!-- ===== 模块二：每日情报站 ===== -->',
    'phil': '<!-- ===== 模块三：每日哲学 ===== -->',
    'movie': '<!-- ===== 模块四：电影片单 ===== -->',
    'book': '<!-- ===== 模块五：书单 ===== -->',
    'mao': '<!-- ===== 模块六：每日毛选 ===== -->',
    'greek': '<!-- ===== 模块八：古希腊文明 ===== -->',
}
pos = {k: s.index(v) for k, v in marks.items()}
i_news = s.index('<script src="news-data.js">')

blocks = {
    'intro': s[pos['intro']:pos['klay']],
    'klay': s[pos['klay']:pos['todo']],
    'todo': s[pos['todo']:pos['hub']],
    'hub': s[pos['hub']:pos['phil']],
    'phil': s[pos['phil']:pos['movie']],
    'movie': s[pos['movie']:pos['book']],
    'book': s[pos['book']:pos['mao']],
    'mao': s[pos['mao']:pos['greek']],
    'greek': s[pos['greek']:i_news],
}

# ---------- 3. 尾部切分：news-data / hub 兜底脚本 / 用户内容 / todo 脚本 ----------
i_news_end = s.index('</script>', i_news) + len('</script>')
i_hubboot = s.index('<script>', i_news_end)
i_hubboot_end = s.index('</script>', i_hubboot) + len('</script>')
hub_boot = s[i_hubboot:i_hubboot_end]

i_nav = s.index('<nav>', i_hubboot_end)
i_todo_key = s.index("var KEY = 'stillHereTodos'", i_nav)
i_todo_start = s.rindex('<script>', 0, i_todo_key)
i_todo_end = s.index('</script>', i_todo_key) + len('</script>')
todo_script = s[i_todo_start:i_todo_end]
user_tail = s[i_hubboot_end:i_todo_start]

# ---------- 4. 希腊块清理：去掉旧 wrap 外层与原章节侧边栏（目录移入站点侧边栏） ----------
g = blocks['greek']
g = g.replace('<div class="greek-wrap" id="greek">\n', '')
import re as _re
g = _re.sub(r'\s*<aside class="greek-side">\s*<div class="greek-side-title">📖 章节目录</div>\s*<ul id="gkToc"></ul>\s*</aside>', '', g, count=1)
g = g.replace('</section>\n    </div>', '</section>')
blocks['greek'] = g

# ---------- 5. 毛选块注入章节目录构建（maoToc 在站点侧边栏） ----------
m = blocks['mao']
anchor = '''          maoShow();
        }

        renderMao(cur);'''
inject = '''          maoShow();
          if (typeof maoTocHi === 'function') { maoTocHi(); }
        }
        var maoTocEl = document.getElementById('maoToc');
        MAO_POOL.forEach(function (p, i) {
          var li = document.createElement('li');
          var b = document.createElement('button');
          b.type = 'button';
          b.textContent = (i + 1) + '. ' + p.topic;
          b.dataset.idx = i;
          b.addEventListener('click', function () { renderMao(i); });
          li.appendChild(b);
          maoTocEl.appendChild(li);
        });
        function maoTocHi() {
          var btns = maoTocEl.querySelectorAll('button');
          for (var i = 0; i < btns.length; i++) { btns[i].className = (i === cur) ? 'active' : ''; }
        }
        maoTocHi();
        renderMao(cur);'''
if anchor in m:
    m = m.replace(anchor, inject, 1)
else:
    raise SystemExit('MAO anchor not found!')
blocks['mao'] = m

# ---------- 6. 页面模板 ----------
NAV = [
    ('test1.html', '🏠 首页 · 待办'),
    ('hub.html', '📰 每日情报站'),
    ('philosophy.html', '🧠 每日哲学'),
    ('movies.html', '🎬 电影片单'),
    ('books.html', '📚 书单'),
    ('mao.html', '📕 每日毛选'),
    ('greek.html', '🏛️ 古希腊文明'),
    ('about friends.html', '👥 关于我的朋友们'),
]

def make_page(fname, title, content, extra_side='', extra_scripts=''):
    lis = []
    for href, label in NAV:
        cur = ' class="cur"' if href == fname else ''
        lis.append('<li><a%s href="%s">%s</a></li>' % (cur, href, label))
    nav_html = '\n'.join(lis)
    contact = '<a class="side-contact" href="mailto:your-email@example.com">✉️ 联系我</a>'
    page = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · Still Here</title>
<link rel="stylesheet" href="style.css">
</head>
<body id="top">
<div class="page-wrap">
<aside class="site-side">
<div class="site-brand">🏛 Still Here</div>
<ul class="site-nav">
%s
</ul>
%s
%s
</aside>
<main class="site-main">
%s
</main>
</div>
%s
</body>
</html>''' % (title, nav_html, extra_side, contact, content, extra_scripts)
    open(os.path.join(OUT, fname), 'w', encoding='utf-8').write(page)
    print('written', fname)

# ---------- 7. 生成 7 页 ----------
make_page('test1.html', '首页 · 待办清单',
          blocks['intro'] + '\n' + blocks['klay'] + '\n' + blocks['todo'],
          extra_scripts=todo_script)

make_page('hub.html', '每日情报站',
          blocks['hub'],
          extra_scripts=hub_boot)

make_page('philosophy.html', '每日哲学', blocks['phil'])

make_page('movies.html', '电影片单', blocks['movie'])

make_page('books.html', '书单', blocks['book'])

make_page('mao.html', '每日毛选', blocks['mao'],
          extra_side='<div class="side-toc-title">📕 章节目录（40 篇）</div>\n<ul id="maoToc"></ul>')

make_page('greek.html', '古希腊文明', blocks['greek'],
          extra_side='<div class="side-toc-title">🏛️ 章节目录（11 讲）</div>\n<ul id="gkToc"></ul>')

print('ALL DONE')
