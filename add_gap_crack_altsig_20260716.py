#!/usr/bin/env python3
# 為 4 個 gap config 的 altSig --addGaus 加 crack 專屬 recipe (bin0/bin3)。
# 病灶: gap crack (η∓1.44~1.57, et7-35) failing 譜寬又亂(主峰~85 broad + 低質量 shoulder~74)。
#   bin0: base meanF 撞界 -5 → eff 離群高 0.9515(vs nominal 0.9407)。
#   bin3: base sosF 撞界 0.5 → DSCB 過寬 undershoot 主峰 → eff 偏低 0.9271。
# 修: 放寬 meanF 下界(-8)、sosF 下界(0.05),讓 addGaus 第二 Gaussian 往更低質量 catch shoulder。
# 只動 altSig bin0/bin3,其餘 fit type/bin 不變。
import os, re

CONFIGS = [
    "settings_htoza_elminiIso0p1_gap_2024.py",
    "settings_htoza_elminiIso0p1_gap_2025.py",
    "settings_htoza_elminiIso0p15_gap_2024.py",
    "settings_htoza_elminiIso0p15_gap_2025.py",
]
CFGDIR = "etc/config/hza_ele"
BAK = ".bak_gapcrackaltsig_20260716"

BLOCK = '''
# --- gap crack (bin0 η-1.57~-1.44, bin3 η+1.44~+1.57) altSig 專屬 (2026-07-16) ---
# crack 低統計、failing 譜寬又亂(主峰~85 broad + 低質量 shoulder~74)。base meanF 撞界 -5
# (bin0 eff 離群高 0.9515)、sosF 撞界 0.5(bin3 DSCB 過寬 undershoot 主峰)。放寬 meanF/sosF
# 下界並讓 addGaus 第二 Gaussian 往更低質量 catch shoulder(收窄 altSig systematic band)。
_crack_altsig = params_with_updates(
    tnpParAltSigFit,
    "meanF[-3.0,-8.0,1.0]",
    "sigmaF[2.5,1.0,6.0]",
    "sigmaF_2[3.5,1.0,8.0]",
    "sosF[0.6,0.05,3.0]",
) + ["meanGF[73.0,66.0,80.0]", "sigmaGF[5.0,2.5,11.0]"]
for _cb in (0, 3):
    tnpParAltSigFit_addGausByBin[_cb] = _crack_altsig
'''

ANCHOR = "tnpParAltSigFit_addGausByBin = {k: (list(v) + _gaus_pars) for k, v in tnpParAltSigFitByBin.items()}"

for cfg in CONFIGS:
    p = os.path.join(CFGDIR, cfg)
    src = open(p).read()
    if "_crack_altsig" in src:
        print(f"[skip] {cfg} already has crack recipe"); continue
    if ANCHOR not in src:
        print(f"[FAIL] {cfg}: anchor not found"); continue
    open(p + BAK, "w").write(src)
    src2 = src.replace(ANCHOR, ANCHOR + "\n" + BLOCK, 1)
    open(p, "w").write(src2)
    print(f"[ok] {cfg} patched (+{BLOCK.count(chr(10))} lines), backup {BAK}")
print("done")
