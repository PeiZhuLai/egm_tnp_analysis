cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh` 2>/dev/null
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH"
cd egm_tnp_analysis
python3 add_altsig_addgaus_20260714.py
echo "--- 驗證全 8 config 的 addGaus 可載入(load spec) ---"
for f in etc/config/hza_ele/settings_htoza_elminiIso*.py; do
  python3 -c "
import importlib.util as u
s=u.spec_from_file_location('c','$f'); m=u.module_from_spec(s)
try:
    s.loader.exec_module(m)
    n=len(m.tnpParAltSigFit_addGausByBin)
    print('  OK', '$f'.split('/')[-1], 'addGausByBin bins=', n)
except Exception as e:
    print('  FAIL', '$f'.split('/')[-1], e)
"
done
