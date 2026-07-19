cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
CONFIGS=(
  elminiIso0p15_gap_2024 elminiIso0p15_gap_2025 elminiIso0p15_nongap_2024 elminiIso0p15_nongap_2025
  elminiIso0p1_gap_2024 elminiIso0p1_gap_2025 elminiIso0p1_nongap_2024 elminiIso0p1_nongap_2025
)
echo "=== rollout altSigBkg --addGaus 8 configs START $(date +%H:%M:%S) ==="
for c in "${CONFIGS[@]}"; do
  MOD=$B.settings_htoza_$c; WP=hza_${c}_sf
  echo "--- [$c] $(date +%H:%M:%S) ---"
  timeout 3000 $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample mcNom || echo "FAIL mcNom $c"
  timeout 3000 $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample data  || echo "FAIL data $c"
  $F $MOD --flag $WP --sumUp --exportJson || echo "FAIL sumUp $c"
  echo "--- DONE $c $(date +%H:%M:%S) ---"
done
echo "=== rollout altSigBkg END $(date +%H:%M:%S) ==="
