#!/bin/bash
# Correct order per config: phaseA(createBins+createHists MC) -> copy data hist -> phaseB(fits+sumUp).
# createBins overwrites the output dir, so copy data hist AFTER phaseA, before fits.
EH=/eos/home-p/pelai/HZa/root_TnP
EC=/eos/cms/store/group/phys_susy/pelai/HZa/root_TnP_local
REPO=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src/egm_tnp_analysis
LOG=$REPO/orchestrate_eoscms_v2_20260717.log
: > "$LOG"
copy_retry() {
  for t in 1 2 3 4 5 6 7 8; do
    if timeout 90 bash -c "cat '$1' > '$2'" 2>/dev/null; then
      local sz=$(timeout 30 bash -c "cat '$2' | wc -c" 2>/dev/null)
      [ "${sz:-0}" -gt 1000 ] && { echo "  copied $(basename $2) ($sz B)"; return 0; }
    fi; sleep 8
  done; echo "  FAILED copy $(basename $2)"; return 1
}
CONFIGS="0p15_nongap_2025 0p1_nongap_2024 0p1_nongap_2025"
for c in $CONFIGS; do
  yr=$(echo $c | grep -oE '202[0-9]$'); flag=hza_elminiIso${c}_sf
  # phaseA: createBins + createHists MC (in container)
  WA=$REPO/wrap_phaseA_${c}.sh; { echo "set -- $c"; cat "$REPO/phaseA_createbins_mchists_eoscms.sh"; } > "$WA"
  echo "=== [$c] $(date +%H:%M:%S) phaseA ===" | tee -a "$LOG"
  cmssw-el7 < "$WA" >> "$LOG" 2>&1
  # copy data hist AFTER createBins (which would clear it)
  echo "=== [$c] $(date +%H:%M:%S) copy data hist ===" | tee -a "$LOG"
  copy_retry "$EH/$flag/Data_${yr}_${flag}.root" "$EC/$flag/Data_${yr}_${flag}.root" | tee -a "$LOG"
  # phaseB: fits + sumUp (in container)
  WB=$REPO/wrap_phaseB_${c}.sh; { echo "set -- $c"; cat "$REPO/rerun_fitsonly_eoscms.sh"; } > "$WB"
  echo "=== [$c] $(date +%H:%M:%S) phaseB fits ===" | tee -a "$LOG"
  cmssw-el7 < "$WB" >> "$LOG" 2>&1
  echo "=== [$c] $(date +%H:%M:%S) CONFIG DONE ===" | tee -a "$LOG"
done
echo "=== ORCHESTRATE_V2 END $(date +%H:%M:%S) ===" | tee -a "$LOG"
