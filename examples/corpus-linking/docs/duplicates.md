# 阶段 1 找重复报告

## 结论

以 0.90 为阈值，22811 条片段里查出 **586 对**高相似，涉及 **946 条片段**（946 / 22811 ≈ 4.1%）。其中**跨领域 72 对**（72 / 586 ≈ 12.3%），**同领域内 514 对**（514 / 586 ≈ 87.7%）。

514 对同领域里有 132 对发生在同一个文件内，其中 25 对是序号相邻的前后两段——这类多半是切分或模板行同构造成的，不是真重复，下面单列。真正值得处理的是跨领域的 72 对：同一段话写在两个领域仓里，口径已经出现分叉（例：「九宫格内」与「两个九宫格」，「时间维度在前」与「类型维度在前」）。

按行序等距抽 30 对人工看：**22 对是真重复，8 对是误报**（章程套话、字段模板、决策记录元数据头这类同构文本），误报率 8 / 30 ≈ 27%。阈值卡在 0.90 时，同模板文本进得来，这是已知代价。

## 这份结果怎么读

- **余弦相似度**：两个向量方向有多接近，1 表示同向、0 表示无关。例：`asset-001234` 与 `meta-001983` 两句话只差「九宫格内 / 两个九宫格」，算出 0.998995。
- **L2 归一化**：把每条向量长度缩到 1，之后点积就等于余弦，省一次开方。
- **分块**：一次只算 512 行 × 22811 列的相似度块（float32 约 46MB），不一次性开 22811 × 22811（约 2GB，14G 内存的机器扛不住）。
- **top-10 最近邻**：每条片段只看和它最像的 10 条，其余 22800 条不看；余弦 ≥ 0.90 才留。
- **成对去重**：`(a, b)` 与 `(b, a)` 规范成 `id_a < id_b` 只留一次，所以 586 行就是 586 对，无重复计数。
- **跨领域**：`source` 里 `#` 前的领域仓不同，例 `quanttide-asset#…` 对 `quanttide-meta#…`；**同领域内** 则相同；**同一文件内** 是 `#` 前后完全相同；**相邻位置** 是同一文件内片段序号差 1，即切分时的前后两段。

## 数字（分母写清）

| 项 | 数 | 分母 |
| --- | --- | --- |
| 片段总数 | 22811 | 条（`data/fragments.tsv`，md5 `c4577ac68613c58ec319ae6112d224cd`） |
| 余弦 ≥ 0.90 的对 | 586 | 对 |
| 参与片段 | 946 | / 22811 ≈ 4.1% |
| 跨领域 | 72 | / 586 ≈ 12.3%（涉及 33 个领域组合，其中 10 对双方相对路径同名，是整份文档拷进另一个仓） |
| 同领域内 | 514 | / 586 ≈ 87.7% |
| └ 同一文件内 | 132 | / 514 |
| └ 跨文件 | 382 | / 514 |
| └ 其中序号相邻 | 25 | / 132 |
| 分数 0.95 至 1.00 | 171 | / 586 |
| 分数 0.90 至 0.95 | 415 | / 586 |
| 抽检真重复 | 22 | / 30 |
| 抽检误报 | 8 | / 30 |
| 双方都能回原文件定位 | 585 | / 586 |

每行 top-1 余弦的分布（分母 22811 行，即每条片段各自最近邻的分数）：

| p50 | p90 | p99 | max |
| --- | --- | --- | --- |
| 0.7598 | 0.8498 | 0.9577 | 0.9999 |

p50 只有 0.76，说明语料整体不重；高分集中在长尾。

## 跨领域重复（72 对，5 例）

按分数降序取前 5，摘要为片段原文前 90 字。

1. **0.998995** `asset-001234` / `meta-001983`
   - `quanttide-asset#docs/handbook/contract/second_brain.md`：第二大脑由 18 种标准资产（九宫格内）加 Context（工作语境）和 Archive（工作归档）两种不占格资产构成，按陈述型记忆和程序型记忆两大九宫格体系组织。
   - `quanttide-meta#data/profile/quanttide-meta/category/index.md`：第二大脑由 18 种标准资产（两个九宫格）加 Context（工作语境）和 Archive（工作归档）两种不占格资产构成，按陈述型记忆和程序型记忆两大九宫格体系组织。
