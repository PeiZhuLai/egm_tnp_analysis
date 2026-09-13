#!/bin/bash
# =============================================================================
# miniIso 專用 driver — 重現 per-bin 微調（addGaus 由 settings 的 addGausBins 決定）
# =============================================================================
# 為何要專用 driver:shared run.sh 走的是另一套序列。至於 addGaus —— 2026-09-12 起
# 本 driver **不再下全域 --addGaus**,改由各 settings 的 addGausBins 逐 bin 決定。
# 理由見下方 run_one() 內的註解。
#
# ---- lineshape(addGaus 模式,fitUtils.py 的 if isaddGaus==1) ----
#   nominal / altBkg / altSigBkg : PASSING=MC template Pass, FAILING=generic ZeeGenLevel
#   altSig                       : PASSING=generic, FAILING=generic(兩者都 generic)
#   generic = etc/inputs/ZeeGenLevel.root 'Mass'(gen-level Z,peak91.2,無解析度無shoulder)
#           ⊗ 解析度(DSCB=altSig/altSigBkg; Gaussian=nominal/altBkg) + addGaus shoulder Gaussian
#
# ---- 微調記錄在哪(單一索引) ----
#   微調「本體」必須留在 8 個 config 的 *_addGaus recipe(fitter 從 config 讀,不能搬走):
#       etc/config/hza_ele/settings_htoza_elminiIso{0p1,0p15}_{gap,nongap}_{2024,2025}.py
#   微調「人可讀清單 + 機制說明」在:
#       doc/HZa/hza_ele_miniiso_lineshape_sfupdate_2026-07-19.md   ← 單一 doc,勿四散
#   通用 recipe(config 裡):
#       寬 Gaussian(shoulder bin,雙峰淺valley): sigmaGF[5.5,4.0,7.5](gap到8)+moderate nF
#       modest-shoulder 高ET bin(gap altSigBkg bin05): 反而小 Gaussian(sigFracF高+窄sigmaGF)
#       altBkg 32-39 continuum: alphaF 上界 0.03(背景升向高質量DY shelf)
#       60GeV spike: alphaF_2 壓平;  峰位移: 收 meanF;  峰太窄: sigmaP/sigmaF 加寬
#   sigFracF 可 config override(fitUtils 4 處已加守衛)。
#
# ---- 前置(進 container + cmsenv) ----
#   cmssw-el7
#   cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src && cmsenv && cd egm_tnp_analysis
#
# ---- 用法 ----
#   STAGE=fits  bash 1_run_miniiso.sh                 # 預設:重跑 fits+sumUp(hists 已在),重現微調
#   STAGE=full  bash 1_run_miniiso.sh                 # 從頭:createBins+createHists+fits+sumUp
#   STAGE=sumup bash 1_run_miniiso.sh                 # 只 sumUp(讀既有 workspace 重出 SF/JSON)
#   bash 1_run_miniiso.sh 0p15_nongap_2024 0p1_gap_2025   # 只跑指定 config(空=全8個)
#   背景: nohup env STAGE=fits bash 1_run_miniiso.sh > run_miniiso_$(date +%Y%m%d).log 2>&1 &
# =============================================================================
set -uo pipefail

if [[ -z "${CMSSW_BASE:-}" ]]; then
  echo "ERROR: CMSSW_BASE 空。請先: cmssw-el7 -> cd \$CMSSW_BASE/src -> cmsenv"; exit 1
fi
pushd "$CMSSW_BASE/src" >/dev/null; eval "$(scram runtime -sh)"; popd >/dev/null
export PYTHONPATH="$CMSSW_BASE/src:${PYTHONPATH:-}"
export PYTHONIOENCODING=UTF-8 LANG=C.UTF-8 LC_ALL=C.UTF-8

STAGE="${STAGE:-fits}"          # full | fits | sumup
B="egm_tnp_analysis.etc.config.hza_ele"

