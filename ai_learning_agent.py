"""
BroadFSC AI 自主学习团队
4个AI Agent自动从全球网站学习，写入本地知识库，同步到IMA

用法:
  python ai_learning_agent.py --agent finance
  python ai_learning_agent.py --agent sales
  python ai_learning_agent.py --agent marketing
  python ai_learning_agent.py --agent competitor
  python ai_learning_agent.py --agent all
"""

import os
import sys
import json
import time
import argparse
import datetime
import random
import hashlib
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# =================== 配置 ===================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ADMIN_CHAT = os.environ.get('TELEGRAM_ADMIN_CHAT_ID', '')  # 你的个人chat_id，用于接收学习报告
IMA_CLIENT_ID = os.environ.get('IMA_CLIENT_ID', '')
IMA_API_KEY = os.environ.get('IMA_API_KEY', '')
IMA_KB_ID = os.environ.get('IMA_KB_ID', 'Ip-fcnRIo40w1DuuyJ4KyEfteqo1YobCajdJ-A-aGfs=')

KNOWLEDGE_DIR = Path(__file__).parent / 'knowledge'
TODAY = datetime.datetime.now().strftime('%Y-%m-%d')
WEEK = datetime.datetime.now().strftime('%Y-W%W')

# =================== 学习源配置 ===================
LEARNING_SOURCES = {
    'finance': [
        {
            'name': 'Investopedia - Technical Analysis',
            'url': 'https://www.investopedia.com/technical-analysis-4689657',
            'topic': 'technical_analysis'
        },
        {
            'name': 'Investopedia - Trading Strategies',
            'url': 'https://www.investopedia.com/trading-4427765',
            'topic': 'trading_strategies'
        },
        {
            'name': 'Investopedia - Fundamental Analysis',
            'url': 'https://www.investopedia.com/fundamental-analysis-4689757',
            'topic': 'fundamental_analysis'
        },
        {
            'name': 'BabyPips - Forex School',
            'url': 'https://www.babypips.com/learn/forex',
            'topic': 'forex_basics'
        },
        {
            'name': 'CFA Institute - Research & Analysis',
            'url': 'https://www.cfainstitute.org/en/research',
            'topic': 'professional_analysis'
        },
        {
            'name': 'Investopedia - Stock Market Basics',
            'url': 'https://www.investopedia.com/stocks-4427785',
            'topic': 'stock_basics'
        },
    ],
    'sales': [
        {
            'name': 'HubSpot Sales Blog',
            'url': 'https://blog.hubspot.com/sales',
            'topic': 'sales_tactics'
        },
        {
            'name': 'Neil Patel - Conversion Optimization',
            'url': 'https://neilpatel.com/blog/conversion-rate-optimization/',
            'topic': 'conversion'
        },
        {
            'name': 'Salesforce Blog - Sales Tips',
            'url': 'https://www.salesforce.com/blog/category/sales/',
            'topic': 'crm_sales'
        },
        {
            'name': 'Close.com Blog - Sales Techniques',
            'url': 'https://www.close.com/blog',
            'topic': 'sales_techniques'
        },
        {
            'name': 'HubSpot - Email Marketing',
            'url': 'https://blog.hubspot.com/email-marketing',
            'topic': 'email_marketing'
        },
        # 🆕 全球顶级销售方法论学习源
        {
            'name': 'SPIN Selling - Huthwaite International',
            'url': 'https://huthwaite.com/resources/blog/',
            'topic': 'spin_selling'
        },
        {
            'name': 'Challenger Sale - Challenger Inc',
            'url': 'https://www.challenger.com/blog/',
            'topic': 'challenger_sale'
        },
        {
            'name': 'Sandler Training Blog',
            'url': 'https://www.sandler.com/blog',
            'topic': 'sandler_method'
        },
        {
            'name': 'FirstSales - Sales Methodologies 2026',
            'url': 'https://firstsales.io/blog/sales-methodologies/',
            'topic': 'sales_methodologies'
        },
        {
            'name': 'Gong Labs - Sales Research',
            'url': 'https://www.gong.io/blog/',
            'topic': 'sales_research'
        },
        {
            'name': 'Sales Hacker - Modern Sales Techniques',
            'url': 'https://www.saleshacker.com/',
            'topic': 'modern_sales'
        },
        {
            'name': 'Corporate Visions - Sales Psychology',
            'url': 'https://www.corporatevisions.com/blog/',
            'topic': 'sales_psychology'
        },
        # 🆕 金融投资领域专用销售学习源
        {
            'name': 'Deloitte - AI in Investment Management Sales',
            'url': 'https://www.deloitte.com/us/en/insights/industry/financial-services/ai-investment-management-sales-marketing.html',
            'topic': 'fintech_sales'
        },
        {
            'name': 'Investopedia - Financial Advisor Tips',
            'url': 'https://www.investopedia.com/financial-advisor-4427703',
            'topic': 'advisor_sales'
        },
        {
            'name': 'WealthManagement.com - Practice Management',
            'url': 'https://www.wealthmanagement.com/practice-management',
            'topic': 'wealth_sales'
        },
    ],
    'marketing': [
        {
            'name': 'Social Media Examiner',
            'url': 'https://www.socialmediaexaminer.com/',
            'topic': 'social_media'
        },
        {
            'name': 'Later Blog - Social Strategy',
            'url': 'https://later.com/blog/',
            'topic': 'content_strategy'
        },
        {
            'name': 'Buffer Blog - Social Media Tips',
            'url': 'https://buffer.com/resources/',
            'topic': 'platform_tips'
        },
        {
            'name': 'Hootsuite Blog',
            'url': 'https://blog.hootsuite.com/',
            'topic': 'social_management'
        },
        {
            'name': 'Sprout Social Insights',
            'url': 'https://sproutsocial.com/insights/',
            'topic': 'analytics_insights'
        },
        {
            'name': 'TikTok Newsroom',
            'url': 'https://newsroom.tiktok.com/en-us',
            'topic': 'tiktok_updates'
        },
    ],
    'competitor': [
        {
            'name': 'eToro Blog',
            'url': 'https://www.etoro.com/news-and-analysis/',
            'topic': 'competitor_etoro'
        },
        {
            'name': 'Webull Education',
            'url': 'https://www.webull.com/education',
            'topic': 'competitor_webull'
        },
        {
            'name': 'Interactive Brokers Insights',
            'url': 'https://www.interactivebrokers.com/en/trading/news-insights.php',
            'topic': 'competitor_ibkr'
        },
        {
            'name': 'Fintech Finance News',
            'url': 'https://ffnews.com/',
            'topic': 'industry_news'
        },
    ]
}

