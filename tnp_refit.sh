#!/usr/bin/env bash
# =============================================================================
# tnp_refit.sh — 通用逐格重擬合 + 重畫。取代 wrap_* / rerun_* / refit_* / run_*batch*
# =============================================================================
# 為什麼需要這個：2026-07 到 09 之間，每次「使用者回報 N 格要調」都新長一個一次性
# 腳本，累積到 114 個 .sh。既有的 refit_bins.sh / refit_one.sh 是通用的，但不能平行、
# 不畫圖、不追狀態、要進 scram，所以沒人用。這支把那些缺口一次補上。
#
# 用法
#   ./tnp_refit.sh [選項] <job> [<job> ...]
#   ./tnp_refit.sh [選項] -f joblist.txt          # 一行一個 job，# 開頭是註解
#
#   job 格式：<config>:<fitType>:<bins>
#     config  別名或 .py 路徑。別名會在 etc/config/hza_ele 與 etc/config/isoMyCorr
#             三處（hza_ele / isoMyCorr / hza_ph_csev）尋找；找到多於一個就中止並列出候選（避免誤用 *_eoscms 變體 ——
#             那個 bug 讓 27 個 job 回 rc=0 卻寫到另一個 baseOutDir）。
#     fitType nominal | altSig | altBkg | altSigBkg
#     bins    18,19,20  或  all
#
#   選項
#     -j N   併行度（預設 4，硬上限 6 —— lxplus 前台規定）
#     -m M   fit | plot | both（預設 both）
#     -t TAG log 目錄後綴（預設今天日期）
#     -n     dry-run：只印前置檢查表，不執行
#     -s     跳過前置檢查表的確認輸出（給 chain 用）
#
#   範例
#     ./tnp_refit.sh elminiIso0p15_nongap_2024:altSig:18,19,20,21
#     ./tnp_refit.sh -j 4 phid_lowpt_2023preBPix:nominal:7 phid_lowpt_2022preEE:nominal:3
#     ./tnp_refit.sh -n elminiIso0p15_nongap_2025:nominal:all
#
# 前置檢查表會印出每個 job 的 settings 路徑、flag、baseOutDir、fitType、bins。
# 這是刻意的：CLAUDE.md 要求每次執行都列出 input/output path，讓它自動發生，
# 而不是靠人記得寫。baseOutDir 印出來也是為了讓「寫到錯的樹」當場看得見。
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 10
ROOT=$PWD

NPAR=4; MODE=both; TAG=$(date +%Y%m%d); DRY=0; QUIET=0; JOBFILE=""
while getopts "j:m:t:f:ns" o; do case $o in
  j) NPAR=$OPTARG ;; m) MODE=$OPTARG ;; t) TAG=$OPTARG ;;
  f) JOBFILE=$OPTARG ;; n) DRY=1 ;; s) QUIET=1 ;;
  *) sed -n '2,40p' "$0"; exit 2 ;;
esac; done
shift $((OPTIND-1))
[ "$NPAR" -gt 6 ] && { echo "!! -j $NPAR 超過 lxplus 前台上限 6，改用 6"; NPAR=6; }

JOBS=()
[ -n "$JOBFILE" ] && while read -r l; do
  l="${l%%#*}"; l="$(echo "$l" | xargs)"; [ -n "$l" ] && JOBS+=("$l")
done < "$JOBFILE"
JOBS+=("$@")
[ ${#JOBS[@]} -eq 0 ] && { sed -n '2,40p' "$0"; exit 2; }

set +u; source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1; set -u
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:${PYTHONPATH:-}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 TNP_NPROC=1
# 這行不是裝飾：PYTHONPATH 設錯時 78 個 summary 曾在 2 分鐘內全滅於
# ModuleNotFoundError，而每個 job 的 rc 看起來都很正常。先撞牆再說。
python3 -c "import egm_tnp_analysis" 2>/dev/null || { echo "!! PYTHONPATH 壞了，中止"; exit 11; }

resolve_cfg(){  # 別名 -> settings 路徑（多於一個候選就中止）
  local a=$1
  [ -f "$a" ] && { echo "$a"; return; }
  local c=(); local p
  for p in etc/config/hza_ele/settings_htoza_$a.py etc/config/isoMyCorr/settings_resolve_$a.py \
           etc/config/hza_ph_csev/settings_resolve_$a.py \
           etc/config/hza_ele/settings_$a.py etc/config/isoMyCorr/settings_$a.py \
           etc/config/hza_ph_csev/settings_$a.py; do
    [ -f "$p" ] && c+=("$p")
  done
  [ ${#c[@]} -eq 1 ] && { echo "${c[0]}"; return; }
  [ ${#c[@]} -eq 0 ] && { echo "NOTFOUND"; return; }
  echo "AMBIGUOUS:${c[*]}"
}
cfg_meta(){  # 印出 "<flag>|<baseOutDir>|<nbins>"
  python3 - "$1" <<'PY' 2>/dev/null
import importlib.util, sys, os, pickle
p=sys.argv[1]
sys.path.insert(0, os.getcwd())
s=importlib.util.spec_from_file_location("cfg_probe", p); m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)
fl=list(getattr(m,'flags',{}) or {})
flag=fl[0] if len(fl)==1 else ("MULTI:"+",".join(fl) if fl else "NOFLAG")
bod=getattr(m,'baseOutDir','?')
nb='?'
try:
    with open(os.path.join(bod, flag, 'bining.pkl'),'rb') as f: nb=str(len(pickle.load(f)['bins']))
except Exception: pass
print("%s|%s|%s"%(flag,bod,nb))
PY
}

# ---- 前置檢查表 ----
declare -a SPEC
echo "=== tnp_refit 前置檢查 ($(date +%F\ %T)) ==="
printf "%-34s %-10s %-14s %s\n" CONFIG FITTYPE BINS "FLAG  /  BASEOUTDIR"
bad=0
for j in "${JOBS[@]}"; do
  IFS=':' read -r alias ft bins <<< "$j"
  cfg=$(resolve_cfg "$alias")
  case "$cfg" in
    NOTFOUND)   echo "  !! 找不到 config: $alias"; bad=1; continue ;;
    AMBIGUOUS:*) echo "  !! $alias 對到多個 config: ${cfg#AMBIGUOUS:}"; bad=1; continue ;;
  esac
  meta=$(cfg_meta "$cfg"); IFS='|' read -r flag bod nb <<< "$meta"
  case "$flag" in ""|NOFLAG|MULTI:*) echo "  !! $cfg 的 flags 無法自動決定: $flag"; bad=1; continue ;; esac
  [ "$bins" = all ] && { [ "$nb" = '?' ] && { echo "  !! $alias 讀不到 bining.pkl，all 無法展開"; bad=1; continue; }
                         bins=$(seq -s, 0 $((nb-1))); }
  case "$ft" in nominal|altSig|altBkg|altSigBkg) ;; *) echo "  !! 未知 fitType: $ft"; bad=1; continue ;; esac
  printf "  %-32s %-10s %-14s %s\n     -> %s\n" "$alias" "$ft" "$(echo $bins|cut -c1-14)" "$flag" "$bod"
  SPEC+=("$cfg|$flag|$ft|$bins")
