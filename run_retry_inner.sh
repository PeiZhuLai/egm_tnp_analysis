cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
cd egm_tnp_analysis
export LANG=C LC_ALL=C
echo "=== retry rerun SCOPE=all MAX_JOBS=2 (skip-done+timeout) START $(date) PID=$$ ==="
SCOPE=all MAX_JOBS=2 bash rerun_hza_ele_20260709.sh
echo "=== retry rerun END $(date) ==="
