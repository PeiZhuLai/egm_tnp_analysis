#!/usr/bin/env python3
# 2026-07-15: 把 et20-35 中央雙峰 bin(18-21)的 addGaus recipe(收窄 DSCB core=尖峰
# + Gaussian 只吃 shoulder)套到其餘 3 個 nongap config(nongap_2024 0p15 已手動加)。
import os, py_compile, shutil, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = ['settings_htoza_elminiIso0p15_nongap_2025.py',
         'settings_htoza_elminiIso0p1_nongap_2024.py',
         'settings_htoza_elminiIso0p1_nongap_2025.py']
BLOCK = '''

# --- bimodal 高統計 bin(18-21, et20-35 中央)專屬 addGaus recipe (2026-07-15) ---
# failing 是「尖峰+shoulder」雙峰。generic addGaus 沿用寬 DSCB core → blob、miss 尖峰。
# 改: 收窄 DSCB core(sharp peak) + Gaussian 只吃 shoulder。.get() 版=bin 不在 ByBin 用 base。
_bimodal_core = ("meanF[0.0,-3.0,3.0]", "sigmaF[1.0,0.5,2.2]", "sigmaF_2[1.4,0.5,3.5]", "sosF[0.3,0.0,1.6]")
_gaus_shoulder = ["meanGF[77.0,73.0,81.0]", "sigmaGF[3.5,2.0,6.0]"]
for _b in (18, 19, 20, 21):
    tnpParAltSigFit_addGausByBin[_b] = params_with_updates(list(tnpParAltSigFitByBin.get(_b, tnpParAltSigFit)), *_bimodal_core) + _gaus_shoulder
    tnpParAltSigBkgFit_addGausByBin[_b] = params_with_updates(list(tnpParAltSigBkgFitByBin.get(_b, tnpParAltSigBkgFit)), *_bimodal_core) + _gaus_shoulder
'''
BAK = '.bak_bimodal_20260715'
ok = True
for fn in FILES:
    p = os.path.join(D, fn)
    txt = open(p).read()
    if '_bimodal_core' in txt:
        print(f'[SKIP] {fn}'); continue
    shutil.copy2(p, p + BAK)
    open(p, 'w').write(txt + BLOCK)
    try:
        py_compile.compile(p, doraise=True); print(f'[OK]   {fn}')
    except py_compile.PyCompileError as e:
        print(f'[FAIL] {fn}: {e}'); ok=False
print('=== ALL OK ===' if ok else '=== FAIL ===')
sys.exit(0 if ok else 1)
