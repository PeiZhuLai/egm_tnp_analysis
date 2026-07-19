#!/usr/bin/env python3
# 2026-07-14: 對其餘 7 個 iso config 附加 altSig --addGaus 變體(gap_2024 已手動加)。
# 加通用區塊: 每個 altSig bin(保留現有調參)再加第二 Gaussian(sigGaussFail, meanGF~78)
# 補 failing 的 FSR/DY 低質量 shoulder。附在檔尾(此時 tnpParAltSigFit/ByBin 已定義)。
import os, py_compile, sys

D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = [
    'settings_htoza_elminiIso0p15_gap_2025.py',
    'settings_htoza_elminiIso0p15_nongap_2024.py',
    'settings_htoza_elminiIso0p15_nongap_2025.py',
    'settings_htoza_elminiIso0p1_gap_2024.py',
    'settings_htoza_elminiIso0p1_gap_2025.py',
    'settings_htoza_elminiIso0p1_nongap_2024.py',
    'settings_htoza_elminiIso0p1_nongap_2025.py',
]

BLOCK = '''

# --- altSig --addGaus 變體 (2026-07-14) ---
# altSig 解析 DSCB 平滑、undershoots failing 的真實 78 shoulder(FSR/DY prompt ee 失隔離)。
# 加第二 Gaussian(sigGaussFail, meanGF~77)補上; pdfFail=sigFracF*DSCB+(1-sigFracF)*Gauss,
# 兩者都算 nSigF(signal),物理上正確(那批確是 Z->ee 電子失隔離)。保留各 bin 現有調參。
_gaus_pars = ["meanGF[77.0,73.0,81.0]", "sigmaGF[4.0,2.0,8.0]"]
tnpParAltSigFit_addGaus = tnpParAltSigFit + _gaus_pars
tnpParAltSigFit_addGausByBin = {k: (list(v) + _gaus_pars) for k, v in tnpParAltSigFitByBin.items()}
'''

BAK = '.bak_altsigaddgaus_20260714'
ok = True
for fn in FILES:
    p = os.path.join(D, fn)
    txt = open(p).read()
    if 'tnpParAltSigFit_addGaus' in txt:
        print(f'[SKIP] {fn}: 已含 addGaus')
        continue
    import shutil
    shutil.copy2(p, p + BAK)
    open(p, 'w').write(txt + BLOCK)
    try:
        py_compile.compile(p, doraise=True)
        print(f'[OK]   {fn}: 附加 + py_compile 通過')
    except py_compile.PyCompileError as e:
        print(f'[FAIL] {fn}: {e}')
        ok = False
print('=== ALL OK ===' if ok else '=== 有 FAIL ===')
sys.exit(0 if ok else 1)
