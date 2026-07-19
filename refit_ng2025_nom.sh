cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_nongap_2025
WP=hza_elminiIso0p15_nongap_2025_sf
echo "=== refit ng2025 nom 18-21 START $(date +%H:%M:%S) ==="
for b in 18 19 20 21; do $F $MOD --flag $WP --doFit --fitSample data --iBin $b; done
echo "=== END $(date +%H:%M:%S) ==="
