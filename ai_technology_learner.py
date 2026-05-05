#!/usr/bin/env python3
"""
AI Technology Daily Learner - 每日自动学习最新AI技术
保存到 knowledge/ai_technology/ 并同步IMA知识库

用法:
  python ai_technology_learner.py          # 运行一次（被GitHub Actions调用）
  python ai_technology_learner.py --dry-run  # 测试模式，不写文件
"""

import os
import sys
import json
import time
import datetime
import hashlib
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# =================== 配置 ===================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ADMIN_CHAT = os.environ.get('TELEGRAM_ADMIN_CHAT_ID', '')
IMA_CLIENT_ID = os.environ.get('IMA_CLIENT_ID', '')
IMA_API_KEY = os.environ.get('IMA_API_KEY', '')
IMA_KB_ID = os.environ.get('IMA_KB_ID', 'Ip-fcnRIo40w1DuuyJ4KyEfteqo1YobCajdJ-A-aGfs=')

KNOWLEDGE_DIR = Path(__file__).parent / 'knowledge' / 'ai_technology'
TODAY = datetime.datetime.now().strftime('%Y-%m-%d')
SEEN_HASH_FILE = KNOWLEDGE_DIR / '.seen_hashes.json'

# =================== 学习源配置 ===================
LEARNING_SOURCES = [
    {
        'name': 'Awesome AI Agents 2026 - GitHub',
        'url': 'https://github.com/Zijian-Ni/awesome-ai-agents-2026',
        'topic': 'agent_overview',
        'source_type': 'github',
    },
    {
        'name': 'State of AI Agent Memory 2026 - Mem0',
        'url': 'https://mem0.ai/blog/state-of-ai-agent-memory-2026',
        'topic': 'memory_system',
        'source_type': 'article',
    },
    {
        'name': 'AI Agent Design Patterns 2026',
        'url': 'https://devops.gheware.com/blog/posts/ai-agent-design-patterns-implementation-guide-2026.html',
        'topic': 'design_patterns',
        'source_type': 'article',
    },
    {
        'name': 'Building Production AI Agents 2026',
        'url': 'https://devstarsj.github.io/2026/02/24/ai-agents-autonomous-systems-tool-use-2026/',
        'topic': 'production_agent',
        'source_type': 'article',
    },
    {
        'name': 'RAG Evolution 2026 - RadarAI',
        'url': 'https://radarai.top/articles/2026-%E5%B9%B4-RAG-%E6%8A%80%E6%9C%AF%E6%9C%80%E6%96%B0%E8%BF%9B%E5%B1%95%E4%B8%8E%E8%90%BD%E5%9C%B0%E5%AE%9E%E8%B7%B5%E6%8C%87%E5%8D%97',
        'topic': 'rag_evolution',
        'source_type': 'article',
    },
    {
        'name': 'MCP Protocol Guide 2026',
        'url': 'https://ofox.ai/zh/blog/mcp-protocol-ai-agent-tools-guide-2026/',
        'topic': 'mcp_protocol',
        'source_type': 'article',
    },
    {
        'name': 'Hermes Self-Improving Agent',
        'url': 'https://ofox.ai/zh/blog/hermes-agent-self-improving-ai-complete-guide-2026/',
        'topic': 'self_improving',
        'source_type': 'article',
    },
    {
        'name': 'Continuous Learning Loop for AI Agent',
        'url': 'https://lukaxiya.github.io/coding-agent-blog/posts/ai-agent-continuous-learning-loop/',
        'topic': 'continuous_learning',
        'source_type': 'article',
    },
]

# =================== Groq AI 提炼 ===================
def ai_summarize(raw_content: str, topic: str, source_name: str) -> str:
    """用 Groq AI 提炼AI技术内容"""
    if not GROQ_API_KEY:
        lines = [l.strip() for l in raw_content.split('\n') if len(l.strip()) > 30]
        return f"# {source_name}\n\n" + '\n'.join(lines[:60])

    prompt = """You are an AI technology researcher for BroadFSC.
Analyze the provided AI technology content and extract key insights.
Focus on: Agent architectures, Memory systems, Learning loops, Tool use patterns, Production best practices.
Format as structured Markdown in Chinese with:
- 核心观点 (Key insights)
- 技术要点 (Technical highlights)
- BroadFSC应用方向 (Application for BroadFSC project)
- 可复用机制 (Reusable mechanisms)
Keep it concise, actionable, and technically deep."""

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': [
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': f"Source: {source_name}\nTopic: {topic}\n\nContent:\n\n{raw_content[:5000]}"}
                ],
                'max_tokens': 2000,
                'temperature': 0.3
            },
            timeout=30
        )
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"    ⚠️ Groq API 错误: {e}")
        lines = [l.strip() for l in raw_content.split('\n') if len(l.strip()) > 30]
        return f"# {source_name}\n\n" + '\n'.join(lines[:50])


