cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
c=elminiIso0p15_gap_2024; MOD=$B.settings_htoza_$c; WP=hza_${c}_sf
echo "=== rerun altSigBkg bin5 ($c) START $(date +%H:%M:%S) ==="
timeout 900 $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample mcNom --iBin 5
timeout 900 $F $MOD --flag $WP --doFit --altSigBkg --addGaus --fitSample data  --iBin 5
$F $MOD --flag $WP --sumUp --exportJson
echo "=== END $(date +%H:%M:%S) ==="