# =================== Groq AI 提炼 ===================
def ai_summarize(raw_content: str, agent_role: str, source_name: str) -> str:
    """用 Groq AI 提炼学到的内容"""
    if not GROQ_API_KEY:
        # 没有API Key时，做简单的文本截断清理
        lines = [l.strip() for l in raw_content.split('\n') if len(l.strip()) > 30]
        return '\n'.join(lines[:50])

    role_prompts = {
        'finance': """You are a finance education specialist for BroadFSC, a licensed investment securities firm.
Extract and summarize the key financial concepts, trading strategies, market insights from this content.
Format as structured Markdown with:
- Key concepts explained simply
- Practical trading tips
- Market insights
- Educational content suitable for retail investors
Keep it educational, factual, and suitable for global investors.""",
        
        'sales': """You are a sales strategy analyst for BroadFSC, a global investment firm.
Extract and summarize the key sales tactics, conversion strategies, and customer acquisition methods.
Format as structured Markdown with:
- Key sales techniques
- Conversion optimization tips
- Customer communication scripts (adaptable)
- Implementation suggestions for financial services
Focus on ethical, compliant sales approaches.""",
        
        'marketing': """You are a digital marketing researcher for BroadFSC.
Extract the key social media strategies, content marketing tips, platform algorithm insights.
Format as structured Markdown with:
- Platform-specific strategies
- Content creation tips
- Engagement tactics
- Algorithm insights
- Applicable action items for our channels (Telegram, TikTok, X, Discord)""",
        
        'competitor': """You are a competitive intelligence analyst for BroadFSC.
Analyze the competitor content and extract:
- Their key messaging and positioning
- Content strategies they use
- Engagement tactics
- What BroadFSC can learn or differentiate from
Format as structured Markdown with actionable insights."""
    }

    prompt = role_prompts.get(agent_role, role_prompts['finance'])
    
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
                    {'role': 'user', 'content': f"Source: {source_name}\n\nContent to analyze:\n\n{raw_content[:6000]}"}
                ],
                'max_tokens': 1500,
                'temperature': 0.3
            },
            timeout=30
        )
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"    ⚠️ Groq API 错误: {e}")
        # fallback: 简单清理
        lines = [l.strip() for l in raw_content.split('\n') if len(l.strip()) > 40]
        return f"# {source_name} 学习笔记\n\n" + '\n'.join(lines[:40])


