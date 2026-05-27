"""青商企业诊断 H5 — Flask 后端（静态文件 + PDF 报告生成 + 飞书推送）"""
import os, datetime, json
import urllib.request
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, 'reports')
os.makedirs(REPORTS, exist_ok=True)

# ── 字体 ──
pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
try:
    pdfmetrics.registerFont(TTFont('SimHeiB', 'C:/Windows/Fonts/msyhbd.ttf'))
except Exception:
    pdfmetrics.registerFont(TTFont('SimHeiB', 'C:/Windows/Fonts/simhei.ttf'))

# ── 颜色 ──
C_GOLD   = HexColor('#D4AF37')
C_TEXT   = HexColor('#2C3E50')
C_MUTED  = HexColor('#7F8C8D')
C_RED    = HexColor('#E74C3C')
C_GREEN  = HexColor('#2ECC71')
C_ORANGE = HexColor('#F39C12')
C_BLUE   = HexColor('#3498DB')
C_PURPLE = HexColor('#9B59B6')
C_LGRAY  = HexColor('#F5F6FA')
C_BAR_BG = HexColor('#E0E0E0')

# ── 样式 ──
S = {
    'cover_brand':  ParagraphStyle('cb', fontName='SimHeiB', fontSize=16, textColor=C_GOLD, alignment=TA_CENTER, leading=24),
    'cover_sub':    ParagraphStyle('cs', fontName='SimHei',  fontSize=9,  textColor=HexColor('#8899AA'), alignment=TA_CENTER, leading=14),
    'cover_title':  ParagraphStyle('ct', fontName='SimHeiB', fontSize=26, textColor=C_GOLD, alignment=TA_CENTER, leading=36),
    'cover_title2': ParagraphStyle('ct2', fontName='SimHeiB', fontSize=22, textColor=C_GOLD, alignment=TA_CENTER, leading=30),
    'cover_company':ParagraphStyle('cc', fontName='SimHei',  fontSize=14, textColor=HexColor('#E0E0E0'), alignment=TA_CENTER, leading=20),
    'cover_score':  ParagraphStyle('csc', fontName='SimHeiB', fontSize=52, textColor=C_GOLD, alignment=TA_CENTER, leading=60),
    'cover_label':  ParagraphStyle('cl', fontName='SimHei',  fontSize=12, textColor=HexColor('#8899AA'), alignment=TA_CENTER, leading=16),
    'h1':    ParagraphStyle('h1', fontName='SimHeiB', fontSize=18, textColor=C_GOLD,   leading=26, spaceAfter=10),
    'h2':    ParagraphStyle('h2', fontName='SimHeiB', fontSize=13, textColor=C_TEXT,   leading=20, spaceAfter=6),
    'h3':    ParagraphStyle('h3', fontName='SimHeiB', fontSize=12, textColor=C_GOLD,   leading=18, spaceAfter=4),
    'body':  ParagraphStyle('bd', fontName='SimHei',  fontSize=10, textColor=C_TEXT,   leading=16),
    'small': ParagraphStyle('sm', fontName='SimHei',  fontSize=9,  textColor=C_MUTED,  leading=14),
    'tiny':  ParagraphStyle('ty', fontName='SimHei',  fontSize=8,  textColor=C_MUTED,  leading=12),
    'bullet':ParagraphStyle('bl', fontName='SimHei',  fontSize=9,  textColor=C_TEXT,   leading=14, leftIndent=12, bulletIndent=0),
    'warn':  ParagraphStyle('wn', fontName='SimHei',  fontSize=9,  textColor=C_RED,    leading=14),
    'ok':    ParagraphStyle('ok', fontName='SimHei',  fontSize=9,  textColor=C_GREEN,  leading=14),
    'title_gold': ParagraphStyle('tg', fontName='SimHeiB', fontSize=12, textColor=C_GOLD, leading=18, spaceAfter=4),
    'title_red':  ParagraphStyle('tr', fontName='SimHeiB', fontSize=12, textColor=C_RED, leading=18, spaceAfter=4),
    'title_orange': ParagraphStyle('to', fontName='SimHeiB', fontSize=12, textColor=C_ORANGE, leading=18, spaceAfter=4),
    'title_green': ParagraphStyle('tgr', fontName='SimHeiB', fontSize=12, textColor=C_GREEN, leading=18, spaceAfter=4),
    'action_title': ParagraphStyle('at', fontName='SimHeiB', fontSize=9, textColor=C_TEXT, leading=14),
    'action_desc':  ParagraphStyle('ad', fontName='SimHei',  fontSize=8, textColor=C_MUTED, leading=12, leftIndent=8),
    'center_small': ParagraphStyle('csm', fontName='SimHei', fontSize=7, textColor=C_MUTED, alignment=TA_CENTER, leading=10),
}

