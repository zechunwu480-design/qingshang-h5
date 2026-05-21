"""青商企业诊断 H5 — Flask 后端（静态文件 + PDF 报告生成）"""
import os, json, datetime
from flask import Flask, request, jsonify, send_from_directory
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, 'reports')
os.makedirs(REPORTS, exist_ok=True)

# 注册中文字体
FONT = 'C:/Windows/Fonts/simhei.ttf'
FONTB = 'C:/Windows/Fonts/msyhbd.ttf'
pdfmetrics.registerFont(TTFont('SimHei', FONT))
try:
    pdfmetrics.registerFont(TTFont('SimHeiB', FONTB))
except Exception:
    pdfmetrics.registerFont(TTFont('SimHeiB', FONT))  # fallback

# ── 颜色 ──
C_BG    = HexColor('#0D1B2A')
C_GOLD  = HexColor('#D4AF37')
C_TEXT  = HexColor('#2C3E50')
C_MUTED = HexColor('#7F8C8D')
C_RED   = HexColor('#E74C3C')
C_GREEN = HexColor('#2ECC71')
C_ORANGE = HexColor('#F39C12')
C_BLUE  = HexColor('#3498DB')
C_PURPLE = HexColor('#9B59B6')
C_LGRAY = HexColor('#F5F6FA')

W, H = A4

# ── 题目 → 中文标签映射 ──
LABELS = {
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
}


def _severity(deduct, thresholds):
    if deduct >= thresholds[1]: return '高风险'
    if deduct >= thresholds[0]: return '中风险'
    return '低风险'


def _build_detail_lines(a):
    """为三个维度生成逐项分析行"""
    lines = {'fin': [], 'tax': [], 'law': []}

    # ── 融资维度 ──
    fin_items = [
        ('total_debt', '负债总额', [30, 50]),
        ('loan_orgs', '贷款机构数', [25, 50]),
        ('overdue', '逾期记录', [30, 60]),
        ('debt_trend', '负债趋势', [20, 40]),
        ('rejections', '被拒记录', [15, 35]),
        ('online_loans', '网贷记录', [15, 40]),
        ('collateral', '抵押物', [20, 35]),
        ('flow_ratio', '流水比例', [15, 35]),
        ('loan_due', '到期压力', [10, 15]),
    ]
    for key, name, th in fin_items:
        val = a.get(key, '-')
        lines['fin'].append(f'{name}：{val}  {_severity(0, th)}')

    # ── 财税维度 ──
    tax_items = [
        ('acc_level', '账务规范度', [15, 35]),
        ('acc_person', '会计负责人', [10, 30]),
        ('tax_grade', '纳税信用等级', [20, 55]),
        ('tax_owed', '欠税/滞纳金', [20, 65]),
        ('invoice', '发票管理', [10, 20]),
        ('social', '社保缴纳', [20, 40]),
    ]
    for key, name, th in tax_items:
        val = a.get(key, '-')
        lines['tax'].append(f'{name}：{val}')

    # ── 法务维度 ──
    law_items = [
        ('contract_dispute', '合同纠纷', [20, 60]),
        ('labor_dispute', '劳动仲裁', [20, 60]),
        ('exec_record', '被执行记录', [25, 70]),
        ('labor_contract', '劳动合同', [15, 35]),
        ('license', '行业资质', [15, 40]),
    ]
    for key, name, th in law_items:
        val = a.get(key, '-')
        lines['law'].append(f'{name}：{val}')

    return lines


