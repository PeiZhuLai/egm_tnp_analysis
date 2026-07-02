#!/bin/bash
# Usage: refit_bins.sh <SETTINGS_MOD> <WP> "<FITFLAGS>" <BIN1> [BIN2 ...]
#   FITFLAGS: extra flags for the fit mode, e.g. "" (nominal data), "--altSig",
#             "--altBkg", "--altSigBkg". Quote as one arg (may be empty "").
# Loops single-bin refits inside the already-entered cmssw-el7 container.
set -e
cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval "$(scram runtime -sh)"
export PYTHONPATH="$CMSSW_BASE/src:${PYTHONPATH:-}"
export PYTHONIOENCODING=UTF-8
export LANG=C.UTF-8 LC_ALL=C.UTF-8
cd egm_tnp_analysis
SETTINGS_MOD="$1"; WP="$2"; FITFLAGS="$3"; shift 3
# 'nom' sentinel = nominal data fit (no extra flags); empty-string args get eaten
# by the cmssw-el7/apptainer wrapper, so callers must pass 'nom' instead of ''.
[ "$FITFLAGS" = "nom" ] && FITFLAGS=""
for b in "$@"; do
  echo "=== refit bin $b ($FITFLAGS) ==="
  python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit $FITFLAGS --iBin "$b" \
    2>&1 | grep -vE "TList::Clear|already deleted|hadd (Source|Target)" | tail -4
done
