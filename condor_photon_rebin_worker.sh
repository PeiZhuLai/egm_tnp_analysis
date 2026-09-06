#!/usr/bin/env bash
# One condor job = one photon measurement, full chain after a binning change.
#   condor_photon_rebin_worker.sh <settings.py> <flag>
#
# Why one job per measurement rather than per (measurement, sample): bining.pkl is
# written once per measurement by --createBins. Two jobs for the same measurement
# would race on it, and a half-written binning is the kind of failure that shows up
# much later as bins that do not line up between data and MC.
#
# Chain: createBins -> createHists (per sample) -> doFit (per sample). The histograms
# have to be refilled from the ntuple because they are made per bin; changing the bin
# edges without refilling would fit the old histograms under new labels.
set -o pipefail
CFG="${1:?settings}"; FLAG="${2:?flag}"

cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src/egm_tnp_analysis || exit 10
source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh || exit 11
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:$PYTHONPATH
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export TNP_NPROC="${TNP_NPROC:-4}"
export TNP_RETRY_LOGDIR="${TNP_RETRY_LOGDIR:-$PWD/condor_fit/eos_retry_logs}"

RETRY=/afs/cern.ch/work/p/pelai/HZa/TnP/eos_retry.sh
run() {  # EOS writes fail silently with exit 0 and an updated mtime; go through the retry
  if [ -x "$RETRY" ]; then "$RETRY" -n 3 -- "$@"; else "$@"; fi
}

echo "[rebin] $(basename "$CFG") host=$(hostname) start=$(date)"

run python3 tnpEGM_fitter.py "$CFG" --flag "$FLAG" --createBins || { echo "[rebin] createBins FAILED"; exit 20; }

# 兩階段,不可交錯:data 的擬合會去讀 MC 的直方圖檔(拿訊號模板),所以必須先把
# 兩個 sample 的直方圖都建好才能開始擬合。先前寫成
#   data createHists -> data doFit -> mcNom createHists -> mcNom doFit
# 結果 data doFit 找不到 DY_MC_NLO_*.root —— 而且 --createBins 會清空輸出目錄,
# 連上一次留下的 MC 檔也一併沒了。
rc_all=0
for SMP in data mcNom; do
  echo "[rebin] --- $SMP createHists"
  run python3 tnpEGM_fitter.py "$CFG" --flag "$FLAG" --createHists --sample "$SMP"
  rc=$?; [ $rc -ne 0 ] && { echo "[rebin] createHists $SMP rc=$rc"; rc_all=$rc; }
done
[ "$rc_all" != "0" ] && { echo "[rebin] 直方圖未建齊,跳過擬合"; exit $rc_all; }

for SMP in mcNom data; do          # MC 先擬合:data 的 altSig 之類會用到 MC 的結果
  echo "[rebin] --- $SMP doFit"
  run python3 tnpEGM_fitter.py "$CFG" --flag "$FLAG" --doFit --fitSample "$SMP"
  rc=$?; [ $rc -ne 0 ] && { echo "[rebin] doFit $SMP rc=$rc"; rc_all=$rc; }
done

[ "$rc_all" = "75" ] && echo "[rebin] EOS WRITE FAILED -- result on disk is stale, resubmit"
echo "[rebin] DONE rc=$rc_all $(date)"
exit $rc_all
