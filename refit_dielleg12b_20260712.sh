cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
echo "=== refit dielleg12b START $(date) ==="
for cfg in dielleg12trigger_nongap_2024 dielleg12trigger_nongap_2025; do
  echo "--- $cfg ---"
  $F $B.settings_htoza_$cfg --flag hza_${cfg}_sf --doFit --fitSample mcNom
  $F $B.settings_htoza_$cfg --flag hza_${cfg}_sf --doFit --fitSample data
  $F $B.settings_htoza_$cfg --flag hza_${cfg}_sf --doFit --altSig
  $F $B.settings_htoza_$cfg --flag hza_${cfg}_sf --sumUp --exportJson
done
echo "=== refit dielleg12b END $(date) ==="
