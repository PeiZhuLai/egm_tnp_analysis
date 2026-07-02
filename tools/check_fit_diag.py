#!/usr/bin/env python3
"""Summarise tnp fit_diagnostics JSONs: per-bin fit status, efficiency, and any
RooFit parameters that ended railed against their min/max bound.

Usage: check_fit_diag.py <fit_diagnostics/<measurement>/<sample>/<fitType>> [bin ...]
If bins are given, only those indices are shown; otherwise all bins.
"""
import json
import os
import sys


def railed(par, tol_frac=0.001):
    lo, hi, v = par.get("min"), par.get("max"), par.get("value")
    if lo is None or hi is None or v is None or hi == lo:
        return None
    span = hi - lo
    if v - lo <= tol_frac * span:
        return "min"
    if hi - v <= tol_frac * span:
        return "max"
    return None


def main():
    d = sys.argv[1]
    wanted = set(int(b) for b in sys.argv[2:]) if len(sys.argv) > 2 else None
    files = sorted(f for f in os.listdir(d) if f.startswith("bin") and f.endswith(".json"))
    for f in files:
        with open(os.path.join(d, f)) as fh:
            j = json.load(fh)
        idx = j["bin"]["index"]
        if wanted is not None and idx not in wanted:
            continue
        fr = j.get("fit_result", {})
        eff = j.get("derived", {}).get("efficiency")
        rail_msgs = []
        for leg in ("pass", "fail"):
            block = fr.get(leg, {})
            for p in block.get("floatParsFinal", []):
                r = railed(p)
                if r and p["name"] not in ("nBkgP", "nBkgF", "nSigP", "nSigF"):
                    rail_msgs.append("%s.%s=%.3g@%s" % (leg, p["name"], p["value"], r))
        sp = fr.get("pass", {}).get("status")
        sfst = fr.get("fail", {}).get("status")
        eff_s = "%.4f" % eff if eff is not None else "  ?  "
        print("bin%02d eff=%s statusP/F=%s/%s  railed: %s"
              % (idx, eff_s, sp, sfst, ", ".join(rail_msgs) if rail_msgs else "-"))


if __name__ == "__main__":
    main()
