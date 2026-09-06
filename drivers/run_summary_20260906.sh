#!/usr/bin/env bash
# 只對「使用者回報的 49 格」所涉及的 23 個 measurement 跑 --sumUp --exportJson。
# 其他 measurement 一律不動（使用者 2026-09-06 明確要求）。
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 10
set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}
export OMP_NUM_THREADS=1 TNP_NPROC=1
LOG=summary_logs_20260906; ST=$LOG/status; mkdir -p "$ST"
NPAR=${NPAR:-5}
one() {
  local cfg="$1" flag="$2" tag="$2"
  [ -f "$ST/$tag" ] && grep -q '^DONE' "$ST/$tag" && { echo "  skip $tag"; return 0; }
  echo "RUNNING $(date +%H:%M:%S)" > "$ST/$tag"
  local T0=$(date +%s) rc=0
  timeout 1800 python3 tnpEGM_fitter.py "etc/config/$cfg" --flag "$flag" --sumUp --exportJson \
      > "$LOG/$tag.log" 2>&1 || rc=$?
  local dt=$(( $(date +%s) - T0 ))
  [ "$rc" -eq 0 ] && echo "DONE ${dt}s" > "$ST/$tag" || echo "FAILED rc=$rc ${dt}s" > "$ST/$tag"
}
echo "### START $(date '+%F %T')  節流 $NPAR"
while IFS='|' read -r cfg flag; do
  [ -z "$cfg" ] && continue
  while [ "$(jobs -rp | wc -l)" -ge "$NPAR" ]; do sleep 3; done
  one "$cfg" "$flag" &
done < affected_measurements_20260906.txt
wait
echo "### DONE $(date '+%F %T')  DONE=$(grep -l '^DONE' "$ST"/* 2>/dev/null|wc -l) FAILED=$(grep -l '^FAILED' "$ST"/* 2>/dev/null|wc -l)"
