#!/usr/bin/env python3
# 2026-07-13: 修 elminiIso 分母 trigger dR-match 邏輯。
# 舊: probe 被要求同時 match leg1 AND leg2 (物理錯,一顆電子只扮一角) -> 分母偏高 ET。
# 新: probe match leg2 OR leg1 OR Ele30 (= dielleg12 ∪ dielleg23 ∪ sielleg30 numerator)。
# 影響 8 檔: elminiIso0p1/0p15 x gap/nongap x 2024/2025,每檔 2 處。
import os, shutil, py_compile, sys

D = os.path.dirname(os.path.abspath(__file__)) + '/etc/config/hza_ele'
FILES = [
    'settings_htoza_elminiIso0p1_gap_2024.py',
    'settings_htoza_elminiIso0p1_gap_2025.py',
    'settings_htoza_elminiIso0p1_nongap_2024.py',
    'settings_htoza_elminiIso0p1_nongap_2025.py',
    'settings_htoza_elminiIso0p15_gap_2024.py',
    'settings_htoza_elminiIso0p15_gap_2025.py',
    'settings_htoza_elminiIso0p15_nongap_2024.py',
    'settings_htoza_elminiIso0p15_nongap_2025.py',
]

OLD = ('&& ( ((passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg2 == 1 && el_hltE23E12leg2_dR < 0.3 && pair_lead_el_sc_et > 15 ) '
       '&& (passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg1L1match == 1) && el_hltE23E12leg1_dR < 0.3 && pair_lead_el_sc_et > 25 ) '
       '|| (passHltEle30WPTightGsf == 1 && el_hltE30single_dR < 0.3 && pair_lead_el_sc_et > 35))')

NEW = ('&& ( (passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg2 == 1 && el_hltE23E12leg2_dR < 0.3 && pair_lead_el_sc_et > 15 ) '
       '|| (passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg1L1match == 1 && el_hltE23E12leg1_dR < 0.3 && pair_lead_el_sc_et > 25 ) '
       '|| (passHltEle30WPTightGsf == 1 && el_hltE30single_dR < 0.3 && pair_lead_el_sc_et > 35))')

BAK = '.bak_minitrig_or_20260713'
ok = True
for fn in FILES:
    p = os.path.join(D, fn)
    txt = open(p).read()
    n = txt.count(OLD)
    if n != 2:
        print(f'[SKIP] {fn}: 找到 {n} 處 OLD (預期 2) -> 不動,請人工檢查')
        ok = False
        continue
    shutil.copy2(p, p + BAK)
    txt2 = txt.replace(OLD, NEW)
    assert txt2.count(NEW) == 2 and OLD not in txt2, fn
    open(p, 'w').write(txt2)
    try:
        py_compile.compile(p, doraise=True)
        print(f'[OK]   {fn}: 2 處已改 + py_compile 通過 (備份 {BAK})')
    except py_compile.PyCompileError as e:
        print(f'[FAIL] {fn}: py_compile 失敗 {e}')
        ok = False
print('=== ALL OK ===' if ok else '=== 有問題,請檢查上面 SKIP/FAIL ===')
sys.exit(0 if ok else 1)
