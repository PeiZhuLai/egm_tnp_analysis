cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`; export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C; cd egm_tnp_analysis
B=egm_tnp_analysis.etc.config.hza_ele
echo "=== sumUp ALL 8 START $(date +%H:%M:%S) ==="
for c in elminiIso0p15_nongap_2024 elminiIso0p15_nongap_2025 elminiIso0p1_nongap_2024 elminiIso0p1_nongap_2025 elminiIso0p15_gap_2024 elminiIso0p15_gap_2025 elminiIso0p1_gap_2024 elminiIso0p1_gap_2025; do
  python3 -m egm_tnp_analysis.tnpEGM_fitter $B.settings_htoza_$c --flag hza_${c}_sf --sumUp --exportJson && echo "[ok] $c"
done
echo "=== END $(date +%H:%M:%S) ==="
