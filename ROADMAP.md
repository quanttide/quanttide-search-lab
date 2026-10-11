# quanttide-search-lab ROADMAP

正式实验的顺序与验收。可动手的细节在 [TODO.md](TODO.md)，实测依据在 [docs/](docs/)，认知依据在洞察仓 `data/insight/default/search-evaluation.md` 与领域路线图 `data/roadmap`（本仓是它们的实验执行层）。

## 顺序

探索优先：手头已有真实查询（`data/paired-sample.jsonl` 60 条配对、`data/search-queries-sample.jsonl` 96 条脱敏查询）和跑通的原型，先跑出第一眼结果；数字有意思，再升级工具（解析五种原始格式、建正式题库）。

1. **跑第一眼**：把配对查询和概念查询对着 tantivy 原型跑，看配对文件排第几、概念查询漏不漏。当天可做，不建题库、不定指标，人眼看结果。
2. **片段对比**：同 20 题两版返回（纯路径 vs 路径 + 片段），人眼判哪版够下一步动作。
3. **决定投入**：第一眼数字有意思——再建正式题库、跑全量 baseline、上查询改写对照；没意思——换猜想或收手。

## 验收约定

- 每个实验给出一条可判定结论，研究记录落 `docs/YYYY-MM-DD-*.md`，数据脱敏落 `data/`
- 结论注明口径与限制
- 建正式题库属于投入升级，见到数字再立项
