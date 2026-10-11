//! vector —— corpus-linking 计算部分的 Rust 移植。
//!
//! 与 examples/corpus-linking/scripts/ 下的 Python 版逐项对照，算法、阈值、参数
//! 照抄（写死在常量里）：
//!   duplicates  = find_duplicates.py   L2 归一化 → 512 行分块点积 → 每行 top-10
//!                 → 余弦 >= 0.90 → 成对去重 (id_a < id_b)
//!   clusters    = find_clusters.py     球形 k-means k=200 / 种子 20261011 / 30 轮
//!   groups      = 本轮新增             duplicates 的对 → 无向图 → 连通分量 →
//!                 按组横跨领域数分 1 / 2-9 / >=10 三档
//!   search      = search.py 的检索段   给定查询向量，归一化 → 全量点积 → top-10
//!
//! 输入与 Python 版同一份，不重算：data/fragments.tsv、data/embedding_ids.tsv、
//! data/embeddings.npy 导出的裸 f32（data/embeddings.f32）。
//! 每个子命令开跑前先过 scripts/manifest.py --check 门禁，不通过拒绝运行。
//!
//! 用法：
//!   cargo run --release --bin vector -- duplicates
//!   cargo run --release --bin vector -- clusters
//!   cargo run --release --bin vector -- groups
//!   cargo run --release --bin vector -- search --query-vec <f32 文件>

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::fs;
use std::io::{BufWriter, Write};
use std::process::Command;
use std::time::Instant;

use rayon::prelude::*;

// ---------- 写死的参数（与 Python 版一字不差） ----------
const DIM: usize = 1024;
const BLOCK: usize = 512;
const TOPK: usize = 10;
const THRESH: f32 = 0.90;
const K: usize = 200;
const SEED: &str = "20261011";
const ITERS: usize = 30;
const TOPN: usize = 10;
const REP_CHARS: usize = 150;

// ---------- 手写块化 f32 点积的分块参数 ----------
const IC: usize = 32; // C 块行数（累加块常驻 L1）
const JC: usize = 64; // C 块列数（B 面板每行连续读 64 个 f32）

// 球形 k-means 初始化：numpy default_rng(20261011).choice(22811, 200, replace=False)
// 的结果。Rust 侧不实现 PCG64，故把种子抽出的下标常量化，保证与 Python 同一批质心。
const INIT_IDX: [usize; 200] = [
    15601, 22777, 4120, 13640, 19147, 10334, 3008, 14586, 17470, 18820, 5518, 15250, 7098, 10005,
    10453, 15273, 21970, 13422, 13078, 8722, 7720, 18903, 22744, 7782, 19583, 18600, 7540, 22808,
    15536, 19236, 16318, 20341, 19095, 11966, 9613, 940, 10129, 15436, 18505, 3052, 1486, 3822,
    10936, 409, 10160, 7800, 19078, 19973, 523, 9990, 16020, 8223, 14734, 15817, 17046, 14675,
    15302, 11366, 15584, 5644, 4856, 10082, 14202, 3833, 9830, 6104, 5217, 7326, 15706, 6191, 439,
    1948, 12202, 17549, 21823, 7432, 22560, 14861, 4701, 9686, 1682, 14254, 21240, 19646, 275,
    17862, 17064, 19619, 15694, 14683, 14322, 11086, 14355, 2456, 103, 20060, 7402, 12602, 17807,
    1453, 19048, 11579, 14915, 6199, 22577, 20957, 6073, 8497, 3188, 19629, 2662, 22337, 14811,
    4031, 6453, 17758, 15039, 9244, 1365, 13198, 2265, 13077, 20329, 13722, 13514, 3484, 17905,
    3198, 8738, 11932, 5999, 20067, 4149, 18024, 10462, 11655, 19877, 17667, 5791, 5368, 4561,
    21208, 17442, 9228, 6746, 15362, 19108, 21522, 3102, 9718, 12198, 15975, 18224, 10622, 829,
    7228, 14976, 21718, 15175, 17494, 16944, 13222, 16236, 1286, 11290, 13628, 4653, 10161, 8576,
    12775, 16064, 19879, 4014, 14826, 17963, 8919, 16893, 4804, 5162, 16990, 16199, 16416, 281,
    9645, 2180, 10822, 2160, 2854, 19273, 21419, 14151, 9666, 16822, 20633, 22141, 18054, 20062,
    10931, 10768, 7250,
];

fn wd() -> String {
    format!("{}/examples/corpus-linking", env!("CARGO_MANIFEST_DIR"))
}
fn data_dir() -> String {
    format!("{}/data", wd())
}
fn path_of(name: &str) -> String {
    format!("{}/{}", data_dir(), name)
}

fn die(msg: &str) -> ! {
    eprintln!("{msg}");
    std::process::exit(1);
}

fn ms(d: std::time::Duration) -> f64 {
    d.as_secs_f64() * 1000.0
}

// ---------- 门禁：manifest.py --check ----------
fn gate(to_stderr: bool) -> std::time::Duration {
    let emit = |msg: String| {
        if to_stderr {
            eprintln!("{msg}");
        } else {
            println!("{msg}");
        }
    };
    let t = Instant::now();
    let script = format!("{}/scripts/manifest.py", wd());
    let out = Command::new("/usr/bin/python3")
        .arg(&script)
        .arg("--check")
        .output()
        .unwrap_or_else(|e| die(&format!("无法执行 {script}：{e}")));
    let mut text = String::from_utf8_lossy(&out.stdout).into_owned();
    text.push_str(&String::from_utf8_lossy(&out.stderr));
    if !out.status.success() {
        emit("门禁 manifest.py --check 未通过，拒绝运行：".to_string());
        for line in text.lines() {
            emit(format!("  {line}"));
        }
        emit("请重跑阶段 0（build_fragments.py → embed.py → manifest.py --write）。".to_string());
        std::process::exit(1);
    }
    emit(format!("门禁通过 —— {}", text.trim()));
    t.elapsed()
}

