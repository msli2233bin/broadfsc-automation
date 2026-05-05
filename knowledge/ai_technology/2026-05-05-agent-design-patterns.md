# AI Agent 设计模式 — 2026 核心技术

*学习日期: 2026-05-05 | 来源: AI Agent Design Patterns 2026*

---

## 一、三大核心模式

### 1. ReAct（推理+行动）

**工作流**: Thought → Action → Observation → Repeat

**基准测试结果**:
| 场景 | 基线 | ReAct | ReAct+CoT |
|------|------|-------|-----------|
| HotpotQA (多跳QA) | 29.4% | 34.3% | **47.8%** |
| Fever (事实验证) | 56.3% | **71.1%** | 69.7% |
| ALFWorld (决策) | 45% | **79%** | - |

**适用**: 外部工具集成、多步问题、研究任务、交互式调试
**不适用**: 简单问题、延迟敏感(<500ms)、需长期规划

### 2. Reflection（反思模式）

**三组件系统**:
- **Actor**: 生成解决方案
- **Evaluator**: 评估质量（PASS/FAIL+反馈）
- **Self-Reflection**: 生成语言反思，存入情景记忆

**基准测试**:
| 场景 | 基线 | Reflexion | 改进 |
|------|------|-----------|------|
| HumanEval (Python) | 80% | **91%** | +11% |
| ALFWorld | 24% | **97%** | +73% |

**关键洞察**: 反思存储在情景记忆中，未来尝试可检索 → 从错误中学习

### 3. Planning（规划模式）

**Plan-and-Execute**: 规划与执行分离，92%任务准确率（ReAct 85%）

| 框架 | 核心创新 |
|------|---------|
| BabyAGI | 三Agent任务循环 |
| Tree of Thoughts | 分支探索+回溯，Game of 24: 4%→**74%** |
| ReWOO | 先规划再全部执行，80% token减少 |

### 模式选择决策树
1. 简单直接？→ 直接提示
2. 质量比速度重要？→ 加 Reflection
3. 复杂多步有依赖？→ Planning
4. 需要多种专业技能？→ Multi-Agent
5. 默认 → ReAct

---

## 二、成本与性能对比

| 模式 | 延迟 | Token开销 | 每查询成本 |
|------|------|----------|-----------|
| Direct Prompting | 1-2s | 基线 | $0.01-0.02 |
| ReAct (3步) | 5-10s | +200-300% | $0.06-0.09 |
| Reflection (2轮) | 8-15s | +100-200% | $0.08-0.12 |
| Plan-and-Execute | 10-20s | +300-400% | $0.12-0.18 |

**生产环境策略**: 按复杂度路由——简单任务用便宜模型，复杂任务用强模型

---

## 三、BroadFSC 落地应用

### 当前系统可用改进
1. **Telegram Bot** → 加 Reflection 层：客户对话后自我评估回复质量
2. **邮件系统** → 加 Planning：拆分邮件策略为规划→执行→验证
3. **内容生成** → 加 ReAct：先搜索实时数据→再生成内容→验证数据准确性
4. **销售系统** → 加 Reflection：每次互动后反思，更新情感档案

---

*来源: devops.gheware.com/blog/posts/ai-agent-design-patterns-implementation-guide-2026.html*
