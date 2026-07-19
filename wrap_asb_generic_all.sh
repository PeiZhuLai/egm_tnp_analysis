cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`; export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C; cd egm_tnp_analysis
B=egm_tnp_analysis.etc.config.hza_ele
echo "=== altSigBkg generic ALL configs START $(date +%H:%M:%S) ==="
for c in elminiIso0p15_nongap_2024 elminiIso0p15_nongap_2025 elminiIso0p1_nongap_2024 elminiIso0p1_nongap_2025 elminiIso0p15_gap_2024 elminiIso0p15_gap_2025 elminiIso0p1_gap_2024 elminiIso0p1_gap_2025; do
  M=$B.settings_htoza_$c; W=hza_${c}_sf
  echo "--- [$c] $(date +%H:%M:%S) ---"
  timeout 1500 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit --altSigBkg --addGaus --fitSample mcNom && echo "[ok] mcNom $c"
  timeout 1500 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit --altSigBkg --addGaus --fitSample data && echo "[ok] data $c"
  python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --sumUp --exportJson && echo "[ok] sumUp $c"
  echo "--- DONE $c $(date +%H:%M:%S) ---"
done
echo "=== END $(date +%H:%M:%S) ==="
