# 阶段 2 找关联报告

## 结论

200 个簇里 **199 个是跨域主题簇**（199 / 200 = 99.5%），唯一一个单域簇是 `c189`（29 名成员全部来自 `quanttide-write`，讲 SDR 叙事）。全部 22811 条片段都落了簇（22811 / 22811 = 100%），跨域簇覆盖 22782 / 22811 = 99.9%。

三件事值得记住：

1. **门槛宽，但不是靠一两条异域成员凑数**。「≥2 个领域」按有没有算，不按多少算——可第二大领域占簇内成员的比例中位数是 **56%**，**177 / 199** 个跨域簇的第二大领域占比 ≥ 10%，只有 22 个簇的第二大领域占比不足 10%（主要是单域大簇 + 一两条外来成员）。
2. **有用的是低领域数簇，高领域数簇多半在聚「怎么写」**。等距抽 6 个跨域簇逐条读（判读是 agent 给的，见下文，供你推翻）：`c000`（元认知）、`c078`（产教融合与获客）主题集中，**2 / 6**；`c039`、`c117`、`c156`、`c196` 是文体簇——清单条目、字段说明、短句混在一起，成员讲的不是同一件事，**4 / 6**。另看 4 个领域数取下限 2 的簇（个税汇算、中华文明、法人记忆、小说文本），**4 / 4** 主题集中。领域数 ≥ 20 的 34 个簇里，路径是 `AGENTS.md` / `index.md` / 仓库顶层文件的成员占 958 / 4992 = 19%，领域数 ≤ 4 的簇只有 71 / 926 = 8%——高领域数簇确实更偏各仓同构文本。
3. **与阶段 1 互证**：阶段 1 那 72 对跨域重复里 **66 对（66 / 72 = 92%）落进同一簇**。重复是关联的极端情形，机器两边算对得上；但两边用的是同一套向量（同源），这只证明链路自洽，不证明聚类质量。

收敛：簇内平均余弦第 1 轮 0.7575 → 第 10 轮 0.7712 → 第 30 轮 0.7719，10 轮之后基本不动。

**一句实话：`k = 200` 是写死的先验、不是调出来的；换 k 簇会变，所以上面的结论只当线索、不当定论。**

## 这份结果怎么读

- **球形 k-means**：先把每条向量长度缩到 1（L2 归一化）再聚类。归一化后余弦的大小顺序与欧氏距离一致，所以「按点积最大分配 → 簇内求平均当新质心 → 归一化」就是在单位球面上做 k-means，分数直接就是余弦，不用换算。
- **质心**：一个簇的中心方向，簇内向量加起来取平均再归一化。它不对应任何一条真实原文，只是方向的平均。
- **代表片段**：簇里与质心余弦最大的那一条，即「最能代表这个方向的原文」。**不给主题名**——机器编的名字是假的，本报告一律写「代表片段」。
- **跨域主题簇**：成员的 `source` 中 `#` 前的领域仓名 ≥ 2 个的簇。领域仓名共 38 个。
- **簇内平均余弦**：每轮更新质心、重新分配后，全体成员与自己所属质心的余弦取平均；值越高簇抱得越紧。
- **`cluster_id`**：`c000` 至 `c199`，编号来自初始化时随机抽中的质心下标，只作标识、没有大小含义。

## 数字（分母写清）