# ── 标签 ──
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


# ═══════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════
def _pct_color(pct):
    if pct >= 72: return C_GREEN
    if pct >= 50: return C_ORANGE
    return C_RED


def _make_bar(pct, color, width=150*mm, height=4*mm):
    """返回一个 Table 模拟进度条"""
    filled = max(1, width * pct / 100) if pct > 0 else 0
    empty = width - filled
    if filled > 0:
        data = [[''] * 1]
        t = Table(data, colWidths=[width], rowHeights=[height])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), color),
            ('ROUNDEDCORNERS', [2, 2, 2, 2]),
        ]))
    else:
        data = [['']]
        t = Table(data, colWidths=[width], rowHeights=[height])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), C_BAR_BG)]))
    return t


def _dim_row(name, score, mx, pct, color):
    """维度得分行：名称 + 分数 + 进度条"""
    bar = _make_bar(pct, color)
    data = [[
        Paragraph(name, S['small']),
        Paragraph(f'{score}/{mx}', ParagraphStyle('ds', fontName='SimHeiB', fontSize=9, textColor=color, alignment=TA_RIGHT, leading=14)),
    ]]
    t = Table(data, colWidths=[40*mm, 50*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return [t, bar, Spacer(1, 4*mm)]


def _match_services(a, scores):
    recs = []
    svc = []
    if a.get('overdue', '').find('未还') > -1: svc.append('信用修复')
    if a.get('loan_due', '') in ('已到期需续贷', '1个月内到期'): svc.append('过桥垫资')
    if a.get('loan_orgs', '') in ('4-5个', '5个以上'): svc.append('债务整合')
    if a.get('rejections', '') in ('2次', '3次以上'): svc.append('担保推荐函')
    if scores.get('fin', 0) < 300: svc.append('银行融资方案设计')
    if not svc: svc.append('融资方案优化')
    recs.append(('金融服务', svc, '核心盈利业务'))

    svc = []
    if a.get('acc_level', '') in ('较混乱', '两套账或无账'): svc.append('账务重建')
    if a.get('flow_ratio', '') in ('私户为主（2:8以下）', '基本走私户'): svc.append('公户流水优化')
    if a.get('tax_grade', '') == 'C级或未知': svc.append('纳税信用修复')
    if a.get('tax_owed', '') == '有（未处理）': svc.append('欠税处理方案')
    if a.get('social', '') != '正常全员缴纳': svc.append('社保合规整改')
    if not svc: svc.append('税务规划')
    recs.append(('财税服务', svc, '融资前置条件'))

    svc = []
    if a.get('contract_dispute', '') in ('有（已结案）', '有（未结案）'): svc.append('合同纠纷处理')
    if a.get('labor_dispute', '') != '无': svc.append('劳动仲裁应对')
    if a.get('exec_record', '') != '无': svc.append('失信记录处理')
    if a.get('labor_contract', '') != '全部签订': svc.append('劳动合同规范化')
    if not svc: svc.append('法律顾问')
    recs.append(('法务服务', svc, '经营风控保障'))
    return recs


def _short_actions(a):
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


def _action_list(items, style_title, style_desc):
    """生成行动方案 Flowable 列表"""
    result = []
    for title, desc in items:
        result.append(Paragraph(f'<b>→ {title}</b>', style_title))
        result.append(Paragraph(desc, style_desc))
        result.append(Spacer(1, 3*mm))
    return result


# ═══════════════════════════════════════
#  PDF 生成（Platypus 自动排版）
# ═══════════════════════════════════════
def _cover_page(c, doc):
    """封面页 - 用 Canvas 直接绘制"""
    from reportlab.lib.pagesizes import A4
    W, H = A4
    c.saveState()
    # 深色背景
    c.setFillColor(HexColor('#0D1B2A'))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # 金色顶线
    c.setFillColor(C_GOLD)
    c.rect(0, H - 30*mm, W, 1.5*mm, fill=1, stroke=0)
    c.restoreState()


def _later_pages(c, doc):
    """内容页 - 添加页眉页脚"""
    c.saveState()
    # 金色顶线
    c.setFillColor(C_GOLD)
    c.rect(0, A4[1] - 18*mm, A4[0], 0.8*mm, fill=1, stroke=0)
    # 页脚
    c.setFillColor(C_MUTED)
    c.setFont('SimHei', 7)
    c.drawCentredString(A4[0]/2, 10*mm, '潮州市青商投资服务有限公司  chaozhouqt.com  本报告仅供参考')
    c.drawRightString(A4[0] - 15*mm, 10*mm, f'第 {doc.page} 页')
    c.restoreState()


def generate_pdf(quiz_data):
    answers = quiz_data.get('answers', {})
    scores = quiz_data.get('scores', {})
    level = quiz_data.get('level', {})
    signals = quiz_data.get('signals', {})
    issues = quiz_data.get('issues', [])
    company = answers.get('company', '未命名')
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f'report_{company}_{ts}.pdf'
    filepath = os.path.join(REPORTS, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=28*mm, bottomMargin=22*mm,
    )
    story = []

    # ━━━━━━━━ 第1页：封面 ━━━━━━━━
    story.append(Spacer(1, 50*mm))
    story.append(Paragraph('青 商 企 服', S['cover_brand']))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('企业综合服务 · 融资 · 财税 · 法务', S['cover_sub']))
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph('企业健康评估', S['cover_title']))
    story.append(Paragraph('专 业 报 告', S['cover_title2']))
    story.append(Spacer(1, 18*mm))
    story.append(Paragraph(company, S['cover_company']))
    story.append(Spacer(1, 12*mm))
    story.append(Paragraph(str(scores.get('total', 0)), S['cover_score']))
    story.append(Paragraph(f'/ 1000 分 · {level.get("label", "")} 级', S['cover_label']))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(level.get('desc', ''), S['cover_label']))
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph(datetime.datetime.now().strftime('%Y年%m月%d日'), S['center_small']))
    story.append(PageBreak())

    # ━━━━━━━━ 第2页：综合评估结论 ━━━━━━━━
    story.append(Paragraph('一、综合评估结论', S['h1']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_GOLD, spaceAfter=8))

    # 基本信息
    info_data = [
        [Paragraph('企业名称', S['small']), Paragraph(company, S['body'])],
        [Paragraph('所属行业', S['small']), Paragraph(answers.get('industry', '-'), S['body'])],
        [Paragraph('成立年限', S['small']), Paragraph(answers.get('establish', '-'), S['body'])],
        [Paragraph('评估日期', S['small']), Paragraph(datetime.datetime.now().strftime('%Y-%m-%d'), S['body'])],
    ]
    info_t = Table(info_data, colWidths=[28*mm, 120*mm])
    info_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, HexColor('#E8E8E8')),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 10*mm))

    # 总分
    story.append(Paragraph('总体评分', S['h2']))
    score_color = _pct_color(scores.get('totalPct', 0))
    sc_style = ParagraphStyle('sc', fontName='SimHeiB', fontSize=36, textColor=score_color, alignment=TA_CENTER, leading=44)
    story.append(Paragraph(str(scores.get('total', 0)), sc_style))
    story.append(Paragraph(f'/ 1000  {level.get("label", "")} 级', S['cover_label']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(level.get('desc', ''), ParagraphStyle('ld', fontName='SimHei', fontSize=10, textColor=C_MUTED, alignment=TA_CENTER, leading=14)))
    story.append(Spacer(1, 10*mm))

    # 三维度
    story.append(Paragraph('三维度得分概览', S['h2']))
    for name, score, mx, pct, color in [
        ('融资维度', scores.get('fin', 0), 450, scores.get('finPct', 0), C_BLUE),
        ('财税维度', scores.get('tax', 0), 320, scores.get('taxPct', 0), C_GOLD),
        ('法务维度', scores.get('law', 0), 230, scores.get('lawPct', 0), C_PURPLE),
    ]:
        story.extend(_dim_row(name, score, mx, pct, color))

    story.append(Spacer(1, 8*mm))

    # 商业信号
    story.append(Paragraph('商业机会信号（内部参考）', S['h2']))
    sig_data = [
        [Paragraph('过桥需求指数', S['small']), Paragraph(signals.get('bridge', '低'), S['body'])],
        [Paragraph('融资紧迫度', S['small']), Paragraph(signals.get('urgency', '低'), S['body'])],
        [Paragraph('客户价值等级', S['small']), Paragraph(f'{signals.get("value", "C")} 级', S['body'])],
    ]
    sig_t = Table(sig_data, colWidths=[35*mm, 50*mm])
    sig_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(sig_t)
    story.append(Spacer(1, 8*mm))

    # 核心问题
    warns = [i for i in issues if i.get('type') == 'warn']
    if warns:
        story.append(Paragraph(f'核心问题（{len(warns)} 项）', ParagraphStyle('wh', fontName='SimHeiB', fontSize=13, textColor=C_RED, leading=20)))
        story.append(Spacer(1, 3*mm))
        for issue in warns:
            story.append(Paragraph(f'● {issue.get("text", "")}', S['warn']))
            story.append(Spacer(1, 2*mm))

    story.append(PageBreak())

    # ━━━━━━━━ 第3页：融资维度 ━━━━━━━━
    story.append(Paragraph('二、融资维度深度分析', ParagraphStyle('fh', fontName='SimHeiB', fontSize=18, textColor=C_BLUE, leading=26)))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_BLUE, spaceAfter=6))
    story.append(Paragraph(f'得分：{scores.get("fin", 0)} / 450', S['small']))
    story.append(Spacer(1, 4*mm))

    fin_desc = '融资维度评估您企业的负债健康度、征信状况和融资能力。' if scores.get('fin', 0) >= 300 else '融资维度存在较多风险项，建议优先处理核心问题以恢复融资能力。'
    story.append(Paragraph(fin_desc, S['body']))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph('逐项分析', S['h3']))
    fin_rows = []
    for key in ['total_debt', 'loan_orgs', 'overdue', 'debt_trend', 'rejections', 'online_loans', 'collateral', 'flow_ratio', 'loan_due', 'expect_amt']:
        val = answers.get(key, '-')
        label = LABELS.get(key, key)
        fin_rows.append([Paragraph(label, S['small']), Paragraph(str(val), S['body'])])
    fin_t = Table(fin_rows, colWidths=[40*mm, 110*mm])
    fin_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, HexColor('#E8E8E8')),
    ]))
    story.append(fin_t)
    story.append(Spacer(1, 6*mm))

    # 动态分析
    story.append(Paragraph('动态分析', S['h3']))
    fin_analysis = []
    if answers.get('overdue', '').find('未还') > -1:
        fin_analysis.append('存在未结清逾期记录，银行将直接拒贷，建议优先结清。')
    if answers.get('loan_orgs', '') in ('4-5个', '5个以上'):
        fin_analysis.append('多头借贷风险显著，建议进行债务整合。')
    if answers.get('rejections', '') in ('2次', '3次以上'):
        fin_analysis.append('近期多次被拒，征信查询过于频繁，建议暂停申请3个月。')
    if answers.get('flow_ratio', '') in ('私户为主（2:8以下）', '基本走私户'):
        fin_analysis.append('公私户流水比例失衡，需逐步将业务收入转入公户。')
    if answers.get('loan_due', '') in ('已到期需续贷', '1个月内到期'):
        fin_analysis.append('贷款即将到期，需尽快启动过桥垫资方案。')
    if not fin_analysis:
        fin_analysis.append('融资维度状况尚可，建议持续优化以获取更优融资条件。')
    for text in fin_analysis:
        story.append(Paragraph(f'● {text}', S['bullet']))
        story.append(Spacer(1, 2*mm))

    story.append(PageBreak())

    # ━━━━━━━━ 第4页：财税维度 ━━━━━━━━
    story.append(Paragraph('三、财税维度深度分析', ParagraphStyle('th', fontName='SimHeiB', fontSize=18, textColor=C_GOLD, leading=26)))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_GOLD, spaceAfter=6))
    story.append(Paragraph(f'得分：{scores.get("tax", 0)} / 320', S['small']))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph('逐项分析', S['h3']))
    tax_rows = []
    for key in ['acc_level', 'acc_person', 'tax_grade', 'tax_owed', 'invoice', 'social']:
        val = answers.get(key, '-')
        label = LABELS.get(key, key)
        tax_rows.append([Paragraph(label, S['small']), Paragraph(str(val), S['body'])])
    tax_t = Table(tax_rows, colWidths=[40*mm, 110*mm])
    tax_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, HexColor('#E8E8E8')),
    ]))
    story.append(tax_t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph('动态分析', S['h3']))
    tax_analysis = []
    if answers.get('acc_level', '') in ('较混乱', '两套账或无账'):
        tax_analysis.append('账务规范度严重不足，银行审查时将直接导致拒贷，需立即重建。')
    if answers.get('tax_grade', '') == 'C级或未知':
        tax_analysis.append('纳税信用等级偏低，影响融资及政府扶持申请。')
    if answers.get('tax_owed', '') == '有（未处理）':
        tax_analysis.append('存在未处理的欠税/滞纳金，将持续影响运营和信用。')
    if answers.get('social', '') != '正常全员缴纳':
        tax_analysis.append('社保缴纳不规范，影响融资审查和社会形象。')
    if not tax_analysis:
        tax_analysis.append('财税维度状况良好，建议持续保持合规经营。')
    for text in tax_analysis:
        story.append(Paragraph(f'● {text}', S['bullet']))
        story.append(Spacer(1, 2*mm))

    story.append(PageBreak())

    # ━━━━━━━━ 第5页：法务维度 ━━━━━━━━
    story.append(Paragraph('四、法务维度深度分析', ParagraphStyle('lh', fontName='SimHeiB', fontSize=18, textColor=C_PURPLE, leading=26)))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_PURPLE, spaceAfter=6))
    story.append(Paragraph(f'得分：{scores.get("law", 0)} / 230', S['small']))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph('逐项分析', S['h3']))
    law_rows = []
    for key in ['contract_dispute', 'labor_dispute', 'exec_record', 'labor_contract', 'license']:
        val = answers.get(key, '-')
        label = LABELS.get(key, key)
        law_rows.append([Paragraph(label, S['small']), Paragraph(str(val), S['body'])])
    law_t = Table(law_rows, colWidths=[40*mm, 110*mm])
    law_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, HexColor('#E8E8E8')),
    ]))
    story.append(law_t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph('动态分析', S['h3']))
    law_analysis = []
    if answers.get('contract_dispute', '') == '有（未结案）':
        law_analysis.append('存在未结案合同纠纷，银行放款前查询法律诉讼将直接拒贷。')
    if answers.get('labor_dispute', '') == '有（未处理）':
        law_analysis.append('存在未处理的劳动仲裁/纠纷，需尽快妥善处理。')
    if answers.get('exec_record', '') == '有记录（当前有效）':
        law_analysis.append('存在当前有效的被执行/失信记录，银行贷款几乎无望。')
    if answers.get('labor_contract', '') != '全部签订':
        law_analysis.append('劳动合同签订不规范，存在劳动争议风险。')
    if answers.get('license', '') != '有':
        law_analysis.append('行业许可证/资质不完善，可能影响经营合规性。')
    if not law_analysis:
        law_analysis.append('法务维度未发现重大风险项，建议持续做好合规管理。')
    for text in law_analysis:
        story.append(Paragraph(f'● {text}', S['bullet']))
        story.append(Spacer(1, 2*mm))

    story.append(PageBreak())

    # ━━━━━━━━ 第6页：行动方案 ━━━━━━━━
    story.append(Paragraph('五、行动方案', S['h1']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_GOLD, spaceAfter=8))

    story.append(Paragraph('短期（1-3个月）— 紧急处理', S['title_red']))
    story.extend(_action_list(_short_actions(answers), S['action_title'], S['action_desc']))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph('中期（3-6个月）— 优化提升', S['title_orange']))
    story.extend(_action_list(_mid_actions(answers), S['action_title'], S['action_desc']))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph('长期（6个月以上）— 持续发展', S['title_green']))
    story.extend(_action_list([
        ('建立长期财税合规体系', '确保财务数据持续满足银行审查标准'),
        ('维护银行关系', '定期沟通，保持授信额度和利率优势'),
        ('法务风控常态化', '合同审核、劳动合规、风险预警持续跟进'),
    ], S['action_title'], S['action_desc']))

    story.append(PageBreak())

    # ━━━━━━━━ 第7页：服务匹配 ━━━━━━━━
    story.append(Paragraph('六、青商服务匹配推荐', S['h1']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_GOLD, spaceAfter=6))
    story.append(Paragraph('根据您的评估结果，以下服务可能对您的企业最为关键：', S['body']))
    story.append(Spacer(1, 6*mm))

    for svc_name, items, tag in _match_services(answers, scores):
        hdr_data = [[
            Paragraph(svc_name, S['h3']),
            Paragraph(tag, ParagraphStyle('stag', fontName='SimHei', fontSize=8, textColor=C_GOLD, alignment=TA_RIGHT, leading=12)),
        ]]
        hdr_t = Table(hdr_data, colWidths=[60*mm, 90*mm])
        hdr_t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        story.append(hdr_t)
        story.append(HRFlowable(width='100%', thickness=0.3, color=HexColor('#E8E8E8'), spaceAfter=4))
        for item in items:
            story.append(Paragraph(f'<font color="#D4AF37">&#9679;</font>  {item}', S['body']))
            story.append(Spacer(1, 2*mm))
        story.append(Spacer(1, 6*mm))

    story.append(PageBreak())

    # ━━━━━━━━ 第8页：附录 + 免责 ━━━━━━━━
    story.append(Paragraph('七、客户填写信息', S['h1']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_GOLD, spaceAfter=8))

    all_rows = []
    for key in ['company', 'industry', 'establish', 'pub_flow',
                'total_debt', 'loan_orgs', 'overdue', 'debt_trend',
                'rejections', 'online_loans', 'collateral', 'flow_ratio',
                'loan_due', 'expect_amt', 'acc_level', 'acc_person',
                'tax_grade', 'tax_owed', 'invoice', 'social',
                'contract_dispute', 'labor_dispute', 'exec_record',
                'labor_contract', 'license']:
        val = answers.get(key, '-')
        label = LABELS.get(key, key)
        all_rows.append([Paragraph(label, S['small']), Paragraph(str(val), S['body'])])
    all_t = Table(all_rows, colWidths=[40*mm, 110*mm])
    all_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, HexColor('#E8E8E8')),
    ]))
    story.append(all_t)
    story.append(Spacer(1, 12*mm))

    # 免责声明
    story.append(Paragraph('免责声明', S['h3']))
    story.append(Paragraph(
        '本报告基于客户自行填写的信息生成，仅供参考，不构成任何投资、融资、税务或法律建议。'
        '具体业务方案需由持牌专业机构根据企业实际情况提供。'
        '潮州市青商投资服务有限公司对基于本报告做出的任何决策不承担法律责任。',
        S['small']
    ))

    # 生成
    doc.build(story, onFirstPage=_cover_page, onLaterPages=_later_pages)
    return filename


