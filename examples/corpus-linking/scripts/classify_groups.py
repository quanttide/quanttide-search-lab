#!/usr/bin/env python3
"""把「近重复组」分成两堆：模板套用（填表）/ 真重复（抄两份）。

为什么不是纯统计：模板套用和真重复在向量上长得一样——都是「同一件事、两种说法」。
差别不在「有多像」，在**差异落在哪儿**。实测六个统计量（骨架占比、最小余弦、
余弦标准差、长度变异系数…）全部与真重复组重叠，只有**位置**这一刀能用。

四轮演进（留档，末轮是定稿）：

  第一轮  并列度 ≥ 0.5 且 长度接近            9/12
  第二轮  只看并列度 ≥ 0.5                    10/12
  第三轮  同文件 / 同目录 / 散开 三档          6/12，其中 5 个是「拿不准」不算判错
  第四轮  同文件 / 兄弟目录 / 散开 三档        5/12，**判错 0**，其余交人看

前两轮各有一条坏判据被抽样验毙掉：
  - 「长度接近」：模板的成员长度会随槽位长短而变（g057 那 14 条长度不一却是模板）
  - 「同一目录」：模板会按对象铺到兄弟目录里（g057 的 8 条在 content/、6 条在 medium/）

第四轮承认机器分不干净：「同目录不同文件」两种情况都有（g058 那 7 份决策头是模板，
g406 那 2 条是真重复），一律标「拿不准」交人，不硬判。

输出三堆：
  模板套用  同一文件里铺开        → 不用管
  拿不准    同目录/兄弟目录不同文件 → 人过一眼（大多只有两条）
  真重复    地址散开              → 要定正本

用法：/usr/bin/python3 scripts/classify_groups.py
产物：data/group_kind.tsv
"""
import csv, collections, difflib, os, re, statistics

WD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(WD, 'data')


def load():
    frag = {}
    for r in open(os.path.join(DATA, 'fragments.tsv'), encoding='utf-8').read().splitlines()[1:]:
        i, t, s = r.split('\t')[:3]
        frag[i] = (t, s)
    groups = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(DATA, 'copy_groups.tsv'), encoding='utf-8'),
                            delimiter='\t'):
        groups[str(r['group_id'])].append(r)
    return frag, groups


def units(t):
    """切要点：先按行，行内再按「；」或列表标记切。"""
    parts = [p.strip() for p in t.split('\n') if p.strip()]
    if len(parts) <= 1:
        s = parts[0] if parts else t
        parts = [p.strip() for p in re.split(r'(?<=；)|(?=-\s?\*\*)|(?=\d+\.\s?\*\*)', s)
                 if p and p.strip()]
    return parts or [t]


def signals(members, frag):
    paths = [frag[m['id']][1].split('#', 1)[1] or '.' for m in members]
    dirs = [os.path.dirname(p) or '.' for p in paths]
    n = len(paths)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    same_dir = sum(1 for i, j in pairs if dirs[i] == dirs[j]) / len(pairs)
    same_file = sum(1 for i, j in pairs if paths[i] == paths[j]) / len(pairs)
    sib = sum(1 for i, j in pairs
              if os.path.dirname(dirs[i]) == os.path.dirname(dirs[j])) / len(pairs)
    lens = [len(frag[m['id']][0]) for m in members]
    cv = (statistics.pstdev(lens) / statistics.mean(lens)) if statistics.mean(lens) else 9.9
    uc = {len(units(frag[m['id']][0])) for m in members}
    sims = []
    for i, j in pairs:
        a, b = frag[members[i]['id']][0], frag[members[j]['id']][0]
        sm = difflib.SequenceMatcher(None, a, b)
        sims.append(2.0 * sum(bk.size for bk in sm.get_matching_blocks()) / (len(a) + len(b)))
    return dict(same_dir=same_dir, same_file=same_file, sib=sib,
                pos=max(same_dir, same_file), len_cv=cv,
                unit_same=(len(uc) == 1), char_sim=statistics.mean(sims))


def r1(s):  # 第一轮：并列 + 长度接近
    return '模板套用' if (s['pos'] >= 0.5 and s['len_cv'] <= 0.25) else '真重复'


