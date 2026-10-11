# 2026-10-11 hermes-session-analyzer 研究记录

研究对象：本机 `apps/hermes-session-analyzer`（下称 hsa）——把本机多个 agent 的会话采集、清洗、归因，量化「搜索为何低效」的流水线工具。研究动机：路线图「采第一批真实 AI 查询」——hsa 手里已有 29550 条真实搜索事件，是现成的第一批数据。

实测日期 2026-10-11（报告生成于 2026-10-09，`data/report/`）。样例数据在 [`../data/search-queries-sample.jsonl`](../data/search-queries-sample.jsonl)。

## 它是什么

```
hsa load   → data/raw/<origin>/      6 个来源：hermes、hermes-backup、pi、opencode、zed、dsh
hsa clean  → data/cleaned/*.parquet  归一化 + 标注搜索事件（28 个字段，含 query、结果、后续动作）
hsa analyze → data/report/           搜索效率报告（Markdown + JSON）
```

「算不算搜索」的口径在 `paths.py`：专用搜索工具名单（grep、search_files、memory_search、session_search、glob、find_path、list_directory……）+ shell 命令里匹配 `grep|rg|find|ls|tree` 等动词。

## 数据规模

| 指标 | 数值 |
| --- | --- |
| 会话 / 消息 / 工具调用 | 628 / 200,094 / 104,438 |
| 搜索事件 | 29,550（含搜索的会话 550 个） |
| 按来源 | pi 9014、zed 7944、hermes 4460、hermes-backup 4164、dsh 3693、opencode 275 |
| 每会话搜索次数 | 中位 19，p90 98，最大 1664 |

## 关键发现（对应路线图三个未知）

**1. AI 怎么查——89.1% 的「搜索」是 shell 命令，不是搜索框。** terminal + bash 合计 26,333 条；专用搜索工具只有 3,217 条（10.9%）。两类查询形态完全不同：

- shell 类是**整条命令**，中位 230 字符、p90 566，常常一条里串起 ls + find + grep + cat，一次要答案：
  `grep -rn "工作台\|Workbench\|workbench" --include=*.md . 2>/dev/null`
- 专用搜索类是**短查询**，中位 34 字符、p90 54、最长 107，含中文的只占 12.3%。三种子形态：
  - 正则/词面（找代码符号）：`def record_audio|arecord|sox|pyaudio|sd\.rec|sounddevice`
  - 路径导航（摸目录结构）：`quanttide-course/data/profile/production-internship/lesson2-release`
  - 概念关键词（搜记忆/会话）：`fiction work profile 认知地图 index 创作动机 创作方法 创作困境 知识图谱`

白话：AI 不是「问一句等答案」，是先用 shell 摸清结构，再用概念词补搜。搜索嵌在动作流里，不是独立动作——搜索后的首个动作 64% 仍是 terminal/bash，读文件只占 7.8%。

**2. 行为模式：连环搜是常态。** 连续搜索（thrashing）占 43.9%，会话内重复查询 12.6%，搜完没行动又搜 3.4%。一个会话中位搜 19 次——AI 用「多次小搜」代替「一次大搜」。

**3. 结果面貌。** 结果字符中位 222、p90 1812；hermes 侧空结果率 36.1%（注意分母是可判定的 144 次，不是全部），错误率 0.6%。

## 对路线图的意义

- **未知 1（AI 怎么查）有了第一批真实分布**：查询短、批量、正则 + 概念词混用、连环搜。我们原型「多词 OR + BM25 取前 10」的返回形态，对得上「短查询」，对不上「一条命令要全部答案」。
- **未知 2（词面够不够）仍未回答**：hsa 量的是 AI 在文件系统、记忆、会话上的搜索行为，不是在知识库上的命中率——概念词查询（如「创作困境 知识图谱」）在词面索引上会不会漏，要拿这批查询对着我们的索引跑才知道。
- **下一步不变，但题目现成了**：拿样例里的概念词查询与正则查询，对本仓 tantivy 原型实测命中与弯路。

## 口径限制

- hermes 与 hermes-backup 是同一批会话的两份快照，session_id 重叠，来源小计双计（总数未去重）。
- zed 来源拿不到工具结果，结果字符恒为 0。
- 空结果率分母是「可判定」子集；报告的 latency 合计为负值，延迟指标不可信。
- 本机单人样本，非产品流量。

## 数据落点与脱敏

`data/search-queries-sample.jsonl`：96 条查询样例（按工具配额抽样，seed=42），每行 `{origin, tool, query}`。脱敏规则：

- `/home/iguo` → `~`，人名 → `[name]`，邮箱 → `[email]`，URL → `[url]`，裸域名 → `[domain]`，密钥形字符串 → `[key]`，设备 ID → `[device]`
- 整条剔除：招聘/薪酬类、他人仓库、含密钥或邮箱的查询

原始 964MB 会话数据不入仓，只留在本机 hsa 仓的 `data/`（其仓自行 gitignore）。
