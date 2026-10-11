#!/usr/bin/env python3
"""按组号区间打印紧凑阅读材料，供人工逐组标记。

用法：/usr/bin/python3 scripts/digest_groups.py <起始序号> <结束序号> [每条截断字数]
组按 group_id 排序后切区间（0 起）。默认每条截 240 字。
"""
import csv, collections, os, sys

WD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(WD, 'data')


def main():
    lo = int(sys.argv[1]); hi = int(sys.argv[2])
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 240
    frag = {}
    for r in open(os.path.join(DATA, 'fragments.tsv'), encoding='utf-8').read().splitlines()[1:]:
        i, t, s = r.split('\t')[:3]
        frag[i] = (t, s)
    groups = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(DATA, 'copy_groups.tsv'), encoding='utf-8'),
                            delimiter='\t'):
        groups[str(r['group_id'])].append(r)
    gids = sorted(groups, key=lambda g: (len(groups[g]), g), reverse=True)
    for gid in gids[lo:hi]:
        ms = groups[gid]
        print('### %s  %d条  %s' % (gid, len(ms), ms[0]['domains'].replace('quanttide-', '')))
        for tag, m in zip('ABCDEFGHIJKLMN', ms):
            t, s = frag[m['id']]
            p = s.split('#', 1)[1]
            print('%s %s  %s' % (tag, m['id'], p))
            body = ' / '.join(x for x in t.split('\n') if x.strip())
            print('  %s%s' % (body[:cap], ' …[截]' if len(body) > cap else ''))
        print()


if __name__ == '__main__':
    main()
