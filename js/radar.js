/* ========== 雷达图渲染 ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  function drawRadar(scores, animated) {
    var canvas = document.getElementById('radarCanvas');
    if (!canvas) return;

    var dpr = window.devicePixelRatio || 1;
    var displaySize = 260;
    canvas.width = displaySize * dpr;
    canvas.height = displaySize * dpr;
    canvas.style.width = displaySize + 'px';
    canvas.style.height = displaySize + 'px';

    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    var cx = displaySize / 2;
    var cy = displaySize / 2;
    var r = displaySize * 0.34;
    var labels = ['金融','财税','法务'];
    var values = [scores.fin || 0, scores.tax || 0, scores.law || 0];
    var angles = labels.map(function(_, i) { return (Math.PI * 2 / 3) * i - Math.PI / 2; });

    function draw(progress) {
      ctx.clearRect(0, 0, displaySize, displaySize);

      // 背景多边形网格（3层）
      for (var ring = 1; ring <= 3; ring++) {
        ctx.beginPath();
        angles.forEach(function(a, i) {
          var x = cx + Math.cos(a) * r * (ring / 3);
          var y = cy + Math.sin(a) * r * (ring / 3);
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        ctx.closePath();
        ctx.strokeStyle = 'rgba(212,175,55,0.12)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // 轴线
      angles.forEach(function(a) {
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
        ctx.strokeStyle = 'rgba(212,175,55,0.15)';
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      // 数据多边形
      ctx.beginPath();
      angles.forEach(function(a, i) {
        var pct = Math.min(1, (values[i] / 100) * progress);
        var x = cx + Math.cos(a) * r * pct;
        var y = cy + Math.sin(a) * r * pct;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = 'rgba(212,175,55,0.22)';
      ctx.fill();
      ctx.strokeStyle = '#D4AF37';
      ctx.lineWidth = 2;
      ctx.stroke();

      // 数据点
      angles.forEach(function(a, i) {
        var pct = Math.min(1, (values[i] / 100) * progress);
        var x = cx + Math.cos(a) * r * pct;
        var y = cy + Math.sin(a) * r * pct;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#D4AF37';
        ctx.fill();
      });

      // 标签
      ctx.fillStyle = '#E8ECF0';
      ctx.font = '13px "PingFang SC", sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      labels.forEach(function(label, i) {
        var x = cx + Math.cos(angles[i]) * (r + 22);
        var y = cy + Math.sin(angles[i]) * (r + 22);
        ctx.fillText(label, x, y);
      });
    }

    if (animated !== false) {
      var start = null;
      var duration = 800;
      function animate(ts) {
        if (!start) start = ts;
        var elapsed = ts - start;
        var progress = Math.min(1, elapsed / duration);
        // easeOutCubic
        progress = 1 - Math.pow(1 - progress, 3);
        draw(progress);
        if (progress < 1) requestAnimationFrame(animate);
      }
      requestAnimationFrame(animate);
    } else {
      draw(1);
    }
  }

  QS.radar = { draw: drawRadar };
})();
