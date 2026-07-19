cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
BINS="34 35 36 37 42 43 44 45"
echo "=== rerun high-ET bins 4 nongap + sumUp START $(date +%H:%M:%S) ==="
for c in elminiIso0p15_nongap_2024 elminiIso0p15_nongap_2025 elminiIso0p1_nongap_2024 elminiIso0p1_nongap_2025; do
  MOD=$B.settings_htoza_$c; WP=hza_${c}_sf
  echo "--- [$c] $(date +%H:%M:%S) ---"
  for b in $BINS; do
    $F $MOD --flag $WP --doFit --altSig    --addGaus --fitSample mcNom --iBin $b
    $F $MOD --flag $WP --doFit --altSig    --addGaus --fitSample data  --iBin $b
    $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample mcNom --iBin $b
    $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample data  --iBin $b
  done
  $F $MOD --flag $WP --sumUp --exportJson
  echo "--- DONE $c $(date +%H:%M:%S) ---"
done
echo "=== END $(date +%H:%M:%S) ==="
