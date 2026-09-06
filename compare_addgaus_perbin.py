#!/usr/bin/env python3
"""Per-bin verdict on whether the extra shoulder Gaussian helps.

The first pass ran --addGaus globally and only kept the totals (699 better, 1766
worse, 2677 unchanged). That was enough to reject switching it on everywhere, but
not to say *which* bins it helps -- and the revert then destroyed the results, so
the list had to be earned again. This writes the per-bin detail to disk first, so
a later revert cannot lose it.

Judgement uses the same statistics-aware metric the tune list settled on: the
largest relative residual over mass bins near the peak that hold at least
MIN_ENTRIES events, plus its Poisson pull. Relative size alone flags low-count
bins where a 20% residual is noise; the pull alone anti-correlates with what is
actually wrong, because a huge-statistics bin gets a large pull from a shape
error too small to matter.
"""
from __future__ import annotations

import argparse
import csv
import glob
import math
import os
import sys
from collections import Counter

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

MIN_ENTRIES = 100      # below this the relative residual is dominated by Poisson noise
PEAK_HALFWIDTH = 5.0   # GeV around the maximum


def frames(path):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return None, {}
    out = {}

    def collect(pad):
        hist = curve = side = None
        for prim in pad.GetListOfPrimitives():
            name = prim.GetName() or ""
            if prim.InheritsFrom("TPad"):
                collect(prim)
            elif prim.InheritsFrom("RooHist"):
                hist, side = prim, ("fail" if "Fail" in name else "pass")
            elif prim.InheritsFrom("RooCurve") and "Comp[" not in name:
                curve = prim
        if hist is not None and curve is not None and side:
            out[side] = (hist, curve)

    for key in f.GetListOfKeys():
        obj = key.ReadObj()
        if obj.InheritsFrom("TCanvas"):
            collect(obj)
    return f, out


def measure(path):
    """{side: (rel, pull)} plus the efficiency, or None if unreadable."""
    if not os.path.exists(path):
        return None
    f, fr = frames(path)
    if f is None:
        return None
    per_side, nsig = {}, {}
    for side, (hist, curve) in fr.items():
        pts = [(hist.GetPointX(i), hist.GetPointY(i))
               for i in range(hist.GetN()) if hist.GetPointY(i) > 0]
        if not pts:
            continue
        peak = max(y for _, y in pts)
        x_peak = next(x for x, y in pts if y == peak)
        near = [(x, y, curve.Eval(x)) for x, y in pts
                if abs(x - x_peak) <= PEAK_HALFWIDTH and y >= MIN_ENTRIES]
        if not near:
            continue
        x, y, c = max(near, key=lambda t: abs(t[1] - t[2]) / t[1])
        per_side[side] = (abs(y - c) / y, abs(y - c) / math.sqrt(y))
    for key in f.GetListOfKeys():
        name = key.GetName()
        if name.endswith(("_resP", "_resF")):
            res = f.Get(name)
            pars = res.floatParsFinal()
            for i in range(pars.getSize()):
                if pars.at(i).GetName().startswith("nSig"):
                    nsig[name[-4:]] = pars.at(i).getVal()
    f.Close()
    eff = None
    if "resP" in nsig and "resF" in nsig:
        tot = nsig["resP"] + nsig["resF"]
        eff = nsig["resP"] / tot if tot else None
    return per_side, eff


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--new", default="/eos/home-p/pelai/HZa/root_TnP",
                    help="tree holding the --addGaus results")
    ap.add_argument("--base", default="/eos/home-p/pelai/HZa/root_TnP_backup_pre_addgaus_20260807",
                    help="tree holding the baseline (no addGaus) results")
    ap.add_argument("--fit-type", default="nominalFit")
    ap.add_argument("--out", default="condor_fit/addgaus_perbin_nominal.csv")
    ap.add_argument("--min-gain", type=float, default=0.005,
                    help="relative-residual drop that counts as an improvement")
    a = ap.parse_args()

    rows, tally = [], Counter()
    for meas in sorted(os.listdir(a.base)):
        for new in sorted(glob.glob(os.path.join(a.new, meas, "*.%s-bin*.root" % a.fit_type))):
            base = os.path.join(a.base, meas, os.path.basename(new))
            before, after = measure(base), measure(new)
            if before is None or after is None:
                tally["無法比較"] += 1
                continue
            fname = os.path.basename(new)
            sample = fname.split("_hza")[0]
            ibin = int(fname.split(".%s-bin" % a.fit_type)[1][:2])
            for side in ("pass", "fail"):
                if side not in before[0] or side not in after[0]:
                    continue
                rb, pb = before[0][side]
                ra, pa = after[0][side]
                delta = ra - rb
                verdict = ("改善" if delta < -a.min_gain else
                           "變差" if delta > a.min_gain else "持平")
                tally[verdict] += 1
                rows.append(dict(measurement=meas, sample=sample, bin=ibin, side=side,
                                 rel_before="%.4f" % rb, rel_after="%.4f" % ra,
                                 pull_before="%.1f" % pb, pull_after="%.1f" % pa,
                                 delta_rel="%+.4f" % delta, verdict=verdict,
                                 eff_before="%.5f" % (before[1] or 0),
                                 eff_after="%.5f" % (after[1] or 0),
                                 delta_eff="%+.5f" % ((after[1] or 0) - (before[1] or 0))))

    rows.sort(key=lambda r: float(r["delta_rel"]))
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else
                           ["measurement", "sample", "bin", "side", "verdict"])
        w.writeheader()
        w.writerows(rows)

    total = sum(tally[k] for k in ("改善", "變差", "持平"))
    print("=== %s: %d 個可比較的 (bin, side) ===" % (a.fit_type, total))
    for k in ("改善", "變差", "持平", "無法比較"):
        if tally[k]:
            print("  %-6s %5d  %5.1f%%" % (k, tally[k], 100.0 * tally[k] / total if total else 0))

    # the actionable output: bins where the Gaussian helps, per measurement
    gain = {}
    for r in rows:
        if r["verdict"] == "改善":
            gain.setdefault(r["measurement"], set()).add(r["bin"])
    print("\n=== 建議開啟 addGaus 的 bin（改善者）===")
    for m in sorted(gain):
        print("  %-34s addGausBins = %s" % (m, tuple(sorted(gain[m]))))
    print("\nwrote %s: %d 列" % (a.out, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
