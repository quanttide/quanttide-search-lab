# 计算部分 Rust 移植对照报告

把 `scripts/find_duplicates.py`、`scripts/find_clusters.py`、`scripts/search.py` 的计算部分用 Rust 重写（`src/bin/vector.rs`，可执行名 `vector`），与 Python 版在同一份输入上逐项对照。输入不重算：`data/fragments.tsv`（22811 条，md5 `c4577ac68613c58ec319ae6112d224cd`）、`data/embedding_ids.tsv`、`data/embeddings.npy` 导出的 `data/embeddings.f32`（导出后与 npy 逐位相等，max abs diff = 0）。每个子命令开跑前先过 `scripts/manifest.py --check` 门禁。

## 结论

1. **三份对照全部一致**：
   - duplicates：586 对 vs 586 对，id 对集合**差集 0**；`id`/`source` 列 587 行逐行全同；分数最大绝对差 **1.0e-6**（587 行里 148 行分数文本末位不同）。
   - clusters：`clusters.rs.tsv` 与 `clusters.tsv` **md5 完全相同**（`3dcccc16aea72eb11a07341d8618e594`），22811 / 22811 条片段同簇一致度 **1.000000**。
   - search：**同一份查询向量**下 top-10 逐行 **10 / 10** 完全一致；再用 `search.py` 本体（重新走 ollama 编码）对比，10 条 id 与顺序全同，仅 1 行分数差 1e-6。
2. **快的部分**：duplicates 全程 348.0 s → 11.9–18.6 s（**19–29 倍**）；clusters 73.0 s → 3.6–3.7 s（**约 20 倍**）；点积段 355.6 s → 11.0–17.5 s（**20–32 倍**）。
3. **没有更快的部分（如实报）**：
   - search 的全量点积只从 13.0 ms 降到 7.9–9.0 ms（1.5–1.7 倍）；读数据两边都约 0.1 s，端到端（不含 ollama 编码）Rust 130–138 ms vs Python 127 ms——**打平、甚至略慢，没有更快**，瓶颈是读 93 MB 文件，不是语言。
   - argpartition 段只快 **2.0–2.5 倍**（1.0 s → 0.41–0.49 s）。
   - 并查集本身不是瓶颈：纯 Python 实测 586 对只要 **0.4 ms**；Rust 报的 0.8–1.4 ms 含建 22811 条 id→下标表与分组，口径不同。
   - 任务里「纯 Python 80 秒以上跑不完」这一句，实测卡死的是 **dot 段**：numpy 单线程 sgemm 355.6 s；不用 numpy、纯 Python 逐元素外推约 **10.4 小时**。并查集不在其列。
4. groups（本轮新增，Python 没有）：586 对 → **435 组 / 946 条片段**；纯 Python 并查集独立复算也是 435 组 / 946 条。三档：跨 1 个领域 **378 组 / 815 条**，跨 2–9 个领域 **57 组 / 131 条**，跨 ≥10 个领域 **0 组**。

## 一、逐项对照

### 1. `duplicates.rs.tsv` vs `duplicates.tsv`

| 项 | Python | Rust | 分母 |
| --- | --- | --- | --- |
| 余弦 ≥ 0.90 的对 | 586 | **586** | / 22811 条片段 |
| id 对集合差集 | — | **0**（仅 Python 0、仅 Rust 0） | 586 对 |
| `id` / `source` 列逐行相同 | — | **587 / 587 行**（含表头） | 587 行 |
| 分数最大绝对差 | — | **1.0e-6** | 586 对 |
| 分数文本末位不同行数 | — | 148 | / 587 行 |
| top1 余弦 p50 / p90 / p99 / max | 0.7598 / 0.8498 / 0.9577 / 0.9999 | **0.7598 / 0.8498 / 0.9577 / 0.9999** | 22811 行 |
| 跨领域 / 同领域内 | 72 / 514 | **72 / 514** | 586 对 |
| 同一文件内 / 其中序号相邻 | 132 / 25 | **132 / 25** | 514 对 |

分数差异全部是末位（f32 累加顺序不同：numpy 走 BLAS，Rust 手写内核 q 升序累加），id 对集合一个不差。