# =================== 网页抓取 ===================
def fetch_url(url: str) -> str:
    """抓取网页内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        
        # 简单提取文本内容（去掉HTML标签）
        text = resp.text
        
        # 移除 script/style 标签内容
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)  # 移除所有HTML标签
        text = re.sub(r'&[a-z]+;', ' ', text)  # 移除HTML实体
        text = re.sub(r'\s+', ' ', text)  # 合并空白
        
        return text[:8000]
    except Exception as e:
        print(f"    ⚠️ 抓取失败 {url}: {e}")
        return ""


# =================== 知识库写入 ===================
def get_content_hash(content: str) -> str:
    """计算内容哈希，用于去重"""
    return hashlib.md5(content[:500].encode()).hexdigest()[:8]


def load_seen_hashes(agent: str) -> set:
    """加载已处理过的内容哈希"""
    hash_file = KNOWLEDGE_DIR / agent / '.seen_hashes.json'
    if hash_file.exists():
        try:
            return set(json.loads(hash_file.read_text()))
        except:
            return set()
    return set()


def save_seen_hashes(agent: str, hashes: set):
    """保存内容哈希"""
    hash_file = KNOWLEDGE_DIR / agent / '.seen_hashes.json'
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    # 只保留最近1000条
    hash_list = list(hashes)[-1000:]
    hash_file.write_text(json.dumps(hash_list), encoding='utf-8')


def write_knowledge(agent: str, topic: str, source_name: str, content: str) -> str:
    """写入知识到本地文件，返回文件路径"""
    kb_dir = KNOWLEDGE_DIR / agent
    kb_dir.mkdir(parents=True, exist_ok=True)
    
    # 按日期+主题命名
    filename = f"{TODAY}-{topic}.md"
    filepath = kb_dir / filename
    
    # 如果文件已存在，追加内容
    if filepath.exists():
        existing = filepath.read_text(encoding='utf-8')
        new_content = f"\n\n---\n\n## 来源: {source_name}\n\n{content}"
        filepath.write_text(existing + new_content, encoding='utf-8')
    else:
        header = f"# {agent.upper()} 学习笔记 - {TODAY}\n\n"
        header += f"**Agent**: {agent} | **主题**: {topic}\n\n---\n\n"
        header += f"## 来源: {source_name}\n\n{content}"
        filepath.write_text(header, encoding='utf-8')
    
    return str(filepath)


def update_index():
    """更新知识库总索引"""
    index_path = KNOWLEDGE_DIR / 'INDEX.md'
    
    # 扫描所有知识文件
    entries = []
    for agent in ['finance', 'sales', 'marketing', 'competitor']:
        agent_dir = KNOWLEDGE_DIR / agent
        if agent_dir.exists():
            files = sorted(agent_dir.glob('*.md'), reverse=True)
            for f in files[:5]:  # 每个agent最新5条
                entries.append(f"- [{f.stem}]({agent}/{f.name}) - {agent}")
    
    index_content = f"""# BroadFSC 知识库总索引

*最后更新: {TODAY}*

## 知识分类

| 分类 | 路径 | 说明 |
|------|------|------|
| 📈 金融知识 | `knowledge/finance/` | 技术分析、基本面、交易策略 |
| 💼 销售方法 | `knowledge/sales/` | 话术、转化策略、客户沟通 |
| 📱 推广策略 | `knowledge/marketing/` | 社媒运营、内容策略、算法洞察 |
| 🔍 竞品分析 | `knowledge/competitor/` | 行业动态、竞品策略、差异化 |

## 最新学习记录

{chr(10).join(entries) if entries else '暂无记录'}

## 使用说明

- **Telegram Bot**: 可直接查询知识库内容
- **IMA 知识库**: 已同步到星台的知识库
- **内容生成**: 金融知识直接转化为TikTok/Telegram内容
"""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index_content, encoding='utf-8')


# =================== IMA 同步 ===================
def sync_to_ima(title: str, content: str) -> bool:
    """同步到 IMA 知识库"""
    if not IMA_CLIENT_ID or not IMA_API_KEY:
        print("    ℹ️ IMA Key 未配置，跳过同步")
        return False
    
    base_url = 'https://ima.qq.com/openapi'
    headers = {
        'ima-openapi-clientid': IMA_CLIENT_ID,
        'ima-openapi-apikey': IMA_API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    try:
        # 创建笔记
        note_resp = requests.post(
            f'{base_url}/note/v1/import_doc',
            headers=headers,
            json={'content': content[:80000], 'content_format': 1, 'folder_id': ''},
            timeout=30
        )
        note_data = note_resp.json()
        doc_id = (note_data.get('data') or {}).get('doc_id')
        
        if not doc_id:
            print(f"    ⚠️ IMA 笔记创建失败: {str(note_data)[:100]}")
            return False
        
        # 添加到知识库
        kb_resp = requests.post(
            f'{base_url}/wiki/v1/add_knowledge',
            headers=headers,
            json={
                'media_type': 11,
                'title': title,
                'knowledge_base_id': IMA_KB_ID,
                'note_info': {'content_id': doc_id}
            },
            timeout=30
        )
        kb_data = kb_resp.json()
        if kb_data.get('suc'):
            print(f"    ✅ IMA 同步成功: {title}")
            return True
        else:
            print(f"    ⚠️ IMA 知识库添加失败: {str(kb_data)[:100]}")
            return False
    except Exception as e:
        print(f"    ⚠️ IMA 同步异常: {e}")
        return False


# =================== Telegram 通知 ===================
def notify_telegram(message: str):
    """发送学习报告到 Telegram 管理员"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_CHAT:
        print("    ℹ️ Telegram 通知未配置")
        return
    
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={
                'chat_id': TELEGRAM_ADMIN_CHAT,
                'text': message[:4096],
                'parse_mode': 'HTML'
            },
            timeout=15
        )
        print("    ✅ 学习报告已推送到 Telegram")
    except Exception as e:
        print(f"    ⚠️ Telegram 通知失败: {e}")