# ═══════════════════════════════════════
#  Flask 路由
# ═══════════════════════════════════════
app = Flask(__name__, static_folder=BASE, static_url_path='')
CORS(app)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')


@app.route('/api/generate-report', methods=['POST'])
def api_report():
    try:
        data = request.get_json(force=True)
        filename = generate_pdf(data)
        base_url = request.host_url.rstrip('/')
        return jsonify({'ok': True, 'url': f'{base_url}/reports/{filename}'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/reports/<path:filename>')
def get_report(filename):
    return send_from_directory(REPORTS, filename)


# ── 飞书 webhook（仅服务端持有，从环境变量读取）──
FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK', '')


def _send_feishu(text):
    """发送消息到飞书 webhook"""
    payload = json.dumps({'msg_type': 'text', 'content': {'text': text}}).encode('utf-8')
    req = urllib.request.Request(
        FEISHU_WEBHOOK,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f'飞书发送失败: {e}')
        return False


def _build_feishu_text(form_data, quiz_data, report_url):
    """构建飞书消息文本"""
    text = '【新客户企业评估】\n'
    text += '联系人：' + form_data.get('name', '-') + '\n'
    text += '电话：' + form_data.get('phone', '-') + '\n'
    answers = quiz_data.get('answers', {}) if quiz_data else {}
    scores = quiz_data.get('scores', {}) if quiz_data else {}
    level = quiz_data.get('level', {}) if quiz_data else {}
    signals = quiz_data.get('signals', {}) if quiz_data else {}
    issues = quiz_data.get('issues', []) if quiz_data else []

    text += '企业：' + answers.get('company', '-') + '\n'
    text += '行业：' + answers.get('industry', '-') + '\n'
    text += '感兴趣服务：' + form_data.get('interest', '未选择') + '\n'

    if scores:
        text += '\n—— 评估结果 ——\n'
        text += f'总分：{scores.get("total", 0)}/1000（{level.get("label", "")}）\n'
        text += f'融资：{scores.get("fin", 0)}/450\n'
        text += f'财税：{scores.get("tax", 0)}/320\n'
        text += f'法务：{scores.get("law", 0)}/230\n'
        text += f'\n过桥需求：{signals.get("bridge", "低")}\n'
        text += f'融资紧迫度：{signals.get("urgency", "低")}\n'
        text += f'客户价值：{signals.get("value", "C")}级\n'

        warns = [i for i in issues if i.get('type') == 'warn']
        if warns:
            text += '\n—— 关键问题 ——\n'
            for issue in warns:
                text += '⚠️ ' + issue.get('text', '') + '\n'

        if answers:
            text += '\n—— 客户填写信息 ——\n'
            for k in ['establish', 'pub_flow', 'total_debt', 'loan_orgs',
                       'overdue', 'expect_amt', 'tax_grade', 'contract_dispute', 'exec_record']:
                label = LABELS.get(k, k)
                text += f'{label}：{answers.get(k, "-")}\n'

    if report_url:
        text += '\n—— 专业报告 ——\n'
        text += 'PDF 下载：' + report_url + '\n'

    return text


@app.route('/api/submit', methods=['POST'])
def api_submit():
    """统一提交接口：生成PDF + 发送飞书"""
    try:
        data = request.get_json(force=True)
        form_data = data.get('form', {})
        quiz_data = data.get('quiz', {})
        base_url = request.host_url.rstrip('/')

        # 验证飞书Webhook配置
        if not FEISHU_WEBHOOK:
            print('警告：未配置FEISHU_WEBHOOK环境变量，跳过飞书通知')

        # 生成 PDF
        report_url = ''
        try:
            filename = generate_pdf(quiz_data)
            report_url = f'{base_url}/reports/{filename}'
        except Exception as e:
            print(f'PDF生成失败: {e}')

        # 发送飞书
        if FEISHU_WEBHOOK:
            feishu_text = _build_feishu_text(form_data, quiz_data, report_url)
            _send_feishu(feishu_text)

        return jsonify({'ok': True, 'reportUrl': report_url})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print('=' * 50)
    print('  青商企业诊断 H5')
    print('  http://localhost:5000')
    print('=' * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
