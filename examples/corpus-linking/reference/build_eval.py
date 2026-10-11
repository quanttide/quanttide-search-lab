#!/usr/bin/env python3
"""从领域 docs/ 类仓库采样生成评测集 docs/eval.tsv。

用法：
    python3 scripts/build_eval.py                     # 重建 tsv 中已有类别
    python3 scripts/build_eval.py --categories 元工程,软件工程
    python3 scripts/build_eval.py --all               # category.md 中全部类别
    python3 scripts/build_eval.py --cache /path/dir   # 复用克隆缓存
"""

import argparse
import base64
import collections
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

ORG = "quanttide"
TARGET = 40
SEED = 20261010
MIN_LEN, MAX_LEN, MIN_CJK = 20, 900, 15

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATEGORY_MD = os.path.join(ROOT, "docs", "category.md")
EVAL_TSV = os.path.join(ROOT, "docs", "eval.tsv")

# 根仓库 .gitmodules 未接线、但确属 docs/ 类的仓库
EXTRA_DOCS_REPOS = {
    "知识工程": ["quanttide-specification-of-knowledge-engineering",
                 "quanttide-tutorial-of-knowledge-engineering"],
}

SKIP_DIRS = {".git", ".github", ".agents", ".quanttide", "node_modules", "__pycache__"}
SKIP_FILES = {"changelog.md", "license", "license.md", "contributing.md"}
CJK = re.compile(r"[一-鿿]")


