#!/usr/bin/env python3
"""Classify photon (phcsev) TnP fits so the unfixable ones are not tuned.

The photon measurements are dominated by a failure mode that no amount of
parameter tuning touches: the failing histogram is empty or nearly so, and the
framework's yield range -- nSigF[nTot*0.9, 0.5, nTot*1.5] -- collapses to the
single point [0.5, 0.5] when nTot is 0. The parameters then cannot move because
they have nowhere to move to, and edm comes out exactly 0. Reading that as "the
fit did not take effect" leads to tuning a bin that has no data in it.

Verdicts, in the order they are tested:
  EMPTY      a leg has < 20 events -- nothing to fit, this is a binning decision
  LOWSTAT    total < 1500 -- likelihood is flat; forcing convergence would give
             parameters set by the seeds but finite-looking errors, which is
             worse than leaving it visibly broken
  NEVER-MIN  every parameter still at its config initial value -- MIGRAD did not
             run (usually a non-finite NLL); the central value is NOT usable
  NO-HESSE   errors all zero but parameters moved -- central value fine, errors are not
  OK         fitted; residual check is what decides whether the shape is right
"""
import glob, os, pickle, sys
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

EMPTY_LEG = 20
LOWSTAT_TOTAL = 1500


def classify(hist_file, fit_file, bname):
    fh = ROOT.TFile.Open(hist_file)
    if not fh or fh.IsZombie():
        return 'NOHIST', 0, 0, ''
    hp = fh.Get('%s_Pass' % bname)
    hf = fh.Get('%s_Fail' % bname)
    nP = hp.Integral() if hp else 0.0
    nF = hf.Integral() if hf else 0.0
    fh.Close()

    if nP < EMPTY_LEG or nF < EMPTY_LEG:
        return 'EMPTY', nP, nF, 'pass=%.0f fail=%.0f' % (nP, nF)

    if not os.path.exists(fit_file):
        return 'MISSING', nP, nF, ''
    fh = ROOT.TFile.Open(fit_file)
    if not fh or fh.IsZombie():
        return 'MISSING', nP, nF, ''
    notes = []
    verdict = 'OK'
    for side, n in (('P', nP), ('F', nF)):
        r = fh.Get('%s_res%s' % (bname, side))
        if not r:
            continue
        pars = r.floatParsFinal()
        ini = {q.GetName(): q.getVal() for q in r.floatParsInit()}
        zero = sum(1 for q in pars if q.getError() == 0.0)
        stuck = sum(1 for q in pars if ini.get(q.GetName()) == q.getVal())
        tot = pars.getSize()
        # stuck 必須是「全部」參數,不能留寬容度。原本寫 tot-2 是為了容納一兩個被釘死的
        # 參數,但釘死的參數根本不在 floatParsFinal 裡,那個寬容度沒有必要 —— 它反而把
        # 「參數撞在邊界上不動」誤判成「MIGRAD 從未執行」。實例:hr9_2023preBPix bin03
        # 的 betaF 撞上界 0.08、nBkgF 觸底 0.5,兩個不動就湊到 tot-2,但它 edm=1.4e-04、
        # covQual=3、七個參數都移動過,是完全正常的擬合。
        # 用 edm/status 而非參數比對來認定「MIGRAD 沒跑」。兩種參數比對都會失準:
        #   stuck >= tot-2  把「參數撞在邊界上不動」誤判成沒最小化
        #                   (hr9_2023preBPix bin03: betaF 撞上界、nBkgF 觸底,但 edm=1.4e-04
        #                    covQual=3,是健康的擬合)
        #   stuck == tot    反過來漏掉「幾乎沒動」的
        #                   (hr9_2022preEE bin00 fail: edm 恰為 0、status=-1、七個誤差全 0,
        #                    但有兩個參數被輕微擾動過,stuck 只有 5/7)
        # edm==0 且 status==-1 是 MIGRAD 未執行的直接指紋,不依賴任何參數比對。
        if r.edm() == 0.0 and r.status() == -1 and zero == tot:
            verdict = 'NEVER-MIN'
            notes.append('%s: %d/%d at init' % (side, stuck, tot))
        elif tot and zero == tot and verdict == 'OK':
            verdict = 'NO-HESSE'
            notes.append('%s: all errors 0' % side)
    fh.Close()
    if verdict == 'OK' and (nP + nF) < LOWSTAT_TOTAL:
        return 'LOWSTAT', nP, nF, 'total=%.0f' % (nP + nF)
    return verdict, nP, nF, '; '.join(notes)


def main(pattern):
    base = '/eos/home-p/pelai/HZa/root_TnP'
    tally = {}
    rows = []
    for d in sorted(glob.glob(os.path.join(base, pattern))):
        flag = os.path.basename(d)
        pkl = os.path.join(d, 'bining.pkl')
        if not os.path.exists(pkl):
            continue
        try:
            bins = pickle.load(open(pkl, 'rb'))['bins']
        except Exception:
            continue
        hist = glob.glob(os.path.join(d, 'Data_*_%s.root' % flag))
        if not hist:
            continue
        for ib, b in enumerate(bins):
            nm = b['name']
            fit = glob.glob(os.path.join(d, 'Data_*.nominalFit-bin%02d_*.root' % ib))
            v, nP, nF, note = classify(hist[0], fit[0] if fit else '', nm)
            tally[v] = tally.get(v, 0) + 1
            rows.append((v, flag, ib, nP, nF, note))

    print('=== %d bins over %d measurements ===' % (
        len(rows), len(set(r[1] for r in rows))))
    for k in ('EMPTY', 'LOWSTAT', 'NEVER-MIN', 'NO-HESSE', 'OK', 'MISSING', 'NOHIST'):
        if tally.get(k):
            print('  %-10s %5d  (%.1f%%)' % (k, tally[k], 100.0 * tally[k] / len(rows)))
    print('\n--- per measurement ---')
    per = {}
    for v, flag, ib, nP, nF, note in rows:
        per.setdefault(flag, {}).setdefault(v, []).append(ib)
    for flag in sorted(per):
        parts = ['%s:%d' % (k, len(v)) for k, v in sorted(per[flag].items())]
        bad = per[flag].get('EMPTY', []) + per[flag].get('NEVER-MIN', [])
        print('  %-52s %s%s' % (flag, ' '.join(parts),
                                ('  bins ' + ','.join(map(str, bad[:8]))) if bad else ''))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '*phcsev*')
