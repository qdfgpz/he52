/* 全站共享侧边栏导航。
   页面里只需保留 <aside class="site-side"></aside> 并在其后引入本文件；
   当前页自动高亮，加新页面只需在 PAGES 里加一行。
   mao / greek 页侧边栏自带的章节目录等额外内容会保留在导航下方。 */
(function () {
  var PAGES = [
    ['index.html', '🏠 首页 · 待办'],
    ['hub.html', '📰 每日情报站'],
    ['philosophy.html', '🧠 每日哲学'],
    ['movies.html', '🎬 电影片单'],
    ['books.html', '📚 书单'],
    ['mao.html', '📕 每日毛选'],
    ['greek.html', '🏛️ 古希腊文明'],
    ['about-friends.html', '👥 关于我的朋友们']
  ];
  var side = document.querySelector('.site-side');
  if (!side) return;

  /* 取 URL 最后一段作为当前页文件名；直接访问 / 时按首页高亮 */
  var here = decodeURIComponent(location.pathname.split('/').pop() || '').toLowerCase();
  if (!here) here = 'index.html';

  var brand = document.createElement('div');
  brand.className = 'site-brand';
  brand.textContent = '🏛 Still Here';

  var ul = document.createElement('ul');
  ul.className = 'site-nav';
  for (var i = 0; i < PAGES.length; i++) {
    var a = document.createElement('a');
    a.href = PAGES[i][0];
    a.textContent = PAGES[i][1];
    if (PAGES[i][0] === here) a.className = 'cur';
    var li = document.createElement('li');
    li.appendChild(a);
    ul.appendChild(li);
  }

  side.insertBefore(brand, side.firstChild);
  side.insertBefore(ul, brand.nextSibling);
})();
