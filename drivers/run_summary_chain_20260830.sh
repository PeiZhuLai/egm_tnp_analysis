#!/usr/bin/env bash
# 等窗口放寬的重跑全部結束,然後自動接 summary(--sumUp --exportJson)與 muon prepare。
#
# 用 setsid 送出,不依賴互動 shell session 存活。判斷前一階段完成看 **status 檔**:
# 32 個檔全部不是 RUNNING 才算完成 —— 不 grep log(會抓到上一輪),不看行程數
# (ps|grep 在 CC 下會自我匹配)。
set -u
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 10
EGM=$PWD
SPARK=/afs/cern.ch/work/p/pelai/HZa/TnP/spark_tnp
WSTATUS=window_logs_20260830/status
LOG=summary_logs_20260830
mkdir -p "$LOG/status"

echo "### WAIT $(date '+%F %T') 等窗口重跑收尾"
while :; do
    tot=$(ls "$WSTATUS" 2>/dev/null | wc -l)
    run=$(grep -l "^RUNNING" "$WSTATUS"/* 2>/dev/null | wc -l)
    [ "$tot" -eq 32 ] && [ "$run" -eq 0 ] && break
    sleep 120
done
echo "### WINDOW DONE $(date '+%F %T')  失敗 $(grep -l FAILED "$WSTATUS"/* 2>/dev/null | wc -l) 個"

set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}
export OMP_NUM_THREADS=1 TNP_NPROC=1
NPAR=${NPAR:-6}

sum_one() {
    local cfg="$1" flag="$2" tag="$3"
    local L="$LOG/${tag}.log"
    echo "RUNNING $(date +%H:%M:%S)" > "$LOG/status/$tag"
    local T0=$(date +%s)
    python3 tnpEGM_fitter.py "$cfg" --flag "$flag" --sumUp --exportJson > "$L" 2>&1
    local rc=$?
    local dt=$(( $(date +%s) - T0 ))
    [ "$rc" -eq 0 ] && echo "DONE ${dt}s" > "$LOG/status/$tag" \
                    || echo "FAILED rc=$rc ${dt}s" > "$LOG/status/$tag"
}

echo "### SUMMARY $(date '+%F %T')"
while read -r cfg flag; do
    [ -z "${flag:-}" ] && continue
    while [ "$(jobs -rp | wc -l)" -ge "$NPAR" ]; do sleep 5; done
    sum_one "$cfg" "$flag" "$flag" &
done < summary_pairs_20260829.txt
wait
echo "### SUMMARY DONE $(date '+%F %T')"

echo "### MUON PREPARE $(date '+%F %T')"
cd "$SPARK" || exit 11
B=/eos/home-p/pelai/HZa/root_mTnP
for era in Run2024 Run2025 Run2026; do
  y=${era#Run}
  for cfg in configs/hza/htoza_muid_${y}.json configs/hza/htoza_simuleg24trigger_${y}.json \
             configs/hza/htoza_dimuleg17trigger_${y}.json configs/hza/htoza_dimuleg8trigger_${y}.json \
             configs/hzg/htozg_muiso0p1_${y}.json configs/hzg/htozg_muiso0p15_${y}.json; do
    [ -f "$cfg" ] || { echo "  跳過(無設定檔) $cfg"; continue; }
    n=$(basename "$cfg" .json)
    echo "##### prepare $n $era $(date +%H:%M)"
    ./tnp_fitter.py prepare muon generalTracks Z "$era" "$cfg" --baseDir "$B" 2>&1 | tail -2
    # muid 額外輸出 hza_muid_<era>_scalefactors.json,custom SF 收集腳本會抓它;
    # 少了 --exportMuidScaleFactors 就不會寫出,而 1_collect_custom_sf.sh 在
    # set -euo pipefail 下會因為找不到來源而整支中止(2026-08-29 踩過)。
    extra=""; [[ "$n" == *muid* ]] && extra="--exportMuidScaleFactors"
    ./tnp_fitter.py prepare muon generalTracks Z "$era" "$cfg" --baseDir "$B" \
        --plotOverlayBinsOnly $extra 2>&1 | tail -2
  done
done
echo "### ALL DONE $(date '+%F %T')"
