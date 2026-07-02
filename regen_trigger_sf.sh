#!/bin/bash
# Regenerate the SF/efficiency summary plots (sumUp) for all electron trigger
# flags in one cmssw-el7 session, so the widened Efficiency y-axis takes effect.
set -e
cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval "$(scram runtime -sh)"
export PYTHONPATH="$CMSSW_BASE/src:${PYTHONPATH:-}"
export PYTHONIOENCODING=UTF-8 LANG=C.UTF-8 LC_ALL=C.UTF-8
cd egm_tnp_analysis
for base in \
  dielleg12trigger_gap_2024 dielleg12trigger_gap_2025 dielleg12trigger_nongap_2024 dielleg12trigger_nongap_2025 \
  dielleg23trigger_gap_2024 dielleg23trigger_gap_2025 dielleg23trigger_nongap_2024 dielleg23trigger_nongap_2025 \
  sielleg30trigger_gap_2024 sielleg30trigger_gap_2025 sielleg30trigger_nongap_2024 sielleg30trigger_nongap_2025 ; do
  echo "==== sumUp $base ===="
  python3 -m egm_tnp_analysis.tnpEGM_fitter \
    "egm_tnp_analysis.etc.config.hza_ele.settings_htoza_${base}" \
    --flag "hza_${base}_sf" --sumUp --exportJson 2>&1 \
    | grep -iv "TList::Clear\|already deleted" | grep -i "Plot controls\|JSON written\|Error\|Traceback" || true
done
