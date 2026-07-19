cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
run_bins () { local c=$1 ft=$2; shift 2; local MOD=$B.settings_htoza_$c WP=hza_${c}_sf
  for b in "$@"; do
    timeout 900 $F $MOD --flag $WP --doFit $ft --addGaus --fitSample mcNom --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit $ft --addGaus --fitSample data  --iBin $b
  done; }
echo "=== v3 config4 + gap START $(date +%H:%M:%S) ==="

# config4 nongap (interrupted by EOS degradation)
c=elminiIso0p1_nongap_2025; echo "--- [$c] $(date +%H:%M:%S) ---"
run_bins $c "--altSig"    18 19 20 21
run_bins $c "--altSigBkg" 18 19 20 21
$F $B.settings_htoza_$c --flag hza_${c}_sf --sumUp --exportJson
echo "--- DONE $c $(date +%H:%M:%S) ---"

# Group C: gap v3 bins 1,2 (0p15 gap 2024/2025)
for c in elminiIso0p15_gap_2024 elminiIso0p15_gap_2025; do
  echo "--- [$c] $(date +%H:%M:%S) ---"
  run_bins $c "--altSig"    1 2
  run_bins $c "--altSigBkg" 1 2
  $F $B.settings_htoza_$c --flag hza_${c}_sf --sumUp --exportJson
  echo "--- DONE $c $(date +%H:%M:%S) ---"
done
echo "=== END $(date +%H:%M:%S) ==="