ALL_CONFIGS=(
  elminiIso0p15_nongap_2024 elminiIso0p15_nongap_2025
  elminiIso0p1_nongap_2024  elminiIso0p1_nongap_2025
  elminiIso0p15_gap_2024    elminiIso0p15_gap_2025
  elminiIso0p1_gap_2024     elminiIso0p1_gap_2025
)
# 允許只跑指定 config(args,可省 elminiIso 前綴)
if [[ $# -gt 0 ]]; then
  CONFIGS=(); for a in "$@"; do CONFIGS+=("${a#elminiIso}"); CONFIGS[-1]="elminiIso${CONFIGS[-1]}"; done
else
  CONFIGS=("${ALL_CONFIGS[@]}")
fi

FIT() { timeout -k 60 "${STAGE_TIMEOUT:-2700}" python3 -m egm_tnp_analysis.tnpEGM_fitter "$1" --flag "$2" "${@:3}"; }

run_one() {
  local c="$1" mod="$B.settings_htoza_$1" wp="hza_$1_sf"
  echo "=========== [$c] STAGE=$STAGE $(date +%H:%M:%S) ==========="
  if [[ "$STAGE" == "full" ]]; then
    FIT "$mod" "$wp" --createBins                 || { echo "FAIL createBins $c"; return 1; }
    FIT "$mod" "$wp" --createHists --sample mcNom  || { echo "FAIL hist mcNom $c"; return 1; }
    FIT "$mod" "$wp" --createHists --sample mcAlt  || { echo "FAIL hist mcAlt $c"; return 1; }
    FIT "$mod" "$wp" --createHists --sample data   || { echo "FAIL hist data $c"; return 1; }
  fi
  if [[ "$STAGE" == "full" || "$STAGE" == "fits" ]]; then
    # 2026-09-12：這裡原本每一行都帶全域 --addGaus。**已經移除，不要加回來。**
    # 當時的理由是「不帶就走 template 分支、吃不到微調」，那在 07 月是對的；但 09-07
    # 之後 addGaus 改成逐 bin 開關(settings 的 addGausBins)，全域旗標會覆蓋掉它，
    # 把 shoulder Gaussian 強加到每一格。完整比對量過:全開會改善 699 個擬合、
    # 弄壞 1766 個 —— 那個成分只在 failing 真的是「窄峰+shoulder」時有東西可描述,
    # 其他格子只是白花一個自由度。不帶旗標時 _addgaus_for_bin() 會照 settings 決定,
    # 該開的格子照樣開,微調照樣吃得到。
    # 要做探索性的全開比較,請在命令列自己加 --addGaus,不要改回這裡。
    FIT "$mod" "$wp" --doFit --fitSample mcNom  || echo "WARN nominal mcNom $c"
    FIT "$mod" "$wp" --doFit --fitSample data   || echo "WARN nominal data $c"
    FIT "$mod" "$wp" --doFit --altSig           || echo "WARN altSig $c"
    FIT "$mod" "$wp" --doFit --altBkg           || echo "WARN altBkg $c"
    FIT "$mod" "$wp" --doFit --altSigBkg        || echo "WARN altSigBkg $c"
  fi
  FIT "$mod" "$wp" --sumUp --exportJson            || { echo "FAIL sumUp $c"; return 1; }
  echo "----------- DONE $c $(date +%H:%M:%S) -----------"
}

echo "=== 1_run_miniiso START STAGE=$STAGE configs=${#CONFIGS[@]} $(date +%H:%M:%S) ==="
for c in "${CONFIGS[@]}"; do run_one "$c"; done
echo "=== END $(date +%H:%M:%S) ==="
echo "SF 更新到 HZgamma: cd HZa/HiggsZaAna/HiggsDNA/scripts && PATH=/usr/bin:\$PATH bash 1_collect_custom_sf.sh && PATH=/usr/bin:\$PATH bash 3_distribute_custom_sf.sh"
