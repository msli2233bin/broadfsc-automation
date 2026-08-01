# RTPeptide 肽产品推广总方案（免费 + 付费）

> 合规底线：所有渠道统一 **Research Use Only（RUO）** 框架。绝不暗示人体使用、疗效、 dosing 或健康获益。落地页/广告/帖子均带 RUO 免责声明。肽为科研化学品（实验室研究用），不是消费品。

---

## 一、已上线 / 可自动化（免费，已搭好）

| # | 渠道 | 状态 | 说明 |
|---|------|------|------|
| 1 | **Telegram 频道** `@rtpeptide_official` | ✅ 每日自动 | `peptide_promotion.py` 每日 02:00 UTC 发产品科普 + 客服页脚；置顶 6 客服帖 |
| 2 | **SEO 产品站** | ✅ 待部署 | `build_peptide_seo.py` → `docs/peptide-seo/`，20 产品页 + sitemap，GitHub Pages 长尾流量 |
| 3 | **邮件 / Substack 周报** | ✅ 已验证 | `peptide_newsletter.py` 用 Groq 生成科研周报，发 Telegram + 产出 HTML（粘 Substack） |
| 4 | **Bluesky** | ⚠️ 账号被封 | 旧号 `bro-adfsc.bsky.social` 已被平台 takedown。代码就绪（`peptide_channels.py`），需新开 `rtpeptide.bsky.social` 再启用 |
| 5 | **X / Twitter** | 🔌 待 key | `peptide_channels.py` 已写，设 `X_BEARER_TOKEN` 即发（免费层 API，肽号有封号风险，监控备用号） |
| 6 | **LinkedIn 有机发帖** | 🔌 待 key | 同上，设 `LINKEDIN_ACCESS_TOKEN` + `LINKEDIN_USER_URN` |
| 7 | **Pinterest** | 🔌 待 key+图 | 设 `PINTEREST_ACCESS_TOKEN` + `PINTEREST_BOARD_ID` + `PINTEREST_IMAGE_BASE`；需配产品图 |

> 规则（按 Michael 要求）：**难注册 + 易死号的渠道不强求**。Reddit / Mastodon 已放弃。X/LinkedIn/Pinterest 代码就位，你给 key 即自动接，不勉强。

---

## 二、付费渠道（花钱的也可以，按 ROI 排序）

### A 级 — 强烈建议，肽类可投、合规框架成熟

**1. Google Search Ads（最高意向流量）**
- 配置：exact-match 商业词（`buy BPC-157 research peptide` / `TB-500 for sale` / `research peptides supplier`），文案只讲纯度/质检/运输，绝不言疗效。
- 关键：必须指向**专用 RUO 落地页**（非普通电商页）。已为你生成 `docs/peptide-seo/landing/<slug>.html`（每产品一页，RUO 免责置顶、COA 提示）。
- 预算：$3k–5k/月起；肽类 CPC 竞价低，窗口期好。
- 开户：ads.google.com → 绑定卡 → 落地页审核通过即投。

**2. LinkedIn Ads（B2B，实验室/机构定向）**
- 定向：研究人员、采购、实验室、 Clinic 业主。CPC $8–15，CTR 0.4–0.7%。
- 适合品牌 + 白皮书引流，复用 `ad_copy.csv` 的 LinkedIn 文案。
- 预算：$3k+/月。

**3. 原生广告 Outbrain / Taboola / Revcontent**
- 程序化信息流，肽类容忍度高于社媒。用 `ad_copy.csv` 的 Native 变体 + 落地页。
- 流量质量参差但 economics 可预测，适合规模化补量。

**4. Push 广告网络 PropellerAds / Evadav / RichPush**
- 对 nutra/科研类流量较友好，按点击/订阅计费，适合广撒网引流到落地页 + 邮件捕获。

### B 级 — 按需，内容/赞助型

**5. 播客赞助**（biohacking / longevity / research-chem 圈）
**6. B2B 目录付费挂名**：ThomasNet、Europages、Kompass、GoodFellow 类（实验室供应目录，长尾精准）
**7. 赞助内容 / Guest Post**：科研博客、行业媒体、longevity 论坛置顶帖
**8. YouTube（科研教育视频）**：高门槛但长尾强，肽类需严格 RUO 话术，建议先做短视频科普

> Meta / TikTok：肽类账号极易被自动审核封禁，按你的原则**不优先**；如要做，用教育向创意 + 独立备用号 + 引流到低限制平台。

---

## 三、我已为你生成的可投放素材

- `docs/peptide-seo/landing/<slug>.html` — **20 个 RUO 广告专用落地页**（Google/LinkedIn/Native 直接投）
- `docs/peptide-seo/ad_copy.csv` — **80 条广告文案**（Google Search / LinkedIn / Native 各变体）
- `docs/peptide-seo/newsletter/latest.html` — 周报 HTML，粘 Substack 即用
- `docs/peptide-seo/products/*.html` — 20 个 SEO 产品页（长尾搜索）

---

## 四、下一步（你拍板）

1. **SEO 站上线** → 本次 push 后 GitHub Pages 自动发布
2. **付费开户**：Google Ads + LinkedIn 起 $3k/月，用我生成的落地页 + 文案
3. **新开 Bluesky 号** `rtpeptide.bsky.social`（旧号已死），代码即接
4. 给 **X / LinkedIn / Pinterest** key（可选），自动加渠道
5. 如需我代生成 Pinterest 产品图 / YouTube 脚本，说一声

> 所有付费渠道需你手动开户充值；落地页、广告文案、自动化发帖我全包，接 key 即跑。报价系统独立，未触碰。