done
[ $bad -eq 1 ] && { echo "=== 有 job 無法解析，全部不執行 ==="; exit 3; }
NTOT=0; for s in "${SPEC[@]}"; do IFS='|' read -r _ _ _ b <<< "$s"; NTOT=$((NTOT + $(echo "$b" | tr ',' ' ' | wc -w))); done
L=logs_refit_$TAG; ST=$L/status
echo "=== 共 $NTOT 格，併行度 $NPAR，模式 $MODE，log: $ROOT/$L ==="
[ $DRY -eq 1 ] && { echo "=== dry-run，結束 ==="; exit 0; }
mkdir -p "$ST"

one(){  # one <tag> <cfg> <flag> <ftArg> <ibin>
  local tag=$1 cfg=$2 flag=$3 fta=$4 ib=$5 rcf=0 rcp=0 rc=0
  echo RUNNING > "$ST/$tag"
  {
    if [ "$MODE" != plot ]; then
      timeout 2700 python3 tnpEGM_fitter.py "$cfg" --flag "$flag" --doFit $fta --iBin "$ib"; rcf=$?
      echo "[tnp_refit] fit rc=$rcf"
    fi
    if [ "$MODE" != fit ] && [ $rcf -eq 0 ]; then
      for t in 1 2 3; do
        timeout 1200 python3 tnpEGM_fitter.py "$cfg" --flag "$flag" --doPlot $fta --iBin "$ib"; rcp=$?
        [ $rcp -eq 0 ] && break
        echo "[tnp_refit] plot 第 $t 次 rc=$rcp，重試（EOS 暫時性錯誤）"; sleep $((t*20))
      done
      echo "[tnp_refit] plot rc=$rcp"
    fi
    # 這裡以前寫 `exit $((...))`。exit 會直接終結這個 subshell，後面的
    # `&& echo DONE || echo FAILED` 永遠不會執行，跑完的格子就永遠停在 RUNNING
    # （2026-09-12 的 48 格 nominal 重跑全中，真實狀態只能從 log 的 rc= 反推）。
    # 用「最後一個指令的結束碼」把狀態交出去，不要用 exit。
    rc=$(( rcf > rcp ? rcf : rcp ))
    echo "[tnp_refit] rc=$rc"
    [ $rc -eq 0 ]
  } > "$L/$tag.log" 2>&1 && echo DONE > "$ST/$tag" || echo FAILED > "$ST/$tag"
  printf "  %-40s %s\n" "$tag" "$(cat "$ST/$tag")"
}

for s in "${SPEC[@]}"; do
  IFS='|' read -r cfg flag ft bins <<< "$s"
  case $ft in nominal) fta="--fitSample data" ;; altSig) fta="--altSig --fitSample data" ;;
              altBkg) fta="--altBkg --fitSample data" ;; altSigBkg) fta="--altSigBkg --fitSample data" ;; esac
  short=$(basename "$cfg" .py | sed 's/^settings_htoza_//; s/^settings_resolve_//; s/^settings_//')
  for b in ${bins//,/ }; do
    one "${short}_${ft}_b$(printf %02d "$b")" "$cfg" "$flag" "$fta" "$b" &
    while [ "$(jobs -rp | wc -l)" -ge "$NPAR" ]; do sleep 5; done
  done
done
wait
echo "=== tnp_refit 完成 $(date +%F\ %T) ==="
printf "DONE=%s FAILED=%s / %s\n" "$(grep -lx DONE "$ST"/* 2>/dev/null | wc -l)" \
                                  "$(grep -lx FAILED "$ST"/* 2>/dev/null | wc -l)" "$NTOT"
grep -lx FAILED "$ST"/* 2>/dev/null | sed 's|.*/|  FAILED: |'
exit 0
