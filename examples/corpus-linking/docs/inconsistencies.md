---
created_at: 2026-10-11
updated_at: 2026-10-11
---

# 规矩组的不一致清单

同一组的成员是「同一段话的多份副本」。散成几份是预期，**要看的只是这几份之间哪句话对不上**。

来源：`data/copy_groups.tsv` 里跨领域 57 组中性质为「规矩与模板」的 17 组。

差异按**要点**比（不按字）：`-` 是基准有、对方没有的要点，`+` 是对方多出来或改过的。

## g000 — algorithm,code,connect,growth

基准 `algorithm-000003`  quanttide-algorithm#AGENTS.md

1. - 最小干预：仅在用户明确请求时操作；

2. - 信息复用：优先使用已有文档内容；

3. - 维护记录：修改后同步更新 CHANGELOG.md；

4. - 原子提交：每次提交包含完整独立变更；

5. - 提交即推送：提交后默认推送到远端，除非用户明确说「只提交不推」。

**对比 `code-000002`**  quanttide-code#AGENTS.md

```diff
- - 提交即推送：提交后默认推送到远端，除非用户明确说「只提交不推」。
+ - 提交即推送：修改完成后直接提交并推送到远端，无需另行请示，除非用户明确说「只提交不推」。
```

**对比 `connect-000145`**  quanttide-connect#docs/specification/AGENTS.md

```diff
- - 最小干预：仅在用户明确请求时操作；
- - 信息复用：优先使用已有文档内容；
- - 维护记录：修改后同步更新 CHANGELOG.md；
- - 原子提交：每次提交包含完整独立变更；
- - 提交即推送：提交后默认推送到远端，除非用户明确说「只提交不推」。
+ 1. **最小干预**：仅在用户明确请求时操作
+ 2. **信息复用**：优先使用已有文档内容
+ 3. **查询契约**：维护前先读取现有文档结构
+ 4. **维护记录**：修改后同步更新 CHANGELOG.md
+ 5. **验证优先**：完成后检查文档格式和内容一致性
+ 6. **原子提交**：每次提交包含完整独立变更
```

**对比 `growth-000002`**  quanttide-growth#AGENTS.md

```diff
- - 最小干预：仅在用户明确请求时操作；
- - 信息复用：优先使用已有文档内容；
- - 维护记录：修改后同步更新 CHANGELOG.md；
- - 原子提交：每次提交包含完整独立变更；
- - 提交即推送：提交后默认推送到远端，除非用户明确说「只提交不推」。
+ 1. **最小干预**：仅在用户明确请求时操作
+ 2. **信息复用**：优先使用已有文档内容
+ 3. **维护记录**：修改后同步更新 CHANGELOG.md
+ 4. **原子提交**：每次提交包含完整独立变更
+ 5. **提交即推送**：提交后默认推送到远端，除非用户明确说"只提交不推"
```


## g001 — execute,project

基准 `execute-000454`  quanttide-execute#docs/bylaw/index.md

1. **第十二条 解释权** 本章程由项目管理办公室负责解释。

**对比 `execute-000463`**  quanttide-execute#docs/bylaw/stage/progress-reporting.md

```diff
- **第十二条 解释权** 本章程由项目管理办公室负责解释。
+ **第七条 解释权** 本章程由项目管理办公室负责解释。
```

**对比 `project-000015`**  quanttide-project#docs/bylaw/index.md

```diff
- **第十二条 解释权** 本章程由项目管理办公室负责解释。
+ **第十四条 解释权** 本章程由项目管理办公室负责解释。
```

**对比 `project-000031`**  quanttide-project#docs/bylaw/stage/delivery.md

```diff
- **第十二条 解释权** 本章程由项目管理办公室负责解释。
+ **第十三条 解释与修订** 本章程由项目管理办公室负责解释与修订。
```

**对比 `project-000044`**  quanttide-project#docs/bylaw/stage/initiation.md

```diff
- **第十二条 解释权** 本章程由项目管理办公室负责解释。
+ **第十二条 解释与修订** 本章程由项目管理办公室负责解释与修订；
+ 修订遵循上位章程第十四条的程序。
```

**对比 `project-000067`**  quanttide-project#docs/bylaw/stage/retrospective.md

```diff
- **第十二条 解释权** 本章程由项目管理办公室负责解释。
+ ### 第二十五条 解释权 本章程由项目管理办公室负责解释。执行过程中对章程条款有疑义的，由项目管理办公室出具书面解释。
```


