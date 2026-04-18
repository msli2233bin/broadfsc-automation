# BroadFSC AI 自主学习团队架构

## 概览

一个 7×24 自动运行的 AI 团队，持续从全球互联网学习销售方法、推广策略、金融知识，自动整理存储到知识库，并分发给各推广渠道使用。

---

## 团队架构

```
┌─────────────────────────────────────────────────────┐
│                  调度中心 (Scheduler)                  │
│            GitHub Actions + 本地 Python              │
│         每天分配学习任务 → 收集结果 → 存入知识库         │
└────────┬──────────┬──────────┬──────────┬────────────┘
         │          │          │          │
    ┌────▼───┐ ┌───▼────┐ ┌──▼───┐ ┌───▼────┐
    │ 销售   │ │ 推广   │ │ 金融 │ │ 竞品   │
    │ 侦察兵 │ │ 研究员 │ │ 学者 │ │ 分析师 │
    └────┬───┘ └───┬────┘ └──┬───┘ └───┬────┘
         │          │          │          │
         └──────────┴─────┬────┴──────────┘
                          ▼
                ┌──────────────────┐
                │   知识库 (Store)   │
                │  本地 MD + IMA    │
                └────────┬─────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        ┌──────────┐ ┌────────┐ ┌──────────┐
        │ 内容生成  │ │ 客服   │ │ 投流     │
        │ (发帖用)  │ │ (Bot)  │ │ (建议)   │
        └──────────┘ └────────┘ └──────────┘
```

---

## 4 个 AI Agent 角色定义

### Agent 1: 销售侦察兵 (Sales Scout)
- **学习目标**: 全球销售方法、话术技巧、客户转化策略
- **学习来源**:
  - HubSpot Blog (销售方法论)
  - Salesforce Blog (CRM最佳实践)
  - Harvard Business Review (B2B销售)
  - Neil Patel Blog (数字营销转化)
  - Grow and Convert (内容营销)
- **产出**: 销售话术库、客户转化策略、A/B测试建议
- **频率**: 每周2次
- **存储路径**: `knowledge/sales/`

### Agent 2: 推广研究员 (Marketing Researcher)
- **学习目标**: 社媒推广策略、病毒式传播技巧、平台算法变化
- **学习来源**:
  - Social Media Examiner
  - Later Blog (Instagram/TikTok策略)
  - Hootsuite Blog
  - Buffer Blog
  - TikTok Creator Portal
  - Reddit r/socialmedia, r/marketing
- **产出**: 推广策略更新、平台算法变化报告、爆款内容模式
- **频率**: 每周3次
- **存储路径**: `knowledge/marketing/`

### Agent 3: 金融学者 (Finance Scholar)
- **学习目标**: 技术分析、基本面分析、宏观经济、投资教育
- **学习来源**:
  - Investopedia (金融术语+策略)
  - BabyPips (技术分析课程)
  - Corporate Finance Institute (基本面)
  - MIT OpenCourseWare (金融理论)
  - CFA Institute Blog (专业分析)
  - TradingView Ideas (实战策略)
- **产出**: 金融知识卡片、视频脚本素材、客服问答库
- **频率**: 每天1次
- **存储路径**: `knowledge/finance/`

### Agent 4: 竞品分析师 (Competitor Analyst)
- **学习目标**: 同行推广策略、内容模式、用户互动方式
- **学习来源**:
  - FinTok 头部账号分析 (@webull, @robinhood, @eToro)
  - 金融类 Telegram 频道
  - 竞品官网和博客
  - SimilarWeb 流量分析
- **产出**: 竞品周报、差异化策略、新机会发现
- **频率**: 每周1次
- **存储路径**: `knowledge/competitors/`

---

## 知识库架构

```
broadfsc-automation/knowledge/
├── sales/                           # 销售方法
│   ├── 2026-W16-sales-tactics.md    # 按周归档
│   ├── conversion-strategies.md     # 转化策略汇总
│   └── cold-outreach-scripts.md     # 冷启动话术
├── marketing/                       # 推广策略
│   ├── 2026-W16-social-trends.md    # 社媒趋势周报
│   ├── tiktok-algorithm-update.md   # TikTok算法变化
│   ├── viral-content-patterns.md    # 爆款内容模式库
│   └── platform-best-practices.md   # 各平台最佳实践
├── finance/                         # 金融知识
│   ├── ta-basics/                   # 技术分析基础
│   │   ├── support-resistance.md
│   │   ├── candlestick-patterns.md
│   │   ├── moving-averages.md
│   │   ├── rsi-macd.md
│   │   ├── fibonacci.md
│   │   └── volume-analysis.md
│   ├── fundamentals/                # 基本面分析
│   │   ├── earnings-guide.md
│   │   ├── macro-indicators.md
│   │   └── valuation-methods.md
│   ├── daily-learn/                 # 每日学习笔记
│   │   └── 2026-04-18-lesson.md
│   └── glossary.md                  # 金融术语词典
├── competitors/                     # 竞品分析
│   ├── weekly-report/               # 竞品周报
│   │   └── 2026-W16-competitor.md
│   └── fintok-top-accounts.md       # FinTok头部账号库
├── company/                         # 公司信息
│   ├── about-broadfsc.md
│   ├── services.md
│   └── faq.md
└── INDEX.md                         # 知识库总索引
```

