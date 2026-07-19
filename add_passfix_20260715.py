#!/usr/bin/env python3
# 2026-07-15: nominal/altBkg addGaus base 加 passing-fix(nominal pin acmsP 防 rail + 收 sigmaP/meanP)。
# 搭配 fitUtils template-passing lineshape。nongap_2024 已手動改,其餘 7 檔在此套。
import os, py_compile, shutil, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = ['settings_htoza_elminiIso%s_%s_%s.py' % (c,r,y)
         for c in ('0p1','0p15') for r in ('gap','nongap') for y in ('2024','2025')
         if not (c=='0p15' and r=='nongap' and y=='2024')]  # nongap_2024 已手動
OLD = '''_gs = ["meanGF[77.0,73.0,81.0]", "sigmaGF[3.5,2.0,6.0]"]
tnpParNomFit_addGaus = tnpParNomFit + _gaus_pars
tnpParNomFit_addGausByBin = {}'''
NEW = '''_gs = ["meanGF[77.0,73.0,81.0]", "sigmaGF[3.5,2.0,6.0]"]
_pass_nom = ("meanP[-0.0,-3.0,3.0]", "sigmaP[1.5,0.5,4.0]", "acmsP[60.0]", "betaP[0.05]", "gammaP[0.05,0.0,0.5]")
_pass_ab  = ("meanP[-0.0,-3.0,3.0]", "sigmaP[1.5,0.5,4.0]")
tnpParNomFit_addGaus = params_with_updates(tnpParNomFit, *_pass_nom) + _gaus_pars
tnpParNomFit_addGausByBin = {}'''
OLD_AB = 'tnpParAltBkgFit_addGaus = tnpParAltBkgFit + _gaus_pars'
NEW_AB = 'tnpParAltBkgFit_addGaus = params_with_updates(tnpParAltBkgFit, *_pass_ab) + _gaus_pars'
ok=True
for fn in FILES:
    p=os.path.join(D,fn); txt=open(p).read()
    if '_pass_nom' in txt: print(f'[SKIP] {fn}'); continue
    if OLD not in txt: print(f'[FAIL] {fn}: 找不到 nominal base block'); ok=False; continue
    if txt.count(OLD_AB)!=1: print(f'[WARN] {fn}: altBkg base 出現 {txt.count(OLD_AB)} 次')
    shutil.copy2(p, p+'.bak_passfix_20260715')
    txt=txt.replace(OLD,NEW).replace(OLD_AB,NEW_AB)
    open(p,'w').write(txt)
    try: py_compile.compile(p,doraise=True); print(f'[OK]   {fn}')
    except py_compile.PyCompileError as e: print(f'[FAIL] {fn}: {e}'); ok=False
print('=== ALL OK ===' if ok else '=== FAIL ==='); sys.exit(0 if ok else 1)
