#!/bin/bash
# Refit several TnP bins in one cmssw-el7 session (amortizes scram setup).
# Usage: refit_bins.sh <settings_mod> <flag> <variant> <bin1,bin2,...>
#   variant: "nom" | "--altSig" | "--altBkg" | "--altSigBkg"
set -e
cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval "$(scram runtime -sh)"
export PYTHONPATH="$CMSSW_BASE/src:${PYTHONPATH:-}"
export PYTHONIOENCODING=UTF-8 LANG=C.UTF-8 LC_ALL=C.UTF-8
cd egm_tnp_analysis
MOD=$1; FLAG=$2; VARIANT=$3; BINS=$4
EXTRA=""
[ "$VARIANT" != "nom" ] && EXTRA="$VARIANT"
for b in ${BINS//,/ }; do
  echo "==== refit $FLAG $VARIANT bin $b ===="
  python3 -m egm_tnp_analysis.tnpEGM_fitter "$MOD" --flag "$FLAG" --doFit $EXTRA --iBin "$b" 2>&1 \
    | grep -iv "TList::Clear\|already deleted" | grep -i "override\|Hessian\|created\|Plots saved" || true
done
