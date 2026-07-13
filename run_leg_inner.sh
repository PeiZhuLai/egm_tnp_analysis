cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
cd egm_tnp_analysis
export LANG=C LC_ALL=C
echo "=== detached rerun SCOPE=leg MAX_JOBS=2 START $(date) PID=$$ ==="
SCOPE=leg MAX_JOBS=2 bash rerun_hza_ele_20260709.sh
echo "=== detached rerun SCOPE=leg END $(date) ==="
