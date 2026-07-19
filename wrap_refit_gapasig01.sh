cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`; export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C; cd egm_tnp_analysis
M=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_gap_2024; W=hza_elminiIso0p15_gap_2024_sf
echo "=== refit gap asig01 WG START $(date +%H:%M:%S) ==="
timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit --altSig --addGaus --fitSample mcNom --iBin 1
timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit --altSig --addGaus --fitSample data --iBin 1
python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --sumUp --exportJson && echo "[ok] sumUp"
echo "=== END $(date +%H:%M:%S) ==="