// ---------- 语料读取（与 Python 版同一份输入） ----------
struct Corpus {
    ids: Vec<String>,
    texts: Vec<String>,
    sources: Vec<String>,
}

fn load_ids() -> Vec<String> {
    let p = path_of("embedding_ids.tsv");
    let s = fs::read_to_string(&p).unwrap_or_else(|e| die(&format!("读 {p} 失败：{e}")));
    let mut ids = Vec::new();
    for (i, line) in s.lines().enumerate() {
        if i == 0 {
            continue; // 表头
        }
        if line.trim().is_empty() {
            continue;
        }
        let id = line
            .split('\t')
            .nth(1)
            .unwrap_or_else(|| die(&format!("{p} 第 {} 行缺第 2 列", i + 1)));
        ids.push(id.to_string());
    }
    ids
}

fn load_corpus() -> Corpus {
    let ids = load_ids();
    let p = path_of("fragments.tsv");
    let s = fs::read_to_string(&p).unwrap_or_else(|e| die(&format!("读 {p} 失败：{e}")));
    let mut map: HashMap<&str, (&str, &str)> = HashMap::new();
    for (i, line) in s.lines().enumerate() {
        if i == 0 {
            continue; // 表头
        }
        if line.trim().is_empty() {
            continue;
        }
        let mut it = line.split('\t');
        let id = it
            .next()
            .unwrap_or_else(|| die(&format!("{p} 第 {} 行缺列", i + 1)));
        let text = it
            .next()
            .unwrap_or_else(|| die(&format!("{p} 第 {} 行缺 text", i + 1)));
        let source = it
            .next()
            .unwrap_or_else(|| die(&format!("{p} 第 {} 行缺 source", i + 1)));
        map.insert(id, (text, source));
    }
    let missing: Vec<&String> = ids
        .iter()
        .filter(|i| !map.contains_key(i.as_str()))
        .collect();
    if !missing.is_empty() {
        die(&format!(
            "fragments.tsv 缺 {} 个向量 id（前 5：{:?}）",
            missing.len(),
            &missing[..missing.len().min(5)]
        ));
    }
    let mut texts = Vec::with_capacity(ids.len());
    let mut sources = Vec::with_capacity(ids.len());
    for id in &ids {
        let (t, s) = map[id.as_str()];
        texts.push(t.to_string());
        sources.push(s.to_string());
    }
    Corpus {
        ids,
        texts,
        sources,
    }
}

fn read_embeddings(n: usize) -> Vec<f32> {
    let p = path_of("embeddings.f32");
    let bytes = fs::read(&p).unwrap_or_else(|e| die(&format!("读 {p} 失败：{e}")));
    if bytes.len() != n * DIM * 4 {
        die(&format!(
            "embeddings.f32 大小 {} 字节，与 {} 条 × {} 维 × 4 不符",
            bytes.len(),
            n,
            DIM
        ));
    }
    let mut v = Vec::with_capacity(n * DIM);
    for c in bytes.chunks_exact(4) {
        v.push(f32::from_le_bytes([c[0], c[1], c[2], c[3]]));
    }
    v
}

/// 行 L2 归一化；零向量保持原样（norm 用 1 顶替），与 Python 版一致。
fn normalize(x: &mut [f32], n: usize) {
    for i in 0..n {
        let row = &mut x[i * DIM..(i + 1) * DIM];
        let mut acc = 0f32;
        for &v in row.iter() {
            acc += v * v;
        }
        let norm = acc.sqrt();
        let d = if norm == 0.0 { 1.0 } else { norm };
        for v in row.iter_mut() {
            *v /= d;
        }
    }
}

fn domain_of(source: &str) -> &str {
    source.split('#').next().unwrap_or(source)
}

// ---------- 手写块化 f32 点积 ----------
/// 转置成 DIM × stride（行主序，每行末尾补 JC 个 0），微内核按列连续读。
fn transpose_padded(x: &[f32], n: usize) -> (Vec<f32>, usize) {
    let stride = n + JC;
    let mut bt = vec![0f32; DIM * stride];
    for k in 0..DIM {
        let dst = &mut bt[k * stride..k * stride + n];
        for (i, d) in dst.iter_mut().enumerate() {
            *d = x[i * DIM + k];
        }
    }
    (bt, stride)
}

/// out（rows × cols，行主序）= x[i0 .. i0+rows] × bt^T。
/// 分块：外层按 IC 行分块并行，块内 C 累加数组（IC × JC，8KB）常驻 L1，
/// B 面板每行连续 JC 个 f32；内核优先走手写 AVX2+FMA，不支持时走标量。
fn gemm(
    x: &[f32],
    n: usize,
    bt: &[f32],
    stride: usize,
    cols: usize,
    i0: usize,
    rows: usize,
    out: &mut [f32],
) {
    debug_assert_eq!(out.len(), rows * cols);
    out.fill(0.0);
    let use_avx = avx_ok();
    out.par_chunks_mut(IC * cols)
        .enumerate()
        .for_each(|(it, chunk)| {
            let rb = it * IC;
            let m_len = chunk.len() / cols;
            let ib = i0 + rb;
            if ib >= n || m_len == 0 {
                return;
            }
            for j0 in (0..cols).step_by(JC) {
                let jc = JC.min(cols - j0);
                #[cfg(target_arch = "x86_64")]
                {
                    if use_avx {
                        unsafe { tile_avx(x, ib, m_len, bt, stride, j0, jc, chunk, cols) };
                        continue;
                    }
                }
                tile_scalar(x, ib, m_len, bt, stride, j0, jc, chunk, cols);
            }
        });
}