| 项 | 数 | 分母 |
| --- | --- | --- |
| 片段总数 | 22811 | 条（`data/fragments.tsv`，md5 `c4577ac68613c58ec319ae6112d224cd`） |
| 簇总数 | 200 | 个（`k` 写死） |
| 空簇 | 0 | / 200 |
| 落簇片段 | 22811 | / 22811 = 100% |
| 跨域主题簇 | **199** | / 200 = 99.5% |
| 单域簇 | 1 | / 200（`c189`，`quanttide-write`，29 成员） |
| 跨域簇覆盖片段 | 22782 | / 22811 = 99.9% |
| 簇成员数 min / p50 / p90 / max | 12 / 113 / 174 / 246 | 200 个簇（p90 为线性插值） |
| 跨域簇的领域数范围 | 2 至 32 | / 38 个领域仓 |
| 第二大领域成员占比中位数 | 56% | 199 个跨域簇 |
| 第二大领域占比 ≥ 10% 的跨域簇 | 177 | / 199 |
| 领域数 ≤ 4 的簇 | 16 | / 200（其中跨域 15） |
| 领域数 ≥ 20 的簇 | 34 | / 200 |
| 簇内平均余弦 第 1 / 10 / 30 轮 | 0.7575 / 0.7712 / 0.7719 | 30 轮 |
| 跨域重复对落进同一簇 | 66 | / 72（阶段 1 的跨域重复，同源） |
| 抽检：主题集中的簇 | 6 | / 10（等距抽 6 + 领域数为 2 的 4） |
| 抽检：文体簇 | 4 | / 10 |

跨域簇按领域数分布（分母 199 个跨域簇）：

| 领域数 | 2–4 | 5–7 | 8–10 | 11–13 | 14–16 | 17–19 | 20–22 | 23–24 | 26 | 32 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 簇数 | 15 | 21 | 24 | 26 | 45 | 34 | 24 | 7 | 2 | 1 |

跨域簇按（领域数 × 成员数）分桶（分母 199 个跨域簇）：成员 50 以上的 181 个、20 至 49 的 15 个、10 至 19 的 3 个；2 至 4 领域的 15 个簇里，成员 ≥ 50 的有 7 个。完整 2 维表在 `data/cluster_summary.json` 的 `cross_domain_distribution.by_domain_count_and_size`。

## 跨域簇前 10（按领域数降序，同数按成员数降序）

1. **c093** —— 32 个领域 / 224 成员，代表片段 `org-000159`
   - 领域：quanttide-agent, quanttide-algorithm, quanttide-asset, quanttide-auth, quanttide-code, quanttide-connect, quanttide-course, quanttide-credit, quanttide-crowd, quanttide-data, quanttide-delib, quanttide-design, quanttide-devops, quanttide-execute, quanttide-finance, quanttide-growth, quanttide-human, quanttide-innov, quanttide-learn, quanttide-media, quanttide-meta, quanttide-org, quanttide-pay, quanttide-product, quanttide-project, quanttide-research, quanttide-secret, quanttide-strategy, quanttide-support, quanttide-think, quanttide-work, quanttide-write
   - 代表片段（`quanttide-org#data/profile/AGENTS.md`）：量潮组织管理档案，记录组织与人物的档案。参考 quanttide-product/data/profile 的建设思路。
2. **c069** —— 26 个领域 / 161 成员，代表片段 `data-000715`
   - 领域：quanttide-agent, quanttide-algorithm, quanttide-asset, quanttide-auth, quanttide-code, quanttide-connect, quanttide-course, quanttide-crowd, quanttide-data, quanttide-delib, quanttide-devops, quanttide-finance, quanttide-growth, quanttide-human, quanttide-learn, quanttide-meta, quanttide-org, quanttide-pay, quanttide-product, quanttide-project, quanttide-secret, quanttide-strategy, quanttide-support, quanttide-think, quanttide-work, quanttide-write
   - 代表片段（`quanttide-data#data/archive/platform/docs/guides/roles/data-analyst.md`）：- 数据分析和挖掘 - 数据可视化和报告 - 决策支持 - 数据需求和沟通
3. **c037** —— 26 个领域 / 150 成员，代表片段 `devops-000002`
   - 领域：quanttide-agent, quanttide-asset, quanttide-auth, quanttide-code, quanttide-connect, quanttide-course, quanttide-crowd, quanttide-data, quanttide-delib, quanttide-design, quanttide-devops, quanttide-execute, quanttide-finance, quanttide-growth, quanttide-human, quanttide-learn, quanttide-meta, quanttide-org, quanttide-product, quanttide-search, quanttide-secret, quanttide-strategy, quanttide-support, quanttide-think, quanttide-work, quanttide-write
   - 代表片段（`quanttide-devops#AGENTS.md`）：**核心划分原则：** - handbook 按**流程**导航，回答"这个环节用什么" - tutorial 按**主题**教学，回答"某个知识点怎么用" - gallery 按**项目**陈列，回答"做成了什么、效果如何" - data/ 下的内容是结构化记录，不是文章 - report/ 结构…