def sh(args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def load_categories():
    """读 docs/category.md，返回 {领域: (英文命名, 根仓库)}。"""
    cats = collections.OrderedDict()
    with open(CATEGORY_MD, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 6 or not cells[4].startswith("`domains/"):
                continue
            cats[cells[1]] = (cells[2].strip("`"), cells[4].strip("`").split("/")[-1])
    return cats


def docs_repos(root_repo, extra):
    """从根仓库 .gitmodules 取 docs/* 子仓库，附加未接线的同类仓库。"""
    content = sh(["gh", "api", "repos/%s/%s/contents/.gitmodules" % (ORG, root_repo),
                  "--jq", ".content"])
    text = base64.b64decode(content.strip()).decode("utf-8")
    names = []
    for block in re.split(r"\n(?=\[submodule)", text):
        path = re.search(r"^\tpath = (docs/\S+)", block, re.M)
        url = re.search(r"^\turl = (\S+)", block, re.M)
        if path and url:
            name = url.group(1).rstrip("/").split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            names.append(name)
    for name in extra:
        if name not in names:
            names.append(name)
    return sorted(set(names))


def clone(cache, name):
    dst = os.path.join(cache, name)
    if os.path.isdir(dst):
        return dst
    p = subprocess.run(["git", "clone", "--depth", "1", "-q",
                        "https://github.com/%s/%s.git" % (ORG, name), dst],
                       capture_output=True, text=True)
    if p.returncode:
        sys.stderr.write("  克隆失败 %s: %s\n" % (name, p.stderr.strip()[:120]))
        return None
    return dst


def clean_block(block):
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


def collect(paths):
    """收集去重后的片段，返回 [(text, repo#path)]；单文件限流交给 sample。"""
    seen, uniq = set(), []
    for path, repo, rel in paths:
        for b in extract(path):
            key = re.sub(r"\W+", "", b)[:80]
            if key in seen:
                continue
            seen.add(key)
            uniq.append((b, "%s#%s" % (repo, rel)))
    return uniq


def sample(uniq, repos, target, seed):
    """跨仓库轮转取样，单文件上限不足时逐级放宽。"""
    def pick(cap):
        by_repo = collections.OrderedDict((r, []) for r in repos)
        per_file = collections.Counter()
        for b, src in uniq:
            repo = src.split("#")[0]
            if repo not in by_repo:
                by_repo[repo] = []
            if per_file[src] < cap:
                by_repo[repo].append((b, src))
                per_file[src] += 1
        rng = random.Random(seed)
        for r in by_repo:
            rng.shuffle(by_repo[r])
        out = []
        while len(out) < target and any(by_repo.values()):
            for r in list(by_repo):
                if by_repo[r] and len(out) < target:
                    out.append(by_repo[r].pop(0))
        return out

    best = []
    for cap in (3, 5, 10, 10 ** 9):
        got = pick(cap)
        if len(got) > len(best):
            best = got
        if len(best) >= target:
            break
    return best


def existing_categories():
    if not os.path.exists(EVAL_TSV):
        return []
    order, seen = [], set()
    with open(EVAL_TSV, encoding="utf-8") as f:
        next(f, None)
        for line in f:
            cat = line.split("\t")[1]
            if cat not in seen:
                seen.add(cat)
                order.append(cat)
    return order


def main():
    ap = argparse.ArgumentParser(description="从领域 docs/ 类仓库采样生成评测集")
    ap.add_argument("--categories", help="逗号分隔的领域名，默认重建 tsv 中已有类别")
    ap.add_argument("--all", action="store_true", help="采样 category.md 中全部类别")
    ap.add_argument("--cache", help="克隆缓存目录，缺省用临时目录")
    ap.add_argument("--target", type=int, default=TARGET, help="每类目标条数")
    args = ap.parse_args()

    cats = load_categories()
    if args.all:
        wanted = list(cats)
    elif args.categories:
        wanted = [c.strip() for c in args.categories.split(",") if c.strip()]
    else:
        wanted = existing_categories()
    unknown = [c for c in wanted if c not in cats]
    if unknown:
        sys.exit("category.md 中没有这些类别: %s" % ", ".join(unknown))

    cache = args.cache or tempfile.mkdtemp(prefix="domain-classifier-")
    rows, stats = [], []
    try:
        for zh in wanted:
            en, root_repo = cats[zh]
            names = docs_repos(root_repo, EXTRA_DOCS_REPOS.get(zh, []))
            paths = []
            for name in names:
                dst = clone(cache, name)
                if not dst:
                    continue
                for base, dirs, files in os.walk(dst):
                    dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                    for fn in sorted(files):
                        if fn.lower().endswith((".md", ".markdown")) and \
                                fn.lower() not in SKIP_FILES:
                            full = os.path.join(base, fn)
                            paths.append((full, name, os.path.relpath(full, dst)))
            uniq = collect(paths)
            picked = sample(uniq, names, args.target, SEED)
            keywords = [zh] + ([en] if en and en != "—" else [])
            stats.append((zh, len(uniq), len(picked),
                          sum(1 for b, _ in picked if any(k in b for k in keywords)),
                          len({s.split("#")[0] for _, s in picked})))
            prefix = root_repo.replace("quanttide-", "")
            for i, (b, src) in enumerate(picked, 1):
                leak = "yes" if any(k in b for k in keywords) else "no"
                rows.append("%s-%03d\t%s\t%s\t%s\t%s" % (prefix, i, zh, b, src, leak))
    finally:
        if not args.cache:
            shutil.rmtree(cache, ignore_errors=True)

    os.makedirs(os.path.dirname(EVAL_TSV), exist_ok=True)
    with open(EVAL_TSV, "w", encoding="utf-8") as f:
        f.write("id\tcategory\ttext\tsource\tname_leak\n")
        f.write("\n".join(rows) + ("\n" if rows else ""))

    print("%-8s %8s %8s %8s %8s" % ("类别", "候选", "采样", "含领域名", "仓库数"))
    for zh, n_uniq, n_pick, n_leak, n_repo in stats:
        print("%-8s %8d %8d %8d %8d" % (zh, n_uniq, n_pick, n_leak, n_repo))
    print("合计 %d 条 -> %s" % (len(rows), os.path.relpath(EVAL_TSV, os.getcwd())))


if __name__ == "__main__":
    main()
