#!/bin/bash
# 2026-09-15：補產 dielleg23trigger_gap_2025 缺失的 MC altSigFit 參考檔。
#
# 為什麼缺它有影響：fitUtils.createWorkspaceForAltSig() 會拿 MC 的 altSigFit 結果
# 覆寫並**固定** alphaF/nF/sigmaF/sigmaF_2。gap_2025 b06 因為參考檔不存在，
# log 印「參考檔不存在或未設定」，退回用設定檔初始值自由擬合 —— 所以它有 11 個
# 浮動參數，而同批的 gap_2026 b05/b06 與 nongap_2024 b14 只有 10/10/7 個。
# 這是生產上的不一致，不是設定差異（三個設定檔的 tnpParAltSigFit 逐字相同）。
#
# ⚠️ 補產之後 b06 的行為會改變：下次擬合起它會被 MC 播種、形狀被釘死。
#    這讓它與另外三格一致，但不保證更好 —— 補完必須重驗 b06 的殘差與效率
#    （判準：效率與 altBkgFit 的一致性，不是只看殘差）。
#
# 只寫 MC 樣本的檔名（DY_MC_LO_2025_*），不會動到任何 data 擬合。
# ⚠ source 要用 set +u 包住（LCG setup 引用未設定變數）。
set -o pipefail
cd "$(dirname "$0")" || exit 10
set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}
python3 -c "import egm_tnp_analysis" || { echo "PYTHONPATH 壞了，中止"; exit 11; }
L=logs_mcaltsig_20260915; mkdir -p "$L"
CFG=etc/config/hza_ele/settings_htoza_dielleg23trigger_gap_2025.py
WP=hza_dielleg23trigger_gap_2025_sf
echo "[mcaltsig $(date '+%F %T')] start  24 bins"
timeout 3600 python3 -m egm_tnp_analysis.tnpEGM_fitter "$CFG" --flag "$WP" --doFit --mcSig --altSig \
    > "$L/mcaltsig.log" 2>&1
rc=$?
echo "[mcaltsig $(date '+%F %T')] done rc=$rc"
exit $rc