# =================== 网页抓取 ===================
def fetch_url(url: str) -> str:
    """抓取网页内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        text = resp.text
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text[:8000]
    except Exception as e:
        print(f"    ⚠️ 抓取失败 {url}: {e}")
        return ""


# =================== 去重机制 ===================
def get_content_hash(content: str) -> str:
    return hashlib.md5(content[:500].encode()).hexdigest()[:8]


def load_seen_hashes() -> set:
    if SEEN_HASH_FILE.exists():
        try:
            return set(json.loads(SEEN_HASH_FILE.read_text(encoding='utf-8')))
        except:
            return set()
    return set()


def save_seen_hashes(hashes: set):
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    hash_list = list(hashes)[-2000:]
    SEEN_HASH_FILE.write_text(json.dumps(hash_list), encoding='utf-8')


# =================== 知识库写入 ===================
def write_knowledge(topic: str, source_name: str, content: str) -> str:
    """写入知识文件，返回文件路径"""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{TODAY}-{topic}.md"
    filepath = KNOWLEDGE_DIR / filename

    header = f"# AI技术学习 - {TODAY}\n\n"
    header += f"**主题**: {topic} | **来源**: {source_name}\n\n---\n\n"

    if filepath.exists():
        existing = filepath.read_text(encoding='utf-8')
        new_content = f"\n\n---\n\n## 来源: {source_name}\n\n{content}"
        filepath.write_text(existing + new_content, encoding='utf-8')
    else:
        filepath.write_text(header + f"## 来源: {source_name}\n\n{content}", encoding='utf-8')

    return str(filepath)


# =================== IMA 同步 ===================
def sync_to_ima(title: str, content: str) -> bool:
    """同步到IMA知识库"""
    if not IMA_CLIENT_ID or not IMA_API_KEY:
        return False
    base_url = 'https://ima.qq.com/openapi'
    headers = {
        'ima-openapi-clientid': IMA_CLIENT_ID,
        'ima-openapi-apikey': IMA_API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }
    try:
        note_resp = requests.post(
            f'{base_url}/note/v1/import_doc',
            headers=headers,
            json={'content': content[:80000], 'content_format': 1, 'folder_id': ''},
            timeout=30
        )
        note_data = note_resp.json()
        doc_id = (note_data.get('data') or {}).get('doc_id')
        if not doc_id:
            return False
        kb_resp = requests.post(
            f'{base_url}/wiki/v1/add_knowledge',
            headers=headers,
            json={'media_type': 11, 'title': title, 'knowledge_base_id': IMA_KB_ID, 'note_info': {'content_id': doc_id}},
            timeout=30
        )
        return kb_resp.json().get('suc', False)
    except:
        return False


# =================== Telegram 通知 ===================
def notify_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_CHAT:
        return
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_ADMIN_CHAT, 'text': message[:4000], 'parse_mode': 'HTML'},
            timeout=15
        )
    except:
        pass


# =================== 主执行逻辑 ===================
def run_daily_learning(dry_run: bool = False):
    print(f"\n{'='*60}")
    print(f"🤖 AI技术每日学习 - {TODAY}")
    print(f"{'='*60}\n")

    seen_hashes = load_seen_hashes()
    results = []

    # 每次选3个来源（轮换学习，避免重复）
    import random
    sources_today = random.sample(LEARNING_SOURCES, min(3, len(LEARNING_SOURCES)))

    for source in sources_today:
        print(f"📡 学习来源: {source['name']}")
        print(f"   URL: {source['url']}")

        raw = fetch_url(source['url'])
        if not raw or len(raw) < 200:
            print(f"   ⚠️ 内容太少，跳过")
            continue

        content_hash = get_content_hash(raw)
        if content_hash in seen_hashes:
            print(f"   ⏭️ 内容未变化，跳过")
            continue

        print(f"   🧠 AI 提炼中...")
        summary = ai_summarize(raw, source['topic'], source['name'])

        if len(summary) < 100:
            print(f"   ⚠️ 提炼结果太短，跳过")
            continue

        if not dry_run:
            filepath = write_knowledge(source['topic'], source['name'], summary)
            seen_hashes.add(content_hash)
            print(f"   ✅ 已写入: {Path(filepath).name}")

            # 同步到IMA
            ima_title = f"🤖 AI技术 - {source['topic']} - {TODAY}"
            if sync_to_ima(ima_title, summary):
                print(f"   ✅ IMA 同步成功")
            else:
                print(f"   ⚠️ IMA 同步跳过（未配置）")
        else:
            print(f"   ✅ [Dry Run] 提炼完成，字数: {len(summary)}")

        results.append({
            'source': source['name'],
            'topic': source['topic'],
            'length': len(summary)
        })
        time.sleep(2)

    if not dry_run:
        save_seen_hashes(seen_hashes)

    # 发送学习报告
    if results:
        report = f"🤖 <b>AI技术每日学习报告</b>\n"
        report += f"📅 日期: {TODAY}\n\n"
        report += f"✅ 完成学习 {len(results)} 个来源:\n"
        for r in results:
            report += f"  • {r['source']}\n"
            report += f"    主题: {r['topic']} | 字数: {r['length']}\n"
        report += f"\n📁 知识已保存到 knowledge/ai_technology/\n"
        report += f"📈 我已变得更好学了，每天进步一点点！"

        notify_telegram(report)
        print(f"\n✅ 学习完成！{len(results)} 个来源已处理")
    else:
        print(f"\n⚠️ 本次没有新内容可学习")

    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='AI技术每日学习')
    parser.add_argument('--dry-run', action='store_true', help='测试模式，不写文件')
    args = parser.parse_args()
    run_daily_learning(dry_run=args.dry_run)
