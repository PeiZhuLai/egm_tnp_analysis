#!/usr/bin/env bash
# Per-bin worker for the catch-up pass: one condor job = one bin, so a single
# pathological bin can no longer drag a whole measurement past the runtime cap.
#   condor_fit_worker_bin.sh <settings.py> <flag> <sample> <fitType> <iBin>
set -o pipefail
CFG="${1:?}"; FLAG="${2:?}"; SAMPLE="${3:?}"; FT="${4:?}"; IBIN="${5:?}"
cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src/egm_tnp_analysis || exit 10
source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh || exit 11
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:$PYTHONPATH
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
case "$FT" in
  nominal) FTARG="" ;; altSig) FTARG="--altSig" ;;
  altBkg) FTARG="--altBkg" ;; altSigBkg) FTARG="--altSigBkg" ;;
  *) echo "unknown fit type $FT"; exit 12 ;;
esac
echo "[binworker] $(basename "$CFG") $SAMPLE $FT bin=$IBIN host=$(hostname) start=$(date)"
python3 tnpEGM_fitter.py "$CFG" --flag "$FLAG" --doFit --fitSample "$SAMPLE" $FTARG --iBin "$IBIN"
rc=$?
echo "[binworker] DONE rc=$rc $(date)"
exit $rc
