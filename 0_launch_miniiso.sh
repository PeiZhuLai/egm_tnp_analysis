#!/bin/bash
# =============================================================================
# miniIso 一鍵啟動器(在 cmssw-el7 container "外" 執行)
# =============================================================================
# 自動:進 cmssw-el7 → cmsenv → 跑 1_run_miniiso.sh(帶 --addGaus,重現微調)。
# 免手動進 container。1_run_miniiso.sh 的 header 記錄所有微調/lineshape。
#
# 用法(直接在 lxplus,不用先進 container、不用記 STAGE):
#   bash 0_launch_miniiso.sh                          # 跑全8 config(用下面 STAGE 設定)
#   bash 0_launch_miniiso.sh 0p15_nongap_2024 0p1_gap_2025   # 只跑指定 config
#   背景(久,建議): nohup bash 0_launch_miniiso.sh > /dev/null 2>&1 &   # log 仍寫下方 LOG
# =============================================================================
set -uo pipefail

# ==== 要換階段就改這一行(三選一) ==============================================
STAGE=fits      # fits  = 重跑 fits + sumUp(hists 已在,重現微調)  ← 平常用這個
#STAGE=full     # full  = 從頭 createBins + createHists + fits + sumUp
#STAGE=sumup    # sumup = 只 sumUp(讀既有 workspace 重出 SF/JSON)
# ============================================================================

SRC=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
WORK="$SRC/egm_tnp_analysis"
ARGS="$*"
TS=$(date +%Y%m%d_%H%M%S)
LOG="$WORK/run_miniiso_${STAGE}_${TS}.log"

echo "=== launch miniIso: STAGE=$STAGE  configs=[${ARGS:-ALL8}]  log=$LOG ==="

# cmssw-el7 開 container,從 stdin 讀命令;外層變數在 heredoc(未加引號 EOF)先展開。
cmssw-el7 <<EOF 2>&1 | tee "$LOG"
cd "$SRC" && cmsenv || { echo "ERROR: cmsenv 失敗"; exit 1; }
cd "$WORK"
STAGE=$STAGE bash 1_run_miniiso.sh $ARGS
EOF

echo "=== done. log: $LOG ==="
