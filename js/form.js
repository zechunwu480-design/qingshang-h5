/* ========== 表单验证 + 统一提交（PDF + 飞书） ========== */
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

  function submitForm(e) {
    e.preventDefault();
    var form = document.getElementById('contactForm');
    if (!validate(form)) return false;

    var fd = new FormData(form);
    var btn = document.getElementById('formSubmit');
    btn.disabled = true;
    btn.textContent = '提交中...';

    // 收集表单数据
    var formData = {
      name: fd.get('name') || '',
      phone: fd.get('phone') || '',
      company: fd.get('company') || '',
      interest: fd.get('interest') || ''
    };

    // 安全获取测评数据
    var quizData = QS.quizData || {};

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/submit', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
      form.style.display = 'none';
      document.getElementById('formSuccess').style.display = 'block';
    };
    xhr.onerror = function() {
      form.style.display = 'none';
      document.getElementById('formSuccess').style.display = 'block';
    };
    xhr.send(JSON.stringify({ form: formData, quiz: quizData }));

    return false;
  }

  /* 测评完成后自动预填 */
  document.addEventListener('DOMContentLoaded', function() {
    // 监听测评提交事件，延迟预填
    var origSubmit = QS.quiz ? QS.quiz.getAnswers : null;
    setInterval(function() { prefillCompany(); }, 2000);
  });

  QS.form = { submit: submitForm, prefillCompany: prefillCompany };
})();