/// 标量内核：q 升序累加（与 Python 版求和同序）。
fn tile_scalar(
    x: &[f32],
    ib: usize,
    m_len: usize,
    bt: &[f32],
    stride: usize,
    j0: usize,
    jc: usize,
    dst: &mut [f32],
    cols: usize,
) {
    let mut cbuf = [[0f32; JC]; IC];
    for q in 0..DIM {
        let brow = &bt[q * stride + j0..q * stride + j0 + JC];
        for m in 0..m_len {
            let a = x[(ib + m) * DIM + q];
            let cb = &mut cbuf[m];
            for r in 0..JC {
                cb[r] += a * brow[r];
            }
        }
    }
    for m in 0..m_len {
        let d = &mut dst[m * cols + j0..m * cols + j0 + jc];
        for r in 0..jc {
            d[r] = cbuf[m][r];
        }
    }
}

#[cfg(target_arch = "x86_64")]
fn avx_ok() -> bool {
    std::arch::is_x86_feature_detected!("avx2") && std::arch::is_x86_feature_detected!("fma")
}
#[cfg(not(target_arch = "x86_64"))]
fn avx_ok() -> bool {
    false
}

/// 手写 AVX2+FMA 内核：每拍 8 个 f32 乘加。
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2,fma")]
unsafe fn tile_avx(
    x: &[f32],
    ib: usize,
    m_len: usize,
    bt: &[f32],
    stride: usize,
    j0: usize,
    jc: usize,
    dst: &mut [f32],
    cols: usize,
) {
    use std::arch::x86_64::*;
    let mut cbuf = [[0f32; JC]; IC];
    for q in 0..DIM {
        let brow = &bt[q * stride + j0..q * stride + j0 + JC];
        let bp = brow.as_ptr();
        for m in 0..m_len {
            let av = _mm256_set1_ps(x[(ib + m) * DIM + q]);
            let cp = cbuf[m].as_mut_ptr();
            for r in 0..JC / 8 {
                let bv = _mm256_loadu_ps(bp.add(r * 8));
                let cv = _mm256_loadu_ps(cp.add(r * 8));
                _mm256_storeu_ps(cp.add(r * 8), _mm256_fmadd_ps(av, bv, cv));
            }
        }
    }
    for m in 0..m_len {
        let d = &mut dst[m * cols + j0..m * cols + j0 + jc];
        for r in 0..jc {
            d[r] = cbuf[m][r];
        }
    }
}

fn dot(a: &[f32], b: &[f32]) -> f32 {
    let mut acc = 0f32;
    for k in 0..DIM {
        acc += a[k] * b[k];
    }
    acc
}

/// 每行 top-k（分数降序，去自身），另给该行最大值。与 np.argpartition(...)[-k:] 等价。
fn topk_excluding_self(row: &[f32], i: usize, k: usize) -> (Vec<(usize, f32)>, f32) {
    let mut top: Vec<(f32, usize)> = Vec::with_capacity(k);
    let mut max = f32::NEG_INFINITY;
    for (j, &s) in row.iter().enumerate() {
        if j == i {
            continue;
        }
        if s > max {
            max = s;
        }
        if top.len() < k {
            top.push((s, j));
            let mut p = top.len() - 1;
            while p > 0 && top[p].0 < top[p - 1].0 {
                top.swap(p, p - 1);
                p -= 1;
            }
        } else if s > top[0].0 {
            top[0] = (s, j);
            let mut p = 0usize;
            loop {
                let l = 2 * p + 1;
                let r = l + 1;
                let mut m = p;
                if l < top.len() && top[l].0 < top[m].0 {
                    m = l;
                }
                if r < top.len() && top[r].0 < top[m].0 {
                    m = r;
                }
                if m == p {
                    break;
                }
                top.swap(p, m);
                p = m;
            }
        }
    }
    top.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal)); // 分数降序
    (top.into_iter().map(|(s, j)| (j, s)).collect(), max)
}

/// numpy percentile 线性插值（method='linear'）。
fn percentile(sorted: &[f32], p: f64) -> f64 {
    let n = sorted.len() as f64;
    let pos = p / 100.0 * (n - 1.0);
    let lo = pos.floor() as usize;
    let hi = pos.ceil() as usize;
    let frac = pos - lo as f64;
    sorted[lo] as f64 * (1.0 - frac) + sorted[hi] as f64 * frac
}

/// duplicates / groups 共用：分块点积 → 每行 top-k → 余弦阈值 → 成对去重。
/// 返回 (候选对, top1 数组, dot 耗时 ms, argpartition 耗时 ms)。
fn compute_pairs(x: &[f32], n: usize) -> (Vec<(usize, usize, f32)>, Vec<f32>, f64, f64) {
    let t_dot = Instant::now();
    let (bt, stride) = transpose_padded(x, n);
    let mut top1 = vec![0f32; n];
    let mut cand: Vec<(usize, usize, f32)> = Vec::new();
    let mut dot_ms = 0.0;

    let t_topk = Instant::now();
    for b0 in (0..n).step_by(BLOCK) {
        let rows = BLOCK.min(n - b0);
        let end = b0 + rows;
        let mut sim = vec![0f32; rows * n];
        let tb = Instant::now();
        gemm(x, n, &bt, stride, n, b0, rows, &mut sim);
        dot_ms += ms(tb.elapsed());

        let row_res: Vec<(f32, Vec<(usize, usize, f32)>)> = sim
            .par_chunks(n)
            .enumerate()
            .map(|(off, row)| {
                let i = b0 + off;
                let (top, max) = topk_excluding_self(row, i, TOPK.min(n - 1));
                let mut pairs = Vec::new();
                for (j, s) in top {
                    if s >= THRESH {
                        let (a, b) = if i < j { (i, j) } else { (j, i) };
                        pairs.push((a, b, s));
                    }
                }
                (max, pairs)
            })
            .collect();
        for (off, (max, pairs)) in row_res.into_iter().enumerate() {
            top1[b0 + off] = max;
            cand.extend(pairs);
        }
        if end % (BLOCK * 20) == 0 || end == n {
            println!(
                "进度 {}/{} ({:.1}%) 已用 {:.0}s",
                end,
                n,
                end as f64 * 100.0 / n as f64,
                t_dot.elapsed().as_secs_f64()
            );
        }
    }
    let topk_ms = ms(t_topk.elapsed()) - dot_ms;
    (cand, top1, dot_ms, topk_ms.max(0.0))
}

