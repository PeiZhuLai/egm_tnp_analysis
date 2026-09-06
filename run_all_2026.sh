#!/bin/bash
# Drive the full TnP chain for the 2026 electron configs (id / trigger / miniIso).
#
# Concurrency is capped like runTnP.sh (lxplus foreground limit). Measured cost of one
# chain: 1 python process, ~0.4 GB RSS, 1 thread, I/O bound -- so the cap is the real
# limit here, not a process explosion.
#
#   MAXPAR=5 nohup bash run_all_2026.sh > log 2>&1 &

set -uo pipefail

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAXPAR="${MAXPAR:-5}"
LOGDIR="${LOGDIR:-$PWD/logs_tnp2026}"
mkdir -p "$LOGDIR"

# elid_gap is run separately as the pilot; SKIP it here by default.
SKIP="${SKIP:-elid_gap}"

CONFIGS=(
  elid_nongap
  elid_nongap_highpT
  elid_nongap_lowpT
  sielleg30trigger_gap
  sielleg30trigger_nongap
  dielleg23trigger_gap
  dielleg23trigger_nongap
  dielleg12trigger_gap
  dielleg12trigger_nongap
  elminiIso0p15_gap
  elminiIso0p15_nongap
  elminiIso0p1_gap
  elminiIso0p1_nongap
  elid_gap
)

running=0
for c in "${CONFIGS[@]}"; do
  [[ -n "$SKIP" && "$c" == "$SKIP" ]] && { echo "skip (pilot): $c"; continue; }
  mod="egm_tnp_analysis.etc.config.hza_ele.settings_htoza_${c}_2026"
  wp="hza_${c}_2026_sf"
  echo "launch: $wp"
  cmssw-el7 -- bash "$BASE/run_full_2026.sh" "$mod" "$wp" > "$LOGDIR/${wp}.log" 2>&1 &
  running=$((running+1))
  if (( running >= MAXPAR )); then
    wait -n 2>/dev/null || wait
    running=$((running-1))
  fi
done
wait
echo "ALL 2026 CHAINS FINISHED"
for f in "$LOGDIR"/*.log; do
  wp=$(basename "$f" .log)
  if grep -q "FULL CHAIN OK" "$f"; then echo "  OK    $wp"
  else echo "  FAIL  $wp : $(grep -E 'STEP FAILED' "$f" | tail -1)"; fi
done
