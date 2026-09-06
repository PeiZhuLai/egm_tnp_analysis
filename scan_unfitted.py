#!/usr/bin/env python3
"""Count fits that never actually ran, by parameter errors rather than status.

RooFitResult::status() is not a reliable marker here: after fixing the
degenerate RooCMSShape peak, fits that demonstrably ran -- parameters moved off
their initial values and all errors came back non-zero -- still report status
-1. Conversely a status of -1 was previously accompanied by every error being
exactly zero, which is the real signature of a minimisation that never happened:
MIGRAD leaves the parameters where they started and RooFit zeroes the errors.

So classify on the errors:
  UNFITTED  every floating parameter has error == 0
  PARTIAL   some errors zero, some not
  FITTED    all errors non-zero
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import sys

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

FIT_TAGS = ("nominalFit", "altSigFit", "altBkgFit", "altSigBkgFit")


def scan(path):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return []
    out = []
    for key in f.GetListOfKeys():
        name = key.GetName()
        obj = f.Get(name)
        if not hasattr(obj, "floatParsFinal"):
            continue
        low = name.lower()
        side = "fail" if "resf" in low else ("pass" if "resp" in low else "?")
        pars = obj.floatParsFinal()
        n = pars.getSize()
        nzero = sum(1 for i in range(n) if pars.at(i).getError() == 0.0)
        state = "UNFITTED" if (n and nzero == n) else ("FITTED" if nzero == 0 else "PARTIAL")
        out.append((side, obj.status(), n, nzero, state))
    f.Close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root-dir", default="/eos/home-p/pelai/HZa/root_TnP")
    ap.add_argument("--out", default="/eos/home-p/pelai/HZa/root_TnP/unfitted_scan.csv")
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    n = 0
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["measurement", "fitType", "sample", "bin", "side",
                    "status", "nFloat", "nZeroErr", "state"])
        for md in sorted(x for x in glob.glob(os.path.join(a.root_dir, "*")) if os.path.isdir(x)):
            meas = os.path.basename(md)
            if a.only and a.only not in meas:
                continue
            for tag in FIT_TAGS:
                for fp in sorted(glob.glob(os.path.join(md, f"*.{tag}-bin*.root"))):
                    fn = os.path.basename(fp)
                    m = re.search(r"-(bin\d+)_", fn)
                    for side, st, nf, nz, state in scan(fp):
                        w.writerow([meas, tag, fn.split(f".{tag}-")[0],
                                    m.group(1) if m else fn, side, st, nf, nz, state])
                        n += 1
            fh.flush()
            print(f"[scan] {meas}: {n}", flush=True)
    print(f"[scan] DONE {a.out} ({n} fits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