4. **c088** —— 24 个领域 / 229 成员，代表片段 `product-000795`
   - 领域：quanttide-agent, quanttide-asset, quanttide-auth, quanttide-course, quanttide-crowd, quanttide-data, quanttide-design, quanttide-execute, quanttide-finance, quanttide-human, quanttide-innov, quanttide-learn, quanttide-media, quanttide-meta, quanttide-org, quanttide-pay, quanttide-product, quanttide-research, quanttide-secret, quanttide-strategy, quanttide-support, quanttide-think, quanttide-work, quanttide-write
   - 代表片段（`quanttide-product#data/profile/index.md`）：量潮是一个以数据驱动的产品体系，专注于提供高质量的数据处理、课程研发、人才招聘等服务。我们的核心理念是：**让每个产品都有章法，让每项服务都可预期**。
5. **c162** —— 24 个领域 / 151 成员，代表片段 `design-000007`
   - 领域：quanttide-agent, quanttide-algorithm, quanttide-asset, quanttide-code, quanttide-connect, quanttide-course, quanttide-data, quanttide-design, quanttide-devops, quanttide-execute, quanttide-finance, quanttide-growth, quanttide-human, quanttide-learn, quanttide-meta, quanttide-org, quanttide-pay, quanttide-product, quanttide-search, quanttide-secret, quanttide-support, quanttide-think, quanttide-work, quanttide-write
   - 代表片段（`quanttide-design#data/profile/qtcloud-product-studio/index.md`）：- 想组织就拖，想看详情就点，想扩展就加——**不用学，直觉会** - 每个操作都有即时反馈（拖拽有轨迹、点击有响应、保存有确认） - 文案只说一次：不重复的品牌标题，不出现"验收验收"式歧义
6. **c059** —— 24 个领域 / 150 成员，代表片段 `human-000036`
   - 领域：quanttide-agent, quanttide-asset, quanttide-code, quanttide-connect, quanttide-course, quanttide-crowd, quanttide-data, quanttide-devops, quanttide-execute, quanttide-finance, quanttide-growth, quanttide-human, quanttide-learn, quanttide-meta, quanttide-org, quanttide-pay, quanttide-product, quanttide-project, quanttide-sales, quanttide-strategy, quanttide-support, quanttide-think, quanttide-work, quanttide-write
   - 代表片段（`quanttide-human#apps/qtcloud-human/src/studio/doc/screens/plan.md`）：- **计划涵盖各模块**：招聘计划、培训计划、绩效计划、薪酬计划……一类计划一条线 - **计划驱动执行**：计划定义周期与目标，模块页面承载执行记录，进度回填到计划 - 状态清晰：草稿 / 进行中 / 已完成，进度可追踪
7. **c105** —— 24 个领域 / 139 成员，代表片段 `product-000144`
   - 领域：quanttide-agent, quanttide-algorithm, quanttide-asset, quanttide-auth, quanttide-code, quanttide-connect, quanttide-course, quanttide-crowd, quanttide-data, quanttide-devops, quanttide-execute, quanttide-finance, quanttide-human, quanttide-learn, quanttide-meta, quanttide-org, quanttide-pay, quanttide-product, quanttide-project, quanttide-search, quanttide-support, quanttide-think, quanttide-work, quanttide-write
   - 代表片段（`quanttide-product#data/journal/default/2026-07-14.md`）：然后呢，就是说有很多设计资料其实都可以降级到客户端层面，也就是说，在这个仓库单仓层面的，这个文档更多的是要聚焦于它的实际使用
