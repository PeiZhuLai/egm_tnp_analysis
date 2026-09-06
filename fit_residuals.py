#!/usr/bin/env python3
"""Data-vs-curve residuals for a stored TnP fit, read out of the saved canvas.

Why this exists: several bins the user flagged look numerically healthy --
covQual=3, tiny edm, no parameter on a limit -- and are still visibly wrong. The
only way to see that is to compare the drawn curve against the drawn points, so
this pulls the RooHist (data) and RooCurve (total pdf) straight out of the
canvas the fitter already saved. No refit, no workspace needed.

  ./fit_residuals.py <fit_result.root> [--side pass|fail|both]

Reports, per 5 GeV slice: data, curve, relative residual and pull. Bins are
ranked by pull so the worst region is obvious. Remember the Poisson floor --
a 15% relative residual on 50 events is 1 sigma and means nothing; the pull
column is what tells you whether a deviation is real.
"""
import argparse, glob, sys
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal


def _pads(canv):
    """Find the pad holding each leg's points+curve.

    The two frameworks nest differently: the electron fitter puts the RooHist
    straight into c_2/c_3, while the muon fitter wraps each leg in plotpadP /
    plotpadF (with a separate ratiopad for the pulls), so this has to recurse.
    """
    out = {}

    def visit(node):
        names = [p.GetName() for p in node.GetListOfPrimitives()]
        if 'h_hPass' in names:
            out.setdefault('pass', node)
        if 'h_hFail' in names:
            out.setdefault('fail', node)
        for o in node.GetListOfPrimitives():
            if o.ClassName() in ('TPad', 'TCanvas'):
                visit(o)

    visit(canv)
    return out


def _curve_and_points(pad):
    hist = curve = None
    for o in pad.GetListOfPrimitives():
        cn = o.ClassName()
        if cn == 'RooHist' and hist is None:
            hist = o
        elif cn == 'RooCurve' and curve is None and 'Comp[' not in o.GetName():
            curve = o
    return hist, curve


def residuals(path, sides):
    fh = ROOT.TFile.Open(path)
    if not fh or fh.IsZombie():
        raise SystemExit('cannot open %s' % path)
    canv = None
    for k in fh.GetListOfKeys():
        if k.GetName().endswith('_Canv'):
            canv = fh.Get(k.GetName())
            break
    if canv is None:
        raise SystemExit('no canvas in %s' % path)

    for side, pad in _pads(canv).items():
        if side not in sides:
            continue
        hist, curve = _curve_and_points(pad)
        if hist is None or curve is None:
            print('  %s: no data/curve pair found' % side)
            continue
        xs, ys = hist.GetX(), hist.GetY()
        rows = []
        for i in range(hist.GetN()):
            x, d = xs[i], ys[i]
            m = curve.interpolate(x)
            err = hist.GetErrorY(i) or (d ** 0.5 if d > 0 else 1.0)
            rows.append((x, d, m, (d - m) / m * 100.0 if m else 0.0,
                         (d - m) / err if err else 0.0))
        # aggregate into 5 GeV slices so the shape, not the binning, is visible
        buckets = {}
        for x, d, m, rel, pull in rows:
            lo = int(x // 5 * 5)
            b = buckets.setdefault(lo, [0.0, 0.0])
            b[0] += d
            b[1] += m
        print('  --- %s ---' % side)
        print('     %-8s %10s %10s %8s %8s' % ('mass', 'data', 'curve', 'rel%', 'pull'))
        worst = []
        for lo in sorted(buckets):
            d, m = buckets[lo]
            if m <= 0:
                continue
            rel = (d - m) / m * 100.0
            pull = (d - m) / (d ** 0.5) if d > 0 else 0.0
            flag = ' <<<' if abs(pull) > 5 and d >= 200 else ''
            print('     %-8s %10.0f %10.0f %8.1f %8.1f%s' % (
                '%d-%d' % (lo, lo + 5), d, m, rel, pull, flag))
            worst.append((abs(pull), lo, rel, d))
        worst.sort(reverse=True)
        sig = [w for w in worst if w[0] > 5 and w[3] >= 200]
        print('     -> %d slice(s) with |pull|>5 and >=200 events%s' % (
            len(sig), (': ' + ', '.join('%d-%d GeV %+.0f%%' % (w[1], w[1] + 5, w[2])
                                        for w in sig[:4])) if sig else ''))
    fh.Close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--side', default='both', choices=['pass', 'fail', 'both'])
    a = ap.parse_args()
    sides = ('pass', 'fail') if a.side == 'both' else (a.side,)
    for p in sorted(glob.glob(a.path)) or [a.path]:
        print('=== %s' % p.split('/')[-1])
        residuals(p, sides)
