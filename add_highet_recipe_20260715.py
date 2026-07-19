#!/usr/bin/env python3
import os, py_compile, shutil, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = ['settings_htoza_elminiIso0p15_nongap_2025.py',
         'settings_htoza_elminiIso0p1_nongap_2024.py',
         'settings_htoza_elminiIso0p1_nongap_2025.py']
BLOCK = '''

# --- high-ET 中央 bin(et50-100: 34-37, et100-500: 42-45)窄核 recipe (2026-07-15) ---
# base altSig(sigmaF up to 8)→ 高 ET 尖峰 failing 被 fit 太寬。收窄 core;無 shoulder Gaussian 自動關。
_highet_core = ("meanF[0.0,-2.5,2.5]", "sigmaF[1.0,0.5,2.5]", "sigmaF_2[1.4,0.5,3.5]", "sosF[0.3,0.0,1.6]")
for _b in (34, 35, 36, 37, 42, 43, 44, 45):
    tnpParAltSigFit_addGausByBin[_b] = params_with_updates(list(tnpParAltSigFitByBin.get(_b, tnpParAltSigFit)), *_highet_core) + _gaus_pars
    tnpParAltSigBkgFit_addGausByBin[_b] = params_with_updates(list(tnpParAltSigBkgFitByBin.get(_b, tnpParAltSigBkgFit)), *_highet_core) + _gaus_pars
'''
ok=True
for fn in FILES:
    p=os.path.join(D,fn); txt=open(p).read()
    if '_highet_core' in txt: print(f'[SKIP] {fn}'); continue
    shutil.copy2(p, p+'.bak_highet_20260715'); open(p,'w').write(txt+BLOCK)
    try: py_compile.compile(p,doraise=True); print(f'[OK]   {fn}')
    except py_compile.PyCompileError as e: print(f'[FAIL] {fn}: {e}'); ok=False
print('=== ALL OK ===' if ok else '=== FAIL ==='); sys.exit(0 if ok else 1)