8. **c183** —— 23 个领域 / 172 成员，代表片段 `crowd-000113`
   - 领域：quanttide-agent, quanttide-algorithm, quanttide-asset, quanttide-connect, quanttide-course, quanttide-crowd, quanttide-data, quanttide-devops, quanttide-execute, quanttide-finance, quanttide-growth, quanttide-human, quanttide-innov, quanttide-learn, quanttide-meta, quanttide-org, quanttide-product, quanttide-sales, quanttide-search, quanttide-support, quanttide-think, quanttide-work, quanttide-write
   - 代表片段（`quanttide-crowd#data/profile/qtcloud/second-brain-init.md`）：1. 理解现有对话流程与格式章程； 2. 将该流程接入资产云，整理为插件 / 可复用配置； 3. 输出一份非技术用户也能看懂的使用说明； 4. 完成一轮测试，记录结果与问题。
9. **c058** —— 23 个领域 / 152 成员，代表片段 `agent-000228`
   - 领域：quanttide-agent, quanttide-asset, quanttide-auth, quanttide-code, quanttide-connect, quanttide-course, quanttide-crowd, quanttide-data, quanttide-delib, quanttide-devops, quanttide-execute, quanttide-growth, quanttide-human, quanttide-learn, quanttide-media, quanttide-meta, quanttide-org, quanttide-pay, quanttide-product, quanttide-secret, quanttide-strategy, quanttide-support, quanttide-work
   - 代表片段（`quanttide-agent#data/context/profile/skills/quanttide-app-design/SKILL.md`）：- **先问"这个端给谁用"再设计**：同名端在不同产品角色不同——`qtcrowd studio`=**众包参与人员端**（认领/交付/结算查看）、`qtcloud-crowd studio`=**管理方端**（人财事审核）——初始化前先确认使用者（管理方/参与方/公众），否则方向全错（曾把参与端…
10. **c072** —— 23 个领域 / 118 成员，代表片段 `data-001065`
    - 领域：quanttide-agent, quanttide-asset, quanttide-auth, quanttide-code, quanttide-connect, quanttide-course, quanttide-crowd, quanttide-data, quanttide-docs, quanttide-execute, quanttide-finance, quanttide-infra, quanttide-innov, quanttide-learn, quanttide-meta, quanttide-org, quanttide-pay, quanttide-product, quanttide-search, quanttide-support, quanttide-think, quanttide-work, quanttide-write
    - 代表片段（`quanttide-data#data/context/journal/quanttide-legal/2026-10-09.md`）：对，因为呃如果有问题的话，他过不了打回来重新做，那么实际上这个就会形成一个反馈数据，我们只要多收集一些反馈信息，我们就能知道这个东西该怎么做了。

前 10 全是领域数 23 至 32 的大簇，成员 118 至 229 条；按第 2 条结论，这一档偏文体簇，**读代表片段即可，不必逐条展开**。想看真主题，看下面低领域数那一组。

## 抽检判读（贴成员供人工复核）

抽样规则（可复现，`find_clusters.py` 跑完会打出同一份素材）：199 个跨域簇按 `cluster_id` 升序取下标 0 / 39 / 78 / 117 / 156 / 195（步长 39）得 6 个，每簇按成员顺序等距取 4 条；另把领域数取下限 2 的簇全部列出（正好 4 个：`c128`、`c142`、`c168`、`c193`），按 `cluster_id` 升序各等距取 3 条。判定标准只有一条：**这些成员是不是在讲同一件事**。

### 等距抽的 6 个

