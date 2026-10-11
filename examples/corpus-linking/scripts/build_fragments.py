#!/usr/bin/env python3
"""阶段 0.1 片段提取：读本地语料，切片段，落盘 data/fragments.tsv。

规则借自 reference/build_eval.py 的 clean_block / extract / collect，
其网络克隆与评测采样部分不采用。全程离线。

用法：
    /usr/bin/python3 scripts/build_fragments.py
"""

import os
import re

DOMAINS_ROOT = os.path.expanduser("~/repos/quanttide/domains")
OUT_TSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "fragments.tsv")

MIN_LEN, MAX_LEN, MIN_CJK = 20, 900, 15

SKIP_DIRS = {".git", ".github", ".agents", ".quanttide", "node_modules", "__pycache__"}
SKIP_FILES = {"readme.md", "changelog.md", "license", "license.md", "contributing.md"}
CJK = re.compile(r"[一-鿿]")


def clean_block(block):
    """清洗单个文本块；不合格返回 None。规则同 reference/build_eval.py。"""
    b = block.strip()
    if not b:
        return None
    lines = [l.strip() for l in b.splitlines() if l.strip()]
    if not lines:
        return None
    if sum(1 for l in lines if l.startswith("|")) > len(lines) * 0.5:
        return None
    if sum(1 for l in lines if l.startswith("#")) > len(lines) * 0.5:
        return None
    stripped = re.sub(r"\[[^\]]*\]\([^)]*\)", "", b)
    stripped = re.sub(r"https?://\S+", "", stripped)
    if len(re.sub(r"\s", "", stripped)) < 20:
        return None
    if len(CJK.findall(b)) < MIN_CJK or not MIN_LEN <= len(b) <= MAX_LEN:
        return None
    if b.count("quanttide-") >= 2 or b.count(".md") >= 2 or b.count("](#") >= 3:
        return None
    if b.rstrip().endswith(("：", ":")) or b.startswith("---"):
        return None
    return re.sub(r"\s+", " ", b).replace("\t", " ").strip()


def extract(path):
    """去 YAML 头、代码块、HTML 注释，按空行切块并清洗。"""
    with open(path, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "\n", text, flags=re.S)
    text = re.sub(r"```.*?```", "\n", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "\n", text, flags=re.S)
    out = []
    for blk in re.split(r"\n\s*\n", text):
        c = clean_block(blk)
        if c:
            out.append(c)
    return out


def md_files(repo_path):
    """按固定顺序遍历仓库内 md 文件，跳过指定目录与文件。"""
    for base, dirs, files in os.walk(repo_path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for fn in sorted(files):
            if fn.lower().endswith((".md", ".markdown")) and fn.lower() not in SKIP_FILES:
                yield os.path.join(base, fn)


def collect():
    """遍历 domains/ 下全部领域仓，收集去重后的片段。"""
    repos = sorted(
        d for d in os.listdir(DOMAINS_ROOT)
        if os.path.isdir(os.path.join(DOMAINS_ROOT, d)) and not d.startswith(".")
    )
    seen, rows = set(), []
    for repo in repos:
        short = repo.replace("quanttide-", "")
        n = 0
        for full in md_files(os.path.join(DOMAINS_ROOT, repo)):
            rel = os.path.relpath(full, os.path.join(DOMAINS_ROOT, repo))
            for b in extract(full):
                key = re.sub(r"\W+", "", b)[:80]
                if key in seen:
                    continue
                seen.add(key)
                n += 1
                rows.append(("%s-%06d" % (short, n), b, "%s#%s" % (repo, rel)))
    return rows


def main():
    rows = collect()
    os.makedirs(os.path.dirname(OUT_TSV), exist_ok=True)
    with open(OUT_TSV, "w", encoding="utf-8") as f:
        f.write("id\ttext\tsource\n")
        for fid, text, source in rows:
            f.write("%s\t%s\t%s\n" % (fid, text, source))
    per_repo = {}
    for _, _, source in rows:
        per_repo[source.split("#")[0]] = per_repo.get(source.split("#")[0], 0) + 1
    print("领域仓数: %d" % len(per_repo))
    print("片段总数: %d -> %s" % (len(rows), OUT_TSV))
    print("片段数最多前 10:")
    for repo, n in sorted(per_repo.items(), key=lambda x: -x[1])[:10]:
        print("  %-28s %6d" % (repo, n))


if __name__ == "__main__":
    main()
