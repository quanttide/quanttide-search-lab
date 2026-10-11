#!/usr/bin/env python3
"""阶段 0.3 向量化落盘：读 data/fragments.tsv，批量请求本地 ollama /api/embed。

用法：
    /usr/bin/python3 scripts/embed.py --limit 50   # 冒烟
    /usr/bin/python3 scripts/embed.py              # 全量
"""

import argparse
import json
import os
import sys
import time
import urllib.request

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_TSV = os.path.join(BASE, "data", "fragments.tsv")
OUT_NPY = os.path.join(BASE, "data", "embeddings.npy")
OUT_IDS = os.path.join(BASE, "data", "embedding_ids.tsv")

URL = "http://127.0.0.1:11434/api/embed"
MODEL = "bge-m3"
DIM = 1024
BATCH = 32
RETRIES = 3


def embed_batch(texts):
    """请求 /api/embed，返回向量列表；失败抛异常。"""
    payload = json.dumps({"model": MODEL, "input": texts}).encode("utf-8")
    req = urllib.request.Request(URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    embs = data.get("embeddings")
    if embs is None or len(embs) != len(texts):
        raise RuntimeError("返回条数不符: 请求 %d 条，返回 %s" %
                           (len(texts), len(embs) if embs is not None else None))
    return embs


def main():
    ap = argparse.ArgumentParser(description="对 fragments.tsv 批量向量化")
    ap.add_argument("--limit", type=int, help="只处理前 N 条（冒烟）")
    args = ap.parse_args()

    with open(IN_TSV, encoding="utf-8") as f:
        header = next(f)
        assert header.rstrip("\n").split("\t") == ["id", "text", "source"], header
        rows = [line.rstrip("\n").split("\t") for line in f if line.strip()]
    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]
    if args.limit:
        ids, texts = ids[:args.limit], texts[:args.limit]
    n = len(texts)
    print("待向量化片段: %d 条" % n)

    embs = np.zeros((n, DIM), dtype=np.float32)
    failed = []  # (行号, id)
    t0 = time.time()
    for i in range(0, n, BATCH):
        batch_ids = ids[i:i + BATCH]
        batch = texts[i:i + BATCH]
        for attempt in range(1, RETRIES + 1):
            try:
                embs[i:i + len(batch)] = np.asarray(embed_batch(batch), dtype=np.float32)
                break
            except Exception as e:
                if attempt == RETRIES:
                    failed.extend((i + j, fid) for j, fid in enumerate(batch_ids))
                    print("批次 %d-%d 失败（重试 %d 次）: %s" %
                          (i, i + len(batch), RETRIES, e), file=sys.stderr)
                else:
                    time.sleep(2 * attempt)
        done = min(i + BATCH, n)
        if done % (BATCH * 50) == 0 or done == n:
            print("进度 %d/%d (%.1f%%) 已用 %.0fs" %
                  (done, n, done * 100.0 / n, time.time() - t0), flush=True)

    os.makedirs(os.path.dirname(OUT_NPY), exist_ok=True)
    np.save(OUT_NPY, embs)
    with open(OUT_IDS, "w", encoding="utf-8") as f:
        f.write("row\tid\n")
        for row, fid in enumerate(ids):
            f.write("%d\t%s\n" % (row, fid))

    print("向量文件: %s shape=%s dtype=%s" % (OUT_NPY, embs.shape, embs.dtype))
    print("id 对照: %s 共 %d 行" % (OUT_IDS, len(ids)))
    if failed:
        print("失败条目 %d 条（已填零向量，不静默丢）：" % len(failed))
        for row, fid in failed:
            print("  行 %d  %s" % (row, fid))
        sys.exit(1)
    print("失败条目: 0 条")


if __name__ == "__main__":
    main()
