cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`; export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C; cd egm_tnp_analysis
M=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_nongap_2024; W=hza_elminiIso0p15_nongap_2024_sf
echo "=== revert b20 altSigBkg START $(date +%H:%M:%S) ==="
timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit --altSigBkg --addGaus --fitSample mcNom --iBin 20
timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit --altSigBkg --addGaus --fitSample data --iBin 20
python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --sumUp --exportJson && echo "[ok] sumUp"
echo "=== END $(date +%H:%M:%S) ==="
