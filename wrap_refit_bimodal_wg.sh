cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`; export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C; cd egm_tnp_analysis
B=egm_tnp_analysis.etc.config.hza_ele
RF(){ local M=$1 W=$2 ft=$3 b=$4; timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit $ft --addGaus --fitSample mcNom --iBin $b; timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --doFit $ft --addGaus --fitSample data --iBin $b; }
echo "=== refit bimodal WG START $(date +%H:%M:%S) ==="
M=$B.settings_htoza_elminiIso0p15_nongap_2024; W=hza_elminiIso0p15_nongap_2024_sf
for b in 18 19 20 21; do RF $M $W "--altSig" $b; RF $M $W "--altSigBkg" $b; done
python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --sumUp --exportJson && echo "[ok] sumUp 2024"
M=$B.settings_htoza_elminiIso0p15_nongap_2025; W=hza_elminiIso0p15_nongap_2025_sf
for b in 18 19 20 21; do RF $M $W "--altSigBkg" $b; done
python3 -m egm_tnp_analysis.tnpEGM_fitter $M --flag $W --sumUp --exportJson && echo "[ok] sumUp 2025"
echo "=== END $(date +%H:%M:%S) ==="