**c000**（成员 59，领域 8）——判读：讲的都是「元 / 元认知」，主题集中。**有意义**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| agent-001061 | docs/tutorial/loop/classification.md | 分类本身就是循环工程的元认知分类监控该运行哪种环。系统成熟的标志是有意识地选择自己所处的环，而不是被动落进某一种。 |
| strategy-000041 | data/insight/strategy-routing.md | 日期：2026-09-07 来源：journal front-matter 实操（打标、聚合、profile 分拆）中提炼的元洞察 |
| think-000927 | apps/qtcloud-think/tests/fixtures/report/2026-03.md | 1. **自我复现知识库设想**： - > “元认知偏好强”（2026-03-15）：“从对话者到记忆管理者、认知分层处理器和叙事流分析师。 |
| think-003048 | data/profile/quanttide-meta/index.md | 元认知是系统对自身的认知：先有目标，才知道该思考什么、认知什么；让系统与认知对抗性协同进化——明确需求后互相举证（互举）。 |

**c039**（成员 140，领域 20）——判读：公关稿姿态、受控词典、考研英语长句、thought 状态机互不相干，聚的是「短条目 + 加粗标签」的写法。**文体簇**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| agent-000028 | data/context/default/write-review/author.md | 公关稿是姿态。“我们很高兴地宣布”——姿态。 技术报告是姿态。“本实验在严格条件下进行”——姿态。 媒体通稿是姿态。“感谢XX提供支持”—— |
| code-000503 | data/context/library/review.md | 第二部分：受控词典 提供约900个经过筛选的“批准词”，每个词通常只对应一个含义和一种词性，以消除歧义。 |
| language-000010 | data/context/gallery/english-sentence.md | 以考研英语（一）2008 年 Text 2 的长句为例，拆出三个单元：U1 主干「互联网与资助机构的压力正在让获取科研成果成为现实」；U2  |
| think-000263 | apps/qtcloud-think/src/studio/doc/models/thought.md | - 状态只前进不后退（raw → clarifying → structured） - **structured 即情境意识实例**——无独 |

**c078**（成员 187，领域 14）——判读：校企合作、教与学鸿沟、交付质量、跨周期对冲，都在讲产教融合怎么获客与留人。**有意义（夹杂口语日志，偏弱）**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| agent-000447 | data/context/profile/skills/quanttide-content-repos/references/business-lines.md | 两类形式：**校企合作**——把课程体系整体带入学校，代表案例＝浙江理工大学计算机系的一系列合作（大数据导论实践课，源于 CPP 课题十年积 |
| course-001012 | docs/tutorial/intro/script.md | **我们要做的，就是用一套系统的方法，填平教与学之间的这个"隐性经验"鸿沟。** |
| product-000700 | data/journal/qtcrowd/2026-08-24.md | 同时，这地方也会给团队一个激励。为了不让这个布置区的任务亏本，我们必须要： 1. 有标准化的质量交付机制； 2. 让工作方法流程更加显性化， |
| strategy-000441 | data/profile/qtclass/index.md | **跨周期对冲结构**：上行期教育推动系统（大家愿意学习，课堂成就势能）；下行期招聘成为压力阀（求职摩擦变大、招聘量超上限，压力反向导入课堂 |

**c117**（成员 39，领域 12）——判读：会话存储、抓取保存步骤、RSS 订阅、备份明文风险互不相干，聚的是「技术说明短条目」。**文体簇**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| agent-000869 | data/library/hermes/session.md | > 注意：消息从 SQLite 原样还原，**不经过上下文压缩器**。压缩只发生在运行时，持久化存储的是未压缩的原始消息。 |
| data-000442 | data/archive/handbook/handling/collecting/scraping/scheduling.md | - 保存：输入需要保存的信息、保存的方式（CSV、数据库……）、保存的路径，进行保存操作，输出成功与否 |
| media-000030 | apps/qtmedia/src/site/docs/index.md | RSS 订阅说明：复制订阅链接到任意阅读器。附 `feed.xml` 链接。 |
| secret-000032 | apps/qtcloud-secret/docs/dev-guide/security.md | **R7. 备份是明文副本** - 备份页导出的 NDJSON 是明文（客户端-服务端交互即明文），保管不当 = 数据直接泄露 - 缓解：加 |