## g002 — org,think

基准 `org-000092`  quanttide-org#data/context/bylaw/audit.md

1. **第十条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。

**对比 `org-000109`**  quanttide-org#data/context/bylaw/bylaw.md

```diff
- **第十条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。
+ **第十六条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。
```

**对比 `org-000313`**  quanttide-org#docs/bylaw/institution/rank.md

```diff
- **第十条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。
+ **第二十二条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。
```

**对比 `org-000357`**  quanttide-org#docs/bylaw/role/secretary.md

```diff
- **第十条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。
+ **第十五条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。
```

**对比 `think-003199`**  quanttide-think#docs/bylaw/index.md

```diff
- **第十条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。
+ **第十一条 章程效力** 本章程自发布之日起生效。与章程不一致的既有实践，应逐步修订。
```

**对比 `think-003221`**  quanttide-think#docs/bylaw/schema.md

```diff
- **第十条 章程效力** 本章程经公司治理机构审议通过，自发布之日起生效。
+ **第十三条 章程效力** 本章程自发布之日起生效。与章程不一致的既有实践，应逐步修订。
```


## g003 — agent,work

基准 `agent-000204`  quanttide-agent#data/context/profile/skills/insight-writing/references/domain-doc-writing.md

1. - **Specification** = 「可接受行为的描述」

2. - **Contract** = 「交互双方义务与保证的、带责任分配的 specification」 - 所有 contract 都可以看作一种 spec，但不是所有 spec 都是 contract。

**对比 `agent-000609`**  quanttide-agent#data/context/profile/skills/quanttide-repo-workflow/SKILL.md

```diff
- - **Specification** = 「可接受行为的描述」
- - **Contract** = 「交互双方义务与保证的、带责任分配的 specification」 - 所有 contract 都可以看作一种 spec，但不是所有 spec 都是 contract。
+ **spec / contract 语汇（2026-09-10 用户给定，落 journal）**：Specification = 「可接受行为的描述」；
+ Contract = 「交互双方义务与保证的、带责任分配的 specification」；
+ **所有 contract 都可看作一种 spec，但不是所有 spec 都是 contract**（spec 上位、contract 下位加义务保证）。写规范/契约类文档前按此判层级，不混用两词。
```

**对比 `agent-000737`**  quanttide-agent#data/context/profile/skills/quanttide-repo-workflow/references/knowledge-work-artifacts.md

```diff
- - **Specification** = 「可接受行为的描述」
- - **Contract** = 「交互双方义务与保证的、带责任分配的 specification」 - 所有 contract 都可以看作一种 spec，但不是所有 spec 都是 contract。
+ - **Specification** = 可接受行为的描述
+ - **Contract** = 交互双方义务与保证的、带责任分配的 specification - 所有 contract 都可看作一种 spec，但不是所有 spec 都是 contract
```

**对比 `work-000331`**  quanttide-work#data/journal/quanttide-founder/2026-09-10.md

```diff
- - **Specification** = 「可接受行为的描述」
- - **Contract** = 「交互双方义务与保证的、带责任分配的 specification」 - 所有 contract 都可以看作一种 spec，但不是所有 spec 都是 contract。
+ - **Specification** 是「可接受行为的描述」
+ - **Contract** 是「交互双方义务与保证的、带责任分配的 specification」 - 所有 contract 都可以看作一种 spec，但不是所有 spec 都是 contract。
```


## g004 — auth,pay

基准 `auth-000181`  quanttide-auth#data/report/tech-decisions/index.md

1. 决策记录文件用英文命名（小写连字符），不带头日期，如 `unified-account-authorization-principles.md`。

**对比 `pay-000370`**  quanttide-pay#data/report/product-decisions/index.md

```diff
- 决策记录文件用英文命名（小写连字符），不带头日期，如 `unified-account-authorization-principles.md`。
+ 决策报告文件用英文命名（小写连字符），不带头日期，如 `product-market-fit.md`。
```

**对比 `pay-000395`**  quanttide-pay#data/report/technical-decisions/index.md

```diff
- 决策记录文件用英文命名（小写连字符），不带头日期，如 `unified-account-authorization-principles.md`。
+ 决策报告文件用英文命名（小写连字符），不带头日期，如 `money-value-object.md`。
```


## g005 — code,work

基准 `code-000947`  quanttide-code#data/profile/qtcloud-work/cli/index.md