def _match_services(a, scores):
    """根据客户答案自动匹配推荐服务"""
    recs = []

    # 金融服务（核心）
    svc_items = []
    if a.get('overdue', '').find('未还') > -1: svc_items.append('信用修复')
    if a.get('loan_due', '') in ('已到期需续贷', '1个月内到期'): svc_items.append('过桥垫资')
    if a.get('loan_orgs', '') in ('4-5个', '5个以上'): svc_items.append('债务整合')
    if a.get('rejections', '') in ('2次', '3次以上'): svc_items.append('担保推荐函')
    if scores['fin'] < 300: svc_items.append('银行融资方案设计')
    if not svc_items: svc_items.append('融资方案优化')
    recs.append(('金融服务', svc_items, '核心盈利业务'))

    # 财税服务
    svc_items = []
    if a.get('acc_level', '') in ('较混乱', '两套账或无账'): svc_items.append('账务重建')
    if a.get('flow_ratio', '') in ('私户为主（2:8以下）', '基本走私户'): svc_items.append('公户流水优化')
    if a.get('tax_grade', '') == 'C级或未知': svc_items.append('纳税信用修复')
    if a.get('tax_owed', '') == '有（未处理）': svc_items.append('欠税处理方案')
    if a.get('social', '') != '正常全员缴纳': svc_items.append('社保合规整改')
    if not svc_items: svc_items.append('税务规划')
    recs.append(('财税服务', svc_items, '融资前置条件'))

    # 法务服务
    svc_items = []
    if a.get('contract_dispute', '') in ('有（已结案）', '有（未结案）'): svc_items.append('合同纠纷处理')
    if a.get('labor_dispute', '') != '无': svc_items.append('劳动仲裁应对')
    if a.get('exec_record', '') != '无': svc_items.append('失信记录处理')
    if a.get('labor_contract', '') != '全部签订': svc_items.append('劳动合同规范化')
    if not svc_items: svc_items.append('法律顾问')
    recs.append(('法务服务', svc_items, '经营风控保障'))

    return recs


def _short_actions(a):
    """短期1-3月行动项"""
    actions = []
    if a.get('overdue', '').find('未还') > -1:
        actions.append(('优先结清逾期欠款', '逾期记录是银行拒贷的首要原因，需优先处理'))
    if a.get('loan_due', '') in ('已到期需续贷', '1个月内到期'):
        actions.append(('启动过桥垫资方案', '贷款即将到期，需在到期前完成过桥安排'))
    if a.get('acc_level', '') in ('较混乱', '两套账或无账'):
        actions.append(('账务梳理与重建', '规范账务是融资审批的基本前提'))
    if a.get('tax_owed', '') == '有（未处理）':
        actions.append(('处理欠税与滞纳金', '欠税不处理会持续影响纳税信用等级'))
    if a.get('rejections', '') in ('2次', '3次以上'):
        actions.append(('暂停贷款申请3个月', '频繁申请会进一步恶化征信，需等待征信恢复'))
    if a.get('contract_dispute', '') == '有（未结案）':
        actions.append(('处理未结案合同纠纷', '未结案纠纷直接影响银行放款审批'))
    if a.get('exec_record', '') == '有记录（当前有效）':
        actions.append(('处理被执行/失信记录', '有效失信记录将导致所有银行贷款被拒'))
    if not actions:
        actions.append(('联系青商顾问获取定制方案', '根据评估结果制定针对性优化计划'))
    return actions


def _mid_actions(a):
    """中期3-6月行动项"""
    actions = []
    if a.get('flow_ratio', '') in ('私户为主（2:8以下）', '基本走私户'):
        actions.append(('公户流水优化', '逐步将业务收入转入公户，提升银行流水质量'))
    if a.get('loan_orgs', '') in ('4-5个', '5个以上'):
        actions.append(('债务整合', '减少贷款机构数量，降低多头借贷风险'))
    if a.get('social', '') != '正常全员缴纳':
        actions.append(('社保合规整改', '逐步实现全员社保缴纳'))
    if a.get('labor_contract', '') != '全部签订':
        actions.append(('劳动合同规范化', '补齐所有员工劳动合同'))
    actions.append(('融资方案对接', '在信用修复后重新匹配银行融资产品'))
    return actions


