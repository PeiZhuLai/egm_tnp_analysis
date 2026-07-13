#!/bin/bash
# 重跑本 session 改動過的 hza_ele 電子 TnP config。
# 改動：(1) samplesDef nominal=LO/alt=NLO  (2) 權重改 in-tree totWeight
#        (3) leg12/leg23 分母移除跨腿匹配（bins 也變）
#
# 前置：先進 cmssw-el7 container 並 cmsenv：
#   cmssw-el7
#   cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src && cmsenv
#   cd egm_tnp_analysis
#   bash rerun_hza_ele_20260709.sh            # 預設跑 8 個 leg config（本任務，bins 有變→全 stage）
#   SCOPE=all bash rerun_hza_ele_20260709.sh  # 跑全部 28（weight/sample 也變）
#
# 說明：每個 config 依序跑 createBins→createHists(mcNom/mcAlt/data)→doFit(5種)→sumUp，
#       config 層級平行 max_jobs=6（符合 lxplus 前台上限）。重且久，建議 nohup 背景：
#   nohup bash rerun_hza_ele_20260709.sh > rerun_leg_$(date +%Y%m%d).log 2>&1 &
set -uo pipefail

if [[ -z "${CMSSW_BASE:-}" ]]; then
  echo "ERROR: CMSSW_BASE 空。請先在 cmssw-el7 裡 cmsenv。"; exit 1
fi
pushd "$CMSSW_BASE/src" >/dev/null; eval "$(scram runtime -sh)"; popd >/dev/null
export PYTHONPATH="$CMSSW_BASE/src:${PYTHONPATH:-}"
export PYTHONIOENCODING=UTF-8 LANG=C.UTF-8 LC_ALL=C.UTF-8

# 每個 fitter stage 套 timeout(預設45分,-k 60秒後SIGKILL)避免 EOS 壞檔導致 multiprocessing 死鎖卡住整批
FIT() { timeout -k 60 "${STAGE_TIMEOUT:-2700}" python3 -m egm_tnp_analysis.tnpEGM_fitter "$1" --flag "$2" "${@:3}"; }

run_one() {  # $1=config basename (無副檔名), 完整 stage chain
  local name="$1"
  local mod="egm_tnp_analysis.etc.config.hza_ele.settings_htoza_${name}"
  local wp="hza_${name}_sf"
  # 方案1: 輸出改寫 eosproject(避開損毀的 eoshome; AFS work 配額滿故用 eosproject)
  local outdir="/eos/cms/store/group/phys_susy/NPS-25-014/root_TnP_local/${wp}"
  local eff_new="${outdir}/egammaEffi.txt"                       # 方案1 完成的
  local eff_old="/eos/home-p/pelai/HZa/root_TnP/${wp}/egammaEffi.txt"  # 方案1前已完成的8個(eoshome)
  # 斷點續跑：只跳過「今晚(DONE_CUTOFF 後)」完成的(eosproject新 或 eoshome舊8個);stale舊production不算
  if { [[ -s "$eff_new" ]] && timeout 30 find "$eff_new" -newermt "${DONE_CUTOFF:-2026-07-09 12:00}" 2>/dev/null | grep -q .; } \
  || { [[ -s "$eff_old" ]] && timeout 30 find "$eff_old" -newermt "${DONE_CUTOFF:-2026-07-09 12:00}" 2>/dev/null | grep -q .; }; then
    echo "[$(date +%H:%M:%S)] SKIP  $name (今晚已完成)"; return 0
  fi
  timeout 120 rm -rf "$outdir" 2>/dev/null; timeout 60 mkdir -p "$outdir" 2>/dev/null   # 清 stale/半成品
  echo "[$(date +%H:%M:%S)] START $name"
  FIT "$mod" "$wp" --createBins                       || { echo "FAIL createBins $name"; return 1; }
  FIT "$mod" "$wp" --createHists --sample mcNom        || { echo "FAIL hist mcNom $name"; return 1; }
  FIT "$mod" "$wp" --createHists --sample mcAlt        || { echo "FAIL hist mcAlt $name"; return 1; }
  FIT "$mod" "$wp" --createHists --sample data         || { echo "FAIL hist data $name"; return 1; }
  FIT "$mod" "$wp" --doFit --fitSample mcNom           || { echo "FAIL fit mcNom $name"; return 1; }
  FIT "$mod" "$wp" --doFit --fitSample data            || { echo "FAIL fit data $name"; return 1; }
  FIT "$mod" "$wp" --doFit --altSig                    || { echo "FAIL altSig $name"; return 1; }
  FIT "$mod" "$wp" --doFit --altBkg                    || { echo "FAIL altBkg $name"; return 1; }
  FIT "$mod" "$wp" --doFit --altSigBkg                 || { echo "FAIL altSigBkg $name"; return 1; }
  FIT "$mod" "$wp" --sumUp --exportJson                || { echo "FAIL sumUp $name"; return 1; }
  echo "[$(date +%H:%M:%S)] DONE  $name"
}

# 8 個 leg config（本任務：分母跨腿移除，bins 有變）
LEG=(
  dielleg12trigger_gap_2024   dielleg12trigger_nongap_2024
  dielleg12trigger_gap_2025   dielleg12trigger_nongap_2025
  dielleg23trigger_gap_2024   dielleg23trigger_nongap_2024
  dielleg23trigger_gap_2025   dielleg23trigger_nongap_2025
)
# 其餘 20 個（weight/sample 也變；bins 未變但重跑 createHists→sumUp 才會吃到新權重）
OTHERS=(
  sielleg30trigger_gap_2024   sielleg30trigger_nongap_2024
  sielleg30trigger_gap_2025   sielleg30trigger_nongap_2025
  elid_gap_2024 elid_nongap_2024 elid_nongap_highpT_2024 elid_nongap_lowpT_2024
  elid_gap_2025 elid_nongap_2025 elid_nongap_highpT_2025 elid_nongap_lowpT_2025
  elminiIso0p1_gap_2024 elminiIso0p1_nongap_2024 elminiIso0p15_gap_2024 elminiIso0p15_nongap_2024
  elminiIso0p1_gap_2025 elminiIso0p1_nongap_2025 elminiIso0p15_gap_2025 elminiIso0p15_nongap_2025
)

SCOPE="${SCOPE:-leg}"
case "$SCOPE" in
  all)    CONFIGS=("${OTHERS[@]}" "${LEG[@]}") ;;   # 全 28 (others 先跑,難的 leg23 2025 留最後等 EOS)
  others) CONFIGS=("${OTHERS[@]}") ;;               # 只剩 20 (leg 已完成時用)
  *)      CONFIGS=("${LEG[@]}") ;;                   # 8 個 leg (預設)
esac
echo "SCOPE=$SCOPE  共 ${#CONFIGS[@]} 個 config，max_jobs=6"

max_jobs="${MAX_JOBS:-6}"; pids=()
for name in "${CONFIGS[@]}"; do
  run_one "$name" &
  pids+=("$!")
  if [[ "${#pids[@]}" -eq "$max_jobs" ]]; then
    for p in "${pids[@]}"; do wait "$p" || echo "  (一個 config chain 有 FAIL，續跑其餘)"; done
    pids=()
  fi
done
for p in "${pids[@]}"; do wait "$p" || echo "  (一個 config chain 有 FAIL)"; done
echo "全部結束。SF JSON 在各 config 的輸出目錄（baseOutDir /eos/home-p/pelai/HZa/root_TnP/ 下）。"