# =================== 主执行逻辑 ===================
def run_agent(agent: str):
    """运行指定 Agent 的学习任务"""
    sources = LEARNING_SOURCES.get(agent, [])
    if not sources:
        print(f"未知 agent: {agent}")
        return
    
    print(f"\n{'='*60}")
    print(f"🤖 {agent.upper()} Agent 启动 - {TODAY}")
    print(f"{'='*60}")
    
    # 随机选3-4个来源（避免每次学相同内容）
    selected = random.sample(sources, min(3, len(sources)))
    
    seen_hashes = load_seen_hashes(agent)
    results = []
    
    for source in selected:
        print(f"\n📡 学习来源: {source['name']}")
        print(f"   URL: {source['url']}")
        
        # 抓取内容
        raw = fetch_url(source['url'])
        if not raw or len(raw) < 200:
            print(f"   ⚠️ 内容太少，跳过")
            continue
        
        # 去重检查
        content_hash = get_content_hash(raw)
        if content_hash in seen_hashes:
            print(f"   ⏭️ 内容未变化，跳过")
            continue
        
        # AI 提炼
        print(f"   🧠 AI 提炼中...")
        summary = ai_summarize(raw, agent, source['name'])
        
        if len(summary) < 100:
            print(f"   ⚠️ 提炼结果太短，跳过")
            continue
        
        # 写入本地知识库
        filepath = write_knowledge(agent, source['topic'], source['name'], summary)
        seen_hashes.add(content_hash)
        
        print(f"   ✅ 已写入: {Path(filepath).name}")
        
        # 同步到 IMA
        ima_title = f"🤖 {agent.upper()} - {source['topic']} - {TODAY}"
        sync_to_ima(ima_title, summary)
        
        results.append({
            'source': source['name'],
            'topic': source['topic'],
            'file': Path(filepath).name,
            'length': len(summary)
        })
        
        time.sleep(2)  # 限速
    
    # 保存哈希记录
    save_seen_hashes(agent, seen_hashes)
    
    # 更新总索引
    update_index()
    
    # 发送学习报告
    if results:
        report = f"📚 <b>AI 学习团队报告</b>\n"
        report += f"🤖 Agent: {agent.upper()}\n"
        report += f"📅 日期: {TODAY}\n\n"
        report += f"✅ 完成学习 {len(results)} 个来源:\n"
        for r in results:
            report += f"  • {r['source']}\n"
            report += f"    主题: {r['topic']} | 字数: {r['length']}\n"
        report += f"\n📁 知识已保存到 knowledge/{agent}/ 并同步到 IMA 知识库"
        
        notify_telegram(report)
        
        print(f"\n✅ 学习完成！{len(results)} 个来源已处理")
    else:
        print(f"\n⚠️ 本次没有新内容可学习")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='BroadFSC AI 自主学习团队')
    parser.add_argument('--agent', choices=['finance', 'sales', 'marketing', 'competitor', 'all'],
                        default='all', help='运行指定Agent')
    args = parser.parse_args()
    
    agents_to_run = ['finance', 'sales', 'marketing', 'competitor'] if args.agent == 'all' else [args.agent]
    
    total_results = []
    for agent in agents_to_run:
        results = run_agent(agent)
        if results:
            total_results.extend(results)
        time.sleep(5)  # Agent 之间间隔
    
    print(f"\n{'='*60}")
    print(f"🎉 AI 学习团队全部完成！共学习 {len(total_results)} 条知识")
    print(f"📁 存储路径: broadfsc-automation/knowledge/")
    print(f"🌐 IMA 知识库: 已同步")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
