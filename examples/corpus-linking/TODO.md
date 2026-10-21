# TODO

[ROADMAP.md](docs/dev-guide/roadmap.md) 的执行清单。每条给出可跑判据，判据通过才勾选；`[ ]` 未做，`[x]` 已做。

**数据源**：本地 `~/repos/quanttide/domains/`，全程离线，不依赖 GitHub。

## 阶段 0 向量化（三件共同的闸门）

- [x] **0.1 片段提取**——读本地语料，切片段：清洗模板文件（`README.md`、`CHANGELOG.md`、`.agents/`、`.quanttide/`）、按内容哈希去重、剔除纯标题/代码块/表格，保留 20 至 900 字且含 ≥15 汉字的段落。
      规则参考 [`reference/build_eval.py`](./reference/build_eval.py) 的 `clean_block` / `extract` / `collect`——旧采样脚本的提取逻辑，网络与评测集部分已废弃，只借这一段。
      产出：`data/fragments.tsv`，三列 `id, text, source`，`source` 形如 `领域仓#相对路径`。
      判据：条数与既有统计同量级（约 2.4 万条）；断网可跑；抽 10 条人工看是否成句。
- [x] **0.2 选 embedding 模型**——选 **`bge-m3`**（1024 维，多语种，中文检索强；`nomic-embed-text` 274MB 与 `all-minilm` 46MB 都偏英文，不用）。已 `ollama pull bge-m3`。
      判据：`ollama list` 有该模型；一条 50 字中文文本能拿到 1024 维向量。
      说明：显存 3GB，向量模型无压力。
- [x] **0.3 向量化落盘**——批量算向量并落盘（`data/embeddings.npy` + `data/embedding_ids.tsv` 对照）。
      判据：向量行数 == `fragments.tsv` 行数；失败条目如实报条数，不静默丢。
      实况：22811 条，shape `(22811, 1024)` float32，失败 0 条，id 顺序与 `fragments.tsv` 完全一致。
- [x] **0.4 记语料指纹**——语料是活的：跑完当口复跑 `build_fragments.py` 已从 22811 变 22812（另会话在改 `quanttide-search`），同一份向量不再对应新语料。把 `fragments.tsv` 的 md5 与条数写进产物（`data/manifest.json`），下游（阶段 1–3）先核指纹再算。
      判据：`data/manifest.json` 有 md5、条数、生成时间、脚本版本；指纹不符时下游脚本拒绝运行并提示重跑。

## 阶段 1 找重复

- [x] **1.1 算高分对**——算片段两两相似度（或近邻检索）取高分对；阈值与算法先写死，跑完不改，要改另起一轮并说明。
      产出：`data/duplicates.tsv`，五列 `id_a, id_b, score, source_a, source_b`。
      判据：抽 30 对人工看，记录误报数；报告里写清阈值、取样量与分母。
- [x] **1.2 出报告**——`docs/duplicates.md`。
      判据：结论先行、术语解释、数字给分母、附复跑命令；把「跨领域重复」与「同领域内重复」分开列。

## 阶段 2 找关联

- [x] **2.1 聚类**——对向量聚类，算法与参数先写死。
      产出：`data/clusters.tsv`（`cluster_id, id, source`）+ 每簇主题摘要。
      判据：簇覆盖率（被聚进簇的片段占比）写清；抽几个簇人工判读有没有意义。
      实况：球形 k-means `k=200`、种子 20261011、30 轮（纯 numpy，75 秒）；覆盖率 22811 / 22811 = 100%；跨域簇 199 / 200。判读 10 个簇（等距 6 + 定向 4）：主题集中 6、文体簇 4，详见 `docs/clusters.md`。产出按本轮指令不编主题名，`每簇主题摘要` 换成**代表片段**（离质心最近一条），另给 `cluster_size` / `domain_count` 与 `data/cluster_summary.json`。
- [x] **2.2 出报告**——`docs/clusters.md`，贴出抽检簇的成员供人工判读。
      实况：结论先行、术语解释、数字给分母、复跑命令齐全，10 个抽检簇的成员逐条贴出；报告写明 `k=200` 是写死的先验、换 k 结果不可比。

## 阶段 3 建索引

- [x] **3.1 建索引与查询入口**——`scripts/search.py "<主题>"`，返回最相近的片段与出处。
- [ ] **3.2 真实主题实测**——拿几个你心里真实的主题查，如实记录命中与不命中。
