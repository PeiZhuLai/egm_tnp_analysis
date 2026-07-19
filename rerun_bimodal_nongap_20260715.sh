cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
echo "=== rerun bimodal bins 18-21 (3 configs) + sumUp 4 nongap START $(date +%H:%M:%S) ==="
for c in elminiIso0p15_nongap_2025 elminiIso0p1_nongap_2024 elminiIso0p1_nongap_2025; do
  MOD=$B.settings_htoza_$c; WP=hza_${c}_sf
  echo "--- [$c] altSig addGaus 18-21 $(date +%H:%M:%S) ---"
  for b in 18 19 20 21; do
    $F $MOD --flag $WP --doFit --altSig --addGaus --fitSample mcNom --iBin $b
    $F $MOD --flag $WP --doFit --altSig --addGaus --fitSample data  --iBin $b
  done
done
echo "--- sumUp 全 4 nongap ---"
for c in elminiIso0p15_nongap_2024 elminiIso0p15_nongap_2025 elminiIso0p1_nongap_2024 elminiIso0p1_nongap_2025; do
  $F $B.settings_htoza_$c --flag hza_${c}_sf --sumUp --exportJson
done
echo "=== END $(date +%H:%M:%S) ==="