2. **0.998645** `asset-001185` / `meta-001989`
   - `quanttide-asset#docs/essay/schema/second-brain.md`：陈述型记忆回答组织「知道什么」的问题，按时间维度（过去、现在、未来）与类型维度（事件类、语义类、自我类）交织为九宫格。
   - `quanttide-meta#data/profile/quanttide-meta/category/index.md`：陈述型记忆回答组织「知道什么」的问题，按类型维度（事件类、语义类、自我类）与时间维度（过去、现在、未来）交织为九宫格。
3. **0.996248** `agent-000878` / `code-000788`
   - `quanttide-agent#data/library/vicoa/index.md`：仓库约 28 万行，核心在 `backend/`（Python）：云端 API 与实时服务器、CLI 与本地 daemon、各智能体的无头运行适配器……
   - `quanttide-code#data/library/vicoa/index.md`：仓库约 28 万行，核心在 `backend/`（Python）：包含云端 API 与实时服务器、CLI 与本地 daemon、各智能体的无头运行适配器……
4. **0.995400** `agent-000204` / `work-000331`
   - `quanttide-agent#data/context/profile/skills/insight-writing/references/domain-doc-writing.md`：Specification = 「可接受行为的描述」；Contract = 「交互双方义务与保证的、带责任分配的 specification」……
   - `quanttide-work#data/journal/quanttide-founder/2026-09-10.md`：Specification 是「可接受行为的描述」；Contract 是「交互双方义务与保证的、带责任分配的 specification」……
5. **0.992735** `agent-000737` / `work-000331`
   - `quanttide-agent#data/context/profile/skills/quanttide-repo-workflow/references/knowledge-work-artifacts.md`：Specification = 可接受行为的描述；Contract = 交互双方义务与保证的、带责任分配的 specification……
   - `quanttide-work#data/journal/quanttide-founder/2026-09-10.md`：Specification 是「可接受行为的描述」；Contract 是「交互双方义务与保证的、带责任分配的 specification」……

前两例是同一段定义写在两个仓里且措辞已分叉，第 3 例是整份文档拷进另一个领域的 `data/library/`，第 4、5 例是同一条术语定义散进日志。

## 同领域内重复（514 对，5 例）

按分数降序取前 5。

1. **0.999875** `work-000025` / `work-000612`
   - `quanttide-work#apps/qtcloud-work/src/cli/data/artifacts/report/review-ui-shot-v2.md`：「通过 / 拒绝」的浅灰是禁用态，还是因为该邮件已判「已拒绝」而锁定？已拒邮件为何还预填……
   - `quanttide-work#data/profile/quanttide/quanttide-design/report/review-qtcloud-human-studio.md`：「通过 / 拒绝」的浅灰是禁用态，还是因为该邮件已判「已拒绝」而锁定？已拒邮件为什么还预填……
2. **0.997894** `think-000920` / `think-000932`（同一文件 `quanttide-think#apps/qtcloud-think/tests/fixtures/report/2026-03.md`）
   - 证据不足：作者提到自己在不同领域的技能和经验，但没有**直接**证据表明他完全依赖系统论进行跨领域知识融合……
   - 证据不足：作者提到自己在不同领域的技能和经验，但没有**提供直接**证据表明他完全依赖系统论进行跨领域知识融合……
3. **0.996786** `data-000821` / `data-000841`（同一文件 `quanttide-data#data/archive/platform/docs/qa/report/test_fixtures.md`）
   - 证据位置: `tests/fixtures/evidence/qtcloud_data_test_fixtures.py:1-390`
   - 证据位置: `tests/fixtures/evidence/qtcloud_data_test_fixtures.py`
4. **0.996352** `agent-000204` / `agent-000737`
   - `quanttide-agent#data/context/profile/skills/insight-writing/references/domain-doc-writing.md`：Specification = 「可接受行为的描述」……
   - `quanttide-agent#data/context/profile/skills/quanttide-repo-workflow/references/knowledge-work-artifacts.md`：Specification = 可接受行为的描述……
5. **0.996314** `human-000087` / `human-000096`
   - `quanttide-human#apps/qtrecurit/docs/dev-guide/recommendation-service-brd.md`：推荐信 = 凭证据出具的**质检报告**，不是商品；付费买不到证据……
   - `quanttide-human#apps/qtrecurit/docs/dev-guide/recommendation-service-design.md`：推荐信 = 加工完成后凭证据出具的**质检报告**，不是商品；付费买不到证据……

