#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 10
set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}
exec /afs/cern.ch/work/p/pelai/HZa/TnP/eos_retry.sh -- \
  python3 tnpEGM_fitter.py etc/config/settings_resolve_pho_lowpt_2023preBPix.py \
  --flag hza_resolve_phid_lowpt_2023preBPix_sf --altSigBkg --doFit --doPlot --iBin 7
