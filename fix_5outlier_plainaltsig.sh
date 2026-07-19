cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
# config:bin (關 addGaus,回 plain altSig)
declare -A M=(
  [elminiIso0p1_gap_2024]=0
  [elminiIso0p15_gap_2025]=0
  [elminiIso0p1_gap_2025]=0
  [elminiIso0p1_nongap_2024]=6
  [elminiIso0p15_nongap_2025]=1
)
echo "=== fix 5 outlier bins: plain altSig START $(date +%H:%M:%S) ==="
for c in "${!M[@]}"; do
  b=${M[$c]}; MOD=$B.settings_htoza_$c; WP=hza_${c}_sf
  echo "--- [$c bin$b] ---"
  $F $MOD --flag $WP --doFit --altSig --fitSample mcNom --iBin $b
  $F $MOD --flag $WP --doFit --altSig --fitSample data  --iBin $b
  $F $MOD --flag $WP --sumUp --exportJson
done
echo "=== END $(date +%H:%M:%S) ==="
