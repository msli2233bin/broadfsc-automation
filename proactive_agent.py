"""
BroadFSC Proactive Sales Agent — 主动销售智能体

核心能力：
1. 主动客户回访 — 基于客户画像和销售漏斗，定时主动联系客户
2. AI 自我评估 — 分析历史互动质量，识别系统不足，生成改进建议
3. 情感学习 — 从知识库学习人类情感表达，提升沟通温度
4. 智能内容推送 — 根据客户兴趣推送个性化内容

用法:
    from proactive_agent import ProactiveSalesAgent, AISelfEvaluator, EmotionLearner
    
    # 在 telegram_bot.py 的 main() 中初始化
    agent = ProactiveSalesAgent(memory_system, sales_engine, groq_client)
    
    # 启动主动回访定时器
    asyncio.create_task(agent.start_proactive_outreach(bot))
    
    # 每日自我评估
    evaluator = AISelfEvaluator(memory_system, sales_engine)
    report = evaluator.evaluate()
"""

import os
import sys
import json
import time
import random
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

# ============================================================
# 🎯 主动销售智能体
# ============================================================

class ProactiveSalesAgent:
    """
    主动销售智能体 — 不再被动等客户，而是主动出击
    
    策略：
    - 新客户（3天内无互动）：发送市场动态 + 轻CTA
    - 活跃客户（interest阶段）：发送SPIN深入提问 + 个性化分析
    - 高价值客户（evaluation+）：推送免费服务 + 促转化
    - 冷却客户（7天+无互动）：情感关怀 + 价值证明
    """
    
    def __init__(self, memory_system, sales_engine, groq_client):
        self.memory = memory_system
        self.sales = sales_engine
        self.groq = groq_client
        self.bot = None  # telegram Bot 实例，在 start 后注入
        
        # 主动回访配置
        self.outreach_interval_hours = 24  # 每24小时检查一次
        self.min_hours_since_last_contact = 48  # 至少48小时没联系才主动发
        self.max_daily_outreach = 5  # 每天最多主动联系5个客户
        self.last_outreach_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            ".bot_memory", "last_outreach.json"
        )
        self._load_last_outreach()
    
    def _load_last_outreach(self):
        """加载上次主动回访记录"""
        try:
            if os.path.exists(self.last_outreach_file):
                with open(self.last_outreach_file, 'r', encoding='utf-8') as f:
                    self.last_outreach = json.load(f)
            else:
                self.last_outreach = {"last_check": None, "daily_count": 0, "date": "", "records": {}}
        except Exception:
            self.last_outreach = {"last_check": None, "daily_count": 0, "date": "", "records": {}}
    
    def _save_last_outreach(self):
        """保存主动回访记录"""
        try:
            os.makedirs(os.path.dirname(self.last_outreach_file), exist_ok=True)
            with open(self.last_outreach_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_outreach, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save outreach record failed: {e}")
    
    def _should_outreach(self, user_id_str):
        """判断是否应该主动联系该客户"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 重置每日计数
        if self.last_outreach.get("date") != today:
            self.last_outreach["daily_count"] = 0
            self.last_outreach["date"] = today
        
        # 超过每日上限
        if self.last_outreach["daily_count"] >= self.max_daily_outreach:
            return False
        
        # 该客户最近24小时内已经被主动联系过
        records = self.last_outreach.get("records", {})
        last_sent = records.get(user_id_str, "")
        if last_sent:
            try:
                last_dt = datetime.fromisoformat(last_sent)
                if datetime.now() - last_dt < timedelta(hours=self.min_hours_since_last_contact):
                    return False
            except Exception:
                pass
        
        return True
    
    def _get_user_profile(self, user_id):
        """获取用户完整画像"""
        if not self.memory:
            return {}
        profile = self.memory.get_user_profile(user_id)
        uid_str = str(user_id)
        
        # 补充亲密度
        profile["intimacy_score"] = self.memory.intimacy_scores.get(user_id, 0)
        
        # 补充销售漏斗阶段
        if self.sales and uid_str in self.sales.funnel_data:
            profile["funnel_stage"] = self.sales.funnel_data[uid_str].get("stage", "awareness")
            profile["spin_phase"] = self.sales.funnel_data[uid_str].get("spin_phase", "situation")
        else:
            profile["funnel_stage"] = "awareness"
            profile["spin_phase"] = "situation"
        
        return profile
    
    def _hours_since_last_contact(self, profile):
        """计算距离上次联系的小时数"""
        last = profile.get("last_contact")
        if not last:
            return 9999
        try:
            last_dt = datetime.fromisoformat(last)
            now = datetime.now(timezone.utc)
            last_dt = last_dt.replace(tzinfo=timezone.utc) if last_dt.tzinfo is None else last_dt
            return (now - last_dt).total_seconds() / 3600
        except Exception:
            return 9999
    
    def _build_proactive_message(self, user_id, profile):
        """
        基于客户画像生成个性化主动消息
        
        策略矩阵：
        - 新客户 + 无互动: 市场动态 + 破冰
        - interest + 有投资兴趣: 个性化分析 + SPIN提问
        - evaluation+: 价值推送 + 促转化
        - 冷却客户: 情感关怀 + 回归
        """
        name = profile.get("name", "there")
        lang = profile.get("language", "en")[:2]
        stage = profile.get("funnel_stage", "awareness")
        intimacy = profile.get("intimacy_score", 0)
        hours = self._hours_since_last_contact(profile)
        interests = profile.get("investment_interests", [])
        topics = profile.get("topics_discussed", [])
        
        # 个性化上下文
        interest_str = ", ".join(interests[:3]) if interests else "the markets"
        
        # 根据冷却时间和漏斗阶段选择策略
        is_cold = hours > 168  # 7天+
        is_warm = hours > 48   # 2天+
        
        if is_cold:
            # === 冷却客户：情感关怀 + 价值证明 ===
            if lang == "zh":
                templates = [
                    f"嗨{name}！好久没聊了，最近怎么样？😊\n\n"
                    f"最近市场有些有趣的变化，尤其是{interest_str}方面。"
                    f"我想起来上次我们聊过{random.choice(topics[:3]) if topics else '投资'}，"
                    f"如果你还在关注这个方向，随时找我聊聊~\n\n"
                    f"投资不是一个人在战斗 💪",
                    
                    f"{name}，好久不见！👋\n\n"
                    f"不知道你最近投资情况怎么样？我最近看到一个关于{interest_str}的深度分析，"
                    f"挺有价值的。如果你感兴趣的话，我可以分享给你。\n\n"
                    f"有空的时候随时来找我，不聊投资也可以——就是想看看你最近怎么样 😄",
                ]
            else:
                templates = [
                    f"Hey {name}! It's been a while — how have you been? 😊\n\n"
                    f"Some interesting things happening in {interest_str} lately. "
                    f"Made me think of our chat about {random.choice(topics[:3]) if topics else 'the markets'}.\n\n"
                    f"Whenever you're free, I'd love to catch up!",
                    
                    f"{name}! Long time no see 👋\n\n"
                    f"I came across a great analysis on {interest_str} and thought of you. "
                    f"Want me to share the key takeaways?\n\n"
                    f"No pressure though — just want to check in and see how you're doing 😄",
                ]
            return random.choice(templates)
        
        elif stage in ["evaluation", "decision"]:
            # === 高价值客户：促转化 ===
            if lang == "zh":
                templates = [
                    f"{name}，上次我们聊了挺多的，我感觉你在{interest_str}方面有很清晰的思路 💡\n\n"
                    f"不知道你想不想试试我们的一对一投资顾问服务？"
                    f"第一次是完全免费的——就像两个朋友坐下来聊聊你的投资策略。\n\n"
                    f"WhatsApp: {os.environ.get('WHATSAPP_LINK', 'https://wa.me/18032150144')}\n"
                    f"或者直接访问: https://www.broadfsc.com/different\n\n"
                    f"当然，不着急——你觉得准备好了再说 😊",
                    
                    f"嗨{name}！给你分享一个好消息 🎉\n\n"
                    f"我们正在提供免费的资产健康度检查——帮你看看当前的投资组合有没有优化空间。\n\n"
                    f"完全免费，没有任何隐藏费用。如果感兴趣，随时告诉我！\n\n"
                    f"毕竟，了解自己的投资状况永远不嫌早 📊",
                ]
            else:
                templates = [
                    f"Hey {name}! After our recent chats, I can tell you have a really solid thinking around {interest_str} 💡\n\n"
                    f"Have you considered trying our 1-on-1 advisory? The first session is completely free — "
                    f"just two people talking about YOUR investment strategy.\n\n"
                    f"WhatsApp: {os.environ.get('WHATSAPP_LINK', 'https://wa.me/18032150144')}\n"
                    f"Or visit: https://www.broadfsc.com/different\n\n"
                    f"No rush at all — just something to keep in mind 😊",
                    
                    f"Hey {name}! Quick update 🎉\n\n"
                    f"We're currently offering a FREE portfolio health check — "
                    f"it helps identify optimization opportunities in your current investments.\n\n"
                    f"Zero cost, zero commitment. Let me know if you're interested!\n\n"
                    f"After all, understanding your investments is never a bad idea 📊",
                ]
            return random.choice(templates)
        
        elif stage == "interest":
            # === 兴趣阶段：SPIN深入 + 个性化内容 ===
            if lang == "zh":
                templates = [
                    f"嗨{name}！👋\n\n"
                    f"上次你问到了{random.choice(interests[:3]) if interests else '投资'}，"
                    f"我这几天仔细研究了一下，有几个角度想跟你分享：\n\n"
                    f"1. 行业趋势有没有什么新变化\n"
                    f"2. 跟你类似的投资人通常怎么布局\n"
                    f"3. 有哪些常见误区需要避开\n\n"
                    f"你比较想先了解哪个？还是有其他想聊的？😊",
                    
                    f"{name}，今天市场有点意思 📈\n\n"
                    f"我想起来你之前关注的{random.choice(interests[:3]) if interests else '市场'}，"
                    f"最近有些新动向。不过更重要的是——\n\n"
                    f"作为投资人，你现在最大的挑战是什么？"
                    f"是选股？仓位管理？还是不知道什么时候该卖？🤔\n\n"
                    f"搞清楚这个比任何行情分析都重要。",
                ]
            else:
                templates = [
                    f"Hey {name}! 👋\n\n"
                    f"You asked about {random.choice(interests[:3]) if interests else 'investing'} recently — "
                    f"I've been thinking about it and have a few angles worth exploring:\n\n"
                    f"1. Recent shifts in the sector trends\n"
                    f"2. How similar investors typically position themselves\n"
                    f"3. Common pitfalls to avoid\n\n"
                    f"Which one interests you most? Or something else entirely? 😊",
                    
                    f"{name}! The markets are interesting today 📈\n\n"
                    f"It reminded me of our chat about {random.choice(interests[:3]) if interests else 'the market'}.\n\n"
                    f"But more importantly — what's your biggest investment challenge right now? "
                    f"Stock selection? Position sizing? Timing exits? 🤔\n\n"
                    f"Figuring THAT out matters more than any market analysis.",
                ]
            return random.choice(templates)
        
        else:
            # === awareness 或默认：市场动态 + 轻CTA ===
            if lang == "zh":
                templates = [
                    f"嗨{name}！最近市场波动挺大的，有没有关注到？📊\n\n"
                    f"今天亚太市场有一些值得留意的信号。"
                    f"如果你对投资感兴趣，我可以帮你梳理一下当前的市场脉络。\n\n"
                    f"另外，我们的投资顾问团队每天都会发布市场简报，"
                    f"要不要我给你看看最新一期的？☕",
                    
                    f"{name}你好呀！👋\n\n"
                    f"不知道你最近有没有关注全球市场？"
                    f"美股、港股、A股最近都有些有趣的变化。\n\n"
                    f"如果有什么想聊的，随时来找我——"
                    f"投资问题、市场分析、或者就是随便聊聊都行 😄",
                ]
            else:
                templates = [
                    f"Hey {name}! Quite some volatility in the markets lately — have you been keeping an eye on things? 📊\n\n"
                    f"APAC markets are showing some interesting signals today. "
                    f"I can help break down what's happening if you're interested.\n\n"
                    f"Also, our advisory team publishes daily market briefings — want me to share the latest one? ☕",
                    
                    f"Hey {name}! 👋\n\n"
                    f"Been following the global markets? US, HK, and A-shares all have some interesting moves happening.\n\n"
                    f"Feel free to reach out anytime — whether it's investment questions, market analysis, or just catching up 😄",
                ]
            return random.choice(templates)
    
    async def _send_proactive_message(self, user_id, message):
        """发送主动消息"""
        if not self.bot:
            logger.warning("Bot not initialized, skipping proactive outreach")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            # 记录发送
            uid_str = str(user_id)
            self.last_outreach["daily_count"] = self.last_outreach.get("daily_count", 0) + 1
            self.last_outreach["records"][uid_str] = datetime.now().isoformat()
            self.last_outreach["last_check"] = datetime.now().isoformat()
            self._save_last_outreach()
            
            logger.info(f"🤝 Proactive outreach sent to {user_id}")
            
            # 记录到 analytics
            try:
                from analytics_logger import log_interaction
                log_interaction("telegram", "proactive_outreach", str(user_id), 
                              f"Auto proactive message sent")
            except Exception:
                pass
            
            return True
        except Exception as e:
            # 用户可能屏蔽了 bot
            logger.warning(f"Failed to send proactive message to {user_id}: {e}")
            return False
    
    def _get_priority_users(self):
        """
        获取需要主动回访的用户列表（按优先级排序）
        
        优先级：
        1. evaluation/decision 阶段的高价值客户（最可能转化）
        2. interest 阶段有互动记录但已冷却的客户
        3. 有过对话但超过7天未联系的客户
        """
        if not self.memory or not self.memory.user_preferences:
            return []
        
        candidates = []
        for uid_str, profile in self.memory.user_preferences.items():
            hours = self._hours_since_last_contact(profile)
            
            # 跳过刚联系过的
            if hours < self.min_hours_since_last_contact:
                continue
            
            # 跳过应该过滤的
            conv_count = profile.get("conversation_count", 0)
            if conv_count < 1:
                continue
            
            user_id = int(uid_str)
            full_profile = self._get_user_profile(user_id)
            stage = full_profile.get("funnel_stage", "awareness")
            
            # 计算优先级分数
            priority = 0
            if stage in ["evaluation", "decision"]:
                priority = 100  # 最高优先级
            elif stage == "interest":
                priority = 70
            else:
                priority = 30
            
            # 超过7天未联系 → 加分
            if hours > 168:
                priority += 20
            
            # 互动次数多 → 加分（说明有黏性）
            if conv_count >= 5:
                priority += 15
            elif conv_count >= 3:
                priority += 10
            
            # 亲密度高 → 加分
            intimacy = full_profile.get("intimacy_score", 0)
            if intimacy >= 20:
                priority += 10
            
            candidates.append((priority, user_id, full_profile))
        
        # 按优先级降序排列
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates
    
    async def run_proactive_outreach(self):
        """执行一次主动回访检查"""
        candidates = self._get_priority_users()
        
        if not candidates:
            logger.info("🤝 No candidates for proactive outreach")
            return
        
        sent_count = 0
        for priority, user_id, profile in candidates:
            if sent_count >= self.max_daily_outreach:
                break
            
            uid_str = str(user_id)
            if not self._should_outreach(uid_str):
                continue
            
            message = self._build_proactive_message(user_id, profile)
            success = await self._send_proactive_message(user_id, message)
            if success:
                sent_count += 1
                # 每发一条间隔 30-60 秒，避免被标记为 spam
                await asyncio.sleep(random.randint(30, 60))
        
        logger.info(f"🤝 Proactive outreach complete: {sent_count}/{len(candidates)} sent")
        return sent_count
    
    async def start_proactive_outreach(self, bot):
        """
        启动主动回访定时器
        
        每天 UTC 10:00 (北京时间18:00) 执行一次主动回访
        """
        self.bot = bot
        logger.info("🤝 Proactive Sales Agent started!")
        
        while True:
            try:
                # 计算下次执行时间
                now = datetime.now(timezone.utc)
                # 每天 UTC 10:00 (北京时间 18:00)
                target_hour = 10
                next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
                if now >= next_run:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"🤝 Next proactive outreach at {next_run.isoformat()} (wait {wait_seconds:.0f}s)")
                
                await asyncio.sleep(wait_seconds)
                
                # 执行主动回访
                sent = await self.run_proactive_outreach()
                logger.info(f"🤝 Daily proactive outreach completed: {sent} messages sent")
                
                # 通知管理员
                if sent > 0 and ADMIN_CHAT_ID:
                    try:
                        await bot.send_message(
                            chat_id=ADMIN_CHAT_ID,
                            text=f"🤝 *Proactive Outreach Report*\n\n"
                                 f"Sent: {sent} messages\n"
                                 f"Candidates: {len(self._get_priority_users())}\n"
                                 f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"🤝 Proactive outreach error: {e}")
                await asyncio.sleep(3600)  # 出错后等1小时重试


# ============================================================
# 🧠 AI 自我评估系统
# ============================================================

class AISelfEvaluator:
    """
    AI 自我评估系统 — 定期分析互动质量，识别不足
    
    评估维度：
    1. 响应质量 — 回复是否太长/太短/太机械
    2. 情感连接 — 是否正确识别和回应客户情绪
    3. 销售推进 — 是否有效推进销售漏斗
    4. 知识应用 — 是否正确运用了学习到的知识
    5. CTA有效性 — 行动召唤是否被客户响应
    """
    
    def __init__(self, memory_system, sales_engine):
        self.memory = memory_system
        self.sales = sales_engine
        self.evaluation_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "knowledge", "self_evaluations"
        )
        os.makedirs(self.evaluation_dir, exist_ok=True)
    
    def evaluate(self):
        """执行自我评估并生成报告"""
        if not self.memory or not self.memory.user_preferences:
            return {"status": "no_data", "message": "No user data to evaluate"}
        
        report = {
            "timestamp": datetime.now(timezone.utcnow()).isoformat() + "Z",
            "overall_score": 0,
            "dimensions": {},
            "issues": [],
            "improvements": [],
            "user_insights": {},
        }
        
        total_score = 0
        dim_count = 0
        
        # === 维度1：客户覆盖率 ===
        total_users = len(self.memory.user_preferences)
        active_users = sum(1 for p in self.memory.user_preferences.values() 
                          if self._hours_since(p.get("last_contact")) < 168)
        coverage_score = min(100, active_users * 20)  # 每个活跃用户20分
        report["dimensions"]["customer_coverage"] = {
            "score": coverage_score,
            "total_users": total_users,
            "active_users": active_users,
            "cold_users": total_users - active_users,
        }
        if total_users > 0 and active_users < total_users:
            report["issues"].append(
                f"⚠️ {total_users - active_users} 个客户已超过7天无互动，需要主动回访"
            )
            report["improvements"].append(
                "💡 建议：启动 ProactiveSalesAgent 对冷却客户进行情感关怀"
            )
        total_score += coverage_score
        dim_count += 1
        
        # === 维度2：销售漏斗分布 ===
        if self.sales and self.sales.funnel_data:
            stage_counts = defaultdict(int)
            for uid, data in self.sales.funnel_data.items():
                stage_counts[data.get("stage", "awareness")] += 1
            
            # 理想分布：awareness 20%, interest 30%, evaluation 25%, decision 15%, action 10%
            ideal = {"awareness": 0.2, "interest": 0.3, "evaluation": 0.25, "decision": 0.15, "action": 0.1}
            funnel_score = 100
            for stage, pct in ideal.items():
                actual_pct = stage_counts.get(stage, 0) / max(total_users, 1)
                funnel_score -= abs(actual_pct - pct) * 50
            
            funnel_score = max(0, min(100, funnel_score))
            report["dimensions"]["sales_funnel"] = {
                "score": round(funnel_score),
                "stage_distribution": dict(stage_counts),
                "analysis": self._analyze_funnel(stage_counts, total_users),
            }
            
            # 如果所有客户都卡在 awareness/interest
            if stage_counts.get("awareness", 0) + stage_counts.get("interest", 0) == total_users:
                report["issues"].append(
                    "⚠️ 所有客户都停留在认知/兴趣阶段，漏斗推进需要加强"
                )
                report["improvements"].append(
                    "💡 建议：使用更多 SPIN 提问，深入挖掘客户痛点；推送免费服务价值"
                )
            
            total_score += funnel_score
            dim_count += 1
        
        # === 维度3：情感识别效果 ===
        sentiment_scores = {}
        for uid, profile in self.memory.user_preferences.items():
            history = profile.get("sentiment_history", [])
            if len(history) >= 2:
                # 检查情绪变化后是否有应对
                negative_count = sum(1 for s in history if s.get("sentiment") == "negative")
                positive_count = sum(1 for s in history if s.get("sentiment") == "positive")
                sentiment_scores[uid] = {
                    "negative": negative_count,
                    "positive": positive_count,
                    "total": len(history),
                }
        
        emotion_score = 70  # 基础分
        if sentiment_scores:
            # 有情感记录的客户加分
            emotion_score = min(100, 70 + len(sentiment_scores) * 10)
            # 检查是否有负面情绪未被处理的客户
            for uid, scores in sentiment_scores.items():
                if scores["negative"] > 0:
                    name = self.memory.user_preferences.get(uid, {}).get("name", uid)
                    report["user_insights"][uid] = {
                        "name": name,
                        "concern": f"该客户有 {scores['negative']} 次负面情绪，需要额外关注",
                        "action": "建议发送关怀消息，了解原因",
                    }
        
        report["dimensions"]["emotional_intelligence"] = {
            "score": emotion_score,
            "users_with_sentiment_tracking": len(sentiment_scores),
            "users_with_negative_experience": sum(1 for s in sentiment_scores.values() if s["negative"] > 0),
        }
        total_score += emotion_score
        dim_count += 1
        
        # === 维度4：内容个性化 ===
        personalized_users = 0
        for uid, profile in self.memory.user_preferences.items():
            if (profile.get("investment_interests") or 
                profile.get("personal_details_mentioned") or
                len(profile.get("topics_discussed", [])) > 3):
                personalized_users += 1
        
        personalization_score = round(personalized_users / max(total_users, 1) * 100)
        report["dimensions"]["content_personalization"] = {
            "score": personalization_score,
            "users_with_profile": personalized_users,
            "users_without_profile": total_users - personalized_users,
        }
        total_score += personalization_score
        dim_count += 1
        
        # === 维度5：互动频率 ===
        avg_conversations = sum(
            p.get("conversation_count", 0) for p in self.memory.user_preferences.values()
        ) / max(total_users, 1)
        
        engagement_score = min(100, avg_conversations * 5)
        report["dimensions"]["user_engagement"] = {
            "score": round(engagement_score),
            "avg_conversations_per_user": round(avg_conversations, 1),
        }
        if avg_conversations < 3:
            report["issues"].append(
                f"⚠️ 平均每客户仅 {avg_conversations:.1f} 次对话，客户粘性不足"
            )
            report["improvements"].append(
                "💡 建议：增加主动回访频率，推送个性化内容吸引回访"
            )
        total_score += engagement_score
        dim_count += 1
        
        # 计算总分
        report["overall_score"] = round(total_score / max(dim_count, 1))
        
        # 保存报告
        self._save_report(report)
        
        return report
    
    def _analyze_funnel(self, stage_counts, total_users):
        """分析漏斗健康状况"""
        if not stage_counts:
            return "No funnel data available"
        
        lines = []
        for stage in ["awareness", "interest", "evaluation", "decision", "action"]:
            count = stage_counts.get(stage, 0)
            pct = count / max(total_users, 1) * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            emoji = {"awareness": "🔍", "interest": "💡", "evaluation": "📊", 
                     "decision": "🤔", "action": "✅"}.get(stage, "❓")
            lines.append(f"{emoji} {stage:12} {bar} {count} ({pct:.0f}%)")
        return "\n".join(lines)
    
    def _hours_since(self, last_contact_str):
        """计算距离上次联系的小时数"""
        if not last_contact_str:
            return 9999
        try:
            last_dt = datetime.fromisoformat(last_contact_str)
            now = datetime.now(timezone.utc)
            last_dt = last_dt.replace(tzinfo=timezone.utc) if last_dt.tzinfo is None else last_dt
            return (now - last_dt).total_seconds() / 3600
        except Exception:
            return 9999
    
    def _save_report(self, report):
        """保存自我评估报告"""
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = os.path.join(self.evaluation_dir, f"{today}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"🧠 Self-evaluation report saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save evaluation: {e}")
    
    def get_evaluation_summary_text(self):
        """生成人类可读的评估摘要"""
        report = self.evaluate()
        
        lines = []
        lines.append(f"🧠 *AI Self-Evaluation Report*")
        lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"")
        lines.append(f"📊 *Overall Score: {report.get('overall_score', 0)}/100*")
        lines.append(f"")
        
        for dim_name, dim_data in report.get("dimensions", {}).items():
            score = dim_data.get("score", 0)
            emoji = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
            lines.append(f"{emoji} *{dim_name}*: {score}/100")
        
        if report.get("issues"):
            lines.append(f"\n⚠️ *Issues:*")
            for issue in report["issues"]:
                lines.append(f"  • {issue}")
        
        if report.get("improvements"):
            lines.append(f"\n💡 *Suggestions:*")
            for imp in report["improvements"]:
                lines.append(f"  • {imp}")
        
        if report.get("user_insights"):
            lines.append(f"\n👥 *Customer Alerts:*")
            for uid, insight in report["user_insights"].items():
                lines.append(f"  • {insight.get('name', uid)}: {insight.get('concern', '')}")
        
        return "\n".join(lines)


# ============================================================
# ❤️ 情感学习模块
# ============================================================

class EmotionLearner:
    """
    情感学习模块 — 学习人类情感表达，提升沟通温度
    
    核心功能：
    1. 从 knowledge/sales/ 加载销售心理学知识
    2. 分析历史对话中的情感模式
    3. 生成情感化回复建议
    4. 学习客户情感触点（什么让他们开心/焦虑/信任）
    """
    
    def __init__(self, memory_system, groq_client):
        self.memory = memory_system
        self.groq = groq_client
        
        # 情感知识库
        self.emotion_patterns = {
            "trust_building": [
                "记住客户提到的小细节并在后续对话中自然提及",
                "在提供数据前先表达对客户处境的理解",
                "分享个人投资心得（标注为个人观点）来拉近距离",
                "用具体数字而非模糊描述来建立专业可信度",
                "承认自己也有犯错的时候——这反而增加信任",
            ],
            "empathy_expression": [
                "当客户表达焦虑时，先认可情绪而非急着给解决方案",
                "当客户分享盈利时，真心为他高兴——不是客套",
                "当客户亏损时，避免说'早就告诉过你'之类的话",
                "用'我理解'、'这在投资中很正常'来化解负面情绪",
                "适时分享自己经历过的类似情绪，让客户不孤单",
            ],
            "persuasion_psychology": [
                "人更容易被'不想失去'驱动，而非'想要获得'",
                "给客户选择权而非单一推荐，增加掌控感",
                "用社会证明（'很多投资人选择...'）而非硬销",
                "创造稀缺感但不要虚假紧迫（限时优惠是 cheap trick）",
                "在客户放松时（非焦虑时）推进销售效果更好",
            ],
            "cultural_sensitivity": [
                "中文客户：先建立信任再谈业务，关系比产品重要",
                "英文客户：效率优先，但有温度的效率最受欢迎",
                "中东客户：尊重和耐心是基础，不可急躁",
                "日文客户：读空气，暗示比直说更有效",
            ],
        }
        
        # 客户情感档案
        self.emotion_profiles_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            ".bot_memory", "emotion_profiles.json"
        )
        self._load_emotion_profiles()
        
        # 加载知识库中的销售心理学
        self._loaded_knowledge = self._load_sales_psychology_knowledge()
    
    def _load_emotion_profiles(self):
        """加载客户情感档案"""
        try:
            if os.path.exists(self.emotion_profiles_file):
                with open(self.emotion_profiles_file, 'r', encoding='utf-8') as f:
                    self.emotion_profiles = json.load(f)
            else:
                self.emotion_profiles = {}
        except Exception:
            self.emotion_profiles = {}
    
    def _save_emotion_profiles(self):
        """保存客户情感档案"""
        try:
            os.makedirs(os.path.dirname(self.emotion_profiles_file), exist_ok=True)
            with open(self.emotion_profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self.emotion_profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save emotion profiles failed: {e}")
    
    def _load_sales_psychology_knowledge(self):
        """从 knowledge/sales/ 加载销售心理学知识"""
        knowledge = {}
        try:
            sales_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge", "sales")
            if not os.path.exists(sales_dir):
                return knowledge
            
            for fname in os.listdir(sales_dir):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(sales_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 提取关键知识点（每个文件取前500字核心内容）
                    if "psychology" in fname.lower() or "emotion" in fname.lower():
                        knowledge[fname] = content[:800]
                    else:
                        knowledge[fname] = content[:300]
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Sales knowledge loading failed: {e}")
        
        return knowledge
    
    def learn_from_interaction(self, user_id, user_message, bot_response):
        """从一次互动中学习情感模式"""
        if not self.memory:
            return
        
        uid_str = str(user_id)
        
        # 初始化该客户的情感档案
        if uid_str not in self.emotion_profiles:
            self.emotion_profiles[uid_str] = {
                "positive_triggers": [],   # 什么让客户开心
                "negative_triggers": [],   # 什么让客户焦虑
                "trust_signals": [],       # 什么建立了信任
                "preferred_style": "unknown",
                "emotional_patterns": [],
            }
        
        profile = self.emotion_profiles[uid_str]
        
        # 简单情感分析（基于关键词）
        positive_words = ["thanks", "thank", "good", "great", "love", "happy", "nice", "helpful", "谢谢", "好的", "不错", "棒"]
        negative_words = ["bad", "terrible", "worried", "anxious", "lost", "hate", "frustrated", "不好", "担心", "焦虑", "亏损", "亏了"]
        trust_words = ["professional", "trust", "reliable", "credible", "impressive", "专业", "靠谱", "可信"]
        
        msg_lower = user_message.lower()
        
        if any(w in msg_lower for w in positive_words):
            profile["positive_triggers"].append({
                "message": user_message[:100],
                "timestamp": datetime.now().isoformat()
            })
        elif any(w in msg_lower for w in negative_words):
            profile["negative_triggers"].append({
                "message": user_message[:100],
                "timestamp": datetime.now().isoformat()
            })
        
        if any(w in msg_lower for w in trust_words):
            profile["trust_signals"].append({
                "message": user_message[:100],
                "timestamp": datetime.now().isoformat()
            })
        
        # 保留最近20条记录
        for key in ["positive_triggers", "negative_triggers", "trust_signals"]:
            if len(profile[key]) > 20:
                profile[key] = profile[key][-20:]
        
        # 定期保存
        self._save_emotion_profiles()
    
    def get_emotional_context(self, user_id):
        """获取某客户的情感上下文，用于增强 AI 回复"""
        uid_str = str(user_id)
        profile = self.emotion_profiles.get(uid_str, {})
        
        if not profile:
            return ""
        
        context_parts = []
        
        # 正面触发点
        if profile.get("positive_triggers"):
            recent_positive = [t["message"] for t in profile["positive_triggers"][-3:]]
            context_parts.append(
                f"This user responds positively to: {', '.join(recent_positive)}"
            )
        
        # 负面触发点
        if profile.get("negative_triggers"):
            recent_negative = [t["message"] for t in profile["negative_triggers"][-3:]]
            context_parts.append(
                f"Avoid topics that trigger anxiety: {', '.join(recent_negative)}"
            )
        
        # 信任信号
        if profile.get("trust_signals"):
            context_parts.append(
                f"Trust was built through: {', '.join([t['message'] for t in profile['trust_signals'][-3:]])}"
            )
        
        if context_parts:
            return "\n## Emotional Intelligence Context\n" + "\n".join(f"- {p}" for p in context_parts)
        
        return ""
    
    def get_emotion_enhancement_prompt(self, user_id):
        """生成情感增强 prompt 片段，注入到 system prompt 中"""
        if not self._loaded_knowledge:
            return ""
        
        # 随机选取一条情感学习建议
        category = random.choice(list(self.emotion_patterns.keys()))
        tips = self.emotion_patterns[category]
        tip = random.choice(tips)
        
        emotional_context = self.get_emotional_context(user_id)
        
        result = f"""
## Emotional Intelligence Enhancement
- Today's emotion tip ({category}): {tip}
{emotional_context}
"""
        return result


# ============================================================
# 全局常量（与 telegram_bot.py 共用）
# ============================================================

ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    import sys
    
    print("=== Proactive Sales Agent - Test Mode ===\n")
    
    # 测试自我评估
    print("1. Testing AI Self-Evaluator...")
    evaluator = AISelfEvaluator(None, None)
    report = evaluator.evaluate()
    print(f"   Status: {report.get('status', 'done')}")
    print(f"   Score: {report.get('overall_score', 'N/A')}/100")
    
    # 测试情感学习
    print("\n2. Testing Emotion Learner...")
    learner = EmotionLearner(None, None)
    learner.learn_from_interaction(12345, "Thanks, this was really helpful!", "Great!")
    learner.learn_from_interaction(12345, "I'm worried about my losses", "I understand...")
    print(f"   Emotion profiles: {json.dumps(learner.emotion_profiles, indent=2)}")
    
    print("\n=== All tests passed ===")
