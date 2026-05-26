/* ========== 表单验证 + 飞书通知（前端子直发） ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  var phoneRegex = /^1[3-9]\d{9}$/;

  function validate(form) {
    var valid = true;
    var groups = form.querySelectorAll('.f-group');
    for (var i = 0; i < groups.length; i++) {
      var input = groups[i].querySelector('input,select');
      if (!input) continue;
      groups[i].classList.remove('has-error');
      if (input.required && !input.value.trim()) {
        groups[i].classList.add('has-error');
        valid = false;
      }
      if (input.name === 'phone' && input.value && !phoneRegex.test(input.value)) {
        groups[i].classList.add('has-error');
        valid = false;
      }
    }
    return valid;
  }

  /* 自动填入测评中的企业名称 */
  function prefillCompany() {
    var qd = QS.quizData;
    if (!qd || !qd.answers || !qd.answers.company) return;
    var input = document.querySelector('#contactForm input[name="company"]');
    if (input && !input.value) input.value = qd.answers.company;
  }

  /* ── 飞书Webhook地址 ── */
  var FEISHU_WEBHOOK = 'https://open.feishu.cn/open-apis/bot/v2/hook/8a3faff5-65f1-473e-93dc-1a8b0655e9bf';

  /* ── 标签映射（与server.py一致）── */
  var LABELS = {
    'company': '企业名称', 'industry': '所属行业', 'establish': '成立年限',
    'pub_flow': '近一年月均公户流水', 'total_debt': '负债总额',
    'loan_orgs': '贷款机构数', 'overdue': '逾期记录', 'debt_trend': '负债变化趋势',
    'rejections': '贷款被拒记录', 'online_loans': '网贷机构数',
    'collateral': '抵押物情况', 'flow_ratio': '公私户流水比例',
    'loan_due': '贷款到期情况', 'expect_amt': '期望融资额度',
    'acc_level': '账务规范程度', 'acc_person': '会计负责人',
    'tax_grade': '纳税信用等级', 'tax_owed': '欠税/滞纳金',
    'invoice': '发票管理', 'social': '员工社保缴纳',
    'contract_dispute': '合同纠纷', 'labor_dispute': '劳动仲裁/纠纷',
    'exec_record': '被执行/失信记录', 'labor_contract': '劳动合同签订',
    'license': '行业许可证/资质',
  };

  /* ── 构建飞书消息文本（与server.py逻辑一致）── */
  function buildFeishuText(formData, quizData) {
    var text = '【新客户企业评估】\n';
    text += '联系人：' + (formData.name || '-') + '\n';
    text += '电话：' + (formData.phone || '-') + '\n';

    var answers = (quizData && quizData.answers) || {};
    var scores = (quizData && quizData.scores) || {};
    var level = (quizData && quizData.level) || {};
    var signals = (quizData && quizData.signals) || {};
    var issues = (quizData && quizData.issues) || [];

    text += '企业：' + (answers.company || '-') + '\n';
    text += '行业：' + (answers.industry || '-') + '\n';
    text += '感兴趣服务：' + (formData.interest || '未选择') + '\n';

    if (scores && Object.keys(scores).length > 0) {
      text += '\n—— 评估结果 ——\n';
      text += '总分：' + (scores.total || 0) + '/1000（' + (level.label || '-') + '级）\n';
      text += '融资：' + (scores.fin || 0) + '/450\n';
      text += '财税：' + (scores.tax || 0) + '/320\n';
      text += '法务：' + (scores.law || 0) + '/230\n';
      text += '\n过桥需求：' + (signals.bridge || '低') + '\n';
      text += '融资紧迫度：' + (signals.urgency || '低') + '\n';
      text += '客户价值：' + (signals.value || 'C') + '级\n';

      var warns = issues.filter(function(i) { return i.type === 'warn'; });
      if (warns.length > 0) {
        text += '\n—— 关键问题 ——\n';
        warns.forEach(function(issue) {
          text += '⚠️ ' + (issue.text || '') + '\n';
        });
      }

      if (answers && Object.keys(answers).length > 0) {
        text += '\n—— 完整答题信息 ——\n';
        var allKeys = ['company','industry','establish','pub_flow',
            'total_debt','loan_orgs','overdue','debt_trend','rejections','online_loans',
            'collateral','flow_ratio','loan_due','expect_amt',
            'acc_level','acc_person','tax_grade','tax_owed','invoice','social',
            'contract_dispute','labor_dispute','exec_record','labor_contract','license'];
        allKeys.forEach(function(k) {
          var label = LABELS[k] || k;
          var val = answers[k] || '-';
          text += label + '：' + val + '\n';
        });
      }
    }

    return text;
  }

  /* ── 发送飞书消息 ── */
  function sendFeishu(text) {
    if (!FEISHU_WEBHOOK) {
      console.warn('飞书Webhook未配置，跳过通知');
      return;
    }
    var payload = JSON.stringify({ msg_type: 'text', content: { text: text } });
    var xhr = new XMLHttpRequest();
    xhr.open('POST', FEISHU_WEBHOOK, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(payload);
  }

  /* ── 提交表单 ── */
  function submitForm(e) {
    e.preventDefault();
    var form = document.getElementById('contactForm');
    if (!validate(form)) return false;

    var fd = new FormData(form);
    var btn = document.getElementById('formSubmit');
    btn.disabled = true;
    btn.textContent = '提交中...';

    var formData = {
      name: fd.get('name') || '',
      phone: fd.get('phone') || '',
      company: fd.get('company') || '',
      interest: fd.get('interest') || ''
    };

    var quizData = QS.quizData || {};

    var feishuText = buildFeishuText(formData, quizData);
    sendFeishu(feishuText);

    form.style.display = 'none';
    document.getElementById('formSuccess').style.display = 'block';

    return false;
  }

  /* 测评完成后自动预填 */
  document.addEventListener('DOMContentLoaded', function() {
    prefillCompany();
  });

  /* ── 暴露给外部配置Webhook地址 ── */
  QS.feishu = {
    setWebhook: function(url) { FEISHU_WEBHOOK = url; }
  };

  QS.form = { submit: submitForm, prefillCompany: prefillCompany };
})();
