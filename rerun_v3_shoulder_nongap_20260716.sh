cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
run_bins () {  # $1=cfg $2=fittype-flag $3=bins
  local c=$1 ft=$2; shift 2
  local MOD=$B.settings_htoza_$c WP=hza_${c}_sf
  for b in "$@"; do
    timeout 900 $F $MOD --flag $WP --doFit $ft --addGaus --fitSample mcNom --iBin $b
    timeout 900 $F $MOD --flag $WP --doFit $ft --addGaus --fitSample data  --iBin $b
  done
}
echo "=== v3 shoulder rollout nongap START $(date +%H:%M:%S) ==="

c=elminiIso0p15_nongap_2024; echo "--- [$c] $(date +%H:%M:%S) ---"
run_bins $c "--altSig"    17 18 19 20 21
run_bins $c "--altSigBkg" 18 19 20 21
$F $B.settings_htoza_$c --flag hza_${c}_sf --sumUp --exportJson
echo "--- DONE $c $(date +%H:%M:%S) ---"

c=elminiIso0p15_nongap_2025; echo "--- [$c] $(date +%H:%M:%S) ---"
run_bins $c "--altSig"    18 19 20 21
run_bins $c "--altSigBkg" 18 19 20 21
$F $B.settings_htoza_$c --flag hza_${c}_sf --sumUp --exportJson
echo "--- DONE $c $(date +%H:%M:%S) ---"

c=elminiIso0p1_nongap_2024; echo "--- [$c] $(date +%H:%M:%S) ---"
run_bins $c "--altSig"    16 18 19 20 21 24
run_bins $c "--altSigBkg" 12 18 19 20 21 22 30
$F $B.settings_htoza_$c --flag hza_${c}_sf --sumUp --exportJson
echo "--- DONE $c $(date +%H:%M:%S) ---"

c=elminiIso0p1_nongap_2025; echo "--- [$c] $(date +%H:%M:%S) ---"
run_bins $c "--altSig"    18 19 20 21
run_bins $c "--altSigBkg" 18 19 20 21
$F $B.settings_htoza_$c --flag hza_${c}_sf --sumUp --exportJson
echo "--- DONE $c $(date +%H:%M:%S) ---"

echo "=== END $(date +%H:%M:%S) ==="
