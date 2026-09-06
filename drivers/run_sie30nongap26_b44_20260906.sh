#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 10
set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}
exec /afs/cern.ch/work/p/pelai/HZa/TnP/eos_retry.sh -- \
  python3 tnpEGM_fitter.py etc/config/hza_ele/settings_htoza_sielleg30trigger_nongap_2026.py \
  --flag hza_sielleg30trigger_nongap_2026_sf --altSigBkg --doFit --doPlot --iBin 44
