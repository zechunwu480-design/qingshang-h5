# 青商企业诊断 H5

潮州市青商投资服务有限公司 - 企业健康诊断平台

## 功能

- 快速企业融资风险预判（30秒3题）
- 完整25题企业健康评估（融资/财税/法务三维度）
- 自动生成专业PDF报告
- 飞书群通知

## 技术栈

| 部分 | 技术 |
|------|------|
| 前端 | HTML5 + CSS + Vanilla JS |
| 后端 | Flask + ReportLab |
| 托管 | Netlify（前端）+ Railway（后端） |

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python server.py

# 访问 http://localhost:5000
```

## 部署

### 前端（Netlify）

1. Connect GitHub repo to Netlify
2. Build command: (empty - pure static)
3. Publish directory: `/`
4. 自动部署已配置

### 后端（Railway）

1. Fork/import this repo to Railway
2. 添加环境变量：
   - `FEISHU_WEBHOOK` - 飞书群机器人Webhook地址
3. Railway 会自动检测并部署

## 环境变量

| 变量 | 说明 |
|------|------|
| `FEISHU_WEBHOOK` | 飞书群机器人Webhook URL |
| `SMTP_HOST` | 邮件SMTP服务器（可选）|
| `SMTP_USER` | 邮件用户名（可选）|
| `SMTP_PASS` | 邮件密码（可选）|

## 项目结构

```
├── index.html          # 主页面
├── css/
│   └── style.css       # 样式
├── js/
│   ├── app.js          # 入口编排
│   ├── quiz.js         # 测评逻辑
│   ├── form.js         # 表单提交
│   ├── report.js       # 报告展示
│   ├── quick.js        # 快速预判
│   ├── animations.js   # 动画
│   └── radar.js        # 雷达图
├── server.py           # Flask后端（PDF生成+飞书通知）
├── requirements.txt    # Python依赖
├── Procfile            # Railway部署配置
└── .env.example        # 环境变量模板
```