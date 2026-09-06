#!/usr/bin/env python3
"""掃描全部 phcsev（photon CSEV）擬合的健康度（唯讀）。

phcsev 用的是 80-100 GeV 的官方質量窗 -> 幾乎沒有 sideband,背景無法被資料決定。
2026-08-23 的分析已知:97% 的 bin 的 nBkg 停在框架下界,擬合效率≈原始計數。
這裡量四件事,看問題到底集中在哪:
  covQual < 3   Hessian 不可信
  edm == 0      MIGRAD 連第一步都沒踏出去（不是解不好,是沒開始找）
  railed        形狀參數撞界
  nBkg at floor 背景停在下界 0.5
"""
import os, sys, glob, ROOT
ROOT.gErrorIgnoreLevel = ROOT.kFatal

B = '/eos/home-p/pelai/HZa/root_TnP'
rows, ntot = [], 0
for d in sorted(glob.glob(os.path.join(B, 'hza_resolve_phcsev_*_sf'))):
    meas = os.path.basename(d).replace('hza_resolve_phcsev_', '').replace('_sf', '')
    for f in sorted(glob.glob(os.path.join(d, 'Data_*nominalFit-bin*.root'))):
        if os.path.basename(f).startswith('.'):
            continue
        ntot += 1
        fh = ROOT.TFile.Open(f)
        if not fh or fh.IsZombie():
            continue
        keys = [k.GetName() for k in fh.GetListOfKeys() if k.GetClassName() == 'RooFitResult']
        if not keys:
            fh.Close(); continue
        base = keys[0].rsplit('_res', 1)[0]
        r = fh.Get(base + '_resF')
        if not r:
            fh.Close(); continue
        d2 = {p.GetName(): (p.getVal(), p.getMin(), p.getMax()) for p in r.floatParsFinal()}
        rails = 0
        for k, (v, lo, hi) in d2.items():
            if k.startswith(('nSig', 'nBkg')):
                continue
            if hi > lo and ((v - lo) / (hi - lo) < 0.02 or (v - lo) / (hi - lo) > 0.98):
                rails += 1
        nb = d2.get('nBkgF', (None, None, None))
        floor = nb[0] is not None and nb[0] <= nb[1] * 1.001 + 1e-9
        rows.append((meas, base.split('_event')[0], r.edm(), r.covQual(), rails, floor))
        fh.Close()

nz = sum(1 for x in rows if x[2] == 0.0)
cq = sum(1 for x in rows if x[3] < 3)
ra = sum(1 for x in rows if x[4] > 0)
fl = sum(1 for x in rows if x[5])
print('掃描 %d 個 phcsev nominalFit（data）\n' % ntot)
print('  edm 恰好 = 0（MIGRAD 沒動）: %4d  (%.0f%%)' % (nz, 100.0 * nz / max(ntot, 1)))
print('  covQual < 3                : %4d  (%.0f%%)' % (cq, 100.0 * cq / max(ntot, 1)))
print('  有形狀參數撞界              : %4d  (%.0f%%)' % (ra, 100.0 * ra / max(ntot, 1)))
print('  nBkgF 停在下界              : %4d  (%.0f%%)' % (fl, 100.0 * fl / max(ntot, 1)))
print('\n依 measurement:')
import collections
per = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
for meas, b, edm, q, rl, f in rows:
    a = per[meas]; a[0] += 1
    if edm == 0.0: a[1] += 1
    if q < 3: a[2] += 1
    if rl > 0: a[3] += 1
    if f: a[4] += 1
print('  %-34s %5s %6s %7s %6s %6s' % ('measurement', 'n', 'edm0', 'covQ<3', '撞界', 'nBkg底'))
for k in sorted(per):
    n, z, q, rl, f = per[k]
    print('  %-34s %5d %6d %7d %6d %6d' % (k, n, z, q, rl, f))
