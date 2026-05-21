/* ========== 简要报告渲染 ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  var DIM_COLORS = {
    fin: '#3498DB',
    tax: '#D4AF37',
    law: '#9B59B6'
  };

  function renderReport(el, scores, level, signals, issues) {
    var levelColor = scores.totalPct >= 72 ? '#2ECC71' : scores.totalPct >= 50 ? '#F39C12' : '#E74C3C';

    var html = '';

    // 分数环
    html += '<div class="report__score-ring">';
    html += '<div class="report__score-num">' + scores.total + '</div>';
    html += '<div class="report__score-max">/ 1000</div>';
    html += '</div>';
    html += '<div class="report__level" style="color:' + levelColor + '">' + level.label + '</div>';
    html += '<div class="report__level-desc">' + level.desc + '</div>';

    // 三维度得分条
    html += '<div class="report__dims">';
    var dims = [
      {key:'fin', name:'融资维度', score:scores.fin, max:450, pct:scores.finPct},
      {key:'tax', name:'财税维度', score:scores.tax, max:320, pct:scores.taxPct},
      {key:'law', name:'法务维度', score:scores.law, max:230, pct:scores.lawPct}
    ];
    dims.forEach(function(d) {
      html += '<div class="report__dim">';
      html += '<div class="report__dim-header"><span class="report__dim-name">' + d.name + '</span><span class="report__dim-score">' + d.score + '/' + d.max + '</span></div>';
      html += '<div class="report__dim-bar"><div class="report__dim-fill" style="width:0%;background:' + DIM_COLORS[d.key] + '" data-target="' + d.pct + '"></div></div>';
      html += '</div>';
    });
    html += '</div>';

    // 雷达图
    html += '<div style="display:flex;justify-content:center;margin:16px 0"><canvas id="radarCanvas" width="260" height="260"></canvas></div>';

    // 问题列表
    if (issues.length > 0) {
      html += '<div class="report__issues"><h3>关键发现</h3>';
      issues.forEach(function(issue) {
        var icon = issue.type === 'warn' ? '⚠️' : '✅';
        var cls = issue.type === 'warn' ? 'warn' : 'ok';
        html += '<div class="report__issue"><span class="report__issue-icon ' + cls + '">' + icon + '</span><span>' + issue.text + '</span></div>';
      });
      html += '</div>';
    }

    // CTA
    html += '<div style="margin-top:24px">';
    html += '<a href="#contact" class="btn btn--gold btn--full">获取完整专业报告</a>';
    html += '<p style="font-size:0.75em;color:#5A6A7A;margin-top:10px">报告将由专业顾问在24小时内发送至您的联系方式</p>';
    html += '</div>';

    el.innerHTML = html;

    // 延迟动画填充维度条
    setTimeout(function() {
      var fills = el.querySelectorAll('.report__dim-fill');
      for (var i = 0; i < fills.length; i++) {
        fills[i].style.width = fills[i].dataset.target + '%';
      }
    }, 200);
  }

  QS.report = { render: renderReport };
})();