1. 判据挂在步骤上，按谁判分三类：`rule` 程序按 `path` / `absent` / `file` 加 `contains` / `run` 当场核，`agent` 由智能体照判准审，`human` 进待拍板清单等人 `order done` 放行。一步算过，等于所有 `rule` 通过、所有 `agent` 判过。

**对比 `work-000115`**  quanttide-work#apps/qtcloud-work/src/cli/docs/dev-guide/workflow.md

```diff
- 判据挂在步骤上，按谁判分三类：`rule` 程序按 `path` / `absent` / `file` 加 `contains` / `run` 当场核，`agent` 由智能体照判准审，`human` 进待拍板清单等人 `order done` 放行。一步算过，等于所有 `rule` 通过、所有 `agent` 判过。
+ 判据挂在步骤上，按谁判分三类：`rule` 由程序按字段判四种判法、`agent` 照说明审、`human` 进待拍板清单。判据的语法与翻译在 `crate::criterion`，本侧只负责真去跑（见 [audit](audit.md)）。
```

**对比 `work-000180`**  quanttide-work#apps/qtcloud-work/src/cli/docs/user-guide/workspace.md

```diff
- 判据挂在步骤上，按谁判分三类：`rule` 程序按 `path` / `absent` / `file` 加 `contains` / `run` 当场核，`agent` 由智能体照判准审，`human` 进待拍板清单等人 `order done` 放行。一步算过，等于所有 `rule` 通过、所有 `agent` 判过。
+ 判据挂在步骤上，按谁判分三类。`rule` 由程序按字段判，四种判法：`path` 存在、`absent` 不存在、`file` 加 `contains` 文件含某段文字、`run` 命令退出码为零；
+ 路径相对工作区根，写绝对路径则按绝对路径。`agent` 由智能体照说明审，逐条回答通过或不通过。`human` 不跑，原样进报告的闸门项等人拍板。
```


## g006 — code,work

基准 `code-001212`  quanttide-code#packages/quanttide-code-toolkit/packages/rust/AGENTS.md

1. 领域模型与规格以 `quanttide-code/docs/specification` 为准；

2. 本库只做表达，不定义领域。

**对比 `work-001666`**  quanttide-work#examples/quanttide-work-lab/packages/rust/AGENTS.md

```diff
- 领域模型与规格以 `quanttide-code/docs/specification` 为准；
- 本库只做表达，不定义领域。
+ 领域模型与规格以 quanttide-work 的 `docs/specification` 为准；
+ 本库只做表达，不定义领域。收进来的每一样都要能在规格里找到出处。
```

**对比 `work-001733`**  quanttide-work#packages/quanttide-work-toolkit/packages/dart/AGENTS.md

```diff
- 领域模型与规格以 `quanttide-code/docs/specification` 为准；
+ 领域模型与规格以 `quanttide-work/docs/specification` 为准；
```


## g007 — credit,work

基准 `credit-000003`  quanttide-credit#AGENTS.md

1. 措辞严格使用既有术语，不用口语。决策思路写在开发者文档里，按「背景 / 选项 / 影响 / 建议」梳理清楚；

2. 不用「要你拍板」这类说法把决策推给用户。待决事项不进 `TODO.md`，TODO 只列可直接动手的事项。

**对比 `work-000003`**  quanttide-work#apps/qtcloud-work/AGENTS.md

```diff
- 措辞严格使用既有术语，不用口语。决策思路写在开发者文档里，按「背景 / 选项 / 影响 / 建议」梳理清楚；
- 不用「要你拍板」这类说法把决策推给用户。待决事项不进 `TODO.md`，TODO 只列可直接动手的事项。
+ 措辞严格使用既有术语，不用口语。决策思路写在开发者文档里，按「背景 / 选项 / 影响 / 建议」梳理清楚。
```

**对比 `work-000344`**  quanttide-work#data/profile/quanttide/quanttide-agent/context/index.md

```diff
- 措辞严格使用既有术语，不用口语。决策思路写在开发者文档里，按「背景 / 选项 / 影响 / 建议」梳理清楚；
- 不用「要你拍板」这类说法把决策推给用户。待决事项不进 `TODO.md`，TODO 只列可直接动手的事项。
+ **术语与决策**：措辞严格使用既有术语，不用口语。决策思路写在开发者文档里，按「背景 / 选项 / 影响 / 建议」梳理清楚；
+ 不用「要你拍板」这类说法把决策推给用户。
```


## g028 — auth,pay

