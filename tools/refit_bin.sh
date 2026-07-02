#!/bin/bash
# Usage: refit_bin.sh <SETTINGS_MOD> <WP> <FITARGS...>
# Runs a single-bin (or arbitrary) tnpEGM_fitter command inside the already-entered
# cmssw-el7 container. Caller must invoke via cmssw-el7 wrapper.
set -e
cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval "$(scram runtime -sh)"
export PYTHONPATH="$CMSSW_BASE/src:${PYTHONPATH:-}"
export PYTHONIOENCODING=UTF-8
export LANG=C.UTF-8 LC_ALL=C.UTF-8
cd egm_tnp_analysis
SETTINGS_MOD="$1"; WP="$2"; shift 2
echo "=== refit: $SETTINGS_MOD $WP $* ==="
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" "$@"
