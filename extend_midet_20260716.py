#!/usr/bin/env python3
# 窄核 recipe 延伸到 et20-35 endcap(16,17,22,23)+ et35-50 全部(24-31),治 meanF rail/太寬。
import os, py_compile, shutil, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = ['settings_htoza_elminiIso%s_%s_%s.py' % (c,r,y)
         for c in ('0p1','0p15') for r in ('gap','nongap') for y in ('2024','2025')]
ADD = "16,17,22,23,24,25,26,27,28,29,30,31,"
# spaced (altSig block) 與 no-space (nom+altBkg block)
OLD_SP = "(32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47)"
NEW_SP = "(16, 17, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47)"
OLD_NS = "(32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47)"
NEW_NS = "(16,17,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47)"
ok=True
for fn in FILES:
    p=os.path.join(D,fn); txt=open(p).read()
    if OLD_SP not in txt and OLD_NS not in txt: print(f'[SKIP] {fn}'); continue
    shutil.copy2(p, p+'.bak_midet_20260716')
    txt=txt.replace(OLD_SP,NEW_SP).replace(OLD_NS,NEW_NS)
    open(p,'w').write(txt)
    try: py_compile.compile(p,doraise=True); print(f'[OK]   {fn}')
    except py_compile.PyCompileError as e: print(f'[FAIL] {fn}: {e}'); ok=False
print('=== ALL OK ===' if ok else '=== FAIL ==='); sys.exit(0 if ok else 1)
