#!/usr/bin/env python3
# Group C: gap v3 shoulder rollout (Joseph flag 0p15_gap 2024/2025 altSig/altSigBkg bin1,2).
# gap bins 1,2 = barrel 大 bin(η∓1.44~0.00, et7-35),failing 雙峰(主峰90 + FSR shoulder78),
# 現況 shoulder over-describe。疊 v3 failing 參數(DSCB 左 tail 推出 alphaF[3.0,2.3,3.5]/nF +
# shoulder Gaussian 收窄),保留既有 override(altSig bin1 pass-stall pin、altSigBkg alphaF_2/sigmaP)。
# gap 解析度較寬 → sigmaGF 上界較 nongap(4.5)略寬(5.5)、sigmaF 上界略寬。
import os

CFGDIR = "etc/config/hza_ele"
BAK = ".bak_gapv3shoulder_20260716"
CONFIGS = ["settings_htoza_elminiIso0p15_gap_2024.py", "settings_htoza_elminiIso0p15_gap_2025.py"]
ANCHOR = "tnpParAltSigBkgFit_addGausByBin = {k: (list(v) + _gaus_pars) for k, v in tnpParAltSigBkgFitByBin.items()}"

BLOCK = '''

# --- gap v3 shoulder rollout: bins 1,2 barrel 大 bin failing 雙峰 shoulder (2026-07-16) ---
# 疊 v3 failing 參數(DSCB 左 tail 推出 + shoulder Gaussian 收窄),保留既有 bin override。
_gap_v3_fail = ("sigmaF[1.0,0.5,2.5]", "sigmaF_2[1.4,0.5,4.0]", "sosF[0.3,0.0,1.6]", "alphaF[3.0,2.3,3.5]", "nF[1.0,0.0,3.0]", "sigmaGF[3.5,2.0,5.5]")
for _gb in (1, 2):
    if _gb in tnpParAltSigFit_addGausByBin:
        tnpParAltSigFit_addGausByBin[_gb] = params_with_updates(list(tnpParAltSigFit_addGausByBin[_gb]), *_gap_v3_fail)
    if _gb in tnpParAltSigBkgFit_addGausByBin:
        tnpParAltSigBkgFit_addGausByBin[_gb] = params_with_updates(list(tnpParAltSigBkgFit_addGausByBin[_gb]), *_gap_v3_fail)
'''

for cfg in CONFIGS:
    p = os.path.join(CFGDIR, cfg)
    s = open(p).read()
    if "gap v3 shoulder rollout" in s:
        print(f"[skip] {cfg} already v3"); continue
    if ANCHOR not in s:
        print(f"[FAIL] {cfg}: anchor not found"); continue
    open(p + BAK, "w").write(s)
    # insert after the LAST occurrence of ANCHOR (the altSigBkg one)
    idx = s.rfind(ANCHOR) + len(ANCHOR)
    s2 = s[:idx] + BLOCK + s[idx:]
    open(p, "w").write(s2)
    print(f"[ok] {cfg} gap v3 appended (backup {BAK})")
print("done")
