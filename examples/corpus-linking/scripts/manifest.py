#!/usr/bin/env python3
"""阶段 0.4 语料指纹：把 data/ 三份产物的指纹写进 data/manifest.json，并可逐条核对。

语料是活的：别的会话改一次 domains/，fragments.tsv 就变一次，向量立刻与片段失配。
所以下游（阶段 1 至 3）开跑前先 `manifest.py --check` 核指纹，不符就拒绝运行。

用法：
    /usr/bin/python3 scripts/manifest.py --write   # 写 manifest.json
    /usr/bin/python3 scripts/manifest.py --check   # 逐条比对，不符退出码 1
"""

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SCRIPTS = os.path.join(BASE, "scripts")
FRAGMENTS = os.path.join(DATA, "fragments.tsv")
EMBEDDINGS = os.path.join(DATA, "embeddings.npy")
IDS = os.path.join(DATA, "embedding_ids.tsv")
MANIFEST = os.path.join(DATA, "manifest.json")

MODEL = "bge-m3"
DIM = 1024


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fragment_count(path):
    """fragments.tsv 的数据行数（不含表头）。"""
    with open(path, "rb") as f:
        n = sum(1 for line in f if line.strip())
    return n - 1


def script_md5s():
    """scripts/ 下全部 .py 的 md5，键为文件名。"""
    out = {}
    for fn in sorted(os.listdir(SCRIPTS)):
        if fn.endswith(".py"):
            out[fn] = md5_file(os.path.join(SCRIPTS, fn))
    return out


def build():
    """读三份产物的实况，组装 manifest（不含 generated_at）。"""
    arr = np.load(EMBEDDINGS, mmap_mode="r")
    shape, dtype = list(arr.shape), str(arr.dtype)
    del arr
    return {
        "fragments": {"count": fragment_count(FRAGMENTS), "md5": md5_file(FRAGMENTS)},
        "embeddings": {
            "shape": shape,
            "dtype": dtype,
            "ids_md5": md5_file(IDS),
            "model": MODEL,
            "dim": DIM,
        },
        "scripts": script_md5s(),
    }


def cmd_write():
    manifest = build()
    manifest["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已写 %s" % MANIFEST)
    print("  fragments.count = %d" % manifest["fragments"]["count"])
    print("  fragments.md5   = %s" % manifest["fragments"]["md5"])
    print("  embeddings      = %s %s ids_md5=%s" % (
        manifest["embeddings"]["shape"], manifest["embeddings"]["dtype"],
        manifest["embeddings"]["ids_md5"]))
    print("  scripts         = %d 个 .py" % len(manifest["scripts"]))
    print("  generated_at    = %s" % manifest["generated_at"])


def cmd_check():
    """逐条比对 manifest 与磁盘实况；不一致打印差在哪一项，退出码 1。"""
    if not os.path.exists(MANIFEST):
        print("manifest 不存在：%s（先跑 --write）" % MANIFEST)
        sys.exit(1)
    with open(MANIFEST, encoding="utf-8") as f:
        saved = json.load(f)
    actual = build()
    problems = []

    def cmp(label, want, got):
        if want != got:
            problems.append("%s 不符：manifest=%r，磁盘=%r" % (label, want, got))

    cmp("fragments.count", saved.get("fragments", {}).get("count"),
        actual["fragments"]["count"])
    cmp("fragments.md5", saved.get("fragments", {}).get("md5"),
        actual["fragments"]["md5"])
    for key in ("shape", "dtype", "ids_md5", "model", "dim"):
        cmp("embeddings.%s" % key, saved.get("embeddings", {}).get(key),
            actual["embeddings"][key])
    saved_scripts = saved.get("scripts", {})
    for fn, want in saved_scripts.items():
        got = actual["scripts"].get(fn)
        if got is None:
            problems.append("scripts.%s 不符：manifest 有，磁盘没有" % fn)
        else:
            cmp("scripts.%s" % fn, want, got)
    for fn in actual["scripts"]:
        if fn not in saved_scripts:
            problems.append("scripts.%s 不符：磁盘有，manifest 没有" % fn)

    if problems:
        for p in problems:
            print(p)
        print("指纹不符（共 %d 项），请重跑阶段 0 后再执行下游。" % len(problems))
        sys.exit(1)
    print("manifest --check 通过：fragments %d 条 md5=%s，embeddings %s %s，"
          "scripts %d 个 .py，与磁盘实况一致。" % (
              actual["fragments"]["count"], actual["fragments"]["md5"],
              actual["embeddings"]["shape"], actual["embeddings"]["dtype"],
              len(actual["scripts"])))


def main():
    ap = argparse.ArgumentParser(description="语料指纹写入与核对")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="写 data/manifest.json")
    g.add_argument("--check", action="store_true", help="逐条核对，不符退出码 1")
    args = ap.parse_args()
    if args.write:
        cmd_write()
    else:
        cmd_check()


if __name__ == "__main__":
    main()
