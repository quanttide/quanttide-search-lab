#!/usr/bin/env python3
"""阶段 2 找关联：聚类，只留「跨域主题簇」。

为什么是「跨域主题簇」而不是全量聚类：
    语料本来就按领域仓分好了（`source` 的 `#` 前就是领域仓名），全量聚类只会把
    这份已知结构重算一遍——簇里绝大多数是同一领域仓内的近邻，看不出新东西。要看
    的是**同一主题横跨多个领域**：这才是「找关联」在这份语料上的意义，也是阶段 1
    那 72 对跨域重复的推广——重复是极端情形（几乎一字不差），关联是同一主题的不
    同表述。

算法（先写死，跑完不许改；要改另起一轮并说明）：
    1. 向量按行 L2 归一化，归一化后点积 = 余弦；
    2. 球形 k-means：k = 200；初始化用固定种子 20261011 随机取 k 个样本当质心；
       迭代 30 轮——分配 = argmax(a @ c.T)，更新 = 簇内均值后重新归一化；
       空簇不更新（保留原质心），空簇数如实打印；
    3. 每轮记录「该轮更新、重新分配后的簇内平均余弦」（全体成员与所属质心余弦的
       均值），收敛曲线写进 cluster_summary.json，报告首末两轮；
    4. 只保留成员来自 ≥2 个领域仓的簇，称「跨域主题簇」；
    5. 每簇给一个**代表片段** = 离质心最近的那一条（簇内余弦最大者）。
       不编主题名——机器编的名字是假的，报告里一律写「代表片段」。

k = 200 是写死的先验、不是调出来的；换 k 簇会变，所以结论只当线索、不当定论。

前置门禁：先跑 manifest.py --check，指纹不符拒绝运行。

用法：
    /usr/bin/python3 scripts/find_clusters.py
"""

import json
import os
import subprocess
import sys
import time

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SCRIPTS = os.path.join(BASE, "scripts")
FRAGMENTS = os.path.join(DATA, "fragments.tsv")
EMBEDDINGS = os.path.join(DATA, "embeddings.npy")
IDS = os.path.join(DATA, "embedding_ids.tsv")
OUT_CLUSTERS = os.path.join(DATA, "clusters.tsv")
OUT_SUMMARY = os.path.join(DATA, "cluster_summary.json")

K = 200            # 写死的先验，不是调出来的
SEED = 20261011    # 固定种子，复跑结果必须一致
ITERS = 30
TOPN = 10          # 报告取前几个跨域簇
REP_CHARS = 150    # 报告里代表片段截断字数
SIZE_BUCKETS = [(2, 4), (5, 9), (10, 19), (20, 49), (50, 10 ** 9)]


def gate():
    """门禁：manifest --check 不过就拒绝运行。"""
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "manifest.py"), "--check"],
        capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        print("门禁 manifest.py --check 未通过，拒绝运行阶段 2：")
        for line in out.splitlines():
            print("  " + line)
        print("请重跑阶段 0（build_fragments.py → embed.py → manifest.py --write）。")
        sys.exit(1)
    print("门禁通过 —— " + out)
    sys.stdout.flush()


def load_fragments():
    """读 id 顺序、每条的正文与出处。返回 ids, texts, sources（均按下标对齐向量）。"""
    with open(IDS, encoding="utf-8") as f:
        next(f)
        ids = [line.rstrip("\n").split("\t")[1] for line in f if line.strip()]
    texts, sources = {}, {}
    with open(FRAGMENTS, encoding="utf-8") as f:
        next(f)
        for line in f:
            if not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            texts[p[0]] = p[1]
            sources[p[0]] = p[2]
    missing = [i for i in ids if i not in texts]
    if missing:
        print("fragments.tsv 缺 %d 个向量 id（前 5：%s），拒绝运行"
              % (len(missing), missing[:5]), file=sys.stderr)
        sys.exit(1)
    return ids, [texts[i] for i in ids], [sources[i] for i in ids]


def one_line(text, limit):
    """正文压成单行并截断，报告用。"""
    s = " ".join(text.split())
    return s if len(s) <= limit else s[:limit] + "…"


