#!/usr/bin/env python3
"""gap_2025 補產 MC altSigFit 參考檔後的驗收：24 格 × 效率一致性。

判準（2026-09-14/15 用四格實測歸納出來的，順序不可顛倒）：
  1. **效率與 altBkgFit 的一致性** —— 決定性。altSig 是離群值時，系統誤差就是它。
     b14 曾出現「殘差 Σ|pull| 90.6 -> 34.9 大好、效率卻從 +2.6% 惡化到 +7.1%」，
     只看殘差會判成成功。
  2. 收斂（edm / covQual）不退步。
  3. 殘差是輔助，不能單獨當依據。

這支比「改前（形狀自由）」與「改後（MC 播種）」每一格對 altBkg 的偏離，
並統計有幾格變好、幾格變差 —— 單格改善不代表整批沒有惡化。
"""
import os, sys, glob
from multiprocessing import Pool

D = '/eos/home-p/pelai/HZa/root_TnP/hza_dielleg23trigger_gap_2025_sf'
SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'snapshot_gap2025_altsig_20260915')
PFX = 'Data_2025_hza_dielleg23trigger_gap_2025_sf'


def eff_of(path):
    import ROOT
    ROOT.gROOT.SetBatch(True); ROOT.gErrorIgnoreLevel = ROOT.kFatal
    if not os.path.exists(path):
        return None
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return None
    try:
        names = [k.GetName() for k in f.GetListOfKeys() if k.GetClassName() == 'RooFitResult']
        rP = f.Get([x for x in names if x.endswith('resP')][0])
        rF = f.Get([x for x in names if x.endswith('resF')][0])
        g = lambda r, n: (r.floatParsFinal().find(n).getVal()
                          if r.floatParsFinal().find(n) else float('nan'))
        a, b = g(rP, 'nSigP'), g(rF, 'nSigF')
        return (a / (a + b), rF.edm(), rF.covQual(), rF.floatParsFinal().getSize())
    finally:
        f.Close()


def one(binname):
    new = eff_of(os.path.join(D, '%s.altSigFit-%s.root' % (PFX, binname)))
    old = eff_of(os.path.join(SNAP, '%s.altSigFit-%s.root' % (PFX, binname)))
    ab = eff_of(os.path.join(D, '%s.altBkgFit-%s.root' % (PFX, binname)))
    return (binname, new, old, ab)


def main():
    bins = sorted({os.path.basename(p).split('.altSigFit-')[1][:-5]
                   for p in glob.glob(os.path.join(SNAP, '*.altSigFit-bin*.root'))})
    with Pool(3, maxtasksperchild=1) as pool:
        res = pool.map(one, bins, chunksize=1)
    print('%-10s %9s %9s %9s %10s %10s  %s'
          % ('bin', 'altBkg', '自由', 'MC播種', '偏離前', '偏離後', '判定'))
    better = worse = same = nocmp = 0
    for b, new, old, ab in res:
        if not (new and old and ab):
            print('%-10s  讀不到' % b[:10]); nocmp += 1; continue
        d_old = (old[0] - ab[0]) / ab[0] * 100
        d_new = (new[0] - ab[0]) / ab[0] * 100
        if   abs(d_new) < abs(d_old) - 0.1: verdict, _ = '好', better
        elif abs(d_new) > abs(d_old) + 0.1: verdict = '差'
        else: verdict = '持平'
        if verdict == '好': better += 1
        elif verdict == '差': worse += 1
        else: same += 1
        print('%-10s %9.4f %9.4f %9.4f %+9.2f%% %+9.2f%%  %s%s'
              % (b[:10], ab[0], old[0], new[0], d_old, d_new, verdict,
                 '' if new[2] >= old[2] else '  ⚠covQual 退步'))
    print('\n效率一致性：變好 %d / 變差 %d / 持平 %d / 無法比 %d' % (better, worse, same, nocmp))
    return 0


if __name__ == '__main__':
    sys.exit(main())
