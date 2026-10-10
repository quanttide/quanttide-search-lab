"""最小 demo：本地仓库全文搜索，SQLite FTS5(trigram) + BM25，零服务零分词。
用法: python3 searchdemo.py build <仓库根> <索引文件>
      python3 searchdemo.py search <索引文件> <查询词>
"""
import sys, os, sqlite3

def md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "target", ".venv"}]
        for f in filenames:
            if f.endswith(".md"):
                yield os.path.join(dirpath, f)

def build(root, db):
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.execute("CREATE VIRTUAL TABLE docs USING fts5(path, body, tokenize='trigram')")
    n = 0
    for p in md_files(root):
        try:
            body = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        con.execute("INSERT INTO docs(path, body) VALUES (?, ?)", (os.path.relpath(p, root), body))
        n += 1
    con.commit()
    print(f"已索引 {n} 个 Markdown 文件 → {db}")

def search(db, q):
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT path, bm25(docs) AS score FROM docs WHERE body MATCH ? ORDER BY score LIMIT 10",
        (q,),
    ).fetchall()
    if not rows:
        print(f"  「{q}」 无结果")
    for path, score in rows:
        print(f"  {score:8.3f}  {path}")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build(sys.argv[2], sys.argv[3])
    else:
        for q in sys.argv[3:]:
            print(f"查询「{q}」")
            search(sys.argv[2], q)
