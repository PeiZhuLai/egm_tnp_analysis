#!/usr/bin/env python3
# v3 shoulder rollout (Joseph punch-list, user 定案採用 v3):
# bimodal/shoulder failing fit 改 v3 recipe = DSCB 左 tail 推出(alphaF[3.0,2.3,3.5],nF[1.0,0.0,3.0])
# + shoulder Gaussian 收窄(sigmaGF 6.0->4.5)。效果: 集中 signal 回主峰(修 bin12 undershoot)、
# shoulder overshoot 略減(bin19)。代價=多幾個 railed 參數(user 已接受)。
# 1) 4 nongap config: _bimodal_core/_gaus_shoulder 換 v3 → 自動更新 bimodal bins 18-21(altSig+altSigBkg)
# 2) 額外 flagged 非-bimodal bin 指派 v3 recipe(per-config)
import os

CFGDIR = "etc/config/hza_ele"
BAK = ".bak_v3shoulder_20260716"

OLD_CORE = '_bimodal_core = ("meanF[0.0,-3.0,3.0]", "sigmaF[1.0,0.5,2.2]", "sigmaF_2[1.4,0.5,3.5]", "sosF[0.3,0.0,1.6]")'
NEW_CORE = '_bimodal_core = ("meanF[0.0,-3.0,3.0]", "sigmaF[1.0,0.5,2.2]", "sigmaF_2[1.4,0.5,3.5]", "sosF[0.3,0.0,1.6]", "alphaF[3.0,2.3,3.5]", "nF[1.0,0.0,3.0]")'
OLD_GS = '_gaus_shoulder = ["meanGF[77.0,73.0,81.0]", "sigmaGF[3.5,2.0,6.0]"]'
NEW_GS = '_gaus_shoulder = ["meanGF[77.0,73.0,81.0]", "sigmaGF[3.2,2.0,4.5]"]'

# 額外 flagged 非-bimodal bin (bimodal 18-21 已由 _bimodal_core 自動涵蓋)
EXTRA = {
    "elminiIso0p15_nongap_2024": {"altSig": [17], "altSigBkg": []},
    "elminiIso0p15_nongap_2025": {"altSig": [], "altSigBkg": []},
    "elminiIso0p1_nongap_2024":  {"altSig": [16, 24], "altSigBkg": [12, 22, 30]},
    "elminiIso0p1_nongap_2025":  {"altSig": [], "altSigBkg": []},
}

# 錨點: highet loop 的 altSigBkg 行(其後 append 額外指派)
ANCHOR = "    tnpParAltSigBkgFit_addGausByBin[_b] = params_with_updates(list(tnpParAltSigBkgFitByBin.get(_b, tnpParAltSigBkgFit)), *_highet_core) + _gaus_pars"

def extra_block(cfgkey):
    a = EXTRA[cfgkey]["altSig"]; b = EXTRA[cfgkey]["altSigBkg"]
    if not a and not b:
        return ""
    lines = ["", "# --- v3 shoulder rollout: 額外 flagged 非-bimodal bin 用 v3 recipe (2026-07-16) ---"]
    if a:
        lines.append(f"for _b in {tuple(a)}:")
        lines.append("    tnpParAltSigFit_addGausByBin[_b] = params_with_updates(list(tnpParAltSigFitByBin.get(_b, tnpParAltSigFit)), *_bimodal_core) + _gaus_shoulder")
    if b:
        lines.append(f"for _b in {tuple(b)}:")
        lines.append("    tnpParAltSigBkgFit_addGausByBin[_b] = params_with_updates(list(tnpParAltSigBkgFitByBin.get(_b, tnpParAltSigBkgFit)), *_bimodal_core) + _gaus_shoulder")
    return "\n".join(lines) + "\n"

for cfgkey, _ in EXTRA.items():
    p = os.path.join(CFGDIR, f"settings_htoza_{cfgkey}.py")
    s = open(p).read()
    if "v3 shoulder rollout" in s:
        print(f"[skip] {cfgkey} already v3"); continue
    if OLD_CORE not in s or OLD_GS not in s:
        print(f"[FAIL] {cfgkey}: core/gs anchor not found"); continue
    if ANCHOR not in s:
        print(f"[FAIL] {cfgkey}: highet anchor not found"); continue
    open(p + BAK, "w").write(s)
    s = s.replace(OLD_CORE, NEW_CORE, 1).replace(OLD_GS, NEW_GS, 1)
    eb = extra_block(cfgkey)
    if eb:
        s = s.replace(ANCHOR, ANCHOR + "\n" + eb, 1)
    open(p, "w").write(s)
    print(f"[ok] {cfgkey}: v3 core/gs + extra={EXTRA[cfgkey]} (backup {BAK})")
print("done")
