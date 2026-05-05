# MCP 协议 & 生产级AI Agent — 2026 核心技术

*学习日期: 2026-05-05 | 来源: MCP协议实战指南 + Building Production AI Agents 2026*

---

## 一、MCP 协议（Model Context Protocol）

### 核心定位
"AI世界的USB接口" — 无论什么品牌的大模型，插上就能用

### 传统Function Calling vs MCP
| 对比 | Function Calling | MCP |
|------|-----------------|-----|
| 标准化 | 各厂商各一套 | 统一开放标准 |
| 复用性 | 换模型要改代码 | 一次开发到处用 |
| 调试 | 各自为政 | 统一Inspector工具 |

### MCP Server三种能力
| 能力 | 说明 | 示例 |
|------|------|------|
| **Tools** | 可被AI调用的函数 | 查天气、读数据库、发邮件 |
| **Resources** | 可被AI读取的数据源 | 文件内容、配置信息 |
| **Prompts** | 预定义的提示词模板 | — |

### 关键踩坑
1. **版本锁定**: `pip install "mcp[cli]>=1.25,<2"`，v2.0有破坏性变更
2. **环境变量**: Claude Code不继承shell环境，必须`--env`显式传递
3. **工具描述是给AI看的**: 描述越清晰，调用准确率越高
4. **传输模式**: 2026规范已从SSE迁移到Streamable HTTP

---

## 二、生产级Agent架构

### 核心原则
**编排器控制Agent，而非反向控制。模型决定"做什么"，编排器决定"是否允许"。**

### 分层记忆架构
| 层级 | 持久性 | 用途 |
|------|--------|------|
| Working Memory | 会话内 | 当前任务上下文 |
| Episodic Store | 中期 | 最近会话快速检索(Redis) |
| Semantic Store | 长期 | 知识库向量检索(Pinecone/Weaviate) |

### 高风险工具审批
```python
REQUIRES_APPROVAL = {"send_email", "delete_record", "publish_content"}
# Agent调用这些工具时，必须人工审批
```

### 成本控制：模型分级路由
```python
router = ChatAnthropic(model="claude-haiku-4-5")      # 路由：便宜快速
executor = ChatAnthropic(model="claude-sonnet-4-5")    # 执行：中等
deep_thinker = ChatAnthropic(model="claude-opus-4-5")  # 深度思考：贵但强
```
**原则**: 使用能可靠完成任务的**最便宜**模型

### 关键监控指标
| 指标 | 告警阈值 |
|------|---------|
| 工具调用次数/任务 | >15次 |
| 任务完成率 | <80% |
| 每任务成本 | P95>$5 |
| 人工升级率 | >5% |

### 常见失败模式
| 类型 | 严重程度 | 防御 |
|------|---------|------|
| 工具调用循环 | 高 | MAX_TOOL_CALLS限制 |
| 上下文窗口耗尽 | 高 | 记忆修剪+压缩 |
| 虚构工具参数 | 高 | Pydantic Schema验证 |
| 不可逆操作 | 极高 | REQUIRES_APPROVAL清单 |
| 成本爆炸 | 高 | 任务级预算追踪 |

---

## 三、BroadFSC 落地应用

### 1. MCP Server 集成
为BroadFSC Bot创建MCP Server，暴露：
- `search_stock`: 股票查询（Tools）
- `market_data`: 实时行情（Resources）
- `analysis_template`: 分析模板（Prompts）

### 2. 高风险操作审批
邮件发送、社媒发布、客户联系 → 需要人工审批

### 3. 成本优化
当前Groq免费 + yfinance免费 → 已是最优
未来扩展时用模型分级路由控制成本

### 4. 可观测性
给所有自动化任务添加结构化追踪，监控：
- 每日发帖成功率
- 邮件open/click率
- Bot对话满意度

---

*来源: ofox.ai/zh/blog/mcp-protocol-ai-agent-tools-guide-2026/, devstarsj.github.io/2026/02/24/ai-agents-autonomous-systems-tool-use-2026/*