/// 规范成 (id_a < id_b) 并按 (a, b) 升序去重，两侧都报到取分数大者。
fn dedup_pairs(cand: &mut Vec<(usize, usize, f32)>) -> Vec<(usize, usize, f32)> {
    cand.sort_by_key(|e| (e.0, e.1));
    let mut ordered: Vec<(usize, usize, f32)> = Vec::with_capacity(cand.len());
    for e in cand.drain(..) {
        match ordered.last_mut() {
            Some(l) if l.0 == e.0 && l.1 == e.1 => {
                if e.2 > l.2 {
                    l.2 = e.2;
                }
            }
            _ => ordered.push(e),
        }
    }
    ordered
}

// ---------- 子命令 1：duplicates ----------
fn cmd_duplicates() {
    let t_gate = gate(false);
    let t0 = Instant::now();
    let corpus = load_corpus();
    let n = corpus.ids.len();
    let mut x = read_embeddings(n);
    let t_read = t0.elapsed();

    let t1 = Instant::now();
    normalize(&mut x, n);
    let t_norm = t1.elapsed();

    println!(
        "片段 {} 条，向量 ({}, {})，块 {}，top-k {}，阈值 {:.2}",
        n, n, DIM, BLOCK, TOPK, THRESH
    );

    let t_calc = Instant::now();
    let (mut cand, top1, dot_ms, topk_ms) = compute_pairs(&x, n);
    let ordered = dedup_pairs(&mut cand);
    let t_calc = t_calc.elapsed();

    let t_write = Instant::now();
    let out = path_of("duplicates.rs.tsv");
    {
        let f = fs::File::create(&out).unwrap_or_else(|e| die(&format!("写 {out} 失败：{e}")));
        let mut w = BufWriter::new(f);
        writeln!(w, "id_a\tid_b\tscore\tsource_a\tsource_b").unwrap();
        for &(a, b, s) in &ordered {
            writeln!(
                w,
                "{}\t{}\t{:.6}\t{}\t{}",
                corpus.ids[a], corpus.ids[b], s, corpus.sources[a], corpus.sources[b]
            )
            .unwrap();
        }
        w.flush().unwrap();
    }
    let t_write = t_write.elapsed();

    // ---- stdout：与 Python 版同一批对照数字 ----
    let mut involved: HashSet<usize> = HashSet::new();
    let (mut cross, mut same_domain) = (0usize, 0usize);
    let (mut same_src, mut adjacent) = (0usize, 0usize);
    for &(a, b, _) in &ordered {
        involved.insert(a);
        involved.insert(b);
        let (sa, sb) = (&corpus.sources[a], &corpus.sources[b]);
        if domain_of(sa) == domain_of(sb) {
            same_domain += 1;
        } else {
            cross += 1;
        }
        if sa == sb {
            same_src += 1;
            let na: i64 = corpus.ids[a].rsplit('-').next().unwrap().parse().unwrap();
            let nb: i64 = corpus.ids[b].rsplit('-').next().unwrap().parse().unwrap();
            if (na - nb).abs() == 1 {
                adjacent += 1;
            }
        }
    }
    let mut sorted_top1 = top1;
    sorted_top1.sort_by(|a, b| a.partial_cmp(b).unwrap());
    println!(
        "对数: {}  参与片段: {} / {}",
        ordered.len(),
        involved.len(),
        n
    );
    println!("跨领域: {cross}  同领域内: {same_domain}");
    println!("同一文件内: {same_src}  其中序号相邻: {adjacent}");
    println!(
        "top1 余弦 p50={:.4} p90={:.4} p99={:.4} max={:.4}",
        percentile(&sorted_top1, 50.0),
        percentile(&sorted_top1, 90.0),
        percentile(&sorted_top1, 99.0),
        *sorted_top1.last().unwrap()
    );
    println!("已写 {out}");
    print_timings(&[
        ("门禁", ms(t_gate)),
        ("读数据", ms(t_read)),
        ("归一化", ms(t_norm)),
        ("计算", ms(t_calc)),
        ("  └ dot（块化点积）", dot_ms),
        ("  └ argpartition（top-k + 阈值 + 去重）", topk_ms),
        ("写盘", ms(t_write)),
    ]);
    println!(
        "[耗时] 合计（不含门禁）{:.1} ms，含门禁 {:.1} ms",
        ms(t_read) + ms(t_norm) + ms(t_calc) + ms(t_write),
        ms(t_gate) + ms(t_read) + ms(t_norm) + ms(t_calc) + ms(t_write)
    );
}

fn print_timings(rows: &[(&str, f64)]) {
    println!("---- 耗时分解 ----");
    for (name, v) in rows {
        println!("[耗时] {:<34} {:>10.1} ms", name, v);
    }
}

fn print_timings_err(rows: &[(&str, f64)]) {
    eprintln!("---- 耗时分解 ----");
    for (name, v) in rows {
        eprintln!("[耗时] {:<34} {:>10.1} ms", name, v);
    }
}

// ---------- 子命令 2：clusters ----------
fn argmax_rows(out: &[f32], cols: usize) -> Vec<usize> {
    out.par_chunks(cols)
        .map(|row| {
            let mut bi = 0usize;
            let mut bs = row[0];
            for j in 1..cols {
                if row[j] > bs {
                    bs = row[j];
                    bi = j;
                }
            }
            bi
        })
        .collect()
}

fn one_line(text: &str, limit: usize) -> String {
    let mut out = String::new();
    let mut in_ws = false;
    for ch in text.chars() {
        if ch.is_whitespace() {
            if !in_ws {
                out.push(' ');
                in_ws = true;
            }
        } else {
            out.push(ch);
            in_ws = false;
        }
    }
    if out.chars().count() <= limit {
        out
    } else {
        out.chars().take(limit).collect::<String>() + "…"
    }
}

