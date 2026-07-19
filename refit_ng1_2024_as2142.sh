cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p1_nongap_2024
WP=hza_elminiIso0p1_nongap_2024_sf
echo "=== refit 0p1_ng2024 altSig bin21,42 START $(date +%H:%M:%S) ==="
for b in 21 42; do $F $MOD --flag $WP --doFit --altSig --iBin $b; done
echo "=== END $(date +%H:%M:%S) ==="
