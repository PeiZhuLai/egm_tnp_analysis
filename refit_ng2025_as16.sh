cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_nongap_2025
WP=hza_elminiIso0p15_nongap_2025_sf
echo "=== refit ng2025 altSig bin16 START $(date +%H:%M:%S) ==="
$F $MOD --flag $WP --doFit --altSig --iBin 16
echo "=== END $(date +%H:%M:%S) ==="
