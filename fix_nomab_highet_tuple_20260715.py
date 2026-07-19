#!/usr/bin/env python3
# 修 nom+altBkg block 的 high-ET loop tuple(無空格)延伸到 endcap。
import os, py_compile, shutil, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = ['settings_htoza_elminiIso%s_%s_%s.py' % (c,r,y)
         for c in ('0p1','0p15') for r in ('gap','nongap') for y in ('2024','2025')]
OLD = "(34,35,36,37,42,43,44,45)"
NEW = "(32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47)"
ok=True
for fn in FILES:
    p=os.path.join(D,fn); txt=open(p).read(); cnt=txt.count(OLD)
    if cnt==0: print(f'[SKIP] {fn}'); continue
    shutil.copy2(p, p+'.bak_nomabhighet_20260715'); open(p,'w').write(txt.replace(OLD,NEW))
    try: py_compile.compile(p,doraise=True); print(f'[OK]   {fn}: {cnt} 處')
    except py_compile.PyCompileError as e: print(f'[FAIL] {fn}: {e}'); ok=False
print('=== ALL OK ===' if ok else '=== FAIL ==='); sys.exit(0 if ok else 1)
