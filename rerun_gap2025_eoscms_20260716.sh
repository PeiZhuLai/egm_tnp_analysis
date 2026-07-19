cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
MOD=egm_tnp_analysis.etc.config.hza_ele.settings_htoza_elminiIso0p15_gap_2025_eoscms
WP=hza_elminiIso0p15_gap_2025_sf
FIT() { timeout 1500 python3 -m egm_tnp_analysis.tnpEGM_fitter "$MOD" --flag "$WP" "$@"; }
echo "=== gap_2025 FULL on eoscms START $(date +%H:%M:%S) ==="
FIT --createBins                              && echo "[ok] createBins"
FIT --createHists --sample mcNom              && echo "[ok] hist mcNom"
FIT --createHists --sample mcAlt              && echo "[ok] hist mcAlt"
FIT --createHists --sample data               && echo "[ok] hist data"
FIT --doFit --fitSample mcNom --addGaus       && echo "[ok] nominal mcNom"
FIT --doFit --fitSample data  --addGaus       && echo "[ok] nominal data"
FIT --doFit --altBkg    --addGaus --fitSample mcNom && echo "[ok] altBkg mcNom"
FIT --doFit --altBkg    --addGaus --fitSample data  && echo "[ok] altBkg data"
FIT --doFit --altSig    --addGaus --fitSample mcNom && echo "[ok] altSig mcNom"
FIT --doFit --altSig    --addGaus --fitSample data  && echo "[ok] altSig data"
FIT --doFit --altSigBkg --addGaus --fitSample mcNom && echo "[ok] altSigBkg mcNom"
FIT --doFit --altSigBkg --addGaus --fitSample data  && echo "[ok] altSigBkg data"
FIT --sumUp --exportJson                      && echo "[ok] sumUp"
echo "=== END $(date +%H:%M:%S) ==="
