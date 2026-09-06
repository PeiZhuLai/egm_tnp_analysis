#!/usr/bin/env python3
"""Judge every fit on how well it actually describes the data, not on status.

MINUIT status says whether the minimiser converged; it says nothing about
whether the curve goes through the points. A fit can converge to a bad shape
(status 0, visibly wrong) or hit an iteration limit while sitting on a perfectly
good one. Since there are ~12k fits here, every one has to be judged by a
number rather than by eye, so this computes for each fit:

  * chi2/ndf of the fitted curve against the data points, from the RooPlot the
    fitter already stored in the canvas;
  * the largest single-bin pull, which catches a curve that is fine on average
    but misses the peak;
  * whether any parameter sits on a boundary (a fit at its limit is a fit that
    wanted to go somewhere it was not allowed).

A sample of the verdicts is meant to be checked against the plots by eye, so
the metric itself is validated rather than trusted.
"""
from __future__ import annotations

import argparse
import csv
import glob
import math
import os
import re
import sys

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

FIT_TAGS = ("nominalFit", "altSigFit", "altBkgFit", "altSigBkgFit")
EDGE_TOL = 1e-3


def pinned_params(res):
    out = []
    pars = res.floatParsFinal()
    for i in range(pars.getSize()):
        p = pars.at(i)
        lo, hi = p.getMin(), p.getMax()
        if not (lo < hi):
            continue
        span, v = hi - lo, p.getVal()
        if v - lo < EDGE_TOL * span or hi - v < EDGE_TOL * span:
            out.append(p.GetName())
    return out


def plot_quality(hist, curve):
    """chi2/ndf and max |pull| of the fitted curve against the data points.

    The canvas stores the drawn RooHist/RooCurve rather than a RooPlot, so the
    comparison is done directly between them; RooCurve::chiSquare is the same
    number the fitter would quote.
    """
    try:
        chi2 = curve.chiSquare(hist, 0)
    except Exception:
        chi2 = None
    mx = 0.0
    try:
        for i in range(hist.GetN()):
            x, y = hist.GetPointX(i), hist.GetPointY(i)
            e = hist.GetErrorY(i)
            # empty bins carry no error and would otherwise report the curve
            # value itself as a pull of tens of thousands
            if y <= 0 or e <= 0:
                continue
            pull = (y - curve.Eval(x)) / e
            mx = max(mx, abs(pull))
    except Exception:
        mx = float("nan")
    return chi2, mx


def judge_file(path):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return [("open", "?", None, None, None, "UNREADABLE")]
    out = []
    frames = {}
    def collect(pad):
        # each sub-pad holds the drawn data (RooHist h_hPass/h_hFail) and the
        # fitted curves; the total pdf is the RooCurve without a Comp[...] tag,
        # the other one is just the background component
        hist = curve = None
        side = None
        for prim in pad.GetListOfPrimitives():
            n = prim.GetName() or ""
            if prim.InheritsFrom("TPad"):
                collect(prim)
            elif prim.InheritsFrom("RooHist"):
                hist = prim
                side = "fail" if "Fail" in n else "pass"
            elif prim.InheritsFrom("RooCurve") and "Comp[" not in n:
                curve = prim
        if hist is not None and curve is not None and side:
            frames[side] = (hist, curve)

    for key in f.GetListOfKeys():
        obj = f.Get(key.GetName())
        if isinstance(obj, ROOT.TCanvas):
            collect(obj)
    for key in f.GetListOfKeys():
        name = key.GetName()
        obj = f.Get(name)
        if not hasattr(obj, "floatParsFinal"):
            continue
        low = name.lower()
        side = "fail" if "resf" in low else ("pass" if "resp" in low else "?")
        chi2, mxpull = plot_quality(*frames[side]) if side in frames else (None, None)
        pin = pinned_params(obj)
        verdict = "OK"
        if chi2 is not None and chi2 > 5:
            verdict = "BAD_SHAPE"
        elif mxpull is not None and not math.isnan(mxpull) and mxpull > 5:
            verdict = "PEAK_MISS"
        elif pin:
            verdict = "AT_LIMIT"
        elif obj.status() != 0:
            verdict = "NOT_CONVERGED"
        out.append((side, obj.status(), chi2, mxpull, ";".join(pin), verdict))
    f.Close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root-dir", default="/eos/home-p/pelai/HZa/root_TnP")
    ap.add_argument("--out", default="/eos/home-p/pelai/HZa/root_TnP/fit_quality.csv")
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    meas_dirs = sorted(d for d in glob.glob(os.path.join(a.root_dir, "*")) if os.path.isdir(d))
    n = 0
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["measurement", "fitType", "sample", "bin", "side",
                    "status", "chi2ndf", "maxpull", "pinned", "verdict"])
        for md in meas_dirs:
            meas = os.path.basename(md)
            if a.only and a.only not in meas:
                continue
            for tag in FIT_TAGS:
                for fp in sorted(glob.glob(os.path.join(md, f"*.{tag}-bin*.root"))):
                    fn = os.path.basename(fp)
                    sample = fn.split(f".{tag}-")[0]
                    m = re.search(r"-(bin\d+)_", fn)
                    b = m.group(1) if m else fn
                    for side, st, chi2, mp, pin, verdict in judge_file(fp):
                        w.writerow([meas, tag, sample, b, side, st,
                                    f"{chi2:.3f}" if chi2 is not None else "",
                                    f"{mp:.2f}" if mp is not None and not math.isnan(mp) else "",
                                    pin, verdict])
                        n += 1
            fh.flush()
            print(f"[judge] {meas}: {n} fits judged", flush=True)
    print(f"[judge] DONE wrote {a.out} ({n} fits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
