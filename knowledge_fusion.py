"""
BroadFSC 知识融合模块 — 运行时跨域知识注入
让每个脚本都能从所有域（Finance/Sales/Marketing/Competitor）拉相关知识
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# --- 路径 ---
KNOWLEDGE_DIR = Path(__file__).parent / 'knowledge'
FUSION_INDEX_PATH = KNOWLEDGE_DIR / 'FUSION_INDEX.md'

# --- 跨域关键词映射 ---
# 当检测到这些关键词时，自动加载对应域的知识
DOMAIN_KEYWORDS = {
    'finance': [
        'stock', 'ticker', 'price', 'rsi', 'macd', 'bollinger', 'ma', 'support',
        'resistance', 'breakout', 'trend', 'volume', 'earnings', 'revenue', 'pe',
        'eps', 'dividend', 'market', 'index', 's&p', 'nasdaq', 'dow', 'gold',
        'btc', 'bitcoin', 'crypto', 'oil', 'forex', 'nvda', 'aapl', 'tsla',
        'msft', 'googl', 'meta', 'amzn', 'technical', 'fundamental', 'overbought',
        'oversold', 'pullback', 'correction', 'bull', 'bear', 'invest', 'trade',
        '股票', '投资', '交易', '行情', '走势', '技术面', '基本面', '财报',
    ],
    'sales': [
        'buy', 'sell', 'subscribe', 'paid', 'free', 'consult', 'advisor',
        'service', 'account', 'portfolio', 'risk', 'return', 'profit',
        'loss', 'strategy', 'recommend', 'advice', 'help', 'need', 'want',
        'cost', 'fee', 'charge', 'price', 'worth', 'value',
        '购买', '订阅', '咨询', '服务', '开户', '账户', '收费', '费用',
    ],
    'marketing': [
        'content', 'post', 'social', 'tiktok', 'twitter', 'telegram',
        'discord', 'youtube', 'instagram', 'viral', 'engage', 'follow',
        'subscribe', 'channel', 'community', 'platform',
    ],
    'competitor': [
        'etoro', 'webull', 'ibkr', 'robinhood', 'fidelity', 'schwab',
        'compare', 'alternative', 'difference', 'better', 'vs', 'versus',
        'why choose', 'what makes',
    ],
}

# --- 知识缓存（脚本级，启动时加载一次）---
_knowledge_cache: Dict[str, Dict[str, str]] = {}
_fusion_loaded = False


def _load_file_content(filepath: Path, max_chars: int = 1000) -> str:
    """加载文件内容，截取关键部分"""
    try:
        content = filepath.read_text(encoding='utf-8')
        if len(content) <= max_chars:
            return content
        # 智能截取：优先取开头摘要 + 中间关键段落
        half = max_chars // 2
        return content[:half] + f"\n\n...(截取 {len(content) - max_chars} 字符)...\n\n" + content[-half:]
    except Exception:
        return ""


def _detect_domains(text: str) -> List[str]:
    """根据文本自动检测需要加载的知识域"""
    text_lower = text.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[domain] = score
    # 按得分排序，取前3个域
    return [d for d, _ in sorted(scores.items(), key=lambda x: -x[1])[:3]]


def load_knowledge_base(force_reload: bool = False) -> Dict[str, Dict[str, str]]:
    """加载整个知识库到内存缓存。
    
    Returns:
        {domain: {filename: content}}
    """
    global _knowledge_cache, _fusion_loaded
    
    if _knowledge_cache and not force_reload:
        return _knowledge_cache
    
    _knowledge_cache = {}
    domain_dirs = ['finance', 'sales', 'marketing', 'competitor']
    
    for domain in domain_dirs:
        domain_path = KNOWLEDGE_DIR / domain
        if not domain_path.exists():
            continue
        
        domain_knowledge = {}
        for f in sorted(domain_path.iterdir()):
            if not f.suffix == '.md' or f.name in ('.seen_hashes.json',):
                continue
            content = _load_file_content(f, max_chars=2000)
            if content:
                # 提取文件头的主题信息
                first_lines = content[:500]
                topic_match = re.search(r'\*\*主题\*\*[：:]\s*(\S+)', first_lines)
                domain_knowledge[f.stem] = content
        
        if domain_knowledge:
            _knowledge_cache[domain] = domain_knowledge
    
    _fusion_loaded = True
    logger.info(f"知识库加载完成: {sum(len(v) for v in _knowledge_cache.values())} 文件, {len(_knowledge_cache)} 域")
    return _knowledge_cache


def get_cross_domain_context(
    query: str,
    auto_detect: bool = True,
    domains: Optional[List[str]] = None,
    max_total_chars: int = 1500,
) -> str:
    """核心函数：根据查询/上下文返回跨域知识。
    
    Args:
        query: 用户消息或任务上下文
        auto_detect: 是否自动检测需要的域
        domains: 手动指定域列表（忽略自动检测）
        max_total_chars: 返回总字符上限
    
    Returns:
        格式化的跨域知识字符串，可直接注入 prompt
    """
    global _knowledge_cache
    
    if not _knowledge_cache:
        load_knowledge_base()
    
    if auto_detect and domains is None:
        domains = _detect_domains(query)
    
    if not domains:
        return ""
    
    # 确定每个域的配额
    chars_per_domain = max_total_chars // max(len(domains), 1)
    
    snippets = []
    for domain in domains:
        if domain not in _knowledge_cache:
            continue
        
        domain_files = _knowledge_cache[domain]
        if not domain_files:
            continue
        
        # 按相关性排序：文件名匹配 query 关键词的排在前面
        query_lower = query.lower()
        scored_files = []
        for fname, content in domain_files.items():
            score = sum(1 for word in query_lower.split() if word.lower() in fname.lower())
            scored_files.append((score, fname, content))
        scored_files.sort(key=lambda x: -x[0])
        
        # 取最相关的1-2个文件
        domain_text = ""
        for _, fname, content in scored_files[:2]:
            excerpt = content[:chars_per_domain // 2]
            if excerpt:
                domain_text += f"\n### {domain}/{fname}\n{excerpt}\n"
        
        if domain_text:
            domain_map = {
                'finance': '📈 金融分析',
                'sales': '💼 销售方法',
                'marketing': '📱 营销策略',
                'competitor': '🔍 竞品分析',
            }
            header = domain_map.get(domain, domain.upper())
            snippets.append(f"\n--- {header} ---{domain_text}")
    
    if snippets:
        return "\n".join(snippets)[:max_total_chars]
    return ""


def get_sales_with_finance_context(user_message: str) -> str:
    """特化：销售场景中注入金融知识。
    当用户问投资相关问题时，同时提供销售话术 + 金融背景。
    """
    return get_cross_domain_context(
        query=user_message,
        domains=['sales', 'finance'],
        max_total_chars=1200
    )


def get_content_with_finance_angle(topic: str) -> str:
    """特化：内容生成时注入金融知识 + 营销策略。
    当生成社交媒体内容时使用。
    """
    return get_cross_domain_context(
        query=topic,
        domains=['finance', 'marketing'],
        max_total_chars=1000
    )


def get_competitor_differentiation(user_concern: str = "") -> str:
    """特化：获取竞品差异点，用于异议处理和销售。
    """
    context = get_cross_domain_context(
        query=user_concern,
        domains=['competitor', 'sales'],
        max_total_chars=800
    )
    return context


def get_realtime_market_brief(tickers: Optional[List[str]] = None) -> str:
    """获取最新的市场参考数据（从market_reference文件）。
    用于盘前简报等场景。
    """
    ref_file = KNOWLEDGE_DIR / 'finance' / 'market_reference_2026_04.md'
    if ref_file.exists():
        return _load_file_content(ref_file, max_chars=1500)
    return ""


def get_technical_analysis_for_ticker(ticker: str) -> str:
    """获取特定品种的技术分析（从实战手册）。
    """
    practice_file = KNOWLEDGE_DIR / 'finance' / '2026-05-06-global_technical_analysis_practice.md'
    if not practice_file.exists():
        return ""
    
    content = practice_file.read_text(encoding='utf-8')
    ticker_upper = ticker.upper()
    
    # 提取该ticker相关的分析段落
    parts = []
    in_case = False
    for line in content.split('\n'):
        if f'案例' in line or f'### ' in line:
            in_case = ticker_upper in line.upper()
        if in_case:
            parts.append(line)
            if len(parts) > 80:  # 最多80行
                break
    
    if parts:
        return '\n'.join(parts[:80])
    
    # fallback: 搜索ticker出现的附近段落
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if ticker_upper in line.upper():
            start = max(0, i - 3)
            end = min(len(lines), i + 15)
            return '\n'.join(lines[start:end])
    
    return ""


# --- 便捷函数：用于脚本 prompt 注入 ---

def get_bot_prompt_injection(user_message: str, user_id: str = "") -> str:
    """为 Telegram Bot 生成 prompt 注入片段。
    自动检测需要的域，返回可直接追加到 system prompt 的文本。
    """
    domains = _detect_domains(user_message)
    # 金融问题总是需要 sales（因为最终目标是转化）
    if 'finance' in domains and 'sales' not in domains:
        domains.append('sales')
    # 销售问题总是需要 finance（因为有知识才有说服力）
    if 'sales' in domains and 'finance' not in domains:
        domains.insert(0, 'finance')
    
    context = get_cross_domain_context(
        query=user_message,
        domains=domains,
        max_total_chars=1200
    )
    
    if context:
        return f"\n\n--- 来自 BroadFSC 知识库的跨域知识（自然地融入回复，不要逐条列出来）---\n{context}\n--- 知识库结束 ---\n"
    return ""


def get_sales_prompt_injection(customer_stage: str = "awareness") -> str:
    """为销售引擎生成 prompt 注入片段。
    根据客户阶段加载对应的销售+金融+竞品知识。
    """
    stage_keywords = {
        'awareness': '首次接触 教育 价值主张',
        'interest': '技术分析 风险 信任',
        'evaluation': '比较 竞品 差异化 深度分析',
        'decision': 'ROI 定价 服务 承诺',
    }
    query = stage_keywords.get(customer_stage, '销售 客户 沟通')
    
    return get_cross_domain_context(
        query=query,
        domains=['sales', 'finance', 'competitor'],
        max_total_chars=1500
    )


def get_content_prompt_injection(topic: str, platform: str = "") -> str:
    """为内容生成引擎生成 prompt 注入片段。
    """
    domains = ['finance', 'marketing']
    if 'compare' in topic.lower() or 'vs' in topic.lower():
        domains.append('competitor')
    
    context = get_cross_domain_context(
        query=topic,
        domains=domains,
        max_total_chars=1000
    )
    
    # 如果有具体ticker，追加技术分析
    ticker_match = re.search(r'\$?([A-Z]{2,5})', topic)
    if ticker_match:
        ticker = ticker_match.group(1)
        ta = get_technical_analysis_for_ticker(ticker)
        if ta:
            context += f"\n\n--- 品种技术分析 ---\n{ta[:500]}"
    
    return context


# --- 初始化 ---
load_knowledge_base()
