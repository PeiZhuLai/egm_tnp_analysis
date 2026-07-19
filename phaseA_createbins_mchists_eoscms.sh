cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
B=egm_tnp_analysis.etc.config.hza_ele
for c in "$@"; do
  MOD=$B.settings_htoza_elminiIso${c}_eoscms; WP=hza_elminiIso${c}_sf
  F() { timeout 1500 python3 -m egm_tnp_analysis.tnpEGM_fitter "$MOD" --flag "$WP" "$@"; }
  echo "--- [$c phaseA] $(date +%H:%M:%S) ---"
  F --createBins                 && echo "[ok] createBins $c"
  F --createHists --sample mcNom && echo "[ok] hist mcNom $c"
  F --createHists --sample mcAlt && echo "[ok] hist mcAlt $c"
  echo "--- PHASEA DONE $c $(date +%H:%M:%S) ---"
done
