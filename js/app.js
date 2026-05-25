/* ========== 入口编排器 ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  /* HTML 转义 */
  QS.escapeHtml = function(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  };

  /* 平滑滚动到锚点 */
  QS.scrollTo = function(selector) {
    var el = document.querySelector(selector);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  /* 案例轮播指示器 */
  function initCaseDots() {
    var scroll = document.getElementById('casesScroll');
    var dots = document.querySelectorAll('.cases-dot');
    if (!scroll || !dots.length) return;

    // 滚动监听
    scroll.addEventListener('scroll', function() {
      var cards = scroll.querySelectorAll('.case-card');
      if (!cards.length) return;
      var scrollLeft = scroll.scrollLeft;
      var cardWidth = cards[0].offsetWidth + 16; // gap
      var activeIdx = Math.round(scrollLeft / cardWidth);
      for (var i = 0; i < dots.length; i++) {
        dots[i].classList.toggle('active', i === activeIdx);
      }
    });

    // 点击跳转
    for (var i = 0; i < dots.length; i++) {
      (function(idx) {
        dots[idx].addEventListener('click', function() {
          var cards = scroll.querySelectorAll('.case-card');
          if (cards[idx]) {
            cards[idx].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
          }
        });
      })(i);
    }
  }

  /* DOM Ready */
  document.addEventListener('DOMContentLoaded', function() {
    // 初始化动画系统
    QS.anim.init();

    // 初始化测评
    QS.quiz.init();

    // 初始化快速预判
    if (QS.quick) QS.quick.init();

    // 案例轮播指示器
    initCaseDots();

    // FAQ 手风琴
    document.addEventListener('click', function(e) {
      var q = e.target.closest('.faq-q');
      if (!q) return;
      var item = q.parentElement;
      item.classList.toggle('open');
    });
  });
})();
