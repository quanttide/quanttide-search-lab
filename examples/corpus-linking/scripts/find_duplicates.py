#!/usr/bin/env python3
"""阶段 1 找重复：对片段向量取高相似对，落盘 duplicates.tsv 与 similarity_stats.json。

算法（先写死，跑完不许改；要改另起一轮并说明）：
    1. 向量按行 L2 归一化，归一化后余弦相似度 = 点积；
    2. 分块计算，块大小 512 行：sim = emb[start:end] @ emb.T，
       一次只开 512×22811 的 float32 块（约 46MB），不一次性开 22811×22811；
    3. 每行去掉自身，取 top-k = 10 最近邻，只保留余弦 >= 0.90 的对；
    4. 成对去重：规范化成 (id_a, id_b) 且 id_a < id_b，同一对只留一次，
       两侧都报到时取分数较大者（对称点积，正常情况下两侧分数相同）；
    5. 按 (id_a, id_b) 升序输出。

前置门禁：先跑 manifest.py --check，指纹不符则拒绝运行并提示重跑阶段 0。

用法：
    /usr/bin/python3 scripts/find_duplicates.py
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
OUT_PAIRS = os.path.join(DATA, "duplicates.tsv")
OUT_STATS = os.path.join(DATA, "similarity_stats.json")

BLOCK = 512
TOPK = 10
THRESH = 0.90


def gate():
    """门禁：manifest --check 不过就拒绝运行。"""
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "manifest.py"), "--check"],
        capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        print("门禁 manifest.py --check 未通过，拒绝运行阶段 1：")
        for line in out.splitlines():
            print("  " + line)
        print("请重跑阶段 0（build_fragments.py → embed.py → manifest.py --write）。")
        sys.exit(1)
    print("门禁通过 —— " + out)
    sys.stdout.flush()


def load_ids_sources():
    with open(IDS, encoding="utf-8") as f:
        next(f)
        ids = [line.rstrip("\n").split("\t")[1] for line in f if line.strip()]
    sources = {}
    with open(FRAGMENTS, encoding="utf-8") as f:
        next(f)
        for line in f:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            sources[parts[0]] = parts[2]
    missing = [i for i in ids if i not in sources]
    if missing:
        print("fragments.tsv 缺 %d 个向量 id（前 5：%s）" % (len(missing), missing[:5]),
              file=sys.stderr)
        sys.exit(1)
    return ids, sources


def main():
    gate()
    ids, sources = load_ids_sources()
    n = len(ids)
    emb = np.load(EMBEDDINGS)
    if emb.shape[0] != n:
        print("向量行数 %d != id 行数 %d，拒绝运行" % (emb.shape[0], n), file=sys.stderr)
        sys.exit(1)
    emb = np.asarray(emb, dtype=np.float32)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    emb = emb / norms
    print("片段 %d 条，向量 %s，块 %d，top-k %d，阈值 %.2f" %
          (n, emb.shape, BLOCK, TOPK, THRESH))

    top1 = np.zeros(n, dtype=np.float64)
    pairs = {}  # (a, b) -> score
    t0 = time.time()
    for start in range(0, n, BLOCK):
        end = min(start + BLOCK, n)
        sim = np.matmul(emb[start:end], emb.T)
        for offset in range(end - start):
            i = start + offset
            row = sim[offset]
            row[i] = -np.inf  # 去掉自身
            top1[i] = row.max()
            k = min(TOPK, n - 1)
            idx = np.argpartition(row, -k)[-k:]
            for j in idx:
                s = float(row[j])
                if s >= THRESH:
                    a, b = (i, j) if i < j else (j, i)
                    if pairs.get((a, b), -1.0) < s:
                        pairs[(a, b)] = s
        if end % (BLOCK * 20) == 0 or end == n:
            print("进度 %d/%d (%.1f%%) 已用 %.0fs" %
                  (end, n, end * 100.0 / n, time.time() - t0), flush=True)

    ordered = sorted(pairs.items())
    with open(OUT_PAIRS, "w", encoding="utf-8") as f:
        f.write("id_a\tid_b\tscore\tsource_a\tsource_b\n")
        for (a, b), s in ordered:
            f.write("%s\t%s\t%.6f\t%s\t%s\n" %
                    (ids[a], ids[b], s, sources[ids[a]], sources[ids[b]]))

    involved = {i for key, _ in ordered for i in key}
    stats = {
        "n_fragments": n,
        "top1_cosine": {
            "p50": float(np.percentile(top1, 50)),
            "p90": float(np.percentile(top1, 90)),
            "p99": float(np.percentile(top1, 99)),
            "max": float(top1.max()),
        },
        "pairs_above_threshold": len(ordered),
        "fragments_in_pairs": len(involved),
        "threshold": THRESH,
        "top_k": TOPK,
        "block_size": BLOCK,
    }
    with open(OUT_STATS, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
        f.write("\n")

    domain = {}
    same_src = 0
    adjacent = 0
    for (a, b) in (k for k, _ in ordered):
        da = sources[ids[a]].split("#")[0]
        db = sources[ids[b]].split("#")[0]
        domain[da == db] = domain.get(da == db, 0) + 1
        if sources[ids[a]] == sources[ids[b]]:
            same_src += 1
            na, nb = int(ids[a].rsplit("-", 1)[1]), int(ids[b].rsplit("-", 1)[1])
            if abs(na - nb) == 1:
                adjacent += 1

    print("对数: %d  参与片段: %d / %d" % (len(ordered), len(involved), n))
    print("跨领域: %d  同领域内: %d" % (domain.get(False, 0), domain.get(True, 0)))
    print("同一文件内: %d  其中序号相邻: %d" % (same_src, adjacent))
    print("top1 余弦 p50=%.4f p90=%.4f p99=%.4f max=%.4f" % (
        stats["top1_cosine"]["p50"], stats["top1_cosine"]["p90"],
        stats["top1_cosine"]["p99"], stats["top1_cosine"]["max"]))
    print("已写 %s" % OUT_PAIRS)
    print("已写 %s" % OUT_STATS)


if __name__ == "__main__":
    main()
