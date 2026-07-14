#!/bin/bash
# 2026-07-13: 重跑 8 個 elminiIso config(trigger dR-match AND->OR 修正,分母 probe 改「match 一條 leg」)。
# 在 cmssw-el7 內執行:  cmssw-el7 < rerun_miniiso_trigfix_20260713.sh
# 每檔全 stage chain,寫回 config baseOutDir(eoshome /eos/home-p/pelai/HZa/root_TnP/)。
set -uo pipefail
cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval "$(scram runtime -sh)"
export PYTHONPATH="$CMSSW_BASE/src:${PYTHONPATH:-}"
export PYTHONIOENCODING=UTF-8 LANG=C.UTF-8 LC_ALL=C.UTF-8
cd egm_tnp_analysis

FIT() { timeout -k 60 "${STAGE_TIMEOUT:-2700}" python3 -m egm_tnp_analysis.tnpEGM_fitter "$1" --flag "$2" "${@:3}"; }

run_one() {
  local name="$1"
  local mod="egm_tnp_analysis.etc.config.hza_ele.settings_htoza_${name}"
  local wp="hza_${name}_sf"
  local outdir="/eos/home-p/pelai/HZa/root_TnP/${wp}"
  timeout 120 rm -rf "$outdir" 2>/dev/null; timeout 60 mkdir -p "$outdir" 2>/dev/null
  echo "[$(date +%H:%M:%S)] START $name"
  FIT "$mod" "$wp" --createBins                 || { echo "FAIL createBins $name"; return 1; }
  FIT "$mod" "$wp" --createHists --sample mcNom  || { echo "FAIL hist mcNom $name"; return 1; }
  FIT "$mod" "$wp" --createHists --sample mcAlt  || { echo "FAIL hist mcAlt $name"; return 1; }
  FIT "$mod" "$wp" --createHists --sample data   || { echo "FAIL hist data $name"; return 1; }
  FIT "$mod" "$wp" --doFit --fitSample mcNom     || { echo "FAIL fit mcNom $name"; return 1; }
  FIT "$mod" "$wp" --doFit --fitSample data      || { echo "FAIL fit data $name"; return 1; }
  FIT "$mod" "$wp" --doFit --altSig              || { echo "FAIL altSig $name"; return 1; }
  FIT "$mod" "$wp" --doFit --altBkg              || { echo "FAIL altBkg $name"; return 1; }
  FIT "$mod" "$wp" --doFit --altSigBkg           || { echo "FAIL altSigBkg $name"; return 1; }
  FIT "$mod" "$wp" --sumUp --exportJson          || { echo "FAIL sumUp $name"; return 1; }
  echo "[$(date +%H:%M:%S)] DONE  $name"
}

CONFIGS=(
  elminiIso0p1_gap_2024   elminiIso0p1_nongap_2024
  elminiIso0p1_gap_2025   elminiIso0p1_nongap_2025
  elminiIso0p15_gap_2024  elminiIso0p15_nongap_2024
  elminiIso0p15_gap_2025  elminiIso0p15_nongap_2025
)
echo "=== rerun miniIso trig-OR fix START $(date) 共 ${#CONFIGS[@]} 檔 max_jobs=6 ==="
max_jobs="${MAX_JOBS:-6}"; pids=()
for name in "${CONFIGS[@]}"; do
  run_one "$name" &
  pids+=("$!")
  if [[ "${#pids[@]}" -eq "$max_jobs" ]]; then
    for p in "${pids[@]}"; do wait "$p" || echo "  (一個 chain FAIL,續跑)"; done
    pids=()
  fi
done
for p in "${pids[@]}"; do wait "$p" || echo "  (一個 chain FAIL)"; done
echo "=== rerun miniIso trig-OR fix END $(date) ==="