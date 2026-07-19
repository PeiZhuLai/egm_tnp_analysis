cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
BINS="16 17 22 23 24 25 26 27 28 29 30 31"
echo "=== rerun mid-ET cfg2-4 (4 fit) + sumUp START $(date +%H:%M:%S) ==="
for c in elminiIso0p15_nongap_2025 elminiIso0p1_nongap_2024 elminiIso0p1_nongap_2025; do
  MOD=$B.settings_htoza_$c; WP=hza_${c}_sf
  echo "--- [$c] $(date +%H:%M:%S) ---"
  for b in $BINS; do
    timeout 900 $F $MOD --flag $WP --doFit --fitSample mcNom --addGaus --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit --fitSample data  --addGaus --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit --altBkg    --addGaus --fitSample mcNom --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit --altBkg    --addGaus --fitSample data  --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit --altSig    --addGaus --fitSample mcNom --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit --altSig    --addGaus --fitSample data  --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample mcNom --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample data  --iBin $b
  done
  $F $MOD --flag $WP --sumUp --exportJson
  echo "--- DONE $c $(date +%H:%M:%S) ---"
done
echo "=== END $(date +%H:%M:%S) ==="
