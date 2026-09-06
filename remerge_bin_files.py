#!/usr/bin/env python3
"""Rebuild measurement-level fit files whose hadd merge silently lost everything.

`hadd -f` crashes non-deterministically on these files -- repeating the same
28-file merge sixteen times aborted five times, both from EOS and from a local
copy, so it is TFileMerger rather than the storage. tnpEGM_fitter.py called it
through os.system() and ignored the status, so a crashed merge left a ~39 kB file
that opens cleanly, reports no error, and contains no fit results at all. The
plotting step then died on a null canvas, which is where the failure finally
surfaced -- attributed to plotting rather than to the merge.

Nothing here actually needs merging: every object is named after its own bin, so
the operation is a concatenation. This rebuilds any merged file whose _resP/_resF
count does not match twice the number of per-bin files beside it. Refitting is
not required -- the per-bin results are intact.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal


def res_key_count(path):
    """Number of stored fit results, or -1 if the file will not open."""
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return -1
    n = sum(1 for k in f.GetListOfKeys()
            if k.GetName().endswith(("_resP", "_resF")))
    f.Close()
    return n


def concat(target, sources):
    tmp = target + ".rebuilding"
    out = ROOT.TFile.Open(tmp, "RECREATE")
    if not out or out.IsZombie():
        raise RuntimeError("cannot open %s" % tmp)
    nobj = 0
    for src in sources:
        fin = ROOT.TFile.Open(src)
        if not fin or fin.IsZombie():
            out.Close()
            os.remove(tmp)
            raise RuntimeError("cannot read %s" % src)
        for key in fin.GetListOfKeys():
            obj = key.ReadObj()
            if not obj:
                fin.Close(); out.Close(); os.remove(tmp)
                raise RuntimeError("unreadable %s in %s" % (key.GetName(), src))
            out.cd()
            obj.Write(key.GetName(), ROOT.TObject.kOverwrite)
            nobj += 1
        fin.Close()
    out.Close()
    # only replace the old file once the new one is complete
    os.replace(tmp, target)
    return nobj


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root-dir", default="/eos/home-p/pelai/HZa/root_TnP")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    merged = sorted(glob.glob(os.path.join(a.root_dir, "*", "*Fit.root")))
    todo = []
    for m in merged:
        per_bin = sorted(glob.glob(m.replace(".root", "-bin*.root")))
        if not per_bin:
            continue
        if res_key_count(m) != 2 * len(per_bin):
            todo.append((m, per_bin))

    print(f"{len(merged)} merged files, {len(todo)} need rebuilding")
    if a.dry_run:
        for m, pb in todo:
            print(f"  would rebuild {m} from {len(pb)} per-bin files")
        return 0

    fixed = failed = 0
    for m, per_bin in todo:
        try:
            nobj = concat(m, per_bin)
            after = res_key_count(m)
            good = after == 2 * len(per_bin)
            fixed += good
            failed += not good
            print(f"  {'OK ' if good else 'BAD'} {os.path.basename(m)}: "
                  f"{len(per_bin)} files -> {nobj} objects, {after} fit results",
                  flush=True)
        except Exception as exc:
            failed += 1
            print(f"  ERR {os.path.basename(m)}: {exc}", flush=True)

    print(f"\nrebuilt {fixed}, failed {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
