#!/usr/bin/env python3
"""检查Bluesky回复是否发送成功"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from atproto import Client

# 登录
client = Client()
profile = client.login('$BLUESKY_HANDLE', '$BLUESKY_APP_PASSWORD')
print(f"✅ 登录成功: @{profile.handle}")

# 原帖子URI
post_uri = 'at://did:plc:w4kf4kbbgvc524y7hlv5cmsz/app.bsky.feed.post/3mldkpu3nnb2c'

# 获取帖子线程
print(f"\n🔍 检查帖子线程: {post_uri}")
thread = client.app.bsky.feed.get_post_thread({'uri': post_uri})

# 显示原帖子
post = thread.thread.post
print(f"\n📄 原帖子:")
print(f"  作者: @{post.author.handle}")
print(f"  内容: {post.record.text[:100]}...")
print(f"  回复数量: {len(thread.thread.replies) if hasattr(thread.thread, 'replies') else 0}")

# 显示所有回复
if hasattr(thread.thread, 'replies') and thread.thread.replies:
    print(f"\n💬 找到 {len(thread.thread.replies)} 条回复:")
    for i, reply in enumerate(thread.thread.replies, 1):
        author = reply.author.handle if hasattr(reply, 'author') else 'unknown'
        text = reply.record.text if hasattr(reply, 'record') and hasattr(reply.record, 'text') else ''
        cid = reply.cid if hasattr(reply, 'cid') else 'unknown'
        print(f"  {i}. @{author}: {text[:80]}...")
        print(f"      CID: {cid}")
else:
    print(f"\n❌ 没有找到回复！")

# 检查我们发送的回复
print(f"\n🔍 检查我们发送的回复 (URI: at://did:plc:w4kf4kbbgvc524y7hlv5cmsz/app.bsky.feed.post/3mle323f2kp2a)")
try:
    our_reply_uri = 'at://did:plc:w4kf4kbbgvc524y7hlv5cmsz/app.bsky.feed.post/3mle323f2kp2a'
    our_reply_thread = client.app.bsky.feed.get_post_thread({'uri': our_reply_uri})
    if hasattr(our_reply_thread, 'thread') and hasattr(our_reply_thread.thread, 'post'):
        our_post = our_reply_thread.thread.post
        print(f"✅ 找到我们的回复:")
        print(f"  内容: {our_post.record.text}")
        print(f"  父帖子: {our_post.reply.parent.uri if hasattr(our_post, 'reply') else 'N/A'}")
        print(f"  根帖子: {our_post.reply.root.uri if hasattr(our_post, 'reply') else 'N/A'}")
    else:
        print(f"❌ 未找到我们的回复")
except Exception as e:
    print(f"❌ 检查失败: {e}")