fn cmd_clusters() {
    let t_gate = gate(false);
    let t0 = Instant::now();
    let corpus = load_corpus();
    let n = corpus.ids.len();
    let mut x = read_embeddings(n);
    let t_read = t0.elapsed();

    let t1 = Instant::now();
    normalize(&mut x, n);
    let t_norm = t1.elapsed();

    // 领域 = source 的 `#` 前，按字典序编号（与 Python sorted(set(...)) 一致）
    let mut domain_names: BTreeSet<&str> = BTreeSet::new();
    for s in &corpus.sources {
        domain_names.insert(domain_of(s));
    }
    let domain_names: Vec<&str> = domain_names.into_iter().collect();
    let domain_pos: HashMap<&str, usize> = domain_names
        .iter()
        .enumerate()
        .map(|(i, d)| (*d, i))
        .collect();
    let domain_idx: Vec<usize> = corpus
        .sources
        .iter()
        .map(|s| domain_pos[domain_of(s)])
        .collect();

    println!(
        "片段 {} 条，向量 ({}, {})，k={}，seed={}，迭代 {} 轮，领域仓 {} 个",
        n,
        n,
        DIM,
        K,
        SEED,
        ITERS,
        domain_names.len()
    );

    let t_calc = Instant::now();
    // 初始化：固定种子抽出的 k 个样本当质心
    let mut c: Vec<f32> = INIT_IDX
        .iter()
        .flat_map(|&i| x[i * DIM..(i + 1) * DIM].to_vec())
        .collect();
    let mut scores = vec![0f32; n * K];
    let (ctp, cstride) = transpose_padded(&c, K);
    gemm(&x, n, &ctp, cstride, K, 0, n, &mut scores);
    let mut assign = argmax_rows(&scores, K);

    let mut curve: Vec<f64> = Vec::with_capacity(ITERS);
    let mut t_iter = Instant::now();
    for it in 0..ITERS {
        // 更新：簇内均值（按行号升序累加，与 np.add.at 同序）后重新归一化
        let mut sums = vec![0f32; K * DIM];
        for i in 0..n {
            let a = assign[i];
            let src = &x[i * DIM..(i + 1) * DIM];
            let dst = &mut sums[a * DIM..(a + 1) * DIM];
            for k in 0..DIM {
                dst[k] += src[k];
            }
        }
        let mut counts = vec![0usize; K];
        for &a in &assign {
            counts[a] += 1;
        }
        let c_old = c;
        let mut c_new = sums;
        for j in 0..K {
            if counts[j] == 0 {
                continue; // 空簇不更新，最后用 c_old 覆盖
            }
            let row = &mut c_new[j * DIM..(j + 1) * DIM];
            let mut acc = 0f32;
            for &v in row.iter() {
                acc += v * v;
            }
            let nn = acc.sqrt();
            for v in row.iter_mut() {
                *v /= nn;
            }
        }
        for j in 0..K {
            if counts[j] == 0 {
                c_new[j * DIM..(j + 1) * DIM].copy_from_slice(&c_old[j * DIM..(j + 1) * DIM]);
            }
        }
        c = c_new;
        // 重新分配
        let (ctp2, cstride2) = transpose_padded(&c, K);
        gemm(&x, n, &ctp2, cstride2, K, 0, n, &mut scores);
        assign = argmax_rows(&scores, K);
        // 该轮簇内平均余弦
        let mut acc = 0f64;
        for i in 0..n {
            acc += dot(
                &x[i * DIM..(i + 1) * DIM],
                &c[assign[i] * DIM..(assign[i] + 1) * DIM],
            ) as f64;
        }
        curve.push(acc / n as f64);
        if (it + 1) % 10 == 0 || it == 0 {
            println!(
                "  第 {:>2}/{} 轮 簇内平均余弦 {:.4}（已用 {:.0}s）",
                it + 1,
                ITERS,
                curve.last().unwrap(),
                t_iter.elapsed().as_secs_f64()
            );
            t_iter = Instant::now();
        }
    }

    // 收尾统计
    let mut member_cos = vec![0f32; n];
    for i in 0..n {
        member_cos[i] = dot(
            &x[i * DIM..(i + 1) * DIM],
            &c[assign[i] * DIM..(assign[i] + 1) * DIM],
        );
    }
    let mut sizes = vec![0usize; K];
    let mut domain_total = vec![vec![0usize; domain_names.len()]; K];
    for i in 0..n {
        sizes[assign[i]] += 1;
        domain_total[assign[i]][domain_idx[i]] += 1;
    }
    let domain_count: Vec<usize> = domain_total
        .iter()
        .map(|v| v.iter().filter(|&&x| x > 0).count())
        .collect();
    let mut rep = vec![usize::MAX; K];
    for i in 0..n {
        let a = assign[i];
        if rep[a] == usize::MAX || member_cos[i] > member_cos[rep[a]] {
            rep[a] = i;
        }
    }
    let t_calc = t_calc.elapsed();

    let t_write = Instant::now();
    let out = path_of("clusters.rs.tsv");
    {
        let mut rows: Vec<(usize, usize)> = (0..n).map(|i| (assign[i], i)).collect();
        rows.sort_by(|a, b| {
            a.0.cmp(&b.0)
                .then_with(|| corpus.ids[a.1].cmp(&corpus.ids[b.1]))
        });
        let f = fs::File::create(&out).unwrap_or_else(|e| die(&format!("写 {out} 失败：{e}")));
        let mut w = BufWriter::new(f);
        writeln!(w, "cluster_id\tid\tsource\tcluster_size\tdomain_count").unwrap();
        for &(j, i) in &rows {
            writeln!(
                w,
                "c{:03}\t{}\t{}\t{}\t{}",
                j, corpus.ids[i], corpus.sources[i], sizes[j], domain_count[j]
            )
            .unwrap();
        }
        w.flush().unwrap();
    }
    let t_write = t_write.elapsed();

    // ---- stdout：与 Python 版同一批对照数字 ----
    let empty: Vec<usize> = (0..K).filter(|&j| sizes[j] == 0).collect();
    let assigned: usize = sizes.iter().sum();
    let cross: Vec<usize> = (0..K).filter(|&j| domain_count[j] >= 2).collect();
    let n_cross_frag: usize = cross.iter().map(|&j| sizes[j]).sum();
    println!(
        "簇 {} 个（非空 {}，空 {}），成员落簇 {} / {}（覆盖率 {:.1}%）",
        K,
        K - empty.len(),
        empty.len(),
        assigned,
        n,
        assigned as f64 * 100.0 / n as f64
    );
    println!(
        "簇内平均余弦：第 1 轮 {:.4} → 第 {} 轮 {:.4}（{} 轮）",
        curve[0],
        ITERS,
        curve[ITERS - 1],
        ITERS
    );
    println!(
        "跨域主题簇 {} / {}，覆盖片段 {} / {}（{:.1}%）",
        cross.len(),
        K,
        n_cross_frag,
        n,
        n_cross_frag as f64 * 100.0 / n as f64
    );
    let mut by_domain: BTreeMap<usize, usize> = BTreeMap::new();
    for &j in &cross {
        *by_domain.entry(domain_count[j]).or_default() += 1;
    }
    println!(
        "跨域簇按领域数分布（分母 {} 个跨域簇）：{}",
        cross.len(),
        by_domain
            .iter()
            .map(|(k, v)| format!("{k} 个领域: {v}"))
            .collect::<Vec<_>>()
            .join(", ")
    );
    let mut order: Vec<usize> = cross.clone();
    order.sort_by(|&a, &b| {
        domain_count[b]
            .cmp(&domain_count[a])
            .then_with(|| sizes[b].cmp(&sizes[a]))
            .then_with(|| a.cmp(&b))
    });
    println!(
        "\n前 {} 个跨域簇（按领域数降序，同数按成员数降序）：",
        order.len().min(TOPN)
    );
    for &j in order.iter().take(TOPN) {
        let doms: Vec<&str> = domain_names
            .iter()
            .enumerate()
            .filter(|&(d, _)| domain_total[j][d] > 0)
            .map(|(_, name)| *name)
            .collect();
        println!(
            "c{:03}  领域数 {}  成员 {}  代表 {}",
            j, domain_count[j], sizes[j], corpus.ids[rep[j]]
        );
        println!("  领域: {}", doms.join(", "));
        println!("  代表片段: {}", one_line(&corpus.texts[rep[j]], REP_CHARS));
        println!("  出处: {}", corpus.sources[rep[j]]);
    }
    println!("\n已写 {out}");
    print_timings(&[
        ("门禁", ms(t_gate)),
        ("读数据", ms(t_read)),
        ("归一化", ms(t_norm)),
        ("计算（30 轮分配+更新+统计）", ms(t_calc)),
        ("写盘", ms(t_write)),
    ]);
    println!(
        "[耗时] 合计（不含门禁）{:.1} ms，含门禁 {:.1} ms",
        ms(t_read) + ms(t_norm) + ms(t_calc) + ms(t_write),
        ms(t_gate) + ms(t_read) + ms(t_norm) + ms(t_calc) + ms(t_write)
    );
}

