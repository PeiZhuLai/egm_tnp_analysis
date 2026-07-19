cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
c=elminiIso0p15_gap_2025; MOD=$B.settings_htoza_$c; WP=hza_${c}_sf
echo "=== v3 gap_2025 bins1,2 START $(date +%H:%M:%S) ==="
for b in 1 2; do
  timeout 900 $F $MOD --flag $WP --doFit --altSig    --addGaus --fitSample mcNom --iBin $b
  timeout 900 $F $MOD --flag $WP --doFit --altSig    --addGaus --fitSample data  --iBin $b
  timeout 900 $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample mcNom --iBin $b
  timeout 900 $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample data  --iBin $b
done
$F $MOD --flag $WP --sumUp --exportJson
echo "=== END $(date +%H:%M:%S) ==="