def generate_pdf(quiz_data):
    """生成8页PDF专业报告"""
    answers = quiz_data.get('answers', {})
    scores = quiz_data.get('scores', {})
    level = quiz_data.get('level', {})
    signals = quiz_data.get('signals', {})
    issues = quiz_data.get('issues', [])

    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    company = answers.get('company', '未命名')
    filename = f'report_{company}_{ts}.pdf'
    filepath = os.path.join(REPORTS, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    detail = _build_detail_lines(answers)
    recs = _match_services(answers, scores)
    short_a = _short_actions(answers)
    mid_a = _mid_actions(answers)

    def header_line(y):
        c.setFillColor(C_GOLD)
        c.rect(0, y, W, 1.5*mm, fill=1, stroke=0)

    def footer(pg):
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 7)
        c.drawCentredString(W/2, 15*mm, '潮州市青商投资服务有限公司 · chaozhouqt.com · 本报告仅供参考，不构成专业建议')
        c.drawRightString(W - 20*mm, 15*mm, f'第 {pg} 页')

    # ━━━━━━━━━━━━━━ 第1页：封面 ━━━━━━━━━━━━━━
    c.setFillColor(C_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header_line(H - 30*mm)

    y = H - 80*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 16)
    c.drawCentredString(W/2, y, '青 商 企 服')
    y -= 10*mm
    c.setFont('SimHei', 9)
    c.setFillColor(HexColor('#8899AA'))
    c.drawCentredString(W/2, y, '企业综合服务 · 融资 · 财税 · 法务')

    y -= 40*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 26)
    c.drawCentredString(W/2, y, '企业健康评估')
    y -= 14*mm
    c.setFont('SimHeiB', 22)
    c.drawCentredString(W/2, y, '专 业 报 告')

    y -= 30*mm
    c.setFillColor(HexColor('#E0E0E0'))
    c.setFont('SimHei', 14)
    c.drawCentredString(W/2, y, company)

    y -= 25*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 56)
    c.drawCentredString(W/2, y, str(scores.get('total', 0)))
    y -= 10*mm
    c.setFillColor(HexColor('#8899AA'))
    c.setFont('SimHei', 12)
    c.drawCentredString(W/2, y, f'/ 1000 分 · {level.get("label", "")} 级')
    y -= 8*mm
    c.setFont('SimHei', 10)
    c.drawCentredString(W/2, y, level.get('desc', ''))

    header_line(30*mm)
    c.setFillColor(HexColor('#8899AA'))
    c.setFont('SimHei', 9)
    c.drawCentredString(W/2, 22*mm, datetime.datetime.now().strftime('%Y年%m月%d日'))
    c.showPage()

    # ━━━━━━━━━━━━━━ 第2页：综合评估 ━━━━━━━━━━━━━━
    c.setFillColor(C_LGRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header_line(H - 20*mm)
    footer(2)

    y = H - 40*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 18)
    c.drawString(25*mm, y, '一、综合评估结论')

    y -= 18*mm
    c.setFillColor(C_TEXT)
    c.setFont('SimHei', 11)
    c.drawString(25*mm, y, f'企业名称：{company}')
    y -= 7*mm
    c.drawString(25*mm, y, f'所属行业：{answers.get("industry", "-")}')
    y -= 7*mm
    c.drawString(25*mm, y, f'成立年限：{answers.get("establish", "-")}')
    y -= 7*mm
    c.drawString(25*mm, y, f'评估日期：{datetime.datetime.now().strftime("%Y-%m-%d")}')

    y -= 16*mm
    c.setFillColor(C_TEXT)
    c.setFont('SimHeiB', 13)
    c.drawString(25*mm, y, '总体评分')

    y -= 14*mm
    # 分数环（简化为文字展示）
    tc = C_GREEN if scores.get('totalPct', 0) >= 72 else C_ORANGE if scores.get('totalPct', 0) >= 50 else C_RED
    c.setFillColor(tc)
    c.setFont('SimHeiB', 36)
    c.drawCentredString(W/2, y + 2*mm, str(scores.get('total', 0)))
    c.setFont('SimHei', 10)
    c.setFillColor(C_MUTED)
    c.drawCentredString(W/2, y - 8*mm, f'/ 1000 · {level.get("label", "")}级')

    y -= 22*mm
    c.setFillColor(C_MUTED)
    c.setFont('SimHei', 10)
    c.drawCentredString(W/2, y, level.get('desc', ''))

    # 三维度概览
    y -= 22*mm
    c.setFillColor(C_TEXT)
    c.setFont('SimHeiB', 13)
    c.drawString(25*mm, y, '三维度得分概览')

    dims_info = [
        ('融资维度', scores.get('fin', 0), 450, scores.get('finPct', 0), C_BLUE),
        ('财税维度', scores.get('tax', 0), 320, scores.get('taxPct', 0), C_GOLD),
        ('法务维度', scores.get('law', 0), 230, scores.get('lawPct', 0), C_PURPLE),
    ]
    for name, score, mx, pct, color in dims_info:
        y -= 16*mm
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 10)
        c.drawString(25*mm, y, name)
        c.setFillColor(color)
        c.setFont('SimHeiB', 10)
        c.drawRightString(W - 25*mm, y, f'{score}/{mx} ({pct}%)')
        # 进度条
        y -= 5*mm
        bar_w = W - 50*mm
        c.setFillColor(HexColor('#E0E0E0'))
        c.roundRect(25*mm, y - 2*mm, bar_w, 4*mm, 2*mm, fill=1, stroke=0)
        c.setFillColor(color)
        if pct > 0:
            c.roundRect(25*mm, y - 2*mm, bar_w * pct / 100, 4*mm, 2*mm, fill=1, stroke=0)

    # 商业信号
    y -= 22*mm
    c.setFillColor(C_TEXT)
    c.setFont('SimHeiB', 13)
    c.drawString(25*mm, y, '商业机会信号（内部参考）')

    y -= 12*mm
    c.setFont('SimHei', 10)
    c.setFillColor(C_TEXT)
    c.drawString(25*mm, y, f'过桥需求指数：{signals.get("bridge", "低")}')
    y -= 7*mm
    c.drawString(25*mm, y, f'融资紧迫度：{signals.get("urgency", "低")}')
    y -= 7*mm
    c.drawString(25*mm, y, f'客户价值等级：{signals.get("value", "C")}级')

    # 核心问题摘要
    warns = [i for i in issues if i.get('type') == 'warn']
    if warns:
        y -= 18*mm
        c.setFillColor(C_RED)
        c.setFont('SimHeiB', 13)
        c.drawString(25*mm, y, f'核心问题（{len(warns)}项）')
        for issue in warns[:5]:
            y -= 8*mm
            c.setFillColor(C_RED)
            c.setFont('SimHei', 9)
            c.drawString(28*mm, y, '●')
            c.setFillColor(C_TEXT)
            c.drawString(34*mm, y, issue.get('text', '')[:50])

    c.showPage()

    # ━━━━━━━━━━━━━━ 第3页：融资维度 ━━━━━━━━━━━━━━
    c.setFillColor(C_LGRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header_line(H - 20*mm)
    footer(3)

    y = H - 40*mm
    c.setFillColor(C_BLUE)
    c.setFont('SimHeiB', 18)
    c.drawString(25*mm, y, '二、融资维度深度分析')

    y -= 10*mm
    c.setFillColor(C_MUTED)
    c.setFont('SimHei', 10)
    c.drawString(25*mm, y, f'得分：{scores.get("fin", 0)} / 450')

    y -= 14*mm
    c.setFillColor(C_TEXT)
    c.setFont('SimHei', 10)
    fin_desc = '融资维度评估您企业的负债健康度、征信状况和融资能力。' if scores.get('fin', 0) >= 300 else '融资维度存在较多风险项，建议优先处理核心问题以恢复融资能力。'
    c.drawString(25*mm, y, fin_desc)

    y -= 14*mm
    c.setFillColor(C_TEXT)
    c.setFont('SimHeiB', 11)
    c.drawString(25*mm, y, '逐项分析')

    fin_keys = ['total_debt', 'loan_orgs', 'overdue', 'debt_trend', 'rejections',
                'online_loans', 'collateral', 'flow_ratio', 'loan_due', 'expect_amt']
    for key in fin_keys:
        y -= 9*mm
        if y < 30*mm:
            c.showPage()
            c.setFillColor(C_LGRAY)
            c.rect(0, 0, W, H, fill=1, stroke=0)
            header_line(H - 20*mm)
            footer(3)
            y = H - 40*mm
        val = answers.get(key, '-')
        label = LABELS.get(key, key)
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 9)
        c.drawString(28*mm, y, label + '：')
        c.setFillColor(C_TEXT)
        c.drawString(28*mm + 45*mm, y, str(val))

    # 动态分析
    y -= 16*mm
    c.setFillColor(C_BLUE)
    c.setFont('SimHeiB', 11)
    c.drawString(25*mm, y, '动态分析')

    analyses = []
    if answers.get('overdue', '').find('未还') > -1:
        analyses.append('存在未结清逾期记录，银行将直接拒贷，建议优先结清。')
    if answers.get('loan_orgs', '') in ('4-5个', '5个以上'):
        analyses.append('多头借贷风险显著，建议进行债务整合。')
    if answers.get('rejections', '') in ('2次', '3次以上'):
        analyses.append('近期多次被拒，征信查询过于频繁，建议暂停申请3个月。')
    if answers.get('flow_ratio', '') in ('私户为主（2:8以下）', '基本走私户'):
        analyses.append('公私户流水比例失衡，需逐步将业务收入转入公户。')
    if answers.get('loan_due', '') in ('已到期需续贷', '1个月内到期'):
        analyses.append('贷款即将到期，需尽快启动过桥垫资方案。')
    if not analyses:
        analyses.append('融资维度状况尚可，建议持续优化以获取更优融资条件。')

    for text in analyses:
        y -= 10*mm
        if y < 30*mm:
            c.showPage()
            c.setFillColor(C_LGRAY)
            c.rect(0, 0, W, H, fill=1, stroke=0)
            header_line(H - 20*mm)
            footer(3)
            y = H - 40*mm
        c.setFillColor(C_TEXT)
        c.setFont('SimHei', 9)
        c.drawString(28*mm, y, '• ' + text)

    c.showPage()

    # ━━━━━━━━━━━━━━ 第4页：财税维度 ━━━━━━━━━━━━━━
    c.setFillColor(C_LGRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header_line(H - 20*mm)
    footer(4)

    y = H - 40*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 18)
    c.drawString(25*mm, y, '三、财税维度深度分析')

    y -= 10*mm
    c.setFillColor(C_MUTED)
    c.setFont('SimHei', 10)
    c.drawString(25*mm, y, f'得分：{scores.get("tax", 0)} / 320')

    y -= 14*mm
    c.setFillColor(C_TEXT)
    c.setFont('SimHeiB', 11)
    c.drawString(25*mm, y, '逐项分析')

    tax_keys = ['acc_level', 'acc_person', 'tax_grade', 'tax_owed', 'invoice', 'social']
    for key in tax_keys:
        y -= 9*mm
        val = answers.get(key, '-')
        label = LABELS.get(key, key)
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 9)
        c.drawString(28*mm, y, label + '：')
        c.setFillColor(C_TEXT)
        c.drawString(28*mm + 45*mm, y, str(val))

    y -= 16*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 11)
    c.drawString(25*mm, y, '动态分析')

    tax_analyses = []
    if answers.get('acc_level', '') in ('较混乱', '两套账或无账'):
        tax_analyses.append('账务规范度严重不足，银行审查时将直接导致拒贷，需立即重建。')
    if answers.get('tax_grade', '') == 'C级或未知':
        tax_analyses.append('纳税信用等级偏低，影响融资及政府扶持申请。')
    if answers.get('tax_owed', '') == '有（未处理）':
        tax_analyses.append('存在未处理的欠税/滞纳金，将持续影响运营和信用。')
    if answers.get('social', '') != '正常全员缴纳':
        tax_analyses.append('社保缴纳不规范，影响融资审查和社会形象。')
    if not tax_analyses:
        tax_analyses.append('财税维度状况良好，建议持续保持合规经营。')

    for text in tax_analyses:
        y -= 10*mm
        c.setFillColor(C_TEXT)
        c.setFont('SimHei', 9)
        c.drawString(28*mm, y, '• ' + text)

    c.showPage()

    # ━━━━━━━━━━━━━━ 第5页：法务维度 ━━━━━━━━━━━━━━
    c.setFillColor(C_LGRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header_line(H - 20*mm)
    footer(5)

    y = H - 40*mm
    c.setFillColor(C_PURPLE)
    c.setFont('SimHeiB', 18)
    c.drawString(25*mm, y, '四、法务维度深度分析')

    y -= 10*mm
    c.setFillColor(C_MUTED)
    c.setFont('SimHei', 10)
    c.drawString(25*mm, y, f'得分：{scores.get("law", 0)} / 230')

    y -= 14*mm
    c.setFillColor(C_TEXT)
    c.setFont('SimHeiB', 11)
    c.drawString(25*mm, y, '逐项分析')

    law_keys = ['contract_dispute', 'labor_dispute', 'exec_record', 'labor_contract', 'license']
    for key in law_keys:
        y -= 9*mm
        val = answers.get(key, '-')
        label = LABELS.get(key, key)
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 9)
        c.drawString(28*mm, y, label + '：')
        c.setFillColor(C_TEXT)
        c.drawString(28*mm + 45*mm, y, str(val))

    y -= 16*mm
    c.setFillColor(C_PURPLE)
    c.setFont('SimHeiB', 11)
    c.drawString(25*mm, y, '动态分析')

    law_analyses = []
    if answers.get('contract_dispute', '') == '有（未结案）':
        law_analyses.append('存在未结案合同纠纷，银行放款前查询法律诉讼将直接拒贷。')
    if answers.get('labor_dispute', '') == '有（未处理）':
        law_analyses.append('存在未处理的劳动仲裁/纠纷，需尽快妥善处理。')
    if answers.get('exec_record', '') == '有记录（当前有效）':
        law_analyses.append('存在当前有效的被执行/失信记录，银行贷款几乎无望。')
    if answers.get('labor_contract', '') != '全部签订':
        law_analyses.append('劳动合同签订不规范，存在劳动争议风险。')
    if answers.get('license', '') != '有':
        law_analyses.append('行业许可证/资质不完善，可能影响经营合规性。')
    if not law_analyses:
        law_analyses.append('法务维度未发现重大风险项，建议持续做好合规管理。')

    for text in law_analyses:
        y -= 10*mm
        c.setFillColor(C_TEXT)
        c.setFont('SimHei', 9)
        c.drawString(28*mm, y, '• ' + text)

    c.showPage()

    # ━━━━━━━━━━━━━━ 第6页：行动方案 ━━━━━━━━━━━━━━
    c.setFillColor(C_LGRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header_line(H - 20*mm)
    footer(6)

    y = H - 40*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 18)
    c.drawString(25*mm, y, '五、行动方案')

    # 短期
    y -= 16*mm
    c.setFillColor(C_RED)
    c.setFont('SimHeiB', 12)
    c.drawString(25*mm, y, '短期（1-3个月）— 紧急处理')

    for title, desc in short_a[:5]:
        y -= 12*mm
        if y < 30*mm:
            c.showPage(); footer(6); y = H - 30*mm
        c.setFillColor(C_TEXT)
        c.setFont('SimHeiB', 9)
        c.drawString(28*mm, y, f'→ {title}')
        y -= 6*mm
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 8)
        c.drawString(32*mm, y, desc)

    # 中期
    y -= 16*mm
    if y < 50*mm:
        c.showPage(); footer(6); y = H - 30*mm
    c.setFillColor(C_ORANGE)
    c.setFont('SimHeiB', 12)
    c.drawString(25*mm, y, '中期（3-6个月）— 优化提升')

    for title, desc in mid_a[:5]:
        y -= 12*mm
        if y < 30*mm:
            c.showPage(); footer(6); y = H - 30*mm
        c.setFillColor(C_TEXT)
        c.setFont('SimHeiB', 9)
        c.drawString(28*mm, y, f'→ {title}')
        y -= 6*mm
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 8)
        c.drawString(32*mm, y, desc)

    # 长期
    y -= 16*mm
    if y < 50*mm:
        c.showPage(); footer(6); y = H - 30*mm
    c.setFillColor(C_GREEN)
    c.setFont('SimHeiB', 12)
    c.drawString(25*mm, y, '长期（6个月以上）— 持续发展')

    long_items = [
        ('建立长期财税合规体系', '确保财务数据持续满足银行审查标准'),
        ('维护银行关系', '定期沟通，保持授信额度和利率优势'),
        ('法务风控常态化', '合同审核、劳动合规、风险预警持续跟进'),
    ]
    for title, desc in long_items:
        y -= 12*mm
        if y < 30*mm:
            c.showPage(); footer(6); y = H - 30*mm
        c.setFillColor(C_TEXT)
        c.setFont('SimHeiB', 9)
        c.drawString(28*mm, y, f'→ {title}')
        y -= 6*mm
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 8)
        c.drawString(32*mm, y, desc)

    c.showPage()

    # ━━━━━━━━━━━━━━ 第7页：服务匹配 ━━━━━━━━━━━━━━
    c.setFillColor(C_LGRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header_line(H - 20*mm)
    footer(7)

    y = H - 40*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 18)
    c.drawString(25*mm, y, '六、青商服务匹配推荐')

    y -= 10*mm
    c.setFillColor(C_MUTED)
    c.setFont('SimHei', 10)
    c.drawString(25*mm, y, '根据您的评估结果，以下服务可能对您的企业最为关键：')

    for svc_name, items, tag in recs:
        y -= 18*mm
        if y < 50*mm:
            c.showPage(); footer(7); y = H - 30*mm
        c.setFillColor(C_GOLD)
        c.setFont('SimHeiB', 13)
        c.drawString(25*mm, y, svc_name)
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 8)
        c.drawRightString(W - 25*mm, y, tag)

        y -= 5*mm
        c.setFillColor(HexColor('#E8E8E8'))
        c.rect(25*mm, y - 1*mm, W - 50*mm, 0.5*mm, fill=1, stroke=0)

        for item in items:
            y -= 8*mm
            if y < 30*mm:
                c.showPage(); footer(7); y = H - 30*mm
            c.setFillColor(C_GOLD)
            c.setFont('SimHei', 9)
            c.drawString(30*mm, y, '●')
            c.setFillColor(C_TEXT)
            c.drawString(36*mm, y, item)

    c.showPage()

    # ━━━━━━━━━━━━━━ 第8页：附录 + 免责 ━━━━━━━━━━━━━━
    c.setFillColor(C_LGRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    header_line(H - 20*mm)
    footer(8)

    y = H - 40*mm
    c.setFillColor(C_GOLD)
    c.setFont('SimHeiB', 18)
    c.drawString(25*mm, y, '七、客户填写信息')

    y -= 14*mm
    all_keys = [
        'company', 'industry', 'establish', 'pub_flow',
        'total_debt', 'loan_orgs', 'overdue', 'debt_trend',
        'rejections', 'online_loans', 'collateral', 'flow_ratio',
        'loan_due', 'expect_amt', 'acc_level', 'acc_person',
        'tax_grade', 'tax_owed', 'invoice', 'social',
        'contract_dispute', 'labor_dispute', 'exec_record',
        'labor_contract', 'license',
    ]
    for key in all_keys:
        y -= 7*mm
        if y < 30*mm:
            c.showPage(); footer(8); y = H - 30*mm
        val = answers.get(key, '-')
        label = LABELS.get(key, key)
        c.setFillColor(C_MUTED)
        c.setFont('SimHei', 8)
        c.drawString(28*mm, y, f'{label}：')
        c.setFillColor(C_TEXT)
        c.setFont('SimHei', 8)
        c.drawString(70*mm, y, str(val))

    # 免责声明
    y -= 25*mm
    if y < 60*mm:
        c.showPage(); footer(8); y = H - 30*mm
    c.setFillColor(C_MUTED)
    c.setFont('SimHeiB', 10)
    c.drawString(25*mm, y, '免责声明')

    y -= 8*mm
    disclaimer = (
        '本报告基于客户自行填写的信息生成，仅供参考，不构成任何投资、融资、'
        '税务或法律建议。具体业务方案需由持牌专业机构根据企业实际情况提供。'
        '潮州市青商投资服务有限公司对基于本报告做出的任何决策不承担法律责任。'
    )
    c.setFont('SimHei', 8)
    lines = disclaimer.split('。')
    for line in lines:
        if not line.strip(): continue
        y -= 6*mm
        c.drawString(28*mm, y, line.strip() + '。')

    c.showPage()
    c.save()
    return filename


# ═══════════════════════════════════════
#  Flask 路由
# ═══════════════════════════════════════
app = Flask(__name__, static_folder=BASE, static_url_path='')


@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')


@app.route('/api/generate-report', methods=['POST'])
def api_report():
    try:
        data = request.get_json(force=True)
        filename = generate_pdf(data)
        base_url = request.host_url.rstrip('/')
        return jsonify({
            'ok': True,
            'url': f'{base_url}/reports/{filename}'
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/reports/<path:filename>')
def get_report(filename):
    return send_from_directory(REPORTS, filename)


if __name__ == '__main__':
    print('=' * 50)
    print('  青商企业诊断 H5 — 后端服务')
    print('  http://localhost:5000')
    print('=' * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
