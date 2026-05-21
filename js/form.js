/* ========== 表单验证 + 飞书提交 + PDF 报告生成 ========== */
window.QS = window.QS || {};

(function(){
  'use strict';

  var WEBHOOK_URL = 'https://open.feishu.cn/open-apis/bot/v2/hook/8a3faff5-65f1-473e-93dc-1a8b0655e9bf';
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

  function buildFeishuMsg(formData, quizData, reportUrl) {
    var text = '【新客户企业评估】\n';
    text += '联系人：' + formData.get('name') + '\n';
    text += '电话：' + formData.get('phone') + '\n';
    text += '企业：' + (quizData && quizData.answers ? quizData.answers.company : '-') + '\n';
    text += '行业：' + (quizData && quizData.answers ? quizData.answers.industry : '-') + '\n';
    text += '感兴趣服务：' + (formData.get('interest') || '未选择') + '\n';

    if (quizData && quizData.scores) {
      text += '\n—— 评估结果 ——\n';
      text += '总分：' + quizData.scores.total + '/1000（' + quizData.level.label + '）\n';
      text += '融资：' + quizData.scores.fin + '/450\n';
      text += '财税：' + quizData.scores.tax + '/320\n';
      text += '法务：' + quizData.scores.law + '/230\n';
      text += '\n过桥需求：' + quizData.signals.bridge + '\n';
      text += '融资紧迫度：' + quizData.signals.urgency + '\n';
      text += '客户价值：' + quizData.signals.value + '级\n';

      if (quizData.issues && quizData.issues.length) {
        text += '\n—— 关键问题 ——\n';
        quizData.issues.forEach(function(issue) {
          if (issue.type === 'warn') text += '⚠️ ' + issue.text + '\n';
        });
      }

      // 客户详细回答
      if (quizData.answers) {
        var a = quizData.answers;
        text += '\n—— 客户填写信息 ——\n';
        text += '成立年限：' + (a.establish||'-') + '\n';
        text += '公户流水：' + (a.pub_flow||'-') + '\n';
        text += '负债总额：' + (a.total_debt||'-') + '\n';
        text += '贷款机构：' + (a.loan_orgs||'-') + '\n';
        text += '逾期记录：' + (a.overdue||'-') + '\n';
        text += '期望额度：' + (a.expect_amt||'-') + '\n';
        text += '纳税等级：' + (a.tax_grade||'-') + '\n';
        text += '合同纠纷：' + (a.contract_dispute||'-') + '\n';
        text += '被执行记录：' + (a.exec_record||'-') + '\n';
      }
    }

    // PDF 下载链接
    if (reportUrl) {
      text += '\n—— 专业报告 ——\n';
      text += 'PDF 下载：' + reportUrl + '\n';
    }

    return { msg_type: 'text', content: { text: text } };
  }

  function submitForm(e) {
    e.preventDefault();
    var form = document.getElementById('contactForm');
    if (!validate(form)) return false;

    var fd = new FormData(form);
    var btn = document.getElementById('formSubmit');
    btn.disabled = true;
    btn.textContent = '生成报告中...';

    // 先调后端生成 PDF
    var quizData = QS.quizData || {};
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/generate-report', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
      var reportUrl = '';
      try {
        var res = JSON.parse(xhr.responseText);
        if (res.ok) reportUrl = res.url;
      } catch(e) {}

      btn.textContent = '提交中...';
      sendToFeishu(fd, quizData, reportUrl, form, btn);
    };
    xhr.onerror = function() {
      // PDF 生成失败，仍然发送文本消息
      btn.textContent = '提交中...';
      sendToFeishu(fd, quizData, '', form, btn);
    };
    xhr.send(JSON.stringify(quizData));
    return false;
  }

  function sendToFeishu(fd, quizData, reportUrl, form, btn) {
    var payload = buildFeishuMsg(fd, quizData, reportUrl);
    var xhr2 = new XMLHttpRequest();
    xhr2.open('POST', WEBHOOK_URL, true);
    xhr2.setRequestHeader('Content-Type', 'application/json');
    xhr2.onload = function() {
      form.style.display = 'none';
      document.getElementById('formSuccess').style.display = 'block';
    };
    xhr2.onerror = function() {
      form.style.display = 'none';
      document.getElementById('formSuccess').style.display = 'block';
    };
    xhr2.send(JSON.stringify(payload));
  }

  QS.form = { submit: submitForm };
})();
