/* ========== 动画系统 ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  /* --- IntersectionObserver 滚动显示 --- */
  function observeReveal() {
    if (!('IntersectionObserver' in window)) {
      // fallback: 直接显示所有
      var els = document.querySelectorAll('.reveal');
      for (var i = 0; i < els.length; i++) els[i].classList.add('is-visible');
      return;
    }
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

    var els = document.querySelectorAll('.reveal');
    for (var i = 0; i < els.length; i++) obs.observe(els[i]);
  }

  /* --- 数字计数动画 --- */
  function animateCounter(el, target, duration) {
    duration = duration || 1500;
    var decimal = parseInt(el.dataset.decimal) || 0;
    var suffix = el.dataset.suffix || '';
    var start = null;

    function step(ts) {
      if (!start) start = ts;
      var progress = Math.min(1, (ts - start) / duration);
      // easeOutQuart
      var ease = 1 - Math.pow(1 - progress, 4);
      var current = target * ease;
      el.textContent = decimal > 0 ? current.toFixed(decimal) : Math.round(current);
      if (progress < 1) requestAnimationFrame(step);
      else el.textContent = decimal > 0 ? target.toFixed(decimal) : target;
    }
    requestAnimationFrame(step);
  }

  /* --- 触发计数器 --- */
  function observeCounters() {
    if (!('IntersectionObserver' in window)) return;
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          var nums = entry.target.querySelectorAll('[data-target]');
          for (var i = 0; i < nums.length; i++) {
            var target = parseFloat(nums[i].dataset.target);
            animateCounter(nums[i], target);
          }
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.3 });

    var sections = document.querySelectorAll('.trust-bar');
    for (var i = 0; i < sections.length; i++) obs.observe(sections[i]);
  }

  QS.anim = {
    init: function() {
      observeReveal();
      observeCounters();
    }
  };
})();
