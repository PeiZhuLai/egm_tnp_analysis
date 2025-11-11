#!/bin/bash
set -euo pipefail

echo "PWD: $PWD"
echo "Setting environment..."

# 0) 记住当前工作目录
workdir="$(pwd)"

# 1) 确保在 SLC7 容器内（你已用 cmssw-el7 进入，这里略）并加载 CMSSW 环境
if [[ -z "${CMSSW_BASE:-}" ]]; then
  echo "ERROR: CMSSW_BASE is empty. Did you run 'cmsenv' (inside cmssw-el7)?"
  exit 1
fi

# 2) 进入 CMSSW src 顶层并加载 runtime
cmssw_src="$CMSSW_BASE/src"
if [[ ! -d "$cmssw_src" ]]; then
  echo "ERROR: $cmssw_src does not exist."
  exit 1
fi

# 加载 runtime（等价于 cmsenv）
pushd "$cmssw_src" >/dev/null
eval "$(scram runtime -sh)"   # 或者：cmsenv
popd >/dev/null

# 3) Python 路徑：把 CMSSW_BASE/src 追加進來
export PYTHONPATH="$cmssw_src:${PYTHONPATH:-}"
# 統一 UTF-8 環境，避免 bytes/str 行為不一致
export PYTHONIOENCODING="${PYTHONIOENCODING:-UTF-8}"
export LANG="${LANG:-C.UTF-8}"
export LC_ALL="${LC_ALL:-C.UTF-8}"

# 選擇性建置 C++ 擴充（histUtils）：預設關閉，避免 ROOT 標頭缺失導致失敗
# 若需要可執行：BUILD_CPP=1 ./run.sh <settings_mod> <WP>
BUILD_CPP="${BUILD_CPP:-0}"
if [[ "$BUILD_CPP" == "1" ]]; then
  if command -v root-config >/dev/null 2>&1; then
    echo "[build] 嘗試建置 C++ 擴充 (histUtils) ..."
    set +e
    bash "$cmssw_src/egm_tnp_analysis/tools/build_histutils.sh"
    rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then
      echo "[build][WARN] 建置失敗，將改用已存在的 .so 或回退機制。"
    fi
  else
    echo "[build][WARN] 找不到 root-config，略過 C++ 擴充建置，使用純 Python 回退。"
  fi
else
  echo "[build] 略過 C++ 擴充建置（可設環境變數 BUILD_CPP=1 啟用）。"
fi

# 4) 包根目录 & 设置文件/模块
baseDir="$cmssw_src/egm_tnp_analysis"

# 选一种方式：
#   A) 用模块路径（推荐）
SETTINGS_MOD=$1
#   B) 或者用 .py 绝对路径（取消下一行注释以改用文件路径）
# SETTINGS_PY="$baseDir/etc/config/settings_resolve_pho_2022preEE.py"

WP=$2   # 你的 working point 名称，例如 'Tight_PhotonID'

## 5) 运行 —— 模块方式最稳，不受当前工作目录影响
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --checkBins
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --createBins
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --createHists
# # ----------- Fitting Procedure --------------
# # ----------- 1 MC Fit -----------------------
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --mcSig
# ## ----------- 2 Data Fit --------------------
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit 
# ## ----------- 3 MC Fit altsig---------------
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altSig
# ## ----------- 4 MC Fit altbkg---------------
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altBkg
# ## ----------- 5 MC Fit altSigBkg--------------
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altSigBkg
## ----------- Get Results --------------
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --sumUp --exportJson
# ----------- Tuning a bin --------------
# rm -fr /eos/home-p/pelai/HZa/root_TnP/passingCustomCutBased_2022preEE/Data_2022preEE_passingCustomCutBased_2022preEE.nominalFit-bin04_ph_sc_eta_0p00To0p80_ph_et_10p00To15p00.root
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --iBin 4
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --mcSig --altSig --iBin 4
