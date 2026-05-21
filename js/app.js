/* ========== 入口编排器 ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  /* 平滑滚动到锚点 */
  QS.scrollTo = function(selector) {
    var el = document.querySelector(selector);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  /* DOM Ready */
  document.addEventListener('DOMContentLoaded', function() {
    // 初始化动画系统
    QS.anim.init();

    // 初始化测评
    QS.quiz.init();
  });
})();