第 1、4、5 例是同一份内容在仓内两处各存一份（评审清单进了 `apps/` 又进了 `data/profile/`，术语定义进了两个 skill），第 2、3 例是同一文件里同一句出现两遍。

## 同一文件内、相邻位置（25 对，5 例）

序号差 1，即切分时的前后两段。多半是模板行并排，不是真重复。

1. **0.968917** `connect-000191` / `connect-000192` `quanttide-connect#docs/specification/medium/memo.md`
   - 下游影响：触发备忘列表更新、通知相关用户等操作
   - 下游影响：触发备忘详情更新、备忘列表刷新等操作
2. **0.968202** `connect-000163` / `connect-000164` `quanttide-connect#docs/specification/content/consensus.md`
   - 下游影响：触发共识图边添加、共识关系列表更新等操作
   - 下游影响：触发共识图边移除、共识关系列表更新等操作
3. **0.955741** `connect-000166` / `connect-000167` `quanttide-connect#docs/specification/content/consensus.md`
   - 下游影响：触发共识图详情更新、相关边清理等操作
   - 下游影响：触发共识图详情更新、路径查询结果更新等操作
4. **0.952237** `connect-000203` / `connect-000204` `quanttide-connect#docs/specification/medium/message.md`
   - 下游影响：触发消息列表刷新、状态同步等操作
   - 下游影响：触发消息列表更新、相关关联清理等操作
5. **0.950325** `human-000574` / `human-000575` `quanttide-human#data/roadmap/qtcloud-human/recruitment/prd.md`
   - 场景：纠正误淘汰——AI 将简历标记为「淘汰」，招聘方改为「通过」并注明原因……
   - 场景：纠正误通过——AI 将简历标记为「通过」，招聘方改为「淘汰」并注明原因……

前 4 例是规格文档里每条操作都带一行「下游影响」，模板相同、动词不同；第 5 例是 PRD 里两个对照场景。这类按切分规则成对出现，处理重复时应先排除。

## 30 对抽检

抽样方式：`data/duplicates.tsv` 按 `(id_a, id_b)` 升序的行序，等距取 30 行（步长 19，共 586 行），可复现。

真重复 22 / 30，误报 8 / 30。误报逐条：

| 行号 | 对 | 为什么不算重复 |
| --- | --- | --- |
| 06 | `connect-000161` / `connect-000165` | 同文件「下游影响」模板行，操作不同 |
| 07 | `connect-000166` / `connect-000167` | 同上 |
| 10 | `course-000599` / `course-000639` | 课程与课时是两个实体，`id` 字段说明同构 |
| 15 | `docs-000057` / `docs-000076` | 同一小说文件里一句话在对话与叙述中各出现一次 |
| 16 | `execute-000463` / `project-000067` | 章程「解释权」套话，条款号不同 |
| 24 | `pay-000396` / `pay-000410` | 决策记录元数据头（日期、类型、状态）同构，对象不同 |
| 26 | `product-000820` / `product-000821` | 同文件两段需求条目，内容不同 |
| 29 | `think-003204` / `think-003225` | 章程「适用范围」套话，结尾词不同（图式 / 情境） |

## 复跑命令

```bash
cd examples/corpus-linking

# 语料或 scripts/ 变过才需要重写指纹；没变就直接核
/usr/bin/python3 scripts/manifest.py --write
/usr/bin/python3 scripts/manifest.py --check

# 阶段 1（先自动过 manifest --check 门禁，约 5.5 分钟）
/usr/bin/python3 scripts/find_duplicates.py
```

算法写死在 `scripts/find_duplicates.py` 头部注释（L2 归一化 → 512 行分块点积 → 每行 top-10 且 ≥ 0.90 → 规范成 `id_a < id_b` 去重），跑完不改；要改另起一轮并说明。

## 已知缺口

- `source` 是快照时的路径，语料在被别的会话改动：1 对（`data-001318` / `data-001338`）里 `quanttide-data#docs/gallery/quanttide-search/index.md` 在磁盘上已不存在，无法回原文定位。
- 每行只取 top-10，若某片段的真重复排在第 11 位以后会漏；本轮不调，调要另起一轮说明。
- 只报分数与出处，没做重复内容的归并建议；归并属阶段 1 之后的事。
