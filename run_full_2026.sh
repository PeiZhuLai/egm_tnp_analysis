#!/bin/bash
# Full TnP chain for one (settings module, WP) pair.
#
# run.sh in this directory has every step except --sumUp commented out, so it cannot
# produce a measurement from scratch. This script runs the complete chain instead and
# leaves run.sh untouched (2024/2025 workflows depend on its current state).
#
# Must be executed inside cmssw-el7 (CMSSW_11_2_0 is slc7).
#   cmssw-el7 -- bash run_full_2026.sh <settings_mod> <WP>

set -uo pipefail

SETTINGS_MOD=$1
WP=$2
SRC=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src

cd "$SRC"
eval "$(scram runtime -sh)"
export PYTHONPATH="$SRC:${PYTHONPATH:-}"
export PYTHONIOENCODING=UTF-8
# tnpEGM_fitter forks a multiprocessing Pool sized to the whole machine by default
# (tnpEGM_fitter.py: len(os.sched_getaffinity(0))). On a shared lxplus node that means
# ~16 procs and ~16 GB per chain during --doFit. Cap it so N chains stay bounded.
export TNP_NPROC="${TNP_NPROC:-3}"
# the settings files use `import etc.inputs...`, so the package dir must be the CWD
cd "$SRC/egm_tnp_analysis"

fit() { python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" "$@"; }

step() {
  local name="$1"; shift
  echo "=== [$WP] $name ==="
  if ! fit "$@"; then
    echo "!!! [$WP] STEP FAILED: $name"
    return 1
  fi
}

step "checkBins"            --checkBins                          || exit 1
step "createBins"           --createBins                         || exit 1
step "createHists mcNom"    --createHists --sample mcNom         || exit 1
step "createHists mcAlt"    --createHists --sample mcAlt         || exit 1
step "createHists data"     --createHists --sample data          || exit 1
step "fit mcNom"            --doFit --fitSample mcNom            || exit 1
step "fit data"             --doFit --fitSample data             || exit 1
step "fit altSig"           --doFit --altSig                     || exit 1
step "fit altBkg"           --doFit --altBkg                     || exit 1
step "fit altSigBkg"        --doFit --altSigBkg                  || exit 1
step "sumUp"                --sumUp --exportJson                 || exit 1

echo "=== [$WP] FULL CHAIN OK ==="
