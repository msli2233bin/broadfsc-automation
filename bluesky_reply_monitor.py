"""
Bluesky 自动回复监控器
========================
自动检测自己帖子下的评论，用AI生成专业回复，提升互动率。

功能：
1. 获取自己最近帖子
2. 检测新评论（未回复过的）
3. 用Groq AI生成专业回复
4. 自动发布回复
5. 将高价值互动者记入 signal_engagers.json

运行：
    python bluesky_reply_monitor.py              # 单次运行
    python bluesky_reply_monitor.py --continuous # 每30分钟运行一次
    python bluesky_reply_monitor.py --dry-run    # 只检测不回复
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from atproto import Client, models
from groq import Groq

# ============================================================
# 配置
# ============================================================
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

STATE_FILE = Path(__file__).parent / ".bot_memory" / "bluesky_reply_monitor.json"
ENGAGER_FILE = Path(__file__).parent / ".bot_memory" / "signal_engagers.json"

# 每次检查最近N篇帖子
CHECK_POST_COUNT = 20

# 每篇帖子最多回复N条评论
MAX_REPLIES_PER_POST = 3

# 每日回复上限
DAILY_LIMIT = 15

# 跳过已有回复的评论（通过CID判断）
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {
        "replied_cids": [],  # 已回复的评论CID
        "daily_count": 0,
        "last_reset": "",
        "total_replies": 0,
    }

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

def reset_daily_count(state):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_reset") != today:
        state["daily_count"] = 0
        state["last_reset"] = today
    return state

# ============================================================
# Bluesky 客户端
# ============================================================
_client = None

def get_client():
    global _client
    if _client is not None:
        return _client
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        logger.error("BLUESKY_HANDLE or BLUESKY_APP_PASSWORD not set!")
        return None
    _client = Client()
    profile = _client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
    logger.info(f"Logged in as {profile.display_name} (@{profile.handle})")
    return _client

# ============================================================
# 获取自己最近的帖子
# ============================================================
def get_my_recent_posts(limit=CHECK_POST_COUNT):
    """获取自己最近的帖子"""
    client = get_client()
    if not client:
        return []
    try:
        response = client.app.bsky.feed.get_author_feed(
            models.AppBskyFeedGetAuthorFeed.Params(
                actor=BLUESKY_HANDLE,
                limit=limit,
            )
        )
        posts = []
        for feed_view in response.feed:
            if hasattr(feed_view, 'post'):
                posts.append(feed_view.post)
        return posts
    except Exception as e:
        logger.error(f"获取帖子失败: {e}")
        return []

# ============================================================
# 获取帖子的评论/回复
# ============================================================
def get_post_replies(post_uri):
    """获取某篇帖子下的所有回复"""
    client = get_client()
    if not client:
        return []
    try:
        thread = client.app.bsky.feed.get_post_thread(
            models.AppBskyFeedGetPostThread.Params(uri=post_uri)
        )
        if not hasattr(thread, 'thread') or not hasattr(thread.thread, 'replies'):
            return []
        return thread.thread.replies
    except Exception as e:
        logger.error(f"获取回复失败 {post_uri}: {e}")
        return []

# ============================================================
# 判断是否应该回复
# ============================================================
def should_reply_to_comment(comment, state):
    """判断是否应该回复这条评论"""
    # 获取评论CID
    comment_cid = str(comment.cid) if hasattr(comment, 'cid') else ""
    if comment_cid in state["replied_cids"]:
        return False, "already_replied"
    
    # 跳过自己的评论
    author_handle = comment.author.handle if hasattr(comment, 'author') and hasattr(comment.author, 'handle') else ""
    if author_handle.lower() == BLUESKY_HANDLE.lower().replace("@", ""):
        return False, "own_comment"
    
    # 获取评论内容
    text = ""
    if hasattr(comment, 'record') and hasattr(comment.record, 'text'):
        text = comment.record.text or ""
    
    if len(text.strip()) < 10:
        return False, "too_short"
    
    return True, "ok"

# ============================================================
# AI 生成回复
# ============================================================
def generate_reply_to_comment(post_text, comment_text, comment_author):
    """用Groq AI生成对评论的回复"""
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set, skipping AI generation")
        return None
    
    prompt = f"""You are a professional investment advisor (NOT a broker) replying to comments on Bluesky.