### 2. `clusters.rs.tsv` vs `clusters.tsv`

| 项 | Python | Rust | 分母 |
| --- | --- | --- | --- |
| 文件 md5 | `3dcccc16aea72eb11a07341d8618e594` | **同左，完全相同** | 22812 行 |
| 簇数 / 跨域簇数 | 200 / 199 | **200 / 199** | 200 个簇 |
| 同簇一致度（两条片段两边同簇） | — | **1.000000**（1,510,272 同簇对全同，258,649,183 不同簇对也全同） | 260,159,455 片段对 |
| cluster_id 逐条相同 | — | **22811 / 22811** | 22811 条 |
| 收敛曲线 第 1 / 10 / 30 轮 | 0.7575 / 0.7712 / 0.7719 | **0.7575 / 0.7712 / 0.7719** | 30 轮 |
| 跨域簇按领域数分布 | 2 领域 4、3 领域 5、4 领域 6 … 32 领域 1 | **逐档相同（合计 199）** | 199 个跨域簇 |

md5 相同意味着簇分配、簇大小、领域数、行序、格式全同——球形 k-means 30 轮后落点完全复现。复跑 `find_clusters.py` 实测输出 md5 不变（`3dcccc16…`，`cluster_summary.json` 也是 `39e6524e…`，与 `docs/clusters.md` 记录一致），基线有效。

### 3. `vector search` vs `search.py`

查询文本「第二大脑 九宫格」，top-10：

| 对比 | 结果 |
| --- | --- |
| 同一查询向量（`data/query_second_brain.f32`，两边共用）：Rust vs Python 检索段（numpy 复现 `search.py` 的数学） | **逐行 10 / 10 完全一致**（含分数 6 位小数与正文预览） |
| `search.py` 本体（重新走 ollama 编码）vs Rust | id 与顺序 **10 / 10 全同**，仅第 8 行分数 0.649814 vs 0.649813（差 1e-6） |
| `docs/search.md` 记录的当轮 top-10 | 10 条 id 与顺序一致，同一条 1e-6 差异 |

第 3 行那 1e-6 来自两次 ollama 编码出的查询向量末位不同（GPU 编码非逐位可复现），不是检索段数学差异——同向量下 10/10 全同。

### 4. `vector groups`（本轮新增，Python 版没有）

| 项 | 数 | 分母 / 说明 |
| --- | --- | --- |
| 输入对（对账 `duplicates.rs.tsv`） | 586 vs 586，共同 586，差集 0 | 文件与重算两路对账 |
| 连通分量（组） | **435** | 586 对建图 |
| 组内片段 | **946** | / 22811 ≈ 4.1%（与 duplicates 参与片段数相同，说明没有片段落在组外） |
| 跨 1 个领域 | **378 组 / 815 条** | / 435 组、/ 946 条 |
| 跨 2–9 个领域 | **57 组 / 131 条** | 同上 |
| 跨 ≥10 个领域 | **0 组 / 0 条** | 同上 |
| 领域数完整分布 | 1: 378、2: 56、4: 1（组）；1: 815、2: 127、4: 4（条） | 合计 435 组 / 946 条 |
| 纯 Python 并查集独立复算 | 435 组 / 946 条 | 与 Rust 相同 |

产出：`data/copy_groups.tsv`（947 行含表头，列 `group_id, group_size, domain_count, domains, id, source`）、`data/copy_groups_stats.json`。`group_id` 按（领域数降序 → 组内片段数降序 → 首个 id 升序）编号 `g000` 起，排序规则写死在代码里。

**三段耗时单独报**（`vector groups` 自己打印，见下节）：dot 13.4–17.8 s、argpartition 0.46–0.49 s、并查集 0.0008–0.0014 s。

## 二、耗时对照表

本机同时跑着浏览器 / 飞书等后台（load average 3–7），Rust 的点积段在各次运行间有 11.0–17.5 s 的波动，故给区间；Python 数字 docs 里有的照抄并注明出处，没有的本次复跑实测。

