#!/usr/bin/env python3
# 2026-07-15: nominal + altBkg 全套改解析(通用 lineshape⊗Gaussian + addGaus)。加各 recipe。
import os, py_compile, shutil, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = ['settings_htoza_elminiIso%s_%s_%s.py' % (c,r,y)
         for c in ('0p1','0p15') for r in ('gap','nongap') for y in ('2024','2025')]
BLOCK = '''

# --- nominal + altBkg --addGaus 全套解析變體 (2026-07-15) ---
# fitUtils isaddGaus: signal=通用 gen-level lineshape ⊗ Gaussian(平滑,無 template shoulder)
# + sigGaussFail 補真實 shoulder。nominal=CMSShape bkg(pin acmsP 防 rail); altBkg=Exp bkg。
# bimodal(中央 et20-35: 18-21): 窄 sigmaF + pin failing bkg + shoulder Gaussian。
# high-ET 中央(34-37,42-45): 窄 sigmaF,Gaussian 自動關。
_gs = ["meanGF[77.0,73.0,81.0]", "sigmaGF[3.5,2.0,6.0]"]
tnpParNomFit_addGaus = tnpParNomFit + _gaus_pars
tnpParNomFit_addGausByBin = {}
_nom_bimodal = params_with_updates(tnpParNomFit, "meanF[0.0,-3.0,3.0]","sigmaF[1.0,0.5,2.2]","acmsF[58.0]","betaF[0.10]","gammaF[0.0,-0.03,0.05]","acmsP[60.0]","betaP[0.05]","gammaP[0.05,0.0,0.5]") + _gs
_nom_highet  = params_with_updates(tnpParNomFit, "meanF[0.0,-2.5,2.5]","sigmaF[1.0,0.5,2.5]","acmsP[60.0]","betaP[0.05]","gammaP[0.05,0.0,0.5]") + _gaus_pars
for _b in (18,19,20,21): tnpParNomFit_addGausByBin[_b] = _nom_bimodal
for _b in (34,35,36,37,42,43,44,45): tnpParNomFit_addGausByBin[_b] = _nom_highet
tnpParAltBkgFit_addGaus = tnpParAltBkgFit + _gaus_pars
tnpParAltBkgFit_addGausByBin = {}
_ab_bimodal = params_with_updates(tnpParAltBkgFit, "meanF[0.0,-3.0,3.0]","sigmaF[1.0,0.5,2.2]","alphaF[-0.02,-0.1,0.02]") + _gs
_ab_highet  = params_with_updates(tnpParAltBkgFit, "meanF[0.0,-2.5,2.5]","sigmaF[1.0,0.5,2.5]") + _gaus_pars
for _b in (18,19,20,21): tnpParAltBkgFit_addGausByBin[_b] = _ab_bimodal
for _b in (34,35,36,37,42,43,44,45): tnpParAltBkgFit_addGausByBin[_b] = _ab_highet
'''
ok=True
for fn in FILES:
    p=os.path.join(D,fn); txt=open(p).read()
    if 'nominal + altBkg --addGaus 全套解析變體' in txt:
        print(f'[SKIP] {fn}'); continue
    shutil.copy2(p, p+'.bak_nomaltbkg_20260715'); open(p,'w').write(txt+BLOCK)
    try: py_compile.compile(p,doraise=True); print(f'[OK]   {fn}')
    except py_compile.PyCompileError as e: print(f'[FAIL] {fn}: {e}'); ok=False
print('=== ALL OK ===' if ok else '=== FAIL ==='); sys.exit(0 if ok else 1)