MY POST: {post_text[:300]}

USER @{comment_author} COMMENTED: {comment_text[:300]}

Rules:
1. Address their SPECIFIC point directly
2. Add ONE concrete insight (number, fact, or observation)
3. Keep it 1-2 sentences, punchy
4. NO opening pleasantries ("Thanks!", "Great question!")
5. NO mentioning BroadFSC or any service
6. Sound like a real trader, not AI
7. If they disagree, acknowledge their view then add your twist

Good example:
"The 88% SMH gain is correct — semiconductors led. The point: broad index stalled while rotation happened. That divergence > consensus."

Bad example:
"Thank you for your comment! I appreciate your perspective on SMH. As many analysts have noted..."

Now reply:"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.8,
        )
        reply = response.choices[0].message.content.strip()
        reply = reply.replace('"', '').replace("'", "")
        if len(reply) > 300:
            reply = reply[:297] + "..."
        return reply
    except Exception as e:
        logger.error(f"AI生成回复失败: {e}")
        return None

# ============================================================
# 发送回复
# ============================================================
def send_reply(parent_uri, parent_cid, reply_text):
    """发送回复到Bluesky"""
    client = get_client()
    if not client:
        return None
    try:
        reply_ref = models.AppBskyFeedPost.ReplyRef(
            parent=models.ComAtprotoRepoStrongRef.Main(uri=parent_uri, cid=parent_cid),
            root=models.ComAtprotoRepoStrongRef.Main(uri=parent_uri, cid=parent_cid),
        )
        result = client.send_post(reply_text, reply_to=reply_ref)
        logger.info(f"  ✅ 回复已发送: {result.uri}")
        return {"uri": str(result.uri), "cid": str(result.cid)}
    except Exception as e:
        logger.error(f"  ❌ 发送回复失败: {e}")
        return None