### 双重存储策略

| 层级 | 存储 | 用途 | 更新方式 |
|------|------|------|----------|
| **L1 本地文件** | `knowledge/*.md` | Git版本控制、团队共享 | Python 脚本自动写入 |
| **L2 IMA 知识库** | 星台的知识库 | Telegram Bot 实时检索 | upload_to_ima 脚本同步 |

---

## 自动化执行方案

### GitHub Actions 工作流

```yaml
# .github/workflows/ai_learning.yml
name: AI Learning Team

on:
  schedule:
    - cron: '0 2 * * *'     # 每天 UTC 02:00 (北京时间10:00) 金融学者
    - cron: '0 4 * * 1,4'   # 周一/四 UTC 04:00 销售侦察兵
    - cron: '0 4 * * 0,2,4' # 周日/二/四 UTC 04:00 推广研究员
    - cron: '0 4 * * 1'     # 周一 UTC 04:00 竞品分析师
  workflow_dispatch:

jobs:
  learn:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python ai_learning_agent.py --agent ${{ matrix.agent }}
    strategy:
      matrix:
        agent: [finance, sales, marketing, competitor]
```

### 核心脚本: ai_learning_agent.py

```
工作流程:
1. 根据 --agent 参数确定学习角色
2. 从预设学习源列表中随机选3-5个URL
3. 用 web_search + web_fetch 抓取内容
4. 用 Groq API 提炼总结（去除噪音，保留精华）
5. 与现有知识库比对（避免重复）
6. 写入本地 MD 文件
7. 同步到 IMA 知识库
8. 生成学习报告推送到 Telegram 管理员
```

---

## 知识分发机制

学到的知识如何被使用：

```
金融学者学到新知识
    │
    ├→ 生成 TikTok 视频脚本（自动）
    ├→ 更新 Telegram Bot 知识库（实时）
    ├→ 生成每日简报素材（每天）
    └→ 存入知识库供客服调用（按需）

推广研究员发现新策略
    │
    ├→ 更新发帖模板和Hook库
    ├→ 调整发帖时间/频率
    └→ 生成A/B测试方案

销售侦察兵学到新话术
    │
    ├→ 更新客服机器人对话模板
    ├→ 优化官网落地页文案建议
    └→ 生成私信转化脚本

竞品分析师发现新动态
    │
    ├→ 调整我们的差异化策略
    ├→ 发现新平台/新机会
    └→ 生成周报推送给管理员
```

---

## 技术实现清单

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| T1 | 创建 `ai_learning_agent.py` | ⭐⭐⭐ | 核心学习引擎 |
| T2 | 创建 `knowledge/` 目录结构 | ⭐⭐⭐ | 知识库骨架 |
| T3 | 创建 `ai_learning.yml` workflow | ⭐⭐⭐ | GitHub Actions 定时任务 |
| T4 | 编写学习源配置文件 | ⭐⭐⭐ | URL列表+抓取规则 |
| T5 | 接入 Groq API 做内容提炼 | ⭐⭐ | 去噪+结构化+去重 |
| T6 | 接入 IMA 知识库同步 | ⭐⭐ | 双重存储 |
| T7 | Telegram 学习报告推送 | ⭐⭐ | 每次学习完成后通知 |
| T8 | 知识检索 API | ⭐ | 供客服Bot实时查询 |
| T9 | 知识去重机制 | ⭐ | 避免重复学习相同内容 |
| T10 | 学习效果追踪 | ⭐ | 知识被使用次数统计 |

---

## 预算：$0

所有组件都是免费的：

| 资源 | 来源 | 费用 |
|------|------|------|
| 学习引擎 | Groq API (免费) | $0 |
| 网页抓取 | web_search + web_fetch | $0 |
| 内容提炼 | llama-3.1-8b-instant | $0 |
| 定时调度 | GitHub Actions (2000min/月) | $0 |
| 知识存储 | 本地文件 + IMA知识库 | $0 |
| 通知推送 | Telegram Bot API | $0 |

---

*本文档由 AI 学习团队自动维护，持续更新。*
