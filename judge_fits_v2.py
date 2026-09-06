#!/usr/bin/env python3
"""Judge fit quality with a statistics-independent metric, and calibrate it.

The first pass used chi2/ndf > 5, which flagged 94% of the fits. That number is
not trustworthy: with millions of events per bin, chi2/ndf climbs simply because
the uncertainties shrink, so a visually perfect curve still fails. Judging by it
would mean "fixing" thousands of fits that are not broken -- exactly the churn
this is meant to end.

What replaces it is the *relative* mismatch between curve and data:

  relmax : largest |data-curve|/data over well-populated bins (>=1% of the peak)
  relpk  : the same restricted to the peak region (within 5 GeV of the maximum),
           which is what actually drives the efficiency
  relbkg : the same in the tails (>15 GeV from the peak), where a background
           that is too low shows up

A 5% shape error is 5% whether the bin holds 10^3 or 10^7 events, so the same
threshold applies everywhere. AT_LIMIT is kept from the first pass unchanged --
a parameter sitting on its boundary is a fact about the fit, not about the
statistics, and it was already the dominant and trustworthy category.

--calibrate prints these numbers for bins whose verdict is known by eye, so the
thresholds are set from evidence rather than guessed.
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
# thresholds, set by --calibrate against bins judged by eye
REL_PEAK_BAD = 0.05      # >5% off through the peak is visibly wrong
REL_BKG_BAD = 0.25       # tails are low-count; allow more before calling it bad
REL_MAX_BAD = 0.30


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


def quality(hist, curve):
    """(chi2ndf, relmax, relpk, relbkg) of curve vs data."""
    try:
        chi2 = curve.chiSquare(hist, 0)
    except Exception:
        chi2 = float("nan")
    xs, ys = [], []
    for i in range(hist.GetN()):
        y = hist.GetPointY(i)
        if y > 0:
            xs.append(hist.GetPointX(i))
            ys.append(y)
    if not ys:
        return chi2, float("nan"), float("nan"), float("nan")
    peak_y = max(ys)
    x_peak = xs[ys.index(peak_y)]
    floor = 0.01 * peak_y            # ignore near-empty bins: relative error there is meaningless
    rel_all, rel_pk, rel_bkg = [], [], []
    for x, y in zip(xs, ys):
        if y < floor:
            continue
        r = abs(y - curve.Eval(x)) / y
        rel_all.append(r)
        if abs(x - x_peak) <= 5:
            rel_pk.append(r)
        elif abs(x - x_peak) > 15:
            rel_bkg.append(r)
    f = lambda v: max(v) if v else float("nan")
    return chi2, f(rel_all), f(rel_pk), f(rel_bkg)


def judge_file(path):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return []
    frames = {}

    def collect(pad):
        hist = curve = None
        side = None
        for prim in pad.GetListOfPrimitives():
            n = prim.GetName() or ""
            if prim.InheritsFrom("TPad"):
                collect(prim)
            elif prim.InheritsFrom("RooHist"):
                hist, side = prim, ("fail" if "Fail" in n else "pass")
            elif prim.InheritsFrom("RooCurve") and "Comp[" not in n:
                curve = prim
        if hist is not None and curve is not None and side:
            frames[side] = (hist, curve)

    for key in f.GetListOfKeys():
        obj = f.Get(key.GetName())
        if isinstance(obj, ROOT.TCanvas):
            collect(obj)

    out = []
    for key in f.GetListOfKeys():
        name = key.GetName()
        obj = f.Get(name)
        if not hasattr(obj, "floatParsFinal"):
            continue
        low = name.lower()
        side = "fail" if "resf" in low else ("pass" if "resp" in low else "?")
        chi2, rmax, rpk, rbkg = quality(*frames[side]) if side in frames else (
            float("nan"),) * 4
        pin = pinned_params(obj)
        # parameter sanity: a width with a huge relative error is unconstrained,
        # and one far wider than its pass-side counterpart is unphysical. This is
        # the bin02 case -- the curve follows the points (relpeak 2.7%) but sigmaF
        # came out 4.28 +/- 0.94 against sigmaP = 1.37, so the shape metric alone
        # would have called it fine.
        loose = []
        pars = obj.floatParsFinal()
        for i in range(pars.getSize()):
            p = pars.at(i)
            if not p.GetName().startswith("sigma"):
                continue
            if p.getVal() > 0 and p.getError() / p.getVal() > 0.20:
                loose.append(f"{p.GetName()}(err {100*p.getError()/p.getVal():.0f}%)")
        ok = lambda v, t: (not math.isnan(v)) and v > t
        if loose and not ok(rpk, REL_PEAK_BAD):
            verdict = "UNCONSTRAINED"
            out.append((side, obj.status(), chi2, rmax, rpk, rbkg,
                        ";".join(pin + loose), verdict))
            continue
        if ok(rpk, REL_PEAK_BAD):
            verdict = "BAD_PEAK"
        elif ok(rbkg, REL_BKG_BAD):
            verdict = "BAD_TAIL"
        elif ok(rmax, REL_MAX_BAD):
            verdict = "BAD_SHAPE"
        elif pin:
            verdict = "AT_LIMIT"
        elif any(pars.at(i).getError() == 0.0 for i in range(pars.getSize())):
            # Not status(): after the RooCMSShape peak fix, fits that demonstrably
            # ran -- parameters off their initial values, every error non-zero --
            # still report 380 or 320, so status() would flag most of the good ones.
            # An error of exactly zero is the reliable marker, because that is what
            # RooFit leaves behind when MIGRAD never touched the parameter.
            verdict = "NOT_MINIMISED"
        else:
            verdict = "OK"
        out.append((side, obj.status(), chi2, rmax, rpk, rbkg, ";".join(pin), verdict))
    f.Close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root-dir", default="/eos/home-p/pelai/HZa/root_TnP")
    ap.add_argument("--out", default="/eos/home-p/pelai/HZa/root_TnP/fit_quality_v2.csv")
    ap.add_argument("--only", default="")
    ap.add_argument("--calibrate", action="store_true",
                    help="print metrics for the bins already judged by eye and stop")
    a = ap.parse_args()

    if a.calibrate:
        # bin02/05/06 of elid_gap_2025 were called bad by eye; the pass side of
        # the same files is visibly fine and acts as the negative control
        d = os.path.join(a.root_dir, "hza_elid_gap_2025_sf")
        print(f"{'file':<34}{'side':<6}{'chi2ndf':>10}{'relmax':>9}{'relpeak':>9}{'reltail':>9}")
        for tag, b in (("altBkgFit", "bin02"), ("altSigBkgFit", "bin05"),
                       ("altSigBkgFit", "bin06"), ("nominalFit", "bin02")):
            for fp in sorted(glob.glob(os.path.join(d, f"Data*.{tag}-{b}_*.root"))):
                for side, st, chi2, rmax, rpk, rbkg, pin, v in judge_file(fp):
                    print(f"{tag+'/'+b:<34}{side:<6}{chi2:>10.2f}{rmax:>9.3f}"
                          f"{rpk:>9.3f}{rbkg:>9.3f}   {v}")
        return 0

    meas_dirs = sorted(x for x in glob.glob(os.path.join(a.root_dir, "*")) if os.path.isdir(x))
    n = 0
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["measurement", "fitType", "sample", "bin", "side", "status",
                    "chi2ndf", "relmax", "relpeak", "reltail", "pinned", "verdict"])
        for md in meas_dirs:
            meas = os.path.basename(md)
            if a.only and a.only not in meas:
                continue
            for tag in FIT_TAGS:
                for fp in sorted(glob.glob(os.path.join(md, f"*.{tag}-bin*.root"))):
                    fn = os.path.basename(fp)
                    m = re.search(r"-(bin\d+)_", fn)
                    for side, st, chi2, rmax, rpk, rbkg, pin, v in judge_file(fp):
                        w.writerow([meas, tag, fn.split(f".{tag}-")[0],
                                    m.group(1) if m else fn, side, st,
                                    f"{chi2:.3f}", f"{rmax:.4f}", f"{rpk:.4f}",
                                    f"{rbkg:.4f}", pin, v])
                        n += 1
            fh.flush()
            print(f"[judge2] {meas}: {n} fits", flush=True)
    print(f"[judge2] DONE {a.out} ({n} fits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
