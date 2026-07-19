cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p1_nongap_2024_eoscms
WP=hza_elminiIso0p1_nongap_2024_sf
F() { timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter "$MOD" --flag "$WP" "$@"; }
echo "=== refit bin19,20 altSig START $(date +%H:%M:%S) ==="
for b in 19 20; do
  F --doFit --altSig --addGaus --fitSample mcNom --iBin $b && echo "[ok] altSig mcNom bin$b"
  F --doFit --altSig --addGaus --fitSample data  --iBin $b && echo "[ok] altSig data bin$b"
done
F --sumUp --exportJson && echo "[ok] sumUp"
echo "=== END $(date +%H:%M:%S) ==="
