cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
for c in nongap_2025 gap_2025; do
  echo "=== sumUp $c START $(date) ==="
  $F $B.settings_htoza_dielleg12trigger_${c} --flag hza_dielleg12trigger_${c}_sf --sumUp --exportJson
  echo "=== sumUp $c END rc=$? ==="
done
