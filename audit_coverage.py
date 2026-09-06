#!/usr/bin/env python3
"""Audit fit coverage against what *should* exist, not against what happens to be on disk.

find_missing_fits.py globs the result files that are already there and flags the
stale or unconverged ones. That misses the case this whole investigation turned
on: a bin whose file was never written at all, because the job segfaulted on a
null pdf and hung until MaxRuntime killed it. Those bins are silently absent from
a glob-based scan, so the gap count looked like it had plateaued at 4325 when the
real number was larger.

Here the expected set is derived from the binning (bining.pkl in each
measurement's output directory) crossed with the samples and fit types actually
requested in the job list. Every (measurement, sample, fitType, bin) is then
classified:

  MISSING   no result file on disk
  UNFITTED  file exists but every floating parameter error is zero
  PARTIAL   some errors zero, some not
  FITTED    all errors non-zero

Only FITTED counts as done. MISSING and UNFITTED both mean "resubmit"; they are
reported separately because they point at different failures -- a job that never
produced output versus one that produced output no minimiser ever touched.
"""
from __future__ import annotations

import argparse
import glob
import os
import pickle
import re
import sys
from collections import Counter, defaultdict

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

TAG_OF = {"nominal": "nominalFit", "altSig": "altSigFit",
          "altBkg": "altBkgFit", "altSigBkg": "altSigBkgFit"}
# sample argument -> the prefix the framework gives the output files
PREFIX_RE = {"data": re.compile(r"^Data_"),
             "mcNom": re.compile(r"^DY_MC_LO_"),
             "mcAlt": re.compile(r"^DY_MC_NLO_")}


def base_out_dir(settings_path):
    """Read baseOutDir straight out of the settings file (no import, no side effects)."""
    with open(settings_path) as fh:
        for line in fh:
            if line.strip().startswith("baseOutDir"):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


def classify(path):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return "MISSING"
    # Judge each side on its own. A file holds resP and resF, and counting their
    # parameters together hides the case this whole exercise is about: one side
    # never minimised -- every one of its errors exactly zero, parameters left on
    # the config's initial values -- while the other side is fine. Pooled, that
    # file shows both zero and non-zero errors and comes out "PARTIAL", which
    # reads like a bin with a parameter on a limit. It is not: half the fit did
    # not happen, and its uncertainties are meaningless.
    sides = {}
    for key in f.GetListOfKeys():
        name = key.GetName()
        if not name.endswith(("_resP", "_resF")):
            continue
        obj = f.Get(name)
        if not hasattr(obj, "floatParsFinal"):
            continue
        pars = obj.floatParsFinal()
        n = pars.getSize()
        if not n:
            continue
        zero = sum(1 for i in range(n) if pars.at(i).getError() == 0.0)
        sides[name[-1]] = "UNFITTED" if zero == n else ("PARTIAL" if zero else "FITTED")
    f.Close()
    if not sides:
        return "MISSING"
    # worst side wins: an unfitted half makes the whole bin unusable
    for verdict in ("UNFITTED", "PARTIAL"):
        if verdict in sides.values():
            return verdict
    return "FITTED"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--joblist", default="condor_fit/joblist.txt",
                    help="(settings, flag, sample, fitType) rows defining what was asked for")
    ap.add_argument("--out", default="condor_fit/joblist_gaps.txt")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    wanted = [l.split() for l in open(a.joblist) if l.strip()]

    # cache the per-measurement binning and file listing: one readdir per directory
    bins_of, listing_of, dir_of = {}, {}, {}
    for cfg, flag, _s, _ft in wanted:
        if flag in bins_of:
            continue
        d = os.path.join(base_out_dir(cfg) or "", flag)
        dir_of[flag] = d
        pkl = os.path.join(d, "bining.pkl")
        try:
            with open(pkl, "rb") as fh:
                bins_of[flag] = pickle.load(fh)["bins"]
        except Exception as exc:
            bins_of[flag] = None
            if not a.quiet:
                print(f"[coverage] {flag}: cannot read binning ({exc.__class__.__name__}) -> skipped",
                      flush=True)
            continue
        try:
            listing_of[flag] = set(os.listdir(d))
        except OSError:
            listing_of[flag] = set()

    rows, tally = [], Counter()
    per_combo = defaultdict(Counter)
    for cfg, flag, sample, ft in wanted:
        bins = bins_of.get(flag)
        if bins is None:
            continue
        tag, pre = TAG_OF[ft], PREFIX_RE[sample]
        for ib, b in enumerate(bins):
            want = f".{tag}-bin%02d_{b['name'].split('_', 1)[1]}.root" % ib
            hit = [n for n in listing_of[flag] if n.endswith(want) and pre.match(n)]
            verdict = classify(os.path.join(dir_of[flag], hit[0])) if hit else "MISSING"
            tally[verdict] += 1
            per_combo[(sample, ft)][verdict] += 1
            if verdict != "FITTED":
                rows.append(f"{cfg} {flag} {sample} {ft} {ib}")
        if not a.quiet:
            print(f"[coverage] {flag} {sample:6s} {ft:9s}: running total {len(rows)} to redo",
                  flush=True)

    with open(a.out, "w") as fh:
        fh.write("\n".join(rows) + ("\n" if rows else ""))

    total = sum(tally.values())
    print(f"\n=== coverage over {total} expected (measurement, sample, fitType, bin) ===")
    for k in ("FITTED", "PARTIAL", "UNFITTED", "MISSING"):
        print(f"  {k:9s} {tally[k]:6d}   {100.0 * tally[k] / total if total else 0:5.1f}%")
    print(f"\n=== not-FITTED by (sample, fitType) ===")
    for k in sorted(per_combo):
        c = per_combo[k]
        bad = c["PARTIAL"] + c["UNFITTED"] + c["MISSING"]
        if bad:
            print(f"  {k[0]:6s} {k[1]:9s}: {bad:5d} bad "
                  f"(missing {c['MISSING']}, unfitted {c['UNFITTED']}, partial {c['PARTIAL']})")
    print(f"\nwrote {a.out}: {len(rows)} jobs to redo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
