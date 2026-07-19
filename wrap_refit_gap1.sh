cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_gap_2024
WP=hza_elminiIso0p15_gap_2024_sf
F() { timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter "$MOD" --flag "$WP" "$@"; }
echo "=== refit gap bin1 altSig v2 START $(date +%H:%M:%S) ==="
F --doFit --altSig --addGaus --fitSample mcNom --iBin 1 && echo "[ok] mcNom"
F --doFit --altSig --addGaus --fitSample data  --iBin 1 && echo "[ok] data"
F --sumUp --exportJson && echo "[ok] sumUp"
echo "=== END $(date +%H:%M:%S) ==="
