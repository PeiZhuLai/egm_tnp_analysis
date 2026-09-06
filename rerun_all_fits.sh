#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Re-run every egm_tnp fit after the histFitter.C fixes (RooCMSShape peak fixed
# for data; HistPdf interpolation order 3 -> 1).
#
# 40% of the stored fits (5363/13516) had never actually run: MnHesse hit a zero
# second derivative on the degenerate peak parameter, the Hessian came back
# invalid, and RooFit left every parameter at its starting value with zero
# errors while still drawing a plausible curve. Tuning per-bin parameters could
# not stick because for those bins no minimisation was happening at all.
#
# Runs 6 measurements at a time (the lxplus foreground limit), one log each.
#   bash rerun_all_fits.sh [settings-name-filter]
# ---------------------------------------------------------------------------
cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src/egm_tnp_analysis || exit 10
source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:$PYTHONPATH

FILTER="${1:-}"
LOGDIR=/eos/home-p/pelai/HZa/root_TnP/rerun_logs
mkdir -p "$LOGDIR"
MAXPAR=6
log(){ echo "[rerun $(date '+%F %T')] $*"; }

run_one() {   # $1 = settings path
  local cfg="$1" name flag rc=0
  name=$(basename "$cfg" .py); name=${name#settings_htoza_}
  # the flag is the single key of the settings' flags dict
  flag=$(python3 - "$cfg" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("s", sys.argv[1])
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
    print(sorted(m.flags)[0])
except Exception:
    print("")
PY
)
  [ -z "$flag" ] && { echo "[skip] $name: cannot read flag" > "$LOGDIR/$name.log"; return 1; }
  : > "$LOGDIR/$name.log"
  for sample in data mcNom mcAlt; do
    for ft in "" "--altSig" "--altBkg" "--altSigBkg"; do
      echo "=== $name $sample ${ft:-nominal} $(date '+%T')" >> "$LOGDIR/$name.log"
      python3 tnpEGM_fitter.py "$cfg" --flag "$flag" --doFit --fitSample "$sample" $ft \
        >> "$LOGDIR/$name.log" 2>&1 || rc=1
    done
  done
  echo "[done] $name rc=$rc $(date)" >> "$LOGDIR/$name.log"
  return $rc
}
export -f run_one
export LOGDIR

mapfile -t CFGS < <(ls etc/config/hza_ele/settings_htoza_*.py | { [ -n "$FILTER" ] && grep "$FILTER" || cat; })
log "re-running ${#CFGS[@]} measurements, $MAXPAR at a time; logs in $LOGDIR"

n=0
for cfg in "${CFGS[@]}"; do
  while [ "$(jobs -rp | wc -l)" -ge "$MAXPAR" ]; do sleep 20; done
  n=$((n+1))
  log "start ($n/${#CFGS[@]}) $(basename "$cfg")"
  run_one "$cfg" &
done
wait
log "ALL RERUN DONE (${#CFGS[@]} measurements)"
