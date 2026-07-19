#!/usr/bin/env python3
# 2026-07-15: altSigBkg(解析 DSCB,同 altSig)也加 addGaus 變體補 failing shoulder。
# 附在檔尾(_gaus_pars 已由 altSig addGaus 區塊定義、tnpParAltSigBkgFitByBin 已定義)。
import os, py_compile, shutil, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = ['settings_htoza_elminiIso%s_%s_%s.py' % (c, r, y)
         for c in ('0p1','0p15') for r in ('gap','nongap') for y in ('2024','2025')]
BLOCK = '''

# --- altSigBkg --addGaus 變體 (2026-07-15) ---
# altSigBkg 的 signal 也是解析 DSCB(RooCBExGaussShapeTNP) → 同 altSig,加第二 Gaussian
# (sigGaussFail, meanGF~77)補 failing 的真實 FSR/DY shoulder。保留各 bin 現有調參。
tnpParAltSigBkgFit_addGaus = tnpParAltSigBkgFit + _gaus_pars
tnpParAltSigBkgFit_addGausByBin = {k: (list(v) + _gaus_pars) for k, v in tnpParAltSigBkgFitByBin.items()}
'''
BAK = '.bak_altsigbkgaddgaus_20260715'
ok = True
for fn in FILES:
    p = os.path.join(D, fn)
    txt = open(p).read()
    if 'tnpParAltSigBkgFit_addGaus' in txt:
        print(f'[SKIP] {fn}: 已含'); continue
    if '_gaus_pars' not in txt:
        print(f'[FAIL] {fn}: 無 _gaus_pars(altSig addGaus 區塊未加?)'); ok=False; continue
    shutil.copy2(p, p + BAK)
    open(p, 'w').write(txt + BLOCK)
    try:
        py_compile.compile(p, doraise=True); print(f'[OK]   {fn}')
    except py_compile.PyCompileError as e:
        print(f'[FAIL] {fn}: {e}'); ok=False
print('=== ALL OK ===' if ok else '=== 有 FAIL ===')
sys.exit(0 if ok else 1)
