#!/bin/bash
set -euo pipefail

echo "PWD: $PWD"
echo "Setting environment..."

workdir="$(pwd)"

if [[ -z "${CMSSW_BASE:-}" ]]; then
  echo "ERROR: CMSSW_BASE is empty. Did you run 'cmsenv' (inside cmssw-el7)?"
  exit 1
fi

cmssw_src="$CMSSW_BASE/src"
if [[ ! -d "$cmssw_src" ]]; then
  echo "ERROR: $cmssw_src does not exist."
  exit 1
fi

pushd "$cmssw_src" >/dev/null
eval "$(scram runtime -sh)"
popd >/dev/null


export PYTHONPATH="$cmssw_src:${PYTHONPATH:-}"
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


baseDir="$cmssw_src/egm_tnp_analysis"

SETTINGS_MOD=$1
WP=$2   


python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --checkBins
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --createBins
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --createHists --sample mcNom
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --createHists --sample mcAlt
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --createHists --sample data
# ----------- Fitting Procedure --------------
# ----------- 1 MC Nominal Fit -----------------------
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --fitSample mcNom
# ----------- 2 Data Fit -----------------------
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --fitSample data
# ----------- 3 MC Fit altsig -----------------------
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altSig
# # ----------- 4 MC Fit altbkg -----------------------
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altBkg
# # ----------- 5 MC Fit altSigBkg -----------------------
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altSigBkg
# # ----------- Get Results -----------------------
python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --sumUp --exportJson



# ----------- Tuning a bin --------------
# For Region
# High pT
# ----------- 2022preEE --------------
# for i in 00 15 20; do
#   python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --iBin ${i}
# done
# ----------- 2022postEE --------------
# for i in 00 15 20; do
#   python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --iBin ${i}
# done
# ----------- 2023postBPix --------------
# for i in 08; do
#   python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --iBin ${i}
# done
# Low pT
# ----------- 2022preEE --------------
# for i in 04 05; do
#   python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altBkg --iBin ${i}
# done


# Single Region
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --mcSig --altSig --iBin 5

# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --iBin 7
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altBkg --iBin 6
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altSig --iBin 1
# python3 -m egm_tnp_analysis.tnpEGM_fitter "$SETTINGS_MOD" --flag "$WP" --doFit --altSigBkg --iBin 6

# sh publish.sh