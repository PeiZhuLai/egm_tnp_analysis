cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_gap_2025_eoscms
WP=hza_elminiIso0p15_gap_2025_sf
F() { timeout 900 python3 -m egm_tnp_analysis.tnpEGM_fitter "$MOD" --flag "$WP" "$@"; }
echo "=== refit gap2025 bin1,2 altSigBkg START $(date +%H:%M:%S) ==="
for b in 1 2; do
  F --doFit --altSigBkg --addGaus --fitSample mcNom --iBin $b && echo "[ok] mcNom bin$b"
  F --doFit --altSigBkg --addGaus --fitSample data  --iBin $b && echo "[ok] data bin$b"
done
F --sumUp --exportJson && echo "[ok] sumUp"
echo "=== END $(date +%H:%M:%S) ==="
