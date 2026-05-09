"""
BroadFSC 从学习成果生成内容
读取AI自主学习Agent的知识库，生成社交媒体内容

用法:
  python content_from_learning.py --platform linkedin
  python content_from_learning.py --platform twitter
  python content_from_learning.py --platform all
"""

import os
import sys
import json
import argparse
import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# =================== 配置 ===================
KNOWLEDGE_DIR = Path(__file__).parent / 'knowledge'
TODAY = datetime.datetime.now().strftime('%Y-%m-%d')
WEEK = datetime.datetime.now().strftime('%Y-W%W')

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# =================== 读取学习内容 ===================
def read_latest_learning(agent_type):
    """读取最新的学习成果"""
    if agent_type == 'finance':
        pattern = '*.md'
        search_dir = KNOWLEDGE_DIR / 'finance'
    elif agent_type == 'sales':
        pattern = '*.md'
        search_dir = KNOWLEDGE_DIR / 'sales'
    elif agent_type == 'marketing':
        pattern = '*.md'
        search_dir = KNOWLEDGE_DIR / 'marketing'
    elif agent_type == 'competitor':
        pattern = '*.md'
        search_dir = KNOWLEDGE_DIR / 'competitor'
    else:
        return []
    
    if not search_dir.exists():
        return []
    
    files = sorted(search_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return []
    
    # 读取最新的3个文件
    items = []
    for f in files[:3]:
        try:
            content = f.read_text(encoding='utf-8')
            items.append({
                'file': f.name,
                'topic': f.stem,
                'content': content[:2000]
            })
        except Exception as e:
            print(f"    ⚠️ 读取 {f.name} 失败: {e}")
    
    return items

def generate_linkedin_content(learning_items):
    """从学习内容生成LinkedIn帖子"""
    if not learning_items:
        return None
    
    content = f"""🚀 Weekly Financial Market Insights ({TODAY})

"""
    
    for i, item in enumerate(learning_items[:3], 1):
        topic = item['topic'].replace('_', ' ').title()
        content_preview = item['content'][:200].replace('#', '').strip()
        
        content += f"{i}. **{topic}**\n"
        if content_preview:
            content += f"   • {content_preview[:150]}...\n"
        content += "\n"
    
    content += """---

📊 Powered by BroadFSC AI Learning Agent
🔗 Analyzing global financial markets 24/7

#FinancialAnalysis #MarketInsights #AI #BroadFSC"""
    
    return content

def generate_twitter_content(learning_items):
    """从学习内容生成Twitter帖子"""
    if not learning_items:
        return None
    
    item = learning_items[0]
    topic = item['topic'].replace('_', ' ').title()
    content_preview = item['content'][:100].replace('#', '').strip()
    
    content = f"""📈 {topic}

{content_preview[:100]}...

🔗 Full analysis: BroadFSC Knowledge Base
🤖 by AI Learning Agent

#Finance #Trading #{topic.split()[0] if ' ' in topic else topic}"""
    
    return content

def generate_instagram_content(learning_items):
    """从学习内容生成Instagram帖子"""
    if not learning_items:
        return None
    
    content = f"""📊 Market Insights of the Week ({TODAY})

Swipe to learn ➡️

🔹 Financial Analysis Updates
🔹 Market Trends Decoded  
🔹 Actionable Insights

---

Powered by BroadFSC AI 🤖
Analyzing global markets 24/7 🌍

#FinancialLiteracy #MarketAnalysis #Investing #BroadFSC #AI #Trading #Stocks"""
    
    return content

# =================== 主程序 ===================
def main():
    parser = argparse.ArgumentParser(description='从学习成果生成社交媒体内容')
    parser.add_argument('--platform', type=str, default='all',
                        choices=['linkedin', 'twitter', 'instagram', 'all'],
                        help='目标平台')
    
    args = parser.parse_args()
    
    print(f"📖 读取学习内容...")
    
    # 读取所有agent的学习成果
    all_learning = {
        'finance': read_latest_learning('finance'),
        'sales': read_latest_learning('sales'),
        'marketing': read_latest_learning('marketing'),
        'competitor': read_latest_learning('competitor'),
    }
    
    # 合并所有学习内容
    combined_items = []
    for agent_type, items in all_learning.items():
        for item in items:
            item['agent'] = agent_type
            combined_items.append(item)
    
    if not combined_items:
        print("⚠️ 没有找到学习内容，请先运行学习agent")
        print("   示例: python ai_learning_agent.py --agent all")
        return
    
    print(f"✅ 读取到 {len(combined_items)} 条学习内容")
    
    # 生成各平台内容
    platforms = ['linkedin', 'twitter', 'instagram'] if args.platform == 'all' else [args.platform]
    
    output_dir = Path(__file__).parent / 'content_output'
    output_dir.mkdir(exist_ok=True)
    
    for platform in platforms:
        print(f"\n📝 生成 {platform.upper()} 内容...")
        
        if platform == 'linkedin':
            content = generate_linkedin_content(combined_items)
        elif platform == 'twitter':
            content = generate_twitter_content(combined_items)
        elif platform == 'instagram':
            content = generate_instagram_content(combined_items)
        
        if content:
            # 保存内容
            output_file = output_dir / f'{platform}_{TODAY}.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已保存到: {output_file}")
            print(f"\n--- {platform.upper()} 内容预览 ---")
            print(content[:300] + "...")
            print("--- 结束 ---\n")
        else:
            print(f"⚠️ 生成 {platform} 内容失败")
    
    print(f"\n🎉 内容生成完成！输出目录: {output_dir}")

if __name__ == '__main__':
    main()