**c156**（成员 112，领域 18）——判读：设计实录、模板库、事件风暴、需求条目都是「需求 / 设计的碎片条目」，话题各不相同。**文体簇**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| agent-000262 | data/context/profile/skills/quanttide-app-design/references/qtcloud-think-studio.md | > 2026-08-22 会话实录——展示设计原则如何在真实迭代中落地。 |
| human-000077 | apps/qtrecurit/docs/dev-guide/multi-tenant-platform-architecture.md | **③ 筛选标准的模板库**——解决"新租户配置从哪来" |
| product-000085 | data/insight/mechanism-inventory.md | - 规格阶段用事件风暴梳理领域事件与业务规则 |
| product-001088 | data/profile/qtcloud-infra/requirement.md | · 用户要把报告归档存储（供后续查阅） · 用户要能检索已收集的报告 |

**c196**（成员 138，领域 22）——判读：工具配置清单、契约字段、ETL Load 步骤、版本计划互不相干，聚的是「字段与步骤清单」。**文体簇**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| agent-000009 | data/context/default/cross-agent.md | - 每个工具独有的功能（Zed 的 UI 主题、Hermes 的 sandbox/checkpoint） - 通过安装获取的内容（默认提示词 |
| asset-001296 | docs/specification/contract/index.md | - `spec_version`: 必选。契约标准版本。跟随标准文件的发布版本。 - `version`: 推荐。资产版本。由用户根据需求自 |
| data-000709 | data/archive/platform/docs/guides/concepts/etl.md | **加载（Load）** - 将转换后的数据写入目标系统 - 支持全量覆盖和增量更新 - 处理加载失败和重试机制 |
| human-000051 | apps/qtcloud-human/src/studio/doc/screens/relation.md | - v0.2：离职交接流程线上化（文档、复盘、评审） - v0.3：生命周期与薪酬/绩效联动（转正调薪、晋升调级） |

### 领域数取下限 2 的 4 个簇

**c128**（成员 24，领域 2：`quanttide-finance` 23 + `quanttide-human` 1）——判读：23 条全是同一个个税教程，主题极集中；但「跨域」只靠 1 条 `quanttide-human` 成员撑着。**有意义（跨域属性偏弱）**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| finance-000370 | docs/tutorial/tax/index.md | 你可能听说过个税退税这件事——每年三四月，有人在朋友圈晒"退税到账XXX元"。你可能也听说过有人不仅没退到钱，反而要补税。 |
| finance-000378 | docs/tutorial/tax/index.md | 进入申报流程后，APP会自动预填你的收入和已缴税额。大多数人走到这一步只需要核对数据有没有遗漏。但有一个选项需要你主动决策——**年终奖的计 |
| finance-000386 | docs/tutorial/tax/index.md | 但注意一条红线：**信息必须真实。** 不要为了多退税去填不存在的房租或虚假的赡养老人信息。税务系统有交叉核验机制，虚假填报被查出来不仅要补 |

**c142**（成员 18，领域 2：`quanttide-think` 10 + `quanttide-write` 8）——判读：地理与文明史的因果分析，两个领域各占一半，是真跨域。**有意义**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| think-001153 | data/archive/context/thought/acad/history_base.md | 中国的大河平原促成了政治统一，欧洲的破碎地形鼓励了多元竞争——两者都是地理赠予的礼物，也是枷锁。 |
| think-001168 | data/archive/context/thought/acad/history_base.md | 2. 为什么“南方政权北伐难于上青天”？ * 现象： 中国历史上，北方统一南方容易，南方北伐成功极其罕见（只有朱元璋是典型例外）。 * 我的 |
| write-000648 | data/archive/journal/essay/2026-04-03.md | 但是古代社会为什么“以牙还牙”的立法思想呢？我们不能简单地用“落后”来解释，而是需要理解前现代社会的信息传播效率低、认知水平低等客观治理因素 |

