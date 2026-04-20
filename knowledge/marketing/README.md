# 推广策略库 - BroadFSC

*由 AI 推广研究员自动维护，每周3次更新*

## 各平台最佳实践（已验证）

### TikTok @AlexTheTrader
- **发布时间**: 周四/五 19:00-21:00 当地时间效果最好
- **最优时长**: 15-30秒（完播率高）
- **钩子公式**: "Most traders make this mistake..." / "This 1 indicator changed everything..."
- **算法关键**: 前3秒留存率 > 互动率 > 完播率
- **内容结构**: 钩子(3s) → 问题(5s) → 解决方案(15s) → CTA(3s)

### Telegram @BroadFSC
- **发布频率**: 工作日 4次/天（已实现自动化）
- **内容类型**: 盘前简报 > 市场分析 > 教育内容 > 行动号召
- **最佳时段**: 开盘前2小时（欧洲/美洲/亚洲分别对应）
- **互动技巧**: 提问帖、投票帖互动率高

### X/Twitter
- **发布频率**: 3-5条/天
- **内容格式**: 图表+分析文字，带$TICKER标签
- **互动**: 转发+评论行业热帖提升曝光
- **Thread**: 多推文长内容互动率比单推高3倍

### Discord
- **频道结构**: #市场分析 #教育内容 #问答 #公告
- **活跃维护**: 每天回复问题建立权威感
- **活动**: 每周直播/AMA 增加粘性

## 爆款内容公式

### Hook 模板（最有效）
```
"Nobody tells you this about [TOPIC]..."
"I analyzed [NUMBER] charts and found [INSIGHT]"
"This [INDICATOR/PATTERN] predicted [EVENT] 3 times in a row"
"Stop doing [COMMON MISTAKE] — do this instead"
```

### 内容日历模板
| 星期 | 内容类型 | 示例主题 |
|------|---------|---------|
| 周一 | 周市场展望 | "This Week's Key Levels to Watch" |
| 周二 | 技术分析教程 | "How to Read Candlestick Patterns" |
| 周三 | 市场解读 | "Why Markets Moved Today" |
| 周四 | 策略分享 | "My Risk Management Rules" |
| 周五 | 周复盘 | "This Week's Best Trades & Lessons" |
| 周六 | 基础知识 | "Beginner's Guide to [CONCEPT]" |
| 周日 | 励志/心态 | "Trading Mindset: Think Long Term" |

## 网站 AI 客服改进经验（2026-04-21）

### v6 核心升级要点
1. **股票识别**：ticker 必须大小写不敏感（`/^[A-Z]+$/` 在 toLowerCase 后永远匹配不到）
2. **Pollinations API**：用 `openai-large` 模型，比 `openai` 质量高很多
3. **AI 回复品味**：system prompt 禁止弱化语言（"it depends"/"Certainly!"/免责声明），要有 conviction
4. **市场数据回复**：必须引用精确价格 + 给出洞察（不只是报数据）
5. **未知 ticker fallback**：不要说 "I can't help"，而是引导用户深入交流
6. **AI-ism 清理**：去掉 "Certainly!", "Of course!", "I'd be happy to help" 等机器人套话
7. **JS 花括号平衡**：一个缺少的 `}` 会让整个脚本解析失败，所有功能全挂

### 关键教训
- 每次修改 JS 后必须验证花括号平衡
- 本地 git 修改必须及时 push
- API key/token 过期是常见故障，每日检查必须包含

---
*AI学习内容将自动追加到此文件*
