#!/usr/bin/env bash
# 只重跑使用者回報過的電子/光子格子，套用 histFitter.C 的模板保護（2026-09-06）。
# 其他 bin 一律不動。
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 10
set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}

LIST=reported_bins_20260906.txt
LOG=logs_reported_20260906; ST=$LOG/status
mkdir -p "$ST"
NPAR=${NPAR:-5}          # lxplus 前景上限 6，留一個給監測
TMO=${TMO:-600}          # 已知 dl12ng24 b46 / mi15 b03 會卡在歸一化 NaN，不讓它們拖住整批

one() {
  local cfg="$1" flag="$2" mode="$3" bin="$4"
  local ft=nominalFit
  case "$mode" in --altSig) ft=altSigFit;; --altBkg) ft=altBkgFit;; --altSigBkg) ft=altSigBkgFit;; esac
  local tag="${flag}__${ft}__b${bin}"
  [ -f "$ST/$tag" ] && grep -q '^DONE' "$ST/$tag" && { echo "  skip $tag"; return 0; }
  echo "RUNNING $(date +%H:%M:%S)" > "$ST/$tag"
  local T0=$(date +%s) rc=0
  timeout "$TMO" python3 tnpEGM_fitter.py "etc/config/$cfg" \
      --flag "$flag" $mode --doFit --doPlot --iBin "$bin" > "$LOG/$tag.log" 2>&1 || rc=$?
  local dt=$(( $(date +%s) - T0 ))
  if [ "$rc" -eq 124 ]; then
    echo "TIMEOUT ${dt}s" > "$ST/$tag"
  elif [ "$rc" -eq 0 ]; then
    echo "DONE ${dt}s" > "$ST/$tag"
  else
    echo "FAILED rc=$rc ${dt}s" > "$ST/$tag"
  fi
}

echo "### START $(date '+%F %T')  節流 $NPAR  timeout ${TMO}s"
while IFS='|' read -r cfg flag mode bin; do
  [[ "$cfg" == \#* || -z "$cfg" ]] && continue
  while [ "$(jobs -rp | wc -l)" -ge "$NPAR" ]; do sleep 3; done
  one "$cfg" "$flag" "$mode" "$bin" &
done < "$LIST"
wait
echo "### DONE $(date '+%F %T')"
echo "  DONE=$(grep -l '^DONE' "$ST"/* 2>/dev/null | wc -l)  TIMEOUT=$(grep -l '^TIMEOUT' "$ST"/* 2>/dev/null | wc -l)  FAILED=$(grep -l '^FAILED' "$ST"/* 2>/dev/null | wc -l)"
