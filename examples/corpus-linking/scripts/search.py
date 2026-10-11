#!/usr/bin/python3
"""阶段 3 建索引 + 查询入口。

「建索引」在当前规模下就是「加载向量 + 精确检索」：22811 条 × 1024 维
float32 全量点积实测 13.6 ms/次（/usr/bin/python3 3.14.4 + numpy 2.3.5，
本机实测，见 docs/search.md）。建 ANN 索引（faiss / hnswlib）在 13.6 ms
上省不出时间，只多两个依赖，所以本轮不建——规模上去再议。

流程：manifest.py --check 门禁 → 读 fragments.tsv + embeddings.npy →
L2 归一化（归一化后余弦相似度 = 点积）→ 同一模型 bge-m3 编码查询 →
点积取 top-k。

用法：
    /usr/bin/python3 scripts/search.py "某主题" [--k 10]
    /usr/bin/python3 scripts/search.py --check   # 一致性校验 A/B（出报告用）
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.request

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SCRIPTS = os.path.join(BASE, "scripts")
FRAGMENTS = os.path.join(DATA, "fragments.tsv")
EMBEDDINGS = os.path.join(DATA, "embeddings.npy")
IDS = os.path.join(DATA, "embedding_ids.tsv")
DUPLICATES = os.path.join(DATA, "duplicates.tsv")

URL = "http://127.0.0.1:11434/api/embed"
MODEL = "bge-m3"
DIM = 1024
BATCH = 32

CHECK_SEED = 42   # 校验 A 的固定种子，写死，换种子结果不可比
CHECK_N_A = 50    # 校验 A 的抽样量
CHECK_TOPK = 10   # 校验 B 的 top-k


def gate():
    """门禁：manifest --check 不过就拒绝运行。"""
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "manifest.py"), "--check"],
        capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        print("门禁 manifest.py --check 未通过，拒绝运行阶段 3：", file=sys.stderr)
        for line in out.splitlines():
            print("  " + line, file=sys.stderr)
        print("请重跑阶段 0（build_fragments.py → embed.py → manifest.py --write）。",
              file=sys.stderr)
        sys.exit(1)
    print("门禁通过 —— " + out, file=sys.stderr)


def load_index():
    """读 id 对照、片段正文与出处、向量并 L2 归一化。"""
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
        print("fragments.tsv 缺 %d 个向量 id（前 5：%s），拒绝运行" %
              (len(missing), missing[:5]), file=sys.stderr)
        sys.exit(1)

    emb = np.load(EMBEDDINGS)
    if emb.shape[0] != len(ids) or emb.shape[1] != DIM:
        print("向量 shape %s 与 id 行数 %d / 维度 %d 不符，拒绝运行" %
              (emb.shape, len(ids), DIM), file=sys.stderr)
        sys.exit(1)
    emb = np.asarray(emb, dtype=np.float32)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    emb = emb / norms
    return ids, texts, sources, emb


def encode(texts):
    """用 bge-m3 批量编码；模型不可用或返回异常直接报错退出，不返回空结果糊弄。"""
    out = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i + BATCH]
        payload = json.dumps({"model": MODEL, "input": chunk}).encode("utf-8")
        req = urllib.request.Request(URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print("查询编码失败：连不上 %s（模型 %s）—— %s: %s" %
                  (URL, MODEL, type(e).__name__, e), file=sys.stderr)
            print("请确认 ollama 已启动、已 pull %s，再重跑。" % MODEL, file=sys.stderr)
            sys.exit(1)
        embs = data.get("embeddings")
        if not embs or len(embs) != len(chunk) or any(len(v) != DIM for v in embs):
            print("查询编码失败：返回向量异常（%s）" % str(data)[:300], file=sys.stderr)
            sys.exit(1)
        out.extend(np.asarray(embs, dtype=np.float32))
    q = np.vstack(out)
    norms = np.linalg.norm(q, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return q / norms


def topk_rows(sim, k):
    """sim: (m, n) 分数矩阵。返回每行 top-k 行号（按分数降序）。"""
    n = sim.shape[1]
    k = min(k, n)
    idx = np.argpartition(sim, -k, axis=1)[:, -k:]
    order = np.argsort(np.take_along_axis(sim, idx, axis=1), axis=1)[:, ::-1]
    return np.take_along_axis(idx, order, axis=1)


def run_query(query, k, ids, texts, sources, emb):
    t0 = time.time()
    q = encode([query])
    t1 = time.time()
    scores = emb @ q[0]
    t2 = time.time()
    idx = topk_rows(scores[None, :], k)[0]
    for i in idx:
        preview = re.sub(r"\s+", " ", texts[ids[i]])[:120]
        print("%.6f\t%s\t%s\t%s" % (scores[i], ids[i], sources[ids[i]], preview))
    print("检索 %d / %d 条：编码 %.0f ms，全量点积 %.1f ms，输出 %d 行" %
          (len(ids), len(ids), (t1 - t0) * 1000, (t2 - t1) * 1000, len(idx)),
          file=sys.stderr)


def run_check(ids, texts, sources, emb):
    """校验 A（自洽）与校验 B（对阶段 1 的跨领域重复对）。"""
    n = len(ids)
    row_of = {fid: i for i, fid in enumerate(ids)}

    # A：固定种子取 50 条，用片段自己的正文当查询，看 top-1 是否是它本人
    rng = random.Random(CHECK_SEED)
    rows_a = sorted(rng.sample(range(n), CHECK_N_A))
    qa = encode([texts[ids[i]] for i in rows_a])
    sim_a = qa @ emb.T
    hit_a, miss_a = 0, []
    for r, i in enumerate(rows_a):
        top = int(np.argmax(sim_a[r]))
        if top == i:
            hit_a += 1
        else:
            miss_a.append((ids[i], ids[top], float(sim_a[r][i]), float(sim_a[r][top])))
    print("校验 A（自洽，种子 %d，用自身正文查询，top-1 是本人）：%d / %d" %
          (CHECK_SEED, hit_a, CHECK_N_A))
    for fid, top_id, s_self, s_top in miss_a:
        print("  未命中 %s：top-1 是 %s（本人 %.6f，对方 %.6f）" %
              (fid, top_id, s_self, s_top))

    # B：duplicates.tsv 里跨领域的对，用 A 侧正文查询，看 B 是否落进 top-10
    pairs = []
    with open(DUPLICATES, encoding="utf-8") as f:
        next(f)
        for line in f:
            if not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            if p[3].split("#")[0] != p[4].split("#")[0]:
                pairs.append((p[0], p[1]))
    absent = [(a, b) for a, b in pairs if a not in row_of or b not in row_of]
    usable = [(a, b) for a, b in pairs if a in row_of and b in row_of]
    qb = encode([texts[a] for a, _ in usable])
    sim_b = qb @ emb.T
    kth = CHECK_TOPK
    hit_b, miss_b = 0, []
    for r, (a, b) in enumerate(usable):
        row = sim_b[r]
        threshold = float(np.partition(row, -kth)[-kth])  # top-k 门槛，含并列算命中
        if row[row_of[b]] >= threshold - 1e-6:
            hit_b += 1
        else:
            miss_b.append((a, b, float(row[row_of[b]]), threshold))
    print("校验 B（对阶段 1：跨领域重复对，用 A 侧正文查询，B 落进 top-%d）：%d / %d" %
          (CHECK_TOPK, hit_b, len(usable)))
    if absent:
        print("  另有 %d 对的 id 不在向量表里（前 5：%s），不计入分母" %
              (len(absent), absent[:5]))
    for a, b, s, thr in miss_b[:10]:
        print("  未命中 %s / %s：B 分数 %.6f，top-%d 门槛 %.6f" %
              (a, b, s, CHECK_TOPK, thr))
    if len(miss_b) > 10:
        print("  ……未命中共 %d 对" % len(miss_b))
    print("注意：这 72 对本身是用同一批向量算出来的，属同源——"
          "它只能证明「检索链路通」，不能证明「召回好」。")
    return hit_a, hit_b, len(usable)


def main():
    ap = argparse.ArgumentParser(description="阶段 3 查询入口：余弦 top-k 检索")
    ap.add_argument("query", nargs="?", help="查询文本，如 \"某主题\"")
    ap.add_argument("--k", type=int, default=10, help="返回条数（默认 10）")
    ap.add_argument("--check", action="store_true",
                    help="跑一致性校验 A/B 并打印结果")
    args = ap.parse_args()

    if not args.check:
        if args.query is None:
            print("缺少查询文本。用法：/usr/bin/python3 scripts/search.py \"某主题\" [--k 10]",
                  file=sys.stderr)
            sys.exit(2)
        if not args.query.strip():
            print("查询文本为空，拒绝检索（不返回空结果糊弄）。", file=sys.stderr)
            sys.exit(2)
        if args.k < 1:
            print("--k 必须 >= 1，收到 %d" % args.k, file=sys.stderr)
            sys.exit(2)

    gate()
    ids, texts, sources, emb = load_index()
    if args.check:
        run_check(ids, texts, sources, emb)
    else:
        run_query(args.query, args.k, ids, texts, sources, emb)


if __name__ == "__main__":
    main()
