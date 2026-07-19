#!/usr/bin/env python3
# altBkg high-ET recipe 沒約束 alphaF → 失敗腿 Exp 背景往高質量上升。加 alphaF[-0.02,-0.1,0.005]。
import os, py_compile, shutil, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = ['settings_htoza_elminiIso%s_%s_%s.py' % (c,r,y)
         for c in ('0p1','0p15') for r in ('gap','nongap') for y in ('2024','2025')]
OLD = '_ab_highet  = params_with_updates(tnpParAltBkgFit, "meanF[0.0,-2.5,2.5]","sigmaF[1.0,0.5,2.5]") + _gaus_pars'
NEW = '_ab_highet  = params_with_updates(tnpParAltBkgFit, "meanF[0.0,-2.5,2.5]","sigmaF[1.0,0.5,2.5]","alphaF[-0.02,-0.1,0.005]") + _gaus_pars'
ok=True
for fn in FILES:
    p=os.path.join(D,fn); txt=open(p).read()
    if OLD not in txt: print(f'[SKIP] {fn}'); continue
    shutil.copy2(p, p+'.bak_abalphaF_20260716'); open(p,'w').write(txt.replace(OLD,NEW))
    try: py_compile.compile(p,doraise=True); print(f'[OK]   {fn}')
    except py_compile.PyCompileError as e: print(f'[FAIL] {fn}: {e}'); ok=False
print('=== ALL OK ===' if ok else '=== FAIL ==='); sys.exit(0 if ok else 1)
