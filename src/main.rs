use std::fs;
use std::path::{Path, PathBuf};
use tantivy::collector::TopDocs;
use tantivy::query::QueryParser;
use tantivy::{doc, schema::{Field, Schema, TextFieldIndexing, IndexRecordOption, TextOptions, Value, STORED, STRING}};
use tantivy::{Index, IndexReader, ReloadPolicy};

fn walk(dir: &Path, out: &mut Vec<PathBuf>) {
    let Ok(rd) = fs::read_dir(dir) else { return };
    for e in rd.flatten() {
        let p = e.path();
        if p.is_dir() {
            let n = p.file_name().unwrap().to_string_lossy().to_string();
            if matches!(n.as_str(), ".git" | "node_modules" | "target" | ".venv") {
                continue;
            }
            walk(&p, out);
        } else if p.extension().is_some_and(|x| x == "md") {
            out.push(p);
        }
    }
}

fn main() {
    let root = std::env::args().nth(1).expect("用法: cargo run --release -- <仓库根> [索引目录] [查询...]");
    let idx_dir = std::env::args().nth(2).unwrap_or_else(|| "search-index".to_string());
    let queries: Vec<String> = std::env::args().skip(3).collect();

    // 1) 建索引
    let mut files = Vec::new();
    walk(Path::new(&root), &mut files);

    let mut sb = Schema::builder();
    let path_f: Field = sb.add_text_field("path", STRING | STORED);
    let indexing = TextFieldIndexing::default()
        .set_tokenizer("jieba")
        .set_index_option(IndexRecordOption::WithFreqsAndPositions);
    let body_f: Field = sb.add_text_field("body", TextOptions::default().set_indexing_options(indexing));
    let schema = sb.build();

    fs::create_dir_all(&idx_dir).unwrap();
    let dir = tantivy::directory::MmapDirectory::open(&idx_dir).unwrap();
    let index = Index::open_or_create(dir, schema).unwrap();
    index
        .tokenizers()
        .register("jieba", tantivy_jieba::JiebaTokenizer::default());

    let mut writer = index.writer(50_000_000).unwrap();
    let mut n = 0usize;
    for p in &files {
        let Ok(body) = fs::read_to_string(p) else { continue };
        let rel = p.strip_prefix(&root).unwrap_or(p).display().to_string();
        writer.add_document(doc!(path_f => rel, body_f => body)).unwrap();
        n += 1;
    }
    writer.commit().unwrap();
    eprintln!("已索引 {n} 个 Markdown 文件 → {idx_dir}");

    // 2) 查询
    let reader: IndexReader = index
        .reader_builder()
        .reload_policy(ReloadPolicy::OnCommitWithDelay)
        .try_into()
        .unwrap();
    let searcher = reader.searcher();
    let parser = QueryParser::for_index(&index, vec![body_f]);

    for q in &queries {
        println!("查询「{q}」");
        let query = parser.parse_query(q).unwrap();
        let top: Vec<(f32, tantivy::DocAddress)> = searcher
            .search(&query, &TopDocs::with_limit(10).order_by_score())
            .unwrap();
        if top.is_empty() {
            println!("  无结果");
        }
        for (score, addr) in top {
            let doc: tantivy::TantivyDocument = searcher.doc(addr).unwrap();
            let path = doc.get_first(path_f).unwrap().as_str().unwrap();
            println!("  {score:8.3}  {path}");
        }
    }
}