def r2(s):  # 第二轮：只看并列
    return '模板套用' if s['pos'] >= 0.5 else '真重复'


def r3(s):  # 第三轮：同文件 / 同目录 / 散开
    if s['same_file'] >= 0.9:
        return '模板套用'
    return '拿不准' if s['same_dir'] >= 0.9 else '真重复'


def r4(s):  # 第四轮（定稿）：同文件 / 兄弟目录 / 散开
    if s['same_file'] >= 0.9:
        return '模板套用'
    return '拿不准' if s['sib'] >= 0.9 else '真重复'


LABELED = {'g057': '模板套用', 'g058': '模板套用', 'g059': '模板套用', 'g060': '模板套用',
           'g061': '模板套用', 'g218': '模板套用', 'g406': '真重复', 'g417': '真重复',
           'g375': '真重复', 'g163': '真重复', 'g339': '真重复', 'g400': '真重复'}


if __name__ == '__main__':
    frag, groups = load()
    rows = []
    for gid, ms in sorted(groups.items(), key=lambda kv: (len(kv[1]), kv[0]), reverse=True):
        s = signals(ms, frag)
        rows.append((gid, len(ms), ms[0]['domains'].replace('quanttide-', ''),
                     r1(s), r2(s), r3(s), r4(s), s))

    out = os.path.join(DATA, 'group_kind.tsv')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('group_id\tsize\tdomains\tkind_r1\tkind_r2\tkind_r3\tkind_r4'
                '\tsame_dir\tsame_file\tsib\tpos\tlen_cv\tunit_same\tchar_sim\tmembers\n')
        for gid, n, d, a, b, c, e, s in rows:
            f.write('%s\t%d\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.3f\t%s\t%.3f\t%s\n' % (
                gid, n, d, a, b, c, e, s['same_dir'], s['same_file'], s['sib'], s['pos'],
                s['len_cv'], s['unit_same'], s['char_sim'],
                ','.join(m['id'] for m in groups[gid])))

    print('=== 全量 %d 组 / %d 条片段 ===' % (len(rows), sum(r[1] for r in rows)))
    for tag, ci in (('第一轮 并列+长度接近', 3), ('第二轮 只看并列≥0.5', 4),
                    ('第三轮 同文件/同目录/散开', 5), ('第四轮 同文件/兄弟目录/散开', 6)):
        k = collections.Counter(r[ci] for r in rows)
        fr = collections.Counter()
        for r in rows:
            fr[r[ci]] += r[1]
        print('  %-24s %s' % (tag, ' · '.join(
            '%s %d 组/%d 条' % (x, k[x], fr[x]) for x in ('模板套用', '拿不准', '真重复') if k[x])))
    print()
    print('=== 抽样验（12 组肉眼判过的）===')
    hdr = '  %-6s %-4s ' % ('轮次', '命中')
    print(hdr + ''.join('%-8s' % g for g in sorted(LABELED)))
    for tag, ci in (('第一轮', 3), ('第二轮', 4), ('第三轮', 5), ('第四轮', 6)):
        hit, cell = 0, []
        for gid, want in sorted(LABELED.items()):
            got = [r[ci] for r in rows if r[0] == gid]
            if not got:
                cell.append('  -  '); continue
            g = got[0]
            hit += g == want
            cell.append(('✓' if g == want else ('◐' if g == '拿不准' else '✗')) + '    ')
        print('  %-6s %2d/12 ' % (tag, hit) + ''.join('%-8s' % c for c in cell))
    print('  ✓判对  ✗判错  ◐交人看（不算判错）')
    print()
    print('=== 第四轮的三堆 ===')
    for x in ('模板套用', '拿不准', '真重复'):
        sub = [r for r in rows if r[6] == x]
        if not sub:
            continue
        print('  %s %d 组 / %d 条  （最大 %d 条）' % (x, len(sub), sum(r[1] for r in sub),
                                                    max(r[1] for r in sub)))
    print()
    print('  真重复堆（要定正本）里跨域的：')
    for gid, n, d, a, b, c, e, s in [r for r in rows if r[6] == '真重复' and ',' in r[2]][:10]:
        print('    %-6s %2d 条  %s' % (gid, n, d))
    print()
    print('产物：%s' % out)