// ---------- 子命令 3：groups（本轮新增） ----------
struct Union {
    p: Vec<usize>,
}

impl Union {
    fn new(n: usize) -> Self {
        Union {
            p: (0..n).collect(),
        }
    }
    fn find(&mut self, a: usize) -> usize {
        let mut r = a;
        while self.p[r] != r {
            r = self.p[r];
        }
        let mut x = a;
        while self.p[x] != r {
            let nx = self.p[x];
            self.p[x] = r;
            x = nx;
        }
        r
    }
    fn union(&mut self, a: usize, b: usize) {
        let ra = self.find(a);
        let rb = self.find(b);
        if ra != rb {
            self.p[rb] = ra;
        }
    }
}

fn read_pair_file(path: &str) -> Option<Vec<(String, String)>> {
    let s = fs::read_to_string(path).ok()?;
    let mut out = Vec::new();
    for (i, line) in s.lines().enumerate() {
        if i == 0 || line.trim().is_empty() {
            continue;
        }
        let mut it = line.split('\t');
        if let (Some(a), Some(b)) = (it.next(), it.next()) {
            out.push((a.to_string(), b.to_string()));
        }
    }
    Some(out)
}

fn cmd_groups() {
    let t_gate = gate(false);
    let t0 = Instant::now();
    let corpus = load_corpus();
    let n = corpus.ids.len();
    let mut x = read_embeddings(n);
    let t_read = t0.elapsed();

    let t1 = Instant::now();
    normalize(&mut x, n);
    let t_norm = t1.elapsed();

    // 与 duplicates 同一套算法重算对（dot / argpartition 分段计时）
    let t_calc = Instant::now();
    let (mut cand, _top1, dot_ms, topk_ms) = compute_pairs(&x, n);
    let ordered = dedup_pairs(&mut cand);
    let t_calc = t_calc.elapsed();

    // 与 duplicates.rs.tsv 对照：文件在就以文件的对建图，文件缺失用重算的对
    let pairs_path = path_of("duplicates.rs.tsv");
    let file_pairs = read_pair_file(&pairs_path);
    let calc_id_pairs: Vec<(String, String)> = ordered
        .iter()
        .map(|&(a, b, _)| (corpus.ids[a].clone(), corpus.ids[b].clone()))
        .collect();
    let (graph_pairs, file_pair_count) = match &file_pairs {
        Some(fp) => {
            let fs: HashSet<&(String, String)> = fp.iter().map(|p| p).collect();
            let cs: HashSet<&(String, String)> = calc_id_pairs.iter().map(|p| p).collect();
            let only_file = fs.len().saturating_sub(fs.intersection(&cs).count());
            let only_calc = cs.len().saturating_sub(fs.intersection(&cs).count());
            println!(
                "对账 duplicates.rs.tsv：文件 {} 对，本命令重算 {} 对，共同 {} 对，仅文件 {} 对，仅本命令 {} 对",
                fp.len(),
                cs.len(),
                fs.intersection(&cs).count(),
                only_file,
                only_calc
            );
            (fs.into_iter().cloned().collect::<Vec<_>>(), fp.len())
        }
        None => {
            println!("未找到 {pairs_path}，用本命令重算的对建图");
            (calc_id_pairs, 0)
        }
    };

    // 并查集：连通分量
    let t_uf = Instant::now();
    let row_of: HashMap<&str, usize> = corpus
        .ids
        .iter()
        .enumerate()
        .map(|(i, id)| (id.as_str(), i))
        .collect();
    let mut uf = Union::new(n);
    let mut involved: HashSet<usize> = HashSet::new();
    for (a, b) in &graph_pairs {
        let (Some(&ia), Some(&ib)) = (row_of.get(a.as_str()), row_of.get(b.as_str())) else {
            continue;
        };
        uf.union(ia, ib);
        involved.insert(ia);
        involved.insert(ib);
    }
    let mut comps: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for &i in &involved {
        let r = uf.find(i);
        comps.entry(r).or_default().push(i);
    }
    let t_uf = t_uf.elapsed();

    // 分组：按每组横跨的领域数分 1 / 2-9 / >=10
    let mut sorted: Vec<(usize, usize, Vec<usize>)> = comps
        .into_values()
        .map(|mut g| {
            g.sort_by(|&a, &b| corpus.ids[a].cmp(&corpus.ids[b]));
            let doms: BTreeSet<&str> = g.iter().map(|&i| domain_of(&corpus.sources[i])).collect();
            (doms.len(), g.len(), g)
        })
        .collect();
    sorted.sort_by(|a, b| {
        b.0.cmp(&a.0) // 领域数降序
            .then_with(|| b.1.cmp(&a.1)) // 组内片段数降序
            .then_with(|| corpus.ids[a.2[0]].cmp(&corpus.ids[b.2[0]]))
    });

    let bucket_of = |d: usize| -> &'static str {
        if d == 1 {
            "1"
        } else if d < 10 {
            "2-9"
        } else {
            ">=10"
        }
    };

    let t_write = Instant::now();
    let out = path_of("copy_groups.tsv");
    {
        let f = fs::File::create(&out).unwrap_or_else(|e| die(&format!("写 {out} 失败：{e}")));
        let mut w = BufWriter::new(f);
        writeln!(w, "group_id\tgroup_size\tdomain_count\tdomains\tid\tsource").unwrap();
        for (gi, (dcount, gsize, members)) in sorted.iter().enumerate() {
            let doms: BTreeSet<&str> = members
                .iter()
                .map(|&i| domain_of(&corpus.sources[i]))
                .collect();
            let dom_str = doms.iter().copied().collect::<Vec<_>>().join(",");
            for &i in members {
                writeln!(
                    w,
                    "g{:03}\t{}\t{}\t{}\t{}\t{}",
                    gi, gsize, dcount, dom_str, corpus.ids[i], corpus.sources[i]
                )
                .unwrap();
            }
        }
        w.flush().unwrap();
    }

    // 统计 json
    let mut buckets: BTreeMap<&str, (usize, usize)> = BTreeMap::new();
    buckets.insert("1", (0, 0));
    buckets.insert("2-9", (0, 0));
    buckets.insert(">=10", (0, 0));
    let mut by_domain_count: BTreeMap<usize, usize> = BTreeMap::new();
    let mut frag_by_domain_count: BTreeMap<usize, usize> = BTreeMap::new();
    for (dcount, gsize, _) in &sorted {
        let b = buckets.entry(bucket_of(*dcount)).or_default();
        b.0 += 1;
        b.1 += gsize;
        *by_domain_count.entry(*dcount).or_default() += 1;
        *frag_by_domain_count.entry(*dcount).or_default() += *gsize;
    }
    let stats = serde_json::json!({
        "params": {
            "threshold": 0.9,
            "top_k": TOPK,
            "block_size": BLOCK,
            "buckets": ["1", "2-9", ">=10"],
            "bucket_rule": "1=只跨 1 个领域，2-9=跨 2-9 个领域，>=10=跨 10 个及以上领域"
        },
        "pairs": graph_pairs.len(),
        "fragments_in_pairs": involved.len(),
        "groups_total": sorted.len(),
        "fragments_in_groups": sorted.iter().map(|g| g.1).sum::<usize>(),
        "buckets": {
            "1": {"groups": buckets["1"].0, "fragments": buckets["1"].1},
            "2-9": {"groups": buckets["2-9"].0, "fragments": buckets["2-9"].1},
            ">=10": {"groups": buckets[">=10"].0, "fragments": buckets[">=10"].1},
        },
        "domain_count_distribution": dom_map(&by_domain_count),
        "fragment_domain_count_distribution": dom_map(&frag_by_domain_count),
        "duplicates_rs_tsv_pairs": file_pair_count,
    });
    let stats_path = path_of("copy_groups_stats.json");
    fs::write(
        &stats_path,
        serde_json::to_string_pretty(&stats).unwrap() + "\n",
    )
    .unwrap_or_else(|e| die(&format!("写 {stats_path} 失败：{e}")));
    let t_write = t_write.elapsed();

    // ---- stdout ----
    println!(
        "对 {} → 片段 {} 条 → 连通分量（组）{} 个，组内片段 {} 条",
        graph_pairs.len(),
        involved.len(),
        sorted.len(),
        sorted.iter().map(|g| g.1).sum::<usize>()
    );
    for name in ["1", "2-9", ">=10"] {
        let &(g, f) = buckets.get(name).unwrap();
        println!("  跨域 {name:>4}：{:>3} 组，{:>4} 片段", g, f);
    }
    println!(
        "领域数分布（分母 {} 组）：{}",
        sorted.len(),
        by_domain_count
            .iter()
            .map(|(k, v)| format!("{k}: {v}"))
            .collect::<Vec<_>>()
            .join(", ")
    );
    println!("\n已写 {out}");
    println!("已写 {stats_path}");
    println!("---- 耗时分解 ----");
    println!("[耗时] {:<34} {:>10.1} ms", "门禁", ms(t_gate));
    println!("[耗时] {:<34} {:>10.1} ms", "读数据", ms(t_read));
    println!("[耗时] {:<34} {:>10.1} ms", "归一化", ms(t_norm));
    println!(
        "[耗时] {:<34} {:>10.1} ms",
        "计算（含 dot + argpartition）",
        ms(t_calc)
    );
    println!("[耗时] {:<34} {:>10.1} ms", "写盘", ms(t_write));
    println!("---- 三段耗时（单独报，纯 Python 在这一段跑不完）----");
    println!(
        "[分段] dot（块化点积）                    {:>10.1} ms",
        dot_ms
    );
    println!(
        "[分段] argpartition（top-k + 阈值 + 去重） {:>10.1} ms",
        topk_ms
    );
    println!(
        "[分段] 并查集（连通分量）                 {:>10.1} ms",
        ms(t_uf)
    );
    println!(
        "[耗时] 合计（不含门禁）{:.1} ms，含门禁 {:.1} ms",
        ms(t_read) + ms(t_norm) + ms(t_calc) + ms(t_write),
        ms(t_gate) + ms(t_read) + ms(t_norm) + ms(t_calc) + ms(t_write)
    );
}

