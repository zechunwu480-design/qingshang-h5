/* ========== 青商企业诊断 - 测评引擎（25题） ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  /* --- 25 道题目定义（联系方式移至留资表单） --- */
  var QUESTIONS = [
    // 第一阶段：基本信息（4题，不计分，s=0）
    {s:0,k:'company',   t:'企业名称',          ty:'text',  req:1},
    {s:0,k:'industry',  t:'所属行业',          ty:'sel',   req:1, opts:['制造业','服务业','餐饮食品','零售商贸','建筑地产','科技','贸易','其他']},
    {s:0,k:'establish', t:'成立年限',          ty:'sel',   req:1, opts:['不到1年','1-3年','3-5年','5-10年','10年以上']},
    {s:0,k:'pub_flow',  t:'近一年月均公户流水', ty:'sel',   req:1, opts:['10万以下','10-30万','30-50万','50-100万','100万以上']},

    // 第二阶段：融资诊断（10题，满分450，s=1）
    {s:1,k:'total_debt',  t:'负债总额（含信用卡、网贷）',       ty:'sel',req:1, opts:['50万以下','50-200万','200-500万','500-1000万','1000万以上'],
     score:{'50万以下':0,'50-200万':15,'200-500万':30,'500-1000万':50,'1000万以上':70}, w:1.2},
    {s:1,k:'loan_orgs',   t:'贷款机构数（银行+小贷）',          ty:'sel',req:1, opts:['0个（无贷款）','1个','2-3个','4-5个','5个以上'],
     score:{'0个（无贷款）':5,'1个':0,'2-3个':25,'4-5个':50,'5个以上':75}, w:1.0},
    {s:1,k:'overdue',     t:'有无逾期记录',                    ty:'sel',req:1, opts:['无逾期','有已还清','有未还（90天内）','有未还（90天以上）'],
     score:{'无逾期':0,'有已还清':30,'有未还（90天内）':60,'有未还（90天以上）':110}, w:1.5},
    {s:1,k:'debt_trend',  t:'近一年负债变化趋势',               ty:'sel',req:1, opts:['比去年减少','差不多','增长30%以内','增长30%-100%','翻倍以上'],
     score:{'比去年减少':0,'差不多':5,'增长30%以内':20,'增长30%-100%':40,'翻倍以上':55}, w:0.8},
    {s:1,k:'rejections',  t:'贷款申请被拒记录',                 ty:'sel',req:1, opts:['无','1次','2次','3次以上'],
     score:{'无':0,'1次':15,'2次':35,'3次以上':65}, w:1.0},
    {s:1,k:'online_loans',t:'网贷机构数',                      ty:'sel',req:1, opts:['0个','1-2个','3-5个','5个以上'],
     score:{'0个':0,'1-2个':15,'3-5个':40,'5个以上':65}, w:0.8},
    {s:1,k:'collateral',  t:'有无固定资产抵押物',               ty:'sel',req:1, opts:['无','有设备','有房产','有厂房','有多种抵押物'],
     score:{'无':35,'有设备':20,'有房产':10,'有厂房':10,'有多种抵押物':0}, w:0.7},
    {s:1,k:'flow_ratio',  t:'公私户流水比例',                   ty:'sel',req:1, opts:['公户为主（8:2以上）','公私各半','私户为主（2:8以下）','基本走私户'],
     score:{'公户为主（8:2以上）':0,'公私各半':15,'私户为主（2:8以下）':35,'基本走私户':50}, w:0.8},
    {s:1,k:'loan_due',    t:'近期是否有贷款到期需续贷',         ty:'sel',req:1, opts:['无贷款','6个月后到期','3个月内到期','1个月内到期','已到期需续贷'],
     score:{'无贷款':0,'6个月后到期':5,'3个月内到期':10,'1个月内到期':15,'已到期需续贷':20}, w:0.5},
    {s:1,k:'expect_amt',  t:'期望融资额度',                    ty:'sel',req:1, opts:['50万以下','50-200万','200-500万','500-1000万','1000万以上']},

    // 第三阶段：财税评估（6题，满分320，s=2）
    {s:2,k:'acc_level',  t:'账务规范程度',     ty:'sel',req:1, opts:['规范（有专业报表）','基本规范','较混乱','两套账或无账'],
     score:{'规范（有专业报表）':0,'基本规范':15,'较混乱':35,'两套账或无账':60}, w:1.2},
    {s:2,k:'acc_person', t:'会计负责人',       ty:'sel',req:1, opts:['专职会计','代理记账','老板自己管','无专人'],
     score:{'专职会计':0,'代理记账':10,'老板自己管':30,'无专人':45}, w:0.8},
    {s:2,k:'tax_grade',  t:'纳税信用等级',     ty:'sel',req:1, opts:['A级','B级','C级或未知'],
     score:{'A级':0,'B级':20,'C级或未知':55}, w:1.2},
    {s:2,k:'tax_owed',   t:'有无欠税/滞纳金',  ty:'sel',req:1, opts:['无','有（已处理）','有（未处理）'],
     score:{'无':0,'有（已处理）':20,'有（未处理）':65}, w:1.0},
    {s:2,k:'invoice',    t:'发票管理',         ty:'sel',req:1, opts:['增值税专票为主','普票为主','专票普票都有','基本不开票'],
     score:{'增值税专票为主':0,'普票为主':15,'专票普票都有':10,'基本不开票':30}, w:0.6},
    {s:2,k:'social',     t:'员工社保缴纳',     ty:'sel',req:1, opts:['正常全员缴纳','部分缴纳','没缴或停缴','不清楚'],
     score:{'正常全员缴纳':0,'部分缴纳':20,'没缴或停缴':40,'不清楚':15}, w:0.8},

    // 第四阶段：法务筛查（5题，满分230，s=3）
    {s:3,k:'contract_dispute',t:'有无合同纠纷',          ty:'sel',req:1, opts:['无','有（已结案）','有（未结案）'],
     score:{'无':0,'有（已结案）':20,'有（未结案）':60}, w:1.2},
    {s:3,k:'labor_dispute',   t:'有无劳动仲裁/纠纷',     ty:'sel',req:1, opts:['无','有（已处理）','有（未处理）'],
     score:{'无':0,'有（已处理）':20,'有（未处理）':60}, w:1.0},
    {s:3,k:'exec_record',     t:'有无被执行/失信记录',   ty:'sel',req:1, opts:['无','有（已移除）','有记录（当前有效）'],
     score:{'无':0,'有（已移除）':25,'有记录（当前有效）':70}, w:1.0},
    {s:3,k:'labor_contract',  t:'员工劳动合同签订',      ty:'sel',req:1, opts:['全部签订','部分签订','基本没签','不清楚'],
     score:{'全部签订':0,'部分签订':15,'基本没签':35,'不清楚':20}, w:0.8},
    {s:3,k:'license',         t:'有无行业许可证/资质',   ty:'sel',req:1, opts:['有','正在申请','无'],
     score:{'有':0,'正在申请':15,'无':40}, w:0.5}
  ];

  var STAGE_NAMES = ['基本信息','融资诊断','财税评估','法务筛查'];
  var DIM_MAX = {fin:450, tax:320, law:230};
  var TOTAL_QUESTIONS = QUESTIONS.length;

  var state = { cur:0, answers:{}, container:null };

  /* --- 评分 --- */
  function calcScores() {
    var a = state.answers;
    var dims = {fin:0, tax:0, law:0};
    QUESTIONS.forEach(function(q) {
      if (!q.score || !q.w) return;
      var val = a[q.k];
      var deduct = (q.score[val] || 0) * q.w;
      if (q.s === 1) dims.fin += deduct;
      else if (q.s === 2) dims.tax += deduct;
      else if (q.s === 3) dims.law += deduct;
    });
    var fin = Math.max(0, Math.min(DIM_MAX.fin, Math.round(DIM_MAX.fin - dims.fin)));
    var tax = Math.max(0, Math.min(DIM_MAX.tax, Math.round(DIM_MAX.tax - dims.tax)));
    var law = Math.max(0, Math.min(DIM_MAX.law, Math.round(DIM_MAX.law - dims.law)));
    var total = fin + tax + law;
    return {fin:fin, tax:tax, law:law, total:total,
            finPct:Math.round(fin/DIM_MAX.fin*100),
            taxPct:Math.round(tax/DIM_MAX.tax*100),
            lawPct:Math.round(law/DIM_MAX.law*100),
            totalPct:Math.round(total/1000*100)};
  }

  function getLevel(total) {
    if (total >= 820) return {label:'AAA',desc:'经营极为稳健，综合实力卓越',cls:'level--aaa'};
    if (total >= 720) return {label:'AA', desc:'经营稳健，抗风险能力较强',   cls:'level--aa'};
    if (total >= 620) return {label:'A',  desc:'经营基本正常，有改进空间',   cls:'level--a'};
    if (total >= 500) return {label:'B',  desc:'存在一定风险，需重点关注',   cls:'level--b'};
    return               {label:'C',  desc:'风险较高，建议优先处理关键问题', cls:'level--c'};
  }

  function getBizSignals() {
    var a = state.answers;
    var signals = {bridge:'低', urgency:'低', value:'C'};
    var loanDue = a.loan_due || '';
    var loanOrgs = a.loan_orgs || '';
    if (loanDue === '已到期需续贷' || (loanDue === '1个月内到期' && (loanOrgs === '2-3个' || loanOrgs === '4-5个' || loanOrgs === '5个以上'))) {
      signals.bridge = '高';
    } else if (loanDue === '3个月内到期' || loanOrgs === '4-5个' || loanOrgs === '5个以上') {
      signals.bridge = '中';
    }
    var rej = a.rejections || '';
    var expAmt = a.expect_amt || '';
    var overdue = a.overdue || '';
    var highAmt = expAmt === '200-500万' || expAmt === '500-1000万' || expAmt === '1000万以上';
    if ((rej === '2次' || rej === '3次以上') && highAmt) signals.urgency = '高';
    else if (rej !== '无' || overdue.indexOf('未还') > -1) signals.urgency = '中';
    var veryHigh = expAmt === '500-1000万' || expAmt === '1000万以上';
    if (veryHigh && signals.bridge === '高') signals.value = 'A';
    else if (highAmt || signals.bridge === '中') signals.value = 'B';
    return signals;
  }

  function getIssues() {
    var a = state.answers;
    var issues = [];
    if (a.overdue && a.overdue.indexOf('未还') > -1)
      issues.push({type:'warn', text:'存在未结清逾期记录，银行和正规金融机构会直接拒贷'});
    if (a.loan_orgs === '4-5个' || a.loan_orgs === '5个以上')
      issues.push({type:'warn', text:'在途贷款机构过多，多头借贷风险显著'});
    if (a.online_loans && a.online_loans !== '0个')
      issues.push({type:'warn', text:'存在网贷记录，部分银行对网贷客户敏感'});
    if (a.rejections === '2次' || a.rejections === '3次以上')
      issues.push({type:'warn', text:'近期贷款多次被拒，征信查询过多'});
    if (a.acc_level === '较混乱' || a.acc_level === '两套账或无账')
      issues.push({type:'warn', text:'账务规范度不足，银行审查时会直接导致拒贷'});
    if (a.tax_grade === 'C级或未知')
      issues.push({type:'warn', text:'纳税信用等级偏低，影响融资及政府扶持申请'});
    if (a.tax_owed === '有（未处理）')
      issues.push({type:'warn', text:'存在未处理的欠税/滞纳金，不处理将持续影响运营'});
    if (a.contract_dispute === '有（未结案）')
      issues.push({type:'warn', text:'存在未结案合同纠纷，银行放款前查询法律诉讼会直接拒贷'});
    if (a.exec_record === '有记录（当前有效）')
      issues.push({type:'warn', text:'存在当前有效的被执行/失信记录，银行贷款几乎无望'});
    if (a.flow_ratio === '私户为主（2:8以下）' || a.flow_ratio === '基本走私户')
      issues.push({type:'warn', text:'公私户流水比例失衡，银行对私户流水认可度低'});
    if (a.overdue === '无逾期' && a.loan_orgs !== '4-5个' && a.loan_orgs !== '5个以上')
      issues.push({type:'ok', text:'征信状况良好，无重大融资障碍'});
    if (a.contract_dispute === '无' && a.labor_dispute === '无' && a.exec_record === '无')
      issues.push({type:'ok', text:'法务维度未发现重大风险项'});
    return issues;
  }

  /* --- 构建卡片 --- */
  function buildCards() {
    var c = state.container;
    c.innerHTML = '';
    QUESTIONS.forEach(function(q, i) {
      var card = document.createElement('div');
      card.className = 'quiz-card';
      card.id = 'qc-' + i;
      var html = '<div class="quiz-card__stage">' + STAGE_NAMES[q.s] + '</div>';
      html += '<div class="quiz-card__q">' + q.t + (q.req ? ' <span class="quiz-card__req">*</span>' : '') + '</div>';
      if (q.ty === 'text') {
        html += '<div style="margin-top:20px"><input class="quiz-input" id="qi-' + i + '" placeholder="请输入" value="' + QS.escapeHtml(state.answers[q.k]||'') + '"></div>';
      } else {
        html += '<div class="quiz-opts">';
        q.opts.forEach(function(opt) {
          var on = state.answers[q.k] === opt ? ' on' : '';
          html += '<div class="quiz-opt' + on + '" data-q="' + i + '" data-v="' + opt.replace(/"/g,'&quot;') + '"><div class="quiz-opt__radio"></div><span>' + opt + '</span></div>';
        });
        html += '</div>';
      }
      html += '<div class="quiz-nav">';
      if (i > 0) html += '<button class="quiz-nav__prev" onclick="QS.quiz.prev()">上一题</button>';
      var nextLabel = i === TOTAL_QUESTIONS - 1 ? '查看结果' : '下一题';
      var disabled = q.req && !state.answers[q.k] ? ' disabled' : '';
      html += '<button class="quiz-nav__next"' + disabled + ' onclick="QS.quiz.next()" id="qn-' + i + '">' + nextLabel + '</button>';
      html += '</div>';
      card.innerHTML = html;
      c.appendChild(card);
    });
  }

  function updateHdr() {
    var q = QUESTIONS[state.cur];
    var pct = Math.round((state.cur + 1) / TOTAL_QUESTIONS * 100);
    document.getElementById('quizFill').style.width = pct + '%';
    document.getElementById('quizLabel').textContent = '第 ' + (state.cur+1) + ' / ' + TOTAL_QUESTIONS + ' 题';
    document.getElementById('quizStage').textContent = STAGE_NAMES[q.s];
    document.getElementById('quizBack').style.display = state.cur > 0 ? 'flex' : 'none';
    var scores = calcScores();
    document.getElementById('quizChip').textContent = scores.total + '分';
  }

  function goCard(idx) {
    state.cur = idx;
    state.container.style.transform = 'translateX(-' + (idx * 100) + 'vw)';
    updateHdr();
  }

  function bindEvents() {
    document.addEventListener('click', function(e) {
      var opt = e.target.closest('.quiz-opt');
      if (!opt) return;
      var qi = parseInt(opt.dataset.q);
      var val = opt.dataset.v;
      var q = QUESTIONS[qi];
      var siblings = opt.parentElement.querySelectorAll('.quiz-opt');
      for (var i = 0; i < siblings.length; i++) siblings[i].classList.remove('on');
      opt.classList.add('on');
      state.answers[q.k] = val;
      var btn = document.getElementById('qn-' + qi);
      if (btn) btn.disabled = false;
      setTimeout(function() {
        if (qi < TOTAL_QUESTIONS - 1) goCard(qi + 1);
        else submitQuiz();
      }, 250);
    });
    document.addEventListener('input', function(e) {
      if (!e.target.classList.contains('quiz-input')) return;
      var qi = parseInt(e.target.id.replace('qi-',''));
      var q = QUESTIONS[qi];
      state.answers[q.k] = e.target.value;
      var btn = document.getElementById('qn-' + qi);
      if (btn) btn.disabled = !e.target.value;
    });
  }

  function submitQuiz() {
    var scores = calcScores();
    var level = getLevel(scores.total);
    var signals = getBizSignals();
    var issues = getIssues();

    // 解锁页面滚动
    document.body.classList.remove('quiz-active');

    document.getElementById('quiz').style.display = 'none';
    var reportSec = document.getElementById('report');
    reportSec.style.display = 'block';
    QS.report.render(reportSec.querySelector('#reportContent'), scores, level, signals, issues);
    setTimeout(function() { QS.radar.draw({fin:scores.finPct, tax:scores.taxPct, law:scores.lawPct}); }, 300);
    reportSec.scrollIntoView({behavior:'smooth'});

    QS.quizData = { answers:state.answers, scores:scores, level:level, signals:signals, issues:issues };
  }

  /* --- 开始测评（从外部按钮调用）--- */
  function startQuiz() {
    document.getElementById('quiz').style.display = 'block';
    document.body.classList.add('quiz-active');
    document.getElementById('quiz').scrollIntoView({behavior:'smooth'});
    if (!state.container) {
      state.container = document.getElementById('quizContainer');
      buildCards();
      bindEvents();
    }
    updateHdr();
  }

  QS.quiz = {
    init: function() {
      // 不自动初始化，等用户点击开始
    },
    start: startQuiz,
    next: function() {
      var q = QUESTIONS[state.cur];
      if (q.req && q.ty === 'text') {
        var input = document.getElementById('qi-' + state.cur);
        if (input) state.answers[q.k] = input.value;
        if (!state.answers[q.k]) { alert('请先填写答案'); return; }
      }
      if (q.req && !state.answers[q.k]) { alert('请先选择答案'); return; }
      if (state.cur < TOTAL_QUESTIONS - 1) goCard(state.cur + 1);
      else submitQuiz();
    },
    prev: function() {
      var q = QUESTIONS[state.cur];
      if (q.ty === 'text') {
        var input = document.getElementById('qi-' + state.cur);
        if (input) state.answers[q.k] = input.value;
      }
      if (state.cur > 0) goCard(state.cur - 1);
    },
    getAnswers: function() { return state.answers; },
    calcScores: calcScores,
    getBizSignals: getBizSignals,
    mergeAnswers: function(extra) {
      if (!extra) return;
      for (var k in extra) {
        if (extra.hasOwnProperty(k) && !state.answers[k]) {
          state.answers[k] = extra[k];
        }
      }
    }
  };
})();