| 项 | Python 实测 | 出处 | Rust 实测 | 倍数 |
| --- | --- | --- | --- | --- |
| duplicates 全程 | **348.0 s** | 本次复跑 `/usr/bin/time`（`docs/duplicates.md` 记「约 5.5 分钟」） | **11.9 – 18.6 s**（4 次） | **19 – 29×** |
| └ dot（分块点积） | **355.6 s** | 本次分段复测 | **11.0 – 17.5 s** | **20 – 32×** |
| └ argpartition（top-k+阈值+去重） | **1.00 s** | 本次分段复测 | **0.41 – 0.49 s** | 2.0 – 2.5× |
| └ 读数据 / 归一化 / 写盘 | 0.07 s / 0.09 s / 0.001 s | 本次分段复测 | 0.10–0.17 s / 0.02 s / 0.001 s | 打平 |
| clusters 全程 | **73.0 s** | 本次复跑（`docs/clusters.md` 记「约 75 秒」） | **3.6 – 3.7 s**（3 次） | **约 20×** |
| └ 30 轮分配+更新+统计 | — | — | 3.32 – 3.45 s | — |
| search 全量点积 | **13.0 ms** | 本次复跑（`docs/search.md` 记 13.6 ms，带载 14.1/14.3/14.5） | **7.9 – 9.0 ms** | 1.5 – 1.7× |
| search 读数据+归一化 | 114 ms | 本次实测（同向量复现） | 121 – 129 ms | 略慢 |
| search 端到端（不含编码） | **127 ms** | 本次实测 | **130 – 138 ms** | 打平、甚至略慢 |
| search 编码（ollama，语言无关，本轮不比） | 2046 ms | 本次复跑（`docs/search.md` 记 3.7–7.6 s，本次模型已热） | 不适用 | — |
| groups 全程 | 无 Python 版 | — | **14.4 – 18.9 s**（3 次） | — |
| 纯 Python 点积全量（不用 numpy） | **约 10.4 小时** | 本次微基准外推：单次 1024 维点积 0.10 ms → 一行扫全库 1.64 s → ×22811 行 | — | — |
| 纯 Python 每行 top-10 | 1.0 ms/行 → 全量 22.5 s | 本次微基准外推 | — | — |
| 纯 Python 并查集（586 对） | **0.4 ms** | 本次实测 | 0.8 – 1.4 ms（含建 id 表+分组） | 口径不同 |

各子命令的耗时分解（Rust 每次运行自行打印）：

```
vector duplicates   门禁 0.10 s｜读数据 0.10–0.17 s｜归一化 0.02 s｜计算 11.7–18.3 s（dot 11.0–17.5，argpartition 0.41–0.49）｜写盘 0.001 s
vector clusters     门禁 0.10 s｜读数据 0.10 s｜归一化 0.02 s｜计算 3.3–3.4 s｜写盘 0.007 s
vector groups       门禁 0.10 s｜读数据 0.10–0.13 s｜归一化 0.02 s｜计算 14.2–18.7 s（dot 13.4–17.8，argpartition 0.46–0.49）｜并查集 0.0008–0.0014 s｜写盘 0.0004 s
vector search       门禁 0.09 s｜读数据 0.10 s｜归一化+查询向量 0.02 s｜计算（点积+top-10）0.008–0.009 s｜写盘 0.000 s
```

**为什么 numpy 的 dot 慢到 355.6 s**：实测 user 342.6 s ≈ wall 348.0 s，即单核跑满——这份 numpy 的 sgemm 没并行，1.07 TFLOP 的矩阵乘（22811×22811×1024×2）折合约 3 GFLOPS。Rust 用 rayon 8 线程 + 手写块化内核跑到 11–17.5 s。换句话说 20–32 倍里既有语言差，也有「numpy 这台机器上单线程 vs rayon 多线程」的并行差，如实记在这里。

## 三、实现与偏差说明

