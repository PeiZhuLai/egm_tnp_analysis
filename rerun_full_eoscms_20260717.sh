cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
B=egm_tnp_analysis.etc.config.hza_ele
# configs passed as args, e.g. bash script 0p15_nongap_2024 0p1_nongap_2024 ...
echo "=== FULL eoscms rerun START $(date +%H:%M:%S) : $* ==="
for c in "$@"; do
  MOD=$B.settings_htoza_elminiIso${c}_eoscms; WP=hza_elminiIso${c}_sf
  F() { timeout 1800 python3 -m egm_tnp_analysis.tnpEGM_fitter "$MOD" --flag "$WP" "$@"; }
  echo "--- [$c] $(date +%H:%M:%S) ---"
  F --createBins                                    && echo "[ok] createBins $c"
  F --createHists --sample mcNom                    && echo "[ok] hist mcNom $c"
  F --createHists --sample mcAlt                    && echo "[ok] hist mcAlt $c"
  F --createHists --sample data                     && echo "[ok] hist data $c"
  F --doFit --fitSample mcNom --addGaus             && echo "[ok] nominal mcNom $c"
  F --doFit --fitSample data  --addGaus             && echo "[ok] nominal data $c"
  F --doFit --altBkg    --addGaus --fitSample mcNom && echo "[ok] altBkg mcNom $c"
  F --doFit --altBkg    --addGaus --fitSample data  && echo "[ok] altBkg data $c"
  F --doFit --altSig    --addGaus --fitSample mcNom && echo "[ok] altSig mcNom $c"
  F --doFit --altSig    --addGaus --fitSample data  && echo "[ok] altSig data $c"
  F --doFit --altSigBkg --addGaus --fitSample mcNom && echo "[ok] altSigBkg mcNom $c"
  F --doFit --altSigBkg --addGaus --fitSample data  && echo "[ok] altSigBkg data $c"
  F --sumUp --exportJson                            && echo "[ok] sumUp $c"
  echo "--- DONE $c $(date +%H:%M:%S) ---"
done
echo "=== END $(date +%H:%M:%S) ==="
