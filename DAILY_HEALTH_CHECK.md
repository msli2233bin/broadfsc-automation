# BroadFSC 每日推广健康检查

## 检查清单

### 1. GitHub Actions
- [ ] daily_promotion.yml — 最近4次运行是否成功？
- [ ] social_posting.yml — 最近1次运行是否成功？
- [ ] update_dashboard.yml — 最近1次运行是否成功？
- [ ] 总运行时间是否超限？（2000分钟/月）

### 2. Telegram 频道
- [ ] @BroadFSC (EN) — 最近24h是否有发帖？
- [ ] @BroadFSC_ES (ES) — 最近24h是否有发帖？
- [ ] @BroadFSC_AR (AR) — 最近24h是否有发帖？

### 3. 社交媒体平台
- [ ] X/Twitter — 最近1天是否有发帖？
- [ ] Mastodon (@msli2233bin) — 账号是否可访问？最近是否有发帖？
- [ ] Discord — 频道是否活跃？

### 4. TikTok
- [ ] Postproxy API 是否可用？
- [ ] 最近是否有发布？

### 5. 客服机器人
- [ ] @BroadInvestBot — 是否在线响应？

### 6. AI 服务
- [ ] Groq API — llama-3.1-8b-instant 是否可用？

### 7. 养号账号
- [ ] Reddit — 账号状态
- [ ] Facebook — 养号进度（Day X/21）

## 常见问题速查

| 问题 | 解决方案 |
|------|----------|
| GitHub Actions 失败 | 检查 logs，常见原因：Secrets 过期、Python 依赖缺失 |
| Telegram 频道无发帖 | 检查 BOT_TOKEN 和 CHANNEL_ID 是否正确 |
| Mastodon 404 | 检查隐私设置 + Token 有效性，发一条测试帖激活页面 |
| X/Twitter 发帖失败 | 检查 OAuth 1.0a 四个 Secret 是否有效 |
| Groq API 失败 | Fallback 内容会自动启用，检查 API Key 是否过期 |
| Analytics Dashboard 失败 | 检查 analytics/ 目录文件是否存在 + git push 权限 |

## 报告模板

```
日期：YYYY-MM-DD
检查人：AI 自动检查

| 平台 | 状态 | 说明 |
|------|------|------|
| GitHub Actions | ✅/⚠️/❌ | ... |
| Telegram EN | ✅/⚠️/❌ | ... |
| Telegram ES | ✅/⚠️/❌ | ... |
| Telegram AR | ✅/⚠️/❌ | ... |
| X/Twitter | ✅/⚠️/❌ | ... |
| Mastodon | ✅/⚠️/❌ | ... |
| Discord | ✅/⚠️/❌ | ... |
| TikTok | ✅/⚠️/❌ | ... |
| 客服机器人 | ✅/⚠️/❌ | ... |
| Groq API | ✅/⚠️/❌ | ... |
```
