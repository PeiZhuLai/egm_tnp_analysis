cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`; export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_nongap_2024; WP=hza_elminiIso0p15_nongap_2024_sf
for ft in altSig altSigBkg; do
  $F $MOD --flag $WP --doFit --$ft --addGaus --fitSample mcNom --iBin 19
  $F $MOD --flag $WP --doFit --$ft --addGaus --fitSample data  --iBin 19
done
$F $MOD --flag $WP --sumUp --exportJson
echo "restore END $(date +%H:%M:%S)"
