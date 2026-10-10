# 搜索原型技术笔记

本仓实测数据、选型版本与 API 坑的唯一落点。关键难点在 [index-difficulties.md](index-difficulties.md)，定位与流程在 [README.md](../README.md)。

2026-10-10 本机实测（Linux、Python 3.14、SQLite 3.46.1、rustc 1.93.1）；数据会过时，采信前重跑。

## 当前原型：tantivy + jieba

```
cargo run --release -- <仓库根> [索引目录] [查询...]
```

索引目录默认 `search-index/`（已 gitignore）。

- 实测本仓 6220 篇 Markdown，索引 + 4 个查询 0.48 秒。
- 「新鲜度」命中且领域 README 排第一（BM25 分数 25.113）。
- 两字词「索引」命中、排序正确——这是 FTS5 trigram 做不到的。

## 对照：SQLite FTS5（原型 `searchdemo.py` 已删，结论保留）

- Python 自带 sqlite3，零服务零分词；6189 篇 Markdown 建索引 4.1 秒，命中按 BM25 排序。
- `rg` 只答「有没有」、顺序无含义；FTS5 答「谁最相关」。
- trigram 的坑：查询词不足三字零结果（索引按三字滑窗切）。实测「索引」无结果、「新鲜度」命中——短词要 `LIKE '%词%'` 兜底。

## 选型核实（crates.io / GitHub API，2026-10-10）

- 采用：tantivy 0.26.2（2026-09-08 发布）+ tantivy-jieba 0.21.0（2026-10-06 发布，依赖 `tantivy ^0.26.0`）。
- tantivy 核心分词器只有 simple/raw/ngram/regex/stemmer，**中文必须接第三方**：tantivy-jieba、cang-jie（0.21.0）。
- 排除项带理由：Meilisearch 要起 HTTP 服务（v1.54.3，2026-10-01）、Quickwit 要对象存储（v0.9.1，2026-09-23）、stork 最后提交停在 2023-07-01。

## tantivy 0.26 API 实踩坑（编译期）

- `TopDocs::with_limit(n)` 只是 builder，必须接 `.order_by_score()` 才是 Collector。
- `Searcher::search` 收 `&C`，collector 按引用传。
- 字段指定分词器不能写 `TEXT.set_tokenizer(...)`，要 `TextFieldIndexing::default().set_tokenizer("jieba")` 包进 `TextOptions::default().set_indexing_options(...)`。
- `MmapDirectory::open` 要求目录已存在，先 `fs::create_dir_all`。