1. **只新增** `src/bin/vector.rs` 与 `Cargo.toml` 的两个依赖（`rayon`、`serde_json`；`Cargo.lock` 随之 +2 行）。`src/main.rs`、`scripts/`、`reference/` 未动（`git diff` 已核）。
2. **算法、阈值、参数照抄**：BLOCK=512、TOPK=10、THRESH=0.90、K=200、SEED=20261011、ITERS=30 写死在常量里；成对去重、argmax 首个最大、空簇保留原质心、簇内均值后重新归一化、`c%03d` 与 `rows.sort(key=(cluster_id, id))` 的行序，都与 Python 版一致。
3. **唯一一处输入级依赖**：k-means 初始化的 200 个质心下标取自 `numpy.random.default_rng(20261011).choice(22811, 200, replace=False)` 的结果，常量化进 `vector.rs`——Rust 侧不实现 PCG64，用同一批初始质心才能对照；随机抽样之后的全部计算都在 Rust 里重写。
4. **内核**：手写块化 f32 点积——外层按 32 行分块 rayon 并行，块内 32×64 的 C 累加数组常驻 L1，B 面板每行连续读 64 个 f32，求和按 q 升序；运行时探测 AVX2+FMA 走手写 intrinsics 内核，不支持则标量。**没有引** ndarray / faer / matrixmultiply。
5. **embeddings.f32 / query_second_brain.f32** 用 `/usr/bin/python3` 各导出一次（前者逐位等于 npy，后者是 ollama `bge-m3` 对「第二大脑 九宫格」的编码），两边共用。`data/` 已 gitignore。
6. **groups 里 dot/argpartition 是重算的**（与 duplicates 同一个函数），为的是在同一处打印三段耗时；重算结果与 `duplicates.rs.tsv` 对账 586 / 586、差集 0，建图用文件里那份对。
7. **诚实记录一次返工**：内核从 gemm 主体抽成独立函数时写盘丢了列偏移 `+ j0`，曾产出 64 对的错误结果；靠与 numpy 逐值对拍定位后修复，上面所有数字都是修复后重跑的。

## 四、复跑命令

```bash
cd /home/iguo/repos/quanttide/domains/quanttide-search/examples/quanttide-search-lab
export PATH=$HOME/.cargo/bin:$PATH

# 一次性导出（已存在可跳过）：npy → 裸 f32；查询向量走 ollama
/usr/bin/python3 -c "
import numpy as np
a = np.load('examples/corpus-linking/data/embeddings.npy')
np.ascontiguousarray(a, dtype='<f4').tofile('examples/corpus-linking/data/embeddings.f32')"

# 门禁（每个子命令内部也会自动跑）
/usr/bin/python3 examples/corpus-linking/scripts/manifest.py --check

cargo build --release --bin vector
./target/release/vector duplicates                                   # → data/duplicates.rs.tsv
./target/release/vector clusters                                     # → data/clusters.rs.tsv
./target/release/vector groups                                       # → data/copy_groups.tsv + copy_groups_stats.json
./target/release/vector search --query-vec examples/corpus-linking/data/query_second_brain.f32

# 对照
md5sum examples/corpus-linking/data/clusters.tsv \
       examples/corpus-linking/data/clusters.rs.tsv                  # 应相同
diff <(sort examples/corpus-linking/data/duplicates.tsv) \
     <(sort examples/corpus-linking/data/duplicates.rs.tsv)           # 只应有分数末位差异

# Python 侧基准（分别约 348 s / 73 s / 2.4 s）
/usr/bin/python3 examples/corpus-linking/scripts/find_duplicates.py
/usr/bin/python3 examples/corpus-linking/scripts/find_clusters.py
/usr/bin/python3 examples/corpus-linking/scripts/search.py "第二大脑 九宫格"
```

## 五、未做条目

- **不写** `similarity_stats.rs.json` 与 clusters 的 summary json：任务只要求三份 tsv 与 `copy_groups` 的两份产出；duplicates / clusters 的对照数字改打印到 stdout。
- **`search.py --check`（校验 A/B）没移植**：它要 122 次 ollama 编码，考的是链路自洽不是数学，本轮的数学对照用同向量 top-10 已覆盖。
- **查询文本编码没移植**（按任务说明走 ollama，语言无关）。
- **`find_clusters.py` 的「抽检素材」打印段没移植**：属报告素材，不参与对照。
- **没调任何阈值 / 参数**（0.90、top-10、k=200、30 轮一律照抄），没引 ANN，没动基线文件——`duplicates.tsv`、`clusters.tsv` 复跑后 md5 均与跑前相同。
- **没提交 git**：本轮只允许 `git status` / `git diff`，提交由维护者处理。
