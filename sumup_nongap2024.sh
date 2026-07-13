cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
echo "=== sumUp nongap_2024 START $(date) ==="
$F $B.settings_htoza_dielleg12trigger_nongap_2024 --flag hza_dielleg12trigger_nongap_2024_sf --sumUp --exportJson
echo "=== sumUp nongap_2024 END $(date) rc=$? ==="
