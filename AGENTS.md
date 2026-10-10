# AGENTS

`quanttide-search-lab` 的 AI 工作约定。实验室定位与回流流程的事实源在 [README](README.md)，本文件只记干活时要带着的判据与已核实的技术事实。

## 放什么

- 只放「正式流程之外先试一试」的原型：不留正本、不承载事实源。结论有效就回流领域 `data/` 与 `docs/`，能长期跑的进 `apps/`，无效的删掉。
- 每个实验必须给出一条可判定的结论，不攒无结论的代码。

## 已核实的技术事实（2026-10-10 本机实测）

- 本地全文搜索先用 SQLite FTS5（trigram + BM25），不上向量库、不起服务：`searchdemo.py`，Python 自带 sqlite3，本仓 6189 篇 Markdown 建索引 4.1 秒。
- trigram 的坑：查询词不足三字零结果（索引按三字滑窗切）。实测「索引」无结果、「新鲜度」命中——短词用 `LIKE '%词%'` 兜底。
- 对照基线 `rg`：只答「有没有」，顺序无含义；FTS5 答「谁最相关」（BM25 排序）。
- 二次开发选型（crates.io / GitHub API 核实，2026-10-10）：tantivy 0.26.2（2026-09-08 发布）+ tantivy-jieba 0.21.0（2026-10-06 发布，依赖 `tantivy ^0.26.0`）。tantivy 核心分词器只有 simple/raw/ngram/regex/stemmer，**中文必须接第三方**（tantivy-jieba、cang-jie 0.21.0）。
- 排除项带理由：Meilisearch 要起 HTTP 服务（v1.54.3，2026-10-01）、Quickwit 要对象存储（v0.9.1，2026-09-23）、stork 最后提交停在 2023-07-01。

## tantivy 路线的实踩坑（编译期，0.26 API）

- `TopDocs::with_limit(n)` 只是 builder，必须接 `.order_by_score()` 才是 Collector。
- `Searcher::search` 收 `&C`，collector 按引用传。
- 字段指定分词器不能写 `TEXT.set_tokenizer(...)`，要 `TextFieldIndexing::default().set_tokenizer("jieba")` 包进 `TextOptions::default().set_indexing_options(...)`。
- `MmapDirectory::open` 要求目录已存在，先 `fs::create_dir_all`。
- 状态：原型在 `/tmp/tantivy-demo`，编译通过、尚未跑出结果——**结论待验证，未入仓**，不得当已验证事实引用。

## 提交

提交后直接推送；逐层更新指针：实验室仓 → 领域仓 → 实验室元仓库 → 根仓。