基准 `auth-000028`  quanttide-auth#apps/qtcloud-auth/docs/dev-guide/ci.md

1. - **触发**：推送 `provider/*` tag（如 `provider/v0.1.0-alpha.8`）；

2. **无手动触发**（生产保护）

3. - **job 1 `build-image`**：Dockerfile 多阶段构建 → 双通道发布（Docker Hub + ACR `quanttide/qtcloud-auth-provider`）→ 各带版本 tag 与 `latest`

4. - **job 2 `deploy`**：Ensure RDS Running → `terraform init/validate/plan/apply`（OSS 远程状态 `qtcloud-auth/terraform.tfstate`），挂 GitHub `production` 环境（可配 required reviewers）

5. - **并发控制**：`concurrency: deploy-provider`，避免同时 apply 竞争状态

**对比 `pay-000061`**  quanttide-pay#apps/qtcloud-pay/docs/dev-guide/ci.md

```diff
- - **触发**：推送 `provider/*` tag（如 `provider/v0.1.0-alpha.8`）；
- **无手动触发**（生产保护）
- - **job 1 `build-image`**：Dockerfile 多阶段构建 → 双通道发布（Docker Hub + ACR `quanttide/qtcloud-auth-provider`）→ 各带版本 tag 与 `latest`
- - **job 2 `deploy`**：Ensure RDS Running → `terraform init/validate/plan/apply`（OSS 远程状态 `qtcloud-auth/terraform.tfstate`），挂 GitHub `production` 环境（可配 required reviewers）
+ - **触发**：推送 `provider/*` tag（如 `provider/v0.1.0-alpha.4`）；
+ **无手动触发**（生产保护，workflow_dispatch 已移除）
+ - **job 1 `build-image`**：Dockerfile 多阶段构建 → 双通道发布（Docker Hub + ACR）→ 各带版本 tag 与 `latest`
+ - **job 2 `deploy`**：`terraform init/validate/plan/apply`（OSS 远程状态），挂 GitHub `production` 环境（可配 Required reviewers）
```


## g029 — auth,pay

基准 `auth-000035`  quanttide-auth#apps/qtcloud-auth/docs/dev-guide/ci.md

1. CI 的 RAM 用户**无 ACR 管理权限**；

2. 且 aliyun CLI cr API 不稳定。仓库由**主账号一次性创建（PUBLIC）**，CI 只负责 docker login（ACR 固定凭证）推送。教训：管理操作交给有权限的账号，CI 只做有凭证的操作。

**对比 `pay-000067`**  quanttide-pay#apps/qtcloud-pay/docs/dev-guide/ci.md

```diff
- CI 的 RAM 用户**无 ACR 管理权限**；
- 且 aliyun CLI cr API 不稳定。仓库由**主账号一次性创建（PUBLIC）**，CI 只负责 docker login（ACR 固定凭证）推送。教训：管理操作交给有权限的账号，CI 只做有凭证的操作。
+ CI 的 RAM 用户**没有 ACR 管理权限**，且 aliyun CLI 的 cr API 不稳定（`version: latest` 下 `ListInstance --InstanceType acr_personal` 已报参数无效）。Ensure 步骤已从 workflow 移除：仓库由主账号一次性创建（PUBLIC），CI 只负责 docker login（ACR 固定凭证）推送。
```


## g030 — auth,pay

基准 `auth-000180`  quanttide-auth#data/report/tech-decisions/index.md

1. - 技术选型与架构决策 - 协议与接口设计决策 - 授权与权限模型决策 - 数据模型与存储决策 - 安全与合规决策

**对比 `pay-000394`**  quanttide-pay#data/report/technical-decisions/index.md

```diff
- - 技术选型与架构决策 - 协议与接口设计决策 - 授权与权限模型决策 - 数据模型与存储决策 - 安全与合规决策
+ - 技术选型与架构决策 - 协议与接口设计决策 - 数据模型与存储决策 - 安全与合规决策 - 性能与可靠性决策
```


## g032 — code,think

基准 `code-001203`  quanttide-code#packages/quanttide-agent-toolkit/packages/rust/AGENTS.md

1. 修改后先提交推送本仓，再更新主仓库的子模块指针。

**对比 `think-003245`**  quanttide-think#docs/specification/AGENTS.md

```diff
- 修改后先提交推送本仓，再更新主仓库的子模块指针。
+ - 修改规范后先提交推送本仓，再更新主仓库的子模块指针。
```


## g037 — course,devops

基准 `course-000418`  quanttide-course#data/context/samples/devops/release.md

1. 遵循语义化版本规范（SemVer）。正式版格式 `vX.Y.Z`，预发布版按开发阶段依次使用 `-alpha.N`、`-beta.N`、`-rc.N` 后缀。

**对比 `devops-000290`**  quanttide-devops#docs/bylaw/lifecycle/release.md

```diff
- 遵循语义化版本规范（SemVer）。正式版格式 `vX.Y.Z`，预发布版按开发阶段依次使用 `-alpha.N`、`-beta.N`、`-rc.N` 后缀。
+ **第三条 版本号规则** 版本号遵循语义化版本规范（SemVer）。正式版格式为 `vX.Y.Z`，预发布版在版本号后加 `-alpha.N`、`-beta.N`、`-rc.N` 等后缀。
```


## g043 — delib,pay

基准 `delib-000011`  quanttide-delib#apps/qtcloud-delib/src/provider/ROADMAP.md

1. 按版本组织，只列直接需要落实到代码的事项。权威路线图见[域级路线图](../../../data/roadmap/)。

**对比 `pay-000117`**  quanttide-pay#apps/qtcloud-pay/src/provider/ROADMAP.md

```diff
- 按版本组织，只列直接需要落实到代码的事项。权威路线图见[域级路线图](../../../data/roadmap/)。
+ 按版本组织，只列直接需要落实到代码的事项。权威路线图见[域级路线图](../../../../data/roadmap/provider.md)。
```


## g047 — media,pay

基准 `media-000002`  quanttide-media#apps/qtmedia/src/site/ROADMAP.md

1. - 每阶段完成后运行 `npm run build` 验证（含 feed/sitemap 生成） - 全部完成后打 `site/v0.1.0` tag 并更新 `src/site/CHANGELOG.md`

**对比 `pay-000031`**  quanttide-pay#apps/qtbusiness/src/site/ROADMAP.md

```diff
- - 每阶段完成后运行 `npm run build` 验证（含 feed/sitemap 生成） - 全部完成后打 `site/v0.1.0` tag 并更新 `src/site/CHANGELOG.md`
+ - 每阶段完成后运行 `npm run build` 验证 - 全部完成后打 `site/v0.1.0` tag 并更新 `src/site/CHANGELOG.md`
```


## g051 — pay,project

基准 `pay-000003`  quanttide-pay#AGENTS.md

1. - 子模块（`apps/qtcloud-pay`、`data/*`、`packages/quanttide-pay-toolkit`）内容先提交到各自仓库，主仓库只记录指针 - Conventional Commits，中文描述（如 `feat(toolkit): ...`）；

2. 文档与代码同批提交 - 提交前核对：相关 `STATUS.md` 待办是否已消化、文档是否同步、`go test ./... && go vet ./...` 是否通过

**对比 `project-000002`**  quanttide-project#AGENTS.md

```diff
- - 子模块（`apps/qtcloud-pay`、`data/*`、`packages/quanttide-pay-toolkit`）内容先提交到各自仓库，主仓库只记录指针 - Conventional Commits，中文描述（如 `feat(toolkit): ...`）；
- 文档与代码同批提交 - 提交前核对：相关 `STATUS.md` 待办是否已消化、文档是否同步、`go test ./... && go vet ./...` 是否通过
+ - 子模块（`apps/qtcloud-project`、`docs/*`、`packages/quanttide-project-toolkit`）内容先提交到各自仓库，主仓库只记录指针 - Conventional Commits，中文描述；
+ 文档与代码同批提交 - 提交前核对：文档是否同步、子模块指针是否已更新
```


## g053 — product,strategy

基准 `product-000001`  quanttide-product#AGENTS.md

1. - `apps/` — 可部署应用 - `packages/toolkit` — 领域共享库/工具集 - `examples/quanttide-product-lab` — 实验室——实验性/原型项目 - `docs/` — 领域文档

**对比 `strategy-000001`**  quanttide-strategy#AGENTS.md

```diff
- - `apps/` — 可部署应用 - `packages/toolkit` — 领域共享库/工具集 - `examples/quanttide-product-lab` — 实验室——实验性/原型项目 - `docs/` — 领域文档
+ - `apps/` — 可部署应用 - `packages/toolkit` — 领域共享库/工具集 - `examples/quanttide-strategy-lab` — 实验室——实验性/原型项目 - `docs/` — 领域文档
```


