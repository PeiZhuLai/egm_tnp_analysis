cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_nongap_2024_eoscms
python3 -m egm_tnp_analysis.tnpEGM_fitter "$MOD" --flag hza_elminiIso0p15_nongap_2024_sf --sumUp --exportJson
echo "SUMUP_EXIT=$?"