def main():
    gate()
    ids, texts, sources = load_fragments()
    n = len(ids)
    emb = np.load(EMBEDDINGS)
    if emb.shape[0] != n:
        print("向量行数 %d != id 行数 %d，拒绝运行" % (emb.shape[0], n), file=sys.stderr)
        sys.exit(1)
    emb = np.asarray(emb, dtype=np.float32)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    x = emb / norms  # 1. L2 归一化
    del emb, norms

    # 领域 = source 的 `#` 前
    domain_names = sorted({s.split("#")[0] for s in sources})
    domain_pos = {d: i for i, d in enumerate(domain_names)}
    domain_idx = np.array([domain_pos[s.split("#")[0]] for s in sources])

    print("片段 %d 条，向量 %s，k=%d，seed=%d，迭代 %d 轮，领域仓 %d 个"
          % (n, x.shape, K, SEED, ITERS, len(domain_names)))

    # 2. 初始化：固定种子随机取 k 个样本当质心
    rng = np.random.default_rng(SEED)
    c = x[rng.choice(n, K, replace=False)].copy()

    t0 = time.time()
    assign = (x @ c.T).argmax(axis=1)
    curve = []  # 3. 每轮簇内平均余弦
    for it in range(ITERS):
        c_old = c
        sums = np.zeros_like(c)
        np.add.at(sums, assign, x)          # 更新：簇内均值
        counts = np.bincount(assign, minlength=K)
        empty = counts == 0
        norms = np.linalg.norm(sums, axis=1, keepdims=True)
        norms[empty] = 1.0
        c = sums / norms                    # 重新归一化
        c[empty] = c_old[empty]             # 空簇不更新，保留原质心
        assign = (x @ c.T).argmax(axis=1)
        curve.append(float(np.einsum("ij,ij->i", x, c[assign]).mean()))
        if (it + 1) % 10 == 0 or it == 0:
            print("  第 %2d/%d 轮 簇内平均余弦 %.4f（已用 %.0fs）"
                  % (it + 1, ITERS, curve[-1], time.time() - t0), flush=True)

    member_cos = np.einsum("ij,ij->i", x, c[assign])   # 成员与所属质心的余弦
    sizes = np.bincount(assign, minlength=K)
    domain_total = np.zeros((K, len(domain_names)), dtype=np.int64)
    np.add.at(domain_total, (assign, domain_idx), 1)
    domain_count = np.count_nonzero(domain_total, axis=1)  # 每簇涉及的领域仓个数

    rep = np.full(K, -1, dtype=np.int64)               # 5. 代表片段
    for j in range(K):
        idx = np.flatnonzero(assign == j)
        if idx.size:
            rep[j] = idx[np.argmax(member_cos[idx])]

    cross = np.flatnonzero(domain_count >= 2)          # 4. 跨域主题簇
    n_cross = int(cross.size)
    n_cross_frag = int(sizes[cross].sum())
    empty_list = [int(j) for j in np.flatnonzero(sizes == 0)]

    # ---- data/clusters.tsv ----
    rows = []
    for j in range(K):
        if sizes[j] == 0:
            continue
        for i in np.flatnonzero(assign == j):
            rows.append((j, i))
    rows.sort(key=lambda t: (t[0], ids[t[1]]))
    with open(OUT_CLUSTERS, "w", encoding="utf-8") as f:
        f.write("cluster_id\tid\tsource\tcluster_size\tdomain_count\n")
        for j, i in rows:
            f.write("c%03d\t%s\t%s\t%d\t%d\n"
                    % (j, ids[i], sources[i], sizes[j], domain_count[j]))

    # ---- data/cluster_summary.json ----
    def bucket_label(size):
        for lo, hi in SIZE_BUCKETS:
            if lo <= size <= hi:
                return "%d-%s" % (lo, "inf" if hi > 10 ** 8 else hi)
        return "?"

    by_domain, by_size, by_grid = {}, {}, {}
    for j in cross:
        d, m = int(domain_count[j]), int(sizes[j])
        b = bucket_label(m)
        by_domain[str(d)] = by_domain.get(str(d), 0) + 1
        by_size[b] = by_size.get(b, 0) + 1
        key = "%d|%s" % (d, b)
        by_grid[key] = by_grid.get(key, 0) + 1
    summary = {
        "params": {"k": K, "seed": SEED, "iterations": ITERS,
                   "n_fragments": n, "dim": int(x.shape[1]),
                   "size_buckets": ["%d-%d" % (lo, min(hi, 10 ** 8))
                                    for lo, hi in SIZE_BUCKETS]},
        "clusters_total": K,
        "clusters_nonempty": K - len(empty_list),
        "clusters_empty": empty_list,
        "fragments_assigned": int(sizes.sum()),
        "clusters_cross_domain": n_cross,
        "fragments_in_cross_domain_clusters": n_cross_frag,
        "cross_domain_distribution": {
            "by_domain_count": dict(sorted(by_domain.items(), key=lambda kv: int(kv[0]))),
            "by_cluster_size": by_size,
            "by_domain_count_and_size": dict(sorted(by_grid.items())),
        },
        "mean_intra_cluster_cosine_per_iteration": [round(v, 6) for v in curve],
        "n_domains": len(domain_names),
        "domains": domain_names,
    }
    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # ---- stdout：报告要用的数字 ----
    print("簇 %d 个（非空 %d，空 %d），成员落簇 %d / %d（覆盖率 %.1f%%）"
          % (K, K - len(empty_list), len(empty_list), int(sizes.sum()), n,
             sizes.sum() * 100.0 / n))
    print("簇内平均余弦：第 1 轮 %.4f → 第 %d 轮 %.4f（%d 轮，%.0fs）"
          % (curve[0], ITERS, curve[-1], ITERS, time.time() - t0))
    print("跨域主题簇 %d / %d，覆盖片段 %d / %d（%.1f%%）"
          % (n_cross, K, n_cross_frag, n, n_cross_frag * 100.0 / n))
    print("跨域簇按领域数分布（分母 %d 个跨域簇）：%s"
          % (n_cross, ", ".join("%s 个领域: %d" % (k, v)
                                for k, v in sorted(by_domain.items(), key=lambda kv: int(kv[0])))))

    order = sorted(cross, key=lambda j: (-domain_count[j], -sizes[j], j))
    print("\n前 %d 个跨域簇（按领域数降序，同数按成员数降序）：" % min(TOPN, len(order)))
    for j in order[:TOPN]:
        doms = [domain_names[d] for d in np.flatnonzero(domain_total[j])]
        print("c%03d  领域数 %d  成员 %d  代表 %s"
              % (j, domain_count[j], sizes[j], ids[rep[j]]))
        print("  领域: %s" % ", ".join(doms))
        print("  代表片段: %s" % one_line(texts[rep[j]], REP_CHARS))
        print("  出处: %s" % sources[rep[j]])

    # 抽检素材：与 docs/clusters.md 的抽样规则一致——跨域簇按 cluster_id 升序等距
    # 取 6 个（步长 (n-1)//5），每簇等距取 4 条；另把领域数取下限 2 的簇全部列出，
    # 按 cluster_id 升序各等距取 3 条。
    step = (len(cross) - 1) // 5
    by_id = sorted(cross)                      # cluster_id 升序
    picks = [(by_id[i * step], 4) for i in range(6)]
    low = [(j, 3) for j in sorted(c for c in cross if domain_count[c] == 2)]
    print("\n抽检素材（与 docs/clusters.md 同规则：等距 6 簇 × 4 条 + 领域数 2 的 %d 簇 × 3 条）："
          % len(low))
    for j, k in picks + low:
        idx = np.flatnonzero(assign == j)
        m = len(idx)
        print("c%03d  领域数 %d 成员 %d：" % (j, domain_count[j], sizes[j]))
        for t in [u * m // k for u in range(k)]:
            i = idx[t]
            print("  %s  %s  %s" % (ids[i], sources[i], one_line(texts[i], 70)))

    print("\n已写 %s" % OUT_CLUSTERS)
    print("已写 %s" % OUT_SUMMARY)


if __name__ == "__main__":
    main()
