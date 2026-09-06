#!/usr/bin/env python3
"""List the (measurement, sample, fitType, bin) fits that still need running.

The first condor pass grouped a whole measurement into one job, which works for
the many fast bins but not for the occasional pathological one: the test job
spent 8 minutes on 25 bins and 80 minutes on a single one, so jobs that contain
several such bins run into the 6 h cap and are killed. Their finished bins
survive -- the fitter writes each bin's file as it goes -- so the fix is to find
what is still missing and resubmit only that, one bin per job.

"Needs running" means the result file is either absent, older than the cutoff
(i.e. left over from before the histFitter fix), or present but with every
parameter error zero, which is the signature of a fit that never minimised.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import time

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

FIT_TAGS = ("nominalFit", "altSigFit", "altBkgFit", "altSigBkgFit")
TAG_TO_ARG = {"nominalFit": "nominal", "altSigFit": "altSig",
              "altBkgFit": "altBkg", "altSigBkgFit": "altSigBkg"}
SAMPLE_OF = {"Data": "data"}   # anything else is MC; refined below


def fit_is_good(path):
    """True if the file holds results whose errors are not all zero."""
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return False
    ok = False
    for key in f.GetListOfKeys():
        obj = f.Get(key.GetName())
        if not hasattr(obj, "floatParsFinal"):
            continue
        pars = obj.floatParsFinal()
        n = pars.getSize()
        if n and any(pars.at(i).getError() != 0.0 for i in range(n)):
            ok = True
    f.Close()
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root-dir", default="/eos/home-p/pelai/HZa/root_TnP")
    ap.add_argument("--joblist", default="condor_fit/joblist.txt",
                    help="the original (settings, flag, sample, fitType) list")
    ap.add_argument("--cutoff", default="2026-08-05 03:00",
                    help="results older than this predate the histFitter fix")
    ap.add_argument("--out", default="condor_fit/joblist_missing.txt")
    a = ap.parse_args()

    cutoff = time.mktime(time.strptime(a.cutoff, "%Y-%m-%d %H:%M"))

    # sample name in the file -> --fitSample argument
    def sample_arg(fname):
        if fname.startswith("Data"):
            return "data"
        return "mcAlt" if "NLO" in fname else "mcNom"

    # measurement -> settings path + flag, from the original job list
    meas_info = {}
    for line in open(a.joblist):
        cfg, flag, _s, _ft = line.split()
        meas_info[flag] = (cfg, flag)

    rows = []
    for md in sorted(x for x in glob.glob(os.path.join(a.root_dir, "*")) if os.path.isdir(x)):
        meas = os.path.basename(md)
        if meas not in meas_info:
            continue
        cfg, flag = meas_info[meas]
        for tag, arg in TAG_TO_ARG.items():
            for fp in sorted(glob.glob(os.path.join(md, f"*.{tag}-bin*.root"))):
                fn = os.path.basename(fp)
                m = re.search(r"-bin(\d+)_", fn)
                if not m:
                    continue
                ibin = int(m.group(1))
                stale = os.path.getmtime(fp) < cutoff
                if stale or not fit_is_good(fp):
                    rows.append(f"{cfg} {flag} {sample_arg(fn)} {arg} {ibin}")
        print(f"[missing] {meas}: {len(rows)} so far", flush=True)

    rows = sorted(set(rows))
    with open(a.out, "w") as fh:
        fh.write("\n".join(rows) + ("\n" if rows else ""))
    print(f"[missing] wrote {a.out}: {len(rows)} (measurement, sample, fitType, bin) jobs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
