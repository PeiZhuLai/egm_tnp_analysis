#!/bin/bash
# Orchestrate eoscms fits for remaining nongap configs: copy existing hists eoshome->eoscms
# (bypass slow 86M-entry createHists data), then createBins + fits + sumUp on eoscms.
EH=/eos/home-p/pelai/HZa/root_TnP
EC=/eos/cms/store/group/phys_susy/pelai/HZa/root_TnP_local
REPO=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src/egm_tnp_analysis
LOG=$REPO/orchestrate_eoscms_nongap_20260717.log
: > "$LOG"
copy_retry() { # $1 src $2 dst
  for t in 1 2 3 4 5 6 7 8; do
    if timeout 90 bash -c "cat '$1' > '$2'" 2>/dev/null; then
      local sz=$(timeout 30 bash -c "cat '$2' | wc -c" 2>/dev/null)
      [ "${sz:-0}" -gt 1000 ] && { echo "  copied $(basename $2) ($sz B)"; return 0; }
    fi; sleep 8
  done; echo "  FAILED copy $(basename $2)"; return 1
}
for c in 0p15_nongap_2025 0p1_nongap_2024 0p1_nongap_2025; do
  yr=$(echo $c | grep -oE '202[0-9]$'); flag=hza_elminiIso${c}_sf
  echo "=== [$c] $(date +%H:%M:%S) copying hists ===" | tee -a "$LOG"
  mkdir -p "$EC/$flag" 2>/dev/null
  copy_retry "$EH/$flag/Data_${yr}_${flag}.root"       "$EC/$flag/Data_${yr}_${flag}.root"       | tee -a "$LOG"
  copy_retry "$EH/$flag/DY_MC_LO_${yr}_${flag}.root"   "$EC/$flag/DY_MC_LO_${yr}_${flag}.root"   | tee -a "$LOG"
  copy_retry "$EH/$flag/DY_MC_NLO_${yr}_${flag}.root"  "$EC/$flag/DY_MC_NLO_${yr}_${flag}.root"  | tee -a "$LOG"
  # container: createBins + fits + sumUp (NO createHists; hists pre-copied)
  WRAP=$REPO/wrap_eoscmsfit_${c}.sh
  { echo "set -- $c"; cat "$REPO/rerun_createbins_fits_eoscms.sh"; } > "$WRAP"
  echo "=== [$c] $(date +%H:%M:%S) container fits ===" | tee -a "$LOG"
  cmssw-el7 < "$WRAP" >> "$LOG" 2>&1
  echo "=== [$c] $(date +%H:%M:%S) done ===" | tee -a "$LOG"
done
echo "=== ORCHESTRATE END $(date +%H:%M:%S) ===" | tee -a "$LOG"
