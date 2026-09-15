#!/bin/bash
# 2026-09-14：對昨夜有擬合改動的 4 個 measurement 做 sumUp + exportJson。
#   elminiIso0p15_nongap_2026  b19 altSigBkg（EDM 2.1e+05 -> 0.000486）
#   elminiIso0p1_nongap_2026   b23 altBkg（sigmaF/meanGF 兩個撞界解除）
#   elid_nongap_lowpT_2024     b05 altSig（EDM 4.12e+09 -> 0.00174）
#   elid_nongap_2024           b12 altSig（改動已撤回，重跑還原輸出檔）
# 其餘 measurement 不動 —— 全部重跑只會把時間戳洗掉，之後判不出哪些真的重做過。
# ⚠ source 要用 set +u 包住（LCG setup 引用未設定變數，開著 -u 會無聲中止只回 rc=1）。
set -o pipefail
cd "$(dirname "$0")" || exit 10
set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}
python3 -c "import egm_tnp_analysis" || { echo "PYTHONPATH 壞了，sumUp 中止"; exit 11; }
L=logs_sumup_20260914; mkdir -p "$L"
rc=0
sum(){ echo "--- $2 ($(date +%T))"; timeout 1800 python3 tnpEGM_fitter.py "$1" --flag "$2" --sumUp --exportJson \
        > "$L/sumup_$2.log" 2>&1 && echo "    rc=0" || { echo "    FAILED rc=$?"; rc=1; }; }
EC=etc/config/hza_ele
sum $EC/settings_htoza_elminiIso0p15_nongap_2026.py hza_elminiIso0p15_nongap_2026_sf
sum $EC/settings_htoza_elminiIso0p1_nongap_2026.py  hza_elminiIso0p1_nongap_2026_sf
sum $EC/settings_htoza_elid_nongap_lowpT_2024.py    hza_elid_nongap_lowpT_2024_sf
sum $EC/settings_htoza_elid_nongap_2024.py          hza_elid_nongap_2024_sf
echo "=== SUMUP DONE $(date +%F\ %T) rc=$rc ==="
exit $rc