// ---------- 子命令 4：search（只比数学） ----------
fn cmd_search(qpath: &str) {
    let t_gate = gate(true);
    let t0 = Instant::now();
    let corpus = load_corpus();
    let n = corpus.ids.len();
    let mut x = read_embeddings(n);
    let t_read = t0.elapsed();

    let t1 = Instant::now();
    normalize(&mut x, n);
    let bytes = fs::read(qpath).unwrap_or_else(|e| die(&format!("读 {qpath} 失败：{e}")));
    if bytes.len() != DIM * 4 {
        die(&format!(
            "{qpath} 大小 {} 字节，不是 {} 维 f32（应为 {} 字节）",
            bytes.len(),
            DIM,
            DIM * 4
        ));
    }
    let mut q: Vec<f32> = bytes
        .chunks_exact(4)
        .map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();
    {
        let mut acc = 0f32;
        for &v in q.iter() {
            acc += v * v;
        }
        let nn = acc.sqrt();
        let d = if nn == 0.0 { 1.0 } else { nn };
        for v in q.iter_mut() {
            *v /= d;
        }
    }
    let t_norm = t1.elapsed();

    let t_calc = Instant::now();
    let scores: Vec<f32> = x.par_chunks(DIM).map(|row| dot(row, &q)).collect();
    // 全量取 top-10（分数降序，并列按行号升序）
    let mut idx: Vec<usize> = (0..n).collect();
    idx.sort_by(|&a, &b| {
        scores[b]
            .partial_cmp(&scores[a])
            .unwrap()
            .then_with(|| a.cmp(&b))
    });
    let top: Vec<usize> = idx.into_iter().take(TOPK).collect();
    let t_calc = t_calc.elapsed();

    // 输出行格式与 search.py 一致：score / id / source / 空白压平后的正文前 120 字
    let t_write = Instant::now();
    let mut out = std::io::stdout();
    for &i in &top {
        let preview: String = collapse_ws(&corpus.texts[i]).chars().take(120).collect();
        writeln!(
            out,
            "{:.6}\t{}\t{}\t{}",
            scores[i], corpus.ids[i], corpus.sources[i], preview
        )
        .unwrap();
    }
    out.flush().unwrap();
    let t_write = t_write.elapsed();

    eprintln!(
        "检索 {} / {} 条：全量点积 {:.1} ms，输出 {} 行",
        n,
        n,
        ms(t_calc),
        top.len()
    );
    print_timings_err(&[
        ("门禁", ms(t_gate)),
        ("读数据", ms(t_read)),
        ("归一化 + 查询向量", ms(t_norm)),
        ("计算（点积 + top-10）", ms(t_calc)),
        ("写盘（stdout）", ms(t_write)),
    ]);
    eprintln!(
        "[耗时] 合计（不含门禁）{:.1} ms，含门禁 {:.1} ms",
        ms(t_read) + ms(t_norm) + ms(t_calc) + ms(t_write),
        ms(t_gate) + ms(t_read) + ms(t_norm) + ms(t_calc) + ms(t_write)
    );
}

fn dom_map(m: &BTreeMap<usize, usize>) -> serde_json::Map<String, serde_json::Value> {
    m.iter()
        .map(|(k, v)| (k.to_string(), serde_json::Value::from(*v)))
        .collect()
}

fn collapse_ws(s: &str) -> String {
    let mut out = String::new();
    let mut in_ws = false;
    for ch in s.chars() {
        if ch.is_whitespace() {
            if !in_ws {
                out.push(' ');
                in_ws = true;
            }
        } else {
            out.push(ch);
            in_ws = false;
        }
    }
    out
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("duplicates") => cmd_duplicates(),
        Some("clusters") => cmd_clusters(),
        Some("groups") => cmd_groups(),
        Some("search") => {
            if args.get(2).map(String::as_str) != Some("--query-vec") || args.get(3).is_none() {
                eprintln!("用法: vector search --query-vec <f32 文件（DIM 个 f32，行主序）>");
                std::process::exit(2);
            }
            cmd_search(&args[3]);
        }
        _ => {
            eprintln!("用法: vector <duplicates|clusters|groups|search --query-vec <文件>>");
            std::process::exit(2);
        }
    }
}
