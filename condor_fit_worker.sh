#!/usr/bin/env bash
# One condor job = one (settings, sample, fitType); the fitter loops the bins.
#   condor_fit_worker.sh <settings.py> <flag> <data|mcNom|mcAlt> <nominal|altSig|altBkg|altSigBkg>
#
# Runs on a worker node instead of the login node: the previous attempt ran six
# measurements in the foreground and each fitter forked far more processes than
# expected -- 204 of them, 154 GB, load average 169 on a shared lxplus node.
set -o pipefail
CFG="${1:?settings}"; FLAG="${2:?flag}"; SAMPLE="${3:?sample}"; FT="${4:?fitType}"

cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src/egm_tnp_analysis || exit 10
source /cvmfs/sft.cern.ch/lcg/views/LCG_107_swan/x86_64-el9-gcc13-opt/setup.sh || exit 11
export PYTHONPATH=/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src:$PYTHONPATH
# keep ROOT/BLAS from fanning out on the worker
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# The fitter forks one process per bin. Left alone it takes every core on the
# machine, so a job holding one requested CPU ran ~13 processes (2.6 h wall,
# 33.5 h CPU) and its apparent memory need was N processes' worth. Keep this
# equal to request_cpus in the submit file.
export TNP_NPROC="${TNP_NPROC:-8}"

case "$FT" in
  nominal)    FTARG="" ;;
  altSig)     FTARG="--altSig" ;;
  altBkg)     FTARG="--altBkg" ;;
  altSigBkg)  FTARG="--altSigBkg" ;;
  *) echo "unknown fit type $FT"; exit 12 ;;
esac
# TNP_ADDGAUS=1 forces the shoulder Gaussian on for EVERY bin. Since 2026-09-07 that
# is almost never what you want: the normal route is the settings file's own
# `addGausBins` (per fit type, per bin), which tnpEGM_fitter._addgaus_for_bin() reads
# with no flag at all. Turning it on globally was measured across a full comparison to
# improve 699 fits and make 1766 worse -- the extra component only has something to
# describe where the failing leg really is "narrow peak + shoulder". Keep this for
# exploratory A/B runs only.
if [ "${TNP_ADDGAUS:-0}" = "1" ]; then
  FTARG="$FTARG --addGaus"
fi

echo "[worker] $(basename "$CFG") $SAMPLE $FT host=$(hostname) start=$(date)"
# Go through eos_retry.sh: ROOT can fail to flush the result to EOS and still exit 0,
# keep the old file, and update its mtime -- so a bare invocation reports success while
# the fit result on disk is stale. Seen at least five times on 2026-08-22..23; a re-run
# fixed it every time. rc=75 means the write kept failing: the output is NOT usable and
# the job must not be counted as done.
RETRY=/afs/cern.ch/work/p/pelai/HZa/TnP/eos_retry.sh
if [ -x "$RETRY" ]; then
  TNP_RETRY_LOGDIR="${TNP_RETRY_LOGDIR:-$PWD/condor_fit/eos_retry_logs}" \
    "$RETRY" -n "${TNP_EOS_RETRY_MAX:-3}" -- \
    python3 tnpEGM_fitter.py "$CFG" --flag "$FLAG" --doFit --fitSample "$SAMPLE" $FTARG
  rc=$?
else
  echo "[worker] WARNING: $RETRY missing -- running without EOS write-failure retry"
  python3 tnpEGM_fitter.py "$CFG" --flag "$FLAG" --doFit --fitSample "$SAMPLE" $FTARG
  rc=$?
fi
[ "$rc" = "75" ] && echo "[worker] EOS WRITE FAILED -- result on disk is stale, resubmit this job"
echo "[worker] DONE rc=$rc $(date)"
exit $rc
