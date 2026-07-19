cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`; export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C; cd egm_tnp_analysis
B=egm_tnp_analysis.etc.config.hza_ele
RF(){ local M=$1 W=$2 ft=$3 b=$4; timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit $ft --addGaus --fitSample mcNom --iBin $b; timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit $ft --addGaus --fitSample data --iBin $b; }
RFnom(){ local M=$1 W=$2 b=$3; timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit --addGaus --fitSample mcNom --iBin $b; timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit --addGaus --fitSample data --iBin $b; }
SU(){ python3 -m egm_tnp_analysis.tnpEGM_fitter $1 --flag $2 --sumUp --exportJson; }
echo "=== refit newbatch START $(date +%H:%M:%S) ==="
M=$B.settings_htoza_elminiIso0p15_nongap_2024; W=hza_elminiIso0p15_nongap_2024_sf; RF $M $W "--altSig" 17; SU $M $W && echo "[ok] sumUp 0p15n24"
M=$B.settings_htoza_elminiIso0p1_nongap_2025; W=hza_elminiIso0p1_nongap_2025_sf; RF $M $W "--altSigBkg" 26; RFnom $M $W 24; SU $M $W && echo "[ok] sumUp 0p1n25"
M=$B.settings_htoza_elminiIso0p15_nongap_2025; W=hza_elminiIso0p15_nongap_2025_sf; RF $M $W "--altSigBkg" 35; RF $M $W "--altSigBkg" 37; SU $M $W && echo "[ok] sumUp 0p15n25"
echo "=== END $(date +%H:%M:%S) ==="