**c168**（成员 52，领域 2：`quanttide-execute` 51 + `quanttide-org` 1）——判读：讲法人作为记忆主体，主题集中；同样靠 1 条异域成员算跨域。**有意义（跨域属性偏弱）**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| execute-000213 | data/insight/consumption/weekly-meeting.md | 周会是法人（公司）以自己的记忆为对象、按周做一次「看清」——它是法人记忆最自然的消费节奏，也是对「看清」的第一条验收。 |
| execute-000250 | data/insight/subject/legal-person-memory-subject.md | - **任务工具**：把「项目/工作区」从容器升格为记忆主体（list=次级法人），指派/截止挂 (list, task) 而非 (pers |
| execute-000274 | data/intention/index.md | 记忆的主体是法人，而且可以层层嵌套。公司是顶层的法人，也是一个聚合根；公司之下有多个业务，每个业务是一个次级法人。 |

**c193**（成员 93，领域 2：`quanttide-docs` 62 + `quanttide-work` 31）——判读：同一部小说的文本分别在两个仓里（`docs` 侧 62 条、`work` 侧 31 条），是阶段 1 跨域重复的放大版，关联来自拷贝而非各自表述。**有意义（成因是重复）**

| id | 相对路径 | 正文前 70 字 |
| --- | --- | --- |
| docs-000113 | examples/quanttide-docs-lab/apps/qtfiction/data/series/校园言情/2_第二章.md | “逸神？先膜后看” “逸神是谁啊？” “逸神你都不知道？经院公认的十年一遇的学术天才，前几天刚在拔尖计划的面试中一个人压制一个组的老师，还把 |
| docs-000591 | examples/quanttide-docs-lab/apps/qtfiction/data/series/职场言情/5_1_家里吃火锅.md | “你昨天说要来吃火锅，我就问了下黎初晓。” |
| work-001036 | data/profile/quanttide/quanttide-write/context/卧室陪伴-写作建议.md | 她笑：“林远亭，像不像你理想里的生产环境？” |

## 复跑命令

```bash
cd examples/corpus-linking

# 门禁：scripts/ 新增过脚本（本轮加了 find_clusters.py）才需要先 --write 重记指纹
/usr/bin/python3 scripts/manifest.py --write
/usr/bin/python3 scripts/manifest.py --check

# 阶段 2（自带 manifest --check 门禁，约 75 秒）
/usr/bin/python3 scripts/find_clusters.py
```

产出 `data/clusters.tsv`（22811 行 + 表头，五列 `cluster_id, id, source, cluster_size, domain_count`）与 `data/cluster_summary.json`（参数、簇数、跨域簇分布、30 轮收敛曲线）。同输入复跑结果一致：两次跑 `clusters.tsv` 的 md5 都是 `3dcccc16aea72eb11a07341d8618e594`，`cluster_summary.json` 都是 `39e6524e4aa2a82159ff412c34847eeb`。

算法（L2 归一化 → 球形 k-means `k=200` / 种子 `20261011` / 30 轮 → 只留 ≥2 领域的簇 → 代表片段 = 离质心最近一条）写死在 `scripts/find_clusters.py` 头部注释，跑完不改；要改另起一轮并说明。依赖只有 numpy 与标准库（本机无 sklearn，分配与更新都是纯 numpy 矩阵运算）。

## 已知缺口

- **`k = 200` 是先验不是调参**：换 k 簇数、边界、领域数都会变，本报告的簇编号与前 10 排名不可跨 k 比较。
- **不给主题名**：只有代表片段，主题要人读；机器编的名字是假的。
- **文体簇与主题簇混在一张表**：按领域数排不出先后（前 10 恰好偏文体簇），挑主题得靠人读成员。
- **抽检只有 10 个簇**（等距 6 + 领域数为 2 的 4）/ 199 个跨域簇，样本小；且「有没有意义」是人的判定，这里的判读是 agent 给的，供你推翻。
- **「跨域」按有没有算**：`c128`、`c168` 靠 1 条异域成员入围（23+1、51+1）。本轮不改算法，要改成按占比算须另起一轮说明。
- **`source` 是快照路径**：语料被别的会话改动后可能与磁盘不一致（阶段 1 已见 1 对）。
