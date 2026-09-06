#!/usr/bin/env python3
"""Audit every egm_tnp_analysis fit at once, instead of one plot at a time.

Reports three things per (measurement, fitType, bin):
  * fit status != 0 on the pass or fail side;
  * parameters sitting on a boundary -- a fit that hit its limit is not a fit,
    and it is the usual reason a bin "goes bad again" after being tuned
    somewhere else;
  * empty (0-byte) plot files, which look like a browser problem but mean the
    plotting step failed and left nothing behind.

Written because the per-bin tuning lives in four independent dictionaries
(tnpParNomFitByBin / AltSig / AltBkg / AltSigBkg) applied through a series of
one-off patch scripts, so coverage drifts between fit types and the same bin
keeps resurfacing. Seeing all of it in one table is the prerequisite for fixing
that structurally.

Usage: audit_fits.py [--debug-dir DIR] [--web-dir DIR] [--out CSV]
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

FIT_TAGS = ("nominalFit", "altSigFit", "altBkgFit", "altSigBkgFit")
# a parameter within this fraction of its range end counts as pinned
EDGE_TOL = 1e-3


def pinned(par):
    lo, hi = par.getMin(), par.getMax()
    if not (lo < hi) or par.isConstant():
        return None
    span = hi - lo
    v = par.getVal()
    if v - lo < EDGE_TOL * span:
        return f"{par.GetName()}={v:.3g}@min({lo:.3g})"
    if hi - v < EDGE_TOL * span:
        return f"{par.GetName()}={v:.3g}@max({hi:.3g})"
    return None


def _walk(d, prefix=""):
    """Yield (name, object) over a TDirectory, one level into subdirectories."""
    for key in d.GetListOfKeys():
        name = key.GetName()
        obj = d.Get(name)
        if hasattr(obj, "GetListOfKeys") and not prefix:
            yield from _walk(obj, name + "/")
        else:
            yield prefix + name, obj


def audit_file(path, binname):
    """Yield (bin, side, status, pinned_pars) for every fit result in a file.

    The output layout is one file per (sample, fitType, bin), so the bin name
    comes from the filename; inside, the results are the resP/resF pair.
    """
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return
    for name, obj in _walk(f):
        if not hasattr(obj, "floatParsFinal"):
            continue
        low = name.lower()
        side = "fail" if "resf" in low else ("pass" if "resp" in low else "?")
        pars = obj.floatParsFinal()
        bad = [p for p in (pinned(pars.at(i)) for i in range(pars.getSize())) if p]
        yield binname, side, obj.status(), bad
    f.Close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    base = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--debug-dir", default=os.path.join(base, "Debug"))
    ap.add_argument("--web-dir", default="/eos/home-p/pelai/www/HZa/sfs")
    ap.add_argument("--out", default=os.path.join(base, "fit_audit.csv"))
    ap.add_argument("--only", default="", help="substring filter on measurement name")
    a = ap.parse_args()

    rows = []
    meas_dirs = sorted(d for d in glob.glob(os.path.join(a.debug_dir, "*")) if os.path.isdir(d))
    for md in meas_dirs:
        meas = os.path.basename(md)
        if a.only and a.only not in meas:
            continue
        for tag in FIT_TAGS:
            # one file per (sample, fitType, bin): <sample>.<tag>-bin<NN>_<...>.root
            for fp in sorted(glob.glob(os.path.join(md, f"*.{tag}-bin*.root"))):
                fn = os.path.basename(fp)
                sample = fn.split(f".{tag}-")[0]
                m = re.search(r"-(bin\d+)_", fn)
                binname = m.group(1) if m else fn
                for b, side, status, bad in audit_file(fp, binname):
                    if status != 0 or bad:
                        rows.append((meas, tag, sample, b, side, status, ";".join(bad)))
        print(f"[audit] {meas}: {len(rows)} issues so far", flush=True)

    # empty plots: they render as a broken image and are easy to miss
    empty = []
    for png in glob.glob(os.path.join(a.web_dir, "*", "*", "fits", "*", "*.png")):
        if os.path.getsize(png) == 0:
            empty.append(png.replace(a.web_dir + "/", ""))

    with open(a.out, "w") as fh:
        fh.write("measurement,fitType,sample,bin,side,status,pinned\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r) + "\n")
    print(f"\n[audit] wrote {a.out}: {len(rows)} problem fits")

    from collections import Counter
    by_meas = Counter(r[0] for r in rows)
    by_tag = Counter(r[1] for r in rows)
    print("\nby fit type:", dict(by_tag))
    print("\nworst measurements:")
    for m, n in by_meas.most_common(12):
        print(f"  {n:5}  {m}")
    print(f"\nempty (0-byte) plots: {len(empty)}")
    for e in empty[:15]:
        print("  " + e)
    if len(empty) > 15:
        print(f"  ... and {len(empty)-15} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
