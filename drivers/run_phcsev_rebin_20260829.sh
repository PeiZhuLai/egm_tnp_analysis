#!/usr/bin/env bash
# phcsev 重新分箱後的重跑鏈:createBins -> createHists -> 四種 data fit -> mcNom fit。
#
# 只跑 2026-08-29 重新分箱的 32 個 measurement（8 個基礎 × 4 個變體）。
# 2023postBPixHole 與 2024 不在此列（使用者選 B,只重分箱有回報問題的 era）。
#
# 節流 6 個平行（lxplus 前台上限）。每個 measurement 一個 log,外加一個 status 檔 ——
# **判斷完成看 status 檔,不要 grep log**:log 會殘留上一輪的內容,而且 grep 抓到的
# 行數不等於狀態（2026-08-29 已經被這個坑咬過一次:用 "Plots saved" 的數量判斷進度,
# 實際上那些 job 早就 rc=1 死了）。
set -u
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 10
set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}
export OMP_NUM_THREADS=1 TNP_NPROC=1

LOGDIR=rebin_logs_20260829
STATUS=$LOGDIR/status
mkdir -p "$STATUS"
NPAR=${NPAR:-6}

run_one() {
    local name="$1"
    local S="etc/config/hza_ph_csev/settings_resolve_phcsev_${name}.py"
    local F="hza_resolve_phcsev_${name}_sf"
    local L="$LOGDIR/${name}.log"
    local T0=$(date +%s)
    : > "$L"
    echo "RUNNING $(date +%H:%M:%S)" > "$STATUS/$name"
    local rc_all=0
    for step in "createBins:--createBins" \
                "createHists:--createHists" \
                "nominal:--doFit --fitSample data" \
                "altSig:--doFit --fitSample data --altSig" \
                "altBkg:--doFit --fitSample data --altBkg" \
                "altSigBkg:--doFit --fitSample data --altSigBkg" \
                "mcNom:--doFit --fitSample mcNom"; do
        local label="${step%%:*}" args="${step#*:}"
        echo "##### $label $(date +%H:%M:%S)" >> "$L"
        python3 tnpEGM_fitter.py "$S" --flag "$F" $args >> "$L" 2>&1
        local rc=$?
        echo "##### $label rc=$rc" >> "$L"
        [ "$rc" -ne 0 ] && rc_all=$rc
    done
    local dt=$(( $(date +%s) - T0 ))
    if [ "$rc_all" -eq 0 ]; then
        echo "DONE ${dt}s $(date +%H:%M:%S)" > "$STATUS/$name"
    else
        echo "FAILED rc=$rc_all ${dt}s $(date +%H:%M:%S)" > "$STATUS/$name"
    fi
}

MEAS=()
for r9 in hr9 lr9; do
  for era in 2022preEE 2022postEE 2023preBPix 2023postBPix; do
    for v in "" "bkg_" "puup_" "pudown_"; do
      n="${r9}_${v}${era}"
      [ "$n" = "hr9_2022preEE" ] && continue      # 試跑已完成
      MEAS+=("$n")
    done
  done
done
echo "### START $(date '+%F %T')  共 ${#MEAS[@]} 個 measurement,節流 $NPAR"

for n in "${MEAS[@]}"; do
    while [ "$(jobs -rp | wc -l)" -ge "$NPAR" ]; do sleep 10; done
    run_one "$n" &
done
wait
echo "### ALL DONE $(date '+%F %T')"
grep -l FAILED "$STATUS"/* 2>/dev/null | sed 's#.*/#  失敗: #' || echo "  全部成功"