# ============================================================
# 更新互动者记录
# ============================================================
def update_engager(comment):
    """将评论者记入 signal_engagers.json"""
    author_handle = comment.author.handle if hasattr(comment, 'author') and hasattr(comment.author, 'handle') else ""
    author_display = comment.author.display_name if hasattr(comment, 'author') and hasattr(comment.author, 'display_name') else ""
    
    if not author_handle:
        return
    
    # 加载现有记录
    engagers = {}
    if ENGAGER_FILE.exists():
        try:
            engagers = json.loads(ENGAGER_FILE.read_text(encoding='utf-8'))
        except Exception:
            engagers = {}
    
    if "engagers" not in engagers:
        engagers["engagers"] = {}
    
    key = author_handle
    if key not in engagers["engagers"]:
        engagers["engagers"][key] = {
            "handle": author_handle,
            "display_name": author_display,
            "platform": "bluesky",
            "engagement_type": "comment_reply",
            "engagement_count": 1,
            "first_engaged": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "last_engaged": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "score": 70,  # 主动评论，高分
            "needs_followup": True,
            "followup_stage": "commented_on_my_post",
        }
    else:
        engagers["engagers"][key]["engagement_count"] += 1
        engagers["engagers"][key]["last_engaged"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        engagers["engagers"][key]["score"] = min(100, engagers["engagers"][key]["score"] + 5)
        engagers["engagers"][key]["needs_followup"] = True
    
    ENGAGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENGAGER_FILE.write_text(json.dumps(engagers, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info(f"  📝 已更新互动者记录: @{author_handle}")

# ============================================================
# 主运行函数
# ============================================================
def run_monitor(dry_run=False):
    """主监控循环"""
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        logger.error("BLUESKY_HANDLE or BLUESKY_APP_PASSWORD not set!")
        return 0
    
    state = load_state()
    state = reset_daily_count(state)
    
    remaining = DAILY_LIMIT - state["daily_count"]
    if remaining <= 0:
        logger.info(f"今日回复上限已达 ({state['daily_count']}/{DAILY_LIMIT})")
        return 0
    
    logger.info(f"开始检查自己最近的帖子（最多{CHECK_POST_COUNT}篇）...")
    
    # 获取自己最近的帖子
    my_posts = get_my_recent_posts(limit=CHECK_POST_COUNT)
    logger.info(f"获取到 {len(my_posts)} 篇帖子")
    
    reply_count = 0
    
    for post in my_posts:
        if reply_count >= remaining:
            break
        
        post_uri = str(post.uri) if hasattr(post, 'uri') else ""
        post_cid = str(post.cid) if hasattr(post, 'cid') else ""
        post_text = post.record.text if hasattr(post, 'record') and hasattr(post.record, 'text') else ""
        
        logger.info(f"\n检查帖子: {post_text[:80]}...")
        
        # 获取这篇帖子的评论
        comments = get_post_replies(post_uri)
        if not comments:
            logger.info(f"  无评论")
            continue
        
        logger.info(f"  发现 {len(comments)} 条评论")
        
        # 筛选需要回复的评论
        to_reply = []
        for comment in comments:
            should, reason = should_reply_to_comment(comment, state)
            if should:
                to_reply.append(comment)
            else:
                logger.debug(f"  跳过评论: {reason}")
        
        if not to_reply:
            logger.info(f"  无新评论需要回复")
            continue
        
        # 最多回复N条
        for comment in to_reply[:MAX_REPLIES_PER_POST]:
            if reply_count >= remaining:
                break
            
            comment_text = comment.record.text if hasattr(comment, 'record') and hasattr(comment.record, 'text') else ""
            comment_author = comment.author.handle if hasattr(comment, 'author') and hasattr(comment.author, 'handle') else "unknown"
            
            logger.info(f"\n  回复 @{comment_author}: {comment_text[:100]}...")
            
            if dry_run:
                logger.info(f"  [DRY RUN] 会回复这条评论")
                continue
            
            # 生成AI回复
            ai_reply = generate_reply_to_comment(post_text, comment_text, comment_author)
            if not ai_reply:
                logger.warning(f"  ⚠️ AI生成失败，跳过")
                continue
            
            logger.info(f"  AI回复: {ai_reply}")
            
            # 发送回复
            comment_cid = str(comment.cid) if hasattr(comment, 'cid') else ""
            result = send_reply(post_uri, comment_cid, ai_reply)
            
            if result:
                # 更新状态
                state["replied_cids"].append(comment_cid)
                state["daily_count"] += 1
                state["total_replies"] = state.get("total_replies", 0) + 1
                reply_count += 1
                
                # 更新互动者记录
                update_engager(comment)
                
                # 保存状态
                save_state(state)
                
                # 随机延迟
                delay = random.randint(30, 90)
                logger.info(f"  等待 {delay} 秒...")
                time.sleep(delay)
            else:
                logger.error(f"  ❌ 回复发送失败")
    
    save_state(state)
    logger.info(f"\n✅ 完成！本次回复 {reply_count} 条，今日总计 {state['daily_count']}/{DAILY_LIMIT}")
    return reply_count

# ============================================================
# 连续运行模式
# ============================================================
def run_continuous():
    """连续运行模式（每30分钟检查一次）"""
    logger.info("🚀 启动连续监控模式（每30分钟检查一次）...")
    while True:
        try:
            run_monitor(dry_run=False)
        except Exception as e:
            logger.error(f"运行出错: {e}")
        logger.info("⏰ 等待30分钟后下次检查...")
        time.sleep(1800)  # 30分钟

# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="Bluesky 自动回复监控器")
    parser.add_argument("--dry-run", action="store_true", help="只检测不回复")
    parser.add_argument("--continuous", action="store_true", help="连续运行模式（每30分钟检查一次）")
    args = parser.parse_args()
    
    if args.continuous:
        run_continuous()
    else:
        run_monitor(dry_run=args.dry_run)
