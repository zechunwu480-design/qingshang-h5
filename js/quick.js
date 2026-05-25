/* ========== 30秒快速预判 ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  var QUESTIONS = [
    {k:'loan_due', t:'近期是否有贷款到期需续贷？',
     opts:['无贷款','6个月后到期','3个月内到期','1个月内到期','已到期需续贷'],
     risk:{'无贷款':0,'6个月后到期':0,'3个月内到期':1,'1个月内到期':2,'已到期需续贷':3}},
    {k:'overdue', t:'有无逾期记录？',
     opts:['无逾期','有已还清','有未还（90天内）','有未还（90天以上）'],
     risk:{'无逾期':0,'有已还清':1,'有未还（90天内）':2,'有未还（90天以上）':3}},
    {k:'acc_level', t:'账务规范程度？',
     opts:['规范（有专业报表）','基本规范','较混乱','两套账或无账'],
     risk:{'规范（有专业报表）':0,'基本规范':0,'较混乱':2,'两套账或无账':3}}
  ];

  var state = { cur:0, answers:{}, container:null, started:false };

  function getRiskLevel() {
    var total = 0;
    QUESTIONS.forEach(function(q) {
      var val = state.answers[q.k];
      total += (q.risk[val] || 0);
    });
    if (total >= 5) return 'high';
    if (total >= 2) return 'mid';
    return 'low';
  }

  function showResult() {
    var level = getRiskLevel();
    var resultEl = document.getElementById('quickResult');
    var quizEl = document.getElementById('quickQuiz');
    quizEl.style.display = 'none';
    resultEl.style.display = 'block';

    var msgs = {
      high: {title:'高风险预警', desc:'您的企业存在较高融资风险，建议立即做完整诊断了解全部问题', color:'var(--clr-danger)'},
      mid:  {title:'部分需关注', desc:'部分维度需要重点关注，建议做完整评估了解详细情况', color:'var(--clr-warning)'},
      low:  {title:'基础良好', desc:'基础状况不错，完整评估可帮您获取更优融资方案', color:'var(--clr-success)'}
    };
    var msg = msgs[level];
    resultEl.querySelector('.quick-result__title').textContent = msg.title;
    resultEl.querySelector('.quick-result__title').style.color = msg.color;
    resultEl.querySelector('.quick-result__desc').textContent = msg.desc;
  }

  function buildCards() {
    var container = document.getElementById('quickContainer');
    if (!container) return;
    container.innerHTML = '';
    QUESTIONS.forEach(function(q, i) {
      var card = document.createElement('div');
      card.className = 'quick-card' + (i === 0 ? ' active' : '');
      card.id = 'qc-' + i;
      var html = '<div class="quick-card__step">' + (i+1) + '/3</div>';
      html += '<div class="quick-card__q">' + q.t + '</div>';
      html += '<div class="quick-opts">';
      q.opts.forEach(function(opt) {
        html += '<div class="quick-opt" data-q="' + i + '" data-v="' + opt + '">' + opt + '</div>';
      });
      html += '</div>';
      card.innerHTML = html;
      container.appendChild(card);
    });
  }

  function goCard(idx) {
    var cards = document.querySelectorAll('.quick-card');
    for (var i = 0; i < cards.length; i++) {
      cards[i].classList.remove('active');
    }
    var target = document.getElementById('qc-' + idx);
    if (target) target.classList.add('active');
  }

  function bindEvents() {
    document.addEventListener('click', function(e) {
      var opt = e.target.closest('.quick-opt');
      if (!opt) return;
      var qi = parseInt(opt.dataset.q);
      var val = opt.dataset.v;
      var q = QUESTIONS[qi];
      state.answers[q.k] = val;

      // 高亮选中
      var siblings = opt.parentElement.querySelectorAll('.quick-opt');
      for (var i = 0; i < siblings.length; i++) siblings[i].classList.remove('on');
      opt.classList.add('on');

      setTimeout(function() {
        if (qi < QUESTIONS.length - 1) {
          goCard(qi + 1);
        } else {
          showResult();
        }
      }, 300);
    });

    // CTA 按钮
    var cta = document.getElementById('quickCTA');
    if (cta) {
      cta.addEventListener('click', function() {
        // 把快速预判的答案同步到完整测评
        if (QS.quiz && QS.quiz.mergeAnswers) {
          QS.quiz.mergeAnswers(state.answers);
        }
        document.getElementById('quickSection').style.display = 'none';
        QS.quiz.start();
      });
    }
  }

  QS.quick = {
    init: function() {
      buildCards();
      bindEvents();
    },
    start: function() {
      var sec = document.getElementById('quickSection');
      if (!sec) return;
      sec.style.display = 'block';
      sec.scrollIntoView({behavior:'smooth'});
      if (!state.started) {
        state.started = true;
        this.init();
      }
    }
  };
})();
