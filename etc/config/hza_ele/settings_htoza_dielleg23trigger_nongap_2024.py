# -*- coding: utf-8 -*-
import os, sys
if '_mod_path' not in globals() or not _mod_path:
    _mod_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    if _mod_path not in sys.path:
        sys.path.insert(0, _mod_path)
from etc.config.fit_param_utils import params_with_updates

#############################################################
########## General settings
#############################################################
# EA reference: https://indico.cern.ch/event/1204277/contributions/5064356/attachments/2538496/4369369/CutBasedPhotonID_20221031.pdf

# baseline selection shared by all branches (keep trailing && for concatenation)
baseline_cut = (
    '(el_pt > 7) &&'
    '(abs(el_sc_eta) < 2.5) &&'
    '(abs(el_dz) < 1.0) &&'
    '(abs(el_dxy) < 0.5) &&'
)


# probe preselection (moved from old flags)
probe_preselection_cut = (
    '(('
    + baseline_cut +
    '(el_sc_et > 10) && ('
    '    (abs(el_sc_eta) < 0.8   && el_hzzMVA > 0.3527)'
    ' || (abs(el_sc_eta) >= 0.8  && abs(el_sc_eta) < 1.479 && el_hzzMVA > 0.2601)'
    ' || (abs(el_sc_eta) >= 1.479 && el_hzzMVA > -0.4954)'
    ' )'
    ') || ('
    + baseline_cut +
    '(el_sc_et < 10) && ('
    '    (abs(el_sc_eta) < 0.8   && el_hzzMVA > 0.9267)'
    ' || (abs(el_sc_eta) >= 0.8  && abs(el_sc_eta) < 1.479 && el_hzzMVA > 0.9138)'
    ' || (abs(el_sc_eta) >= 1.479 && el_hzzMVA > 0.9683)'
    ' )'
    '))'
)

# flag to be Tested
flags = {
    'hza_dielleg23trigger_nongap_2024_sf': '(passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg1L1match == 1 && el_hltE23E12leg1_dR < 0.3)',
}

# /eos/cms/store/group/phys_egamma/ec/nkasarag/EGM_comm/TnP_samples/2022/sim/DY_NLO/merged_Run3Summer22MiniAODv4-130X_mcRun3_2022_realistic_v5-v2.root
baseOutDir = '/eos/home-p/pelai/HZa/root_TnP/'

#############################################################
########## samples definition  - preparing the samples
#############################################################
### samples are defined in etc/inputs/tnpSampleDef.py
### not: you can setup another sampleDef File in inputs
import etc.inputs.tnpSampleDef as tnpSamples
tnpTreeDir = 'tnpEleTrig'

samplesDef = {
        'data'  : tnpSamples.Run3_2024_ele['Data_2024'].clone(),
        'mcNom' : tnpSamples.Run3_2024_ele['DY_MC_LO_2024'].clone(),
        'tagSel': tnpSamples.Run3_2024_ele['DY_MC_LO_2024'].clone(),
        'mcAlt': tnpSamples.Run3_2024_ele['DY_MC_NLO_2024'].clone(),
    }
## can add data sample easily
# samplesDef['data'].add_sample( tnpSamples.Run3_2024['Data_2024D'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2024['Data_2024E'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2024['Data_2024F'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2024['Data_2024G'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2024['Data_2024H'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2024['Data_2024I'] )


## can add data sample easily
# samplesDef['data'].add_sample(tnpSamples.Run3_124X_PromptReco2022G['data_Run2022G'].clone()) 
## some sample-based cuts... general cuts defined here after
## require mcTruth on MC DY samples and additional cuts
## all the samples MUST have different names (i.e. sample.name must be different for all)
## if you need to use 2 times the same sample, then rename the second one
#samplesDef['data'  ].set_cut('run >= 273726')
samplesDef['data' ].set_tnpTree(tnpTreeDir)
if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_tnpTree(tnpTreeDir)
if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_tnpTree(tnpTreeDir)
if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_tnpTree(tnpTreeDir)

if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_mcTruth()
if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_mcTruth()
if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_mcTruth()
if not samplesDef['tagSel'] is None:
    samplesDef['tagSel'].rename('mcAltSel_DY_MC_LO_2024')
    samplesDef['tagSel'].set_cut('tag_Ele_pt > 40 && abs(tag_sc_eta) < 2.17 && (tag_Ele_q + el_q) == 0')

## set MC weight, simple way (use tree weight) 
# weightName = 'totWeight'
# if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_weight(weightName)
# if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_weight(weightName)
# if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_weight(weightName)

## set MC weight, can use several pileup rw for different data taking 
# mcNom_puFile = '/eos/cms/store/group/phys_egamma/ec/tnpTuples/Prompt2023/pileupReweightingFiles/preBPIX/DY_madgraph_pho.pu.puTree.root'
# mcAlt_puFile = '/eos/cms/store/group/phys_egamma/ec/tnpTuples/Prompt2023/pileupReweightingFiles/preBPIX/DY_amcatnloext_pho.pu.puTree.root'
weightName = 'totWeight'   ## HZa: in-tree totWeight = weight(gen)*PUweight (was stale 2023 friend)
if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_weight(weightName)
if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_weight(weightName)
if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_weight(weightName)
# if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_puTree(mcNom_puFile)
# if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_puTree(mcAlt_puFile)
# if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_puTree(mcNom_puFile)

#############################################################
########## bining definition  [can be nD bining]
#############################################################
biningDef = [
   { 'var' : 'el_sc_eta' , 'type': 'float', 'bins': [-2.5,-2.0,-1.566,-0.8, 0.0, 0.8, 1.566, 2.0, 2.5] },
   { 'var' : 'el_et' , 'type': 'float', 'bins': [7,25,27,35,50,100,500] },
]

#############################################################
########## Cuts definition for all samples
#############################################################
### cut
cutBase   = 'tag_Ele_pt > 40 && abs(tag_sc_eta) < 2.17 && (tag_Ele_q + el_q) == 0 &&' + probe_preselection_cut

# can add addtionnal cuts for some bins (first check bin number using tnpEGM --checkBins)
additionalCuts = { 
   0 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   1 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   2 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   3 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   4 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   5 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   6 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   7 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   8 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
   9 : 'sqrt( 2*event_met_pfmet*tag_Ele_pt*(1-cos(event_met_pfphi-tag_Ele_phi))) < 45',
}

#### or remove any additional cut (default)
additionalCuts = None

#############################################################
########## fitting params to tune fit by hand if necessary
#############################################################
tnpParNomFit = [
    "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.5,5.0]",
    "meanF[-0.0,-5.0,5.0]","sigmaF[0.9,0.5,5.0]",
    "acmsP[65.,45.,90.]","betaP[0.05,0.005,0.10]","gammaP[0.1, -2, 2]","peakP[87.0,82.0,90.0]",
    "acmsF[65.,45.,90.]","betaF[0.05,0.005,0.10]","gammaF[0.1, -2, 2]","peakF[87.0,82.0,90.0]",
    ]
# Failing-leg CMSShape bkg too large: pull the turn-on (acmsF) below the Z peak
# so the background is a smooth falling shape under the resonance instead of a
# hump at ~85, and free betaF/gammaF.
_failbkg_nom = ("acmsF[62.,45.,72.]", "betaF[0.04,0.002,0.15]", "gammaF[0.10,-0.5,1.5]")
# Passing-leg signal stuck narrow at its 0.9 init -> undershoots the (broad, endcap)
# data Z peak/shoulders. Widen sigmaP, graded by eta (broader in the endcap).
_passwiden_ec = ("meanP[0.0,-2.0,2.0]", "sigmaP[2.0,1.2,4.0]")   # endcap eta bins
_passwiden_mid = ("meanP[0.0,-2.0,2.0]", "sigmaP[1.6,1.0,3.5]")  # transition bins
_passwiden_bl = ("meanP[0.0,-2.0,2.0]", "sigmaP[1.0,0.7,2.5]")   # barrel: sharp peak, light widen only
tnpParNomFitByBin = {
    17: params_with_updates(tnpParNomFit, *_passwiden_ec),
    18: params_with_updates(tnpParNomFit, *_passwiden_mid),
    20: params_with_updates(tnpParNomFit, *_failbkg_nom, *_passwiden_bl),
    21: params_with_updates(tnpParNomFit, *_passwiden_mid),
    22: params_with_updates(tnpParNomFit, *_failbkg_nom, *_passwiden_ec),
    23: params_with_updates(tnpParNomFit, *_failbkg_nom),
    31: params_with_updates(tnpParNomFit, *_failbkg_nom),
    39: params_with_updates(tnpParNomFit, *_failbkg_nom),
}

# # 15
# tnpParNomFit = [
#     "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.5,5.0]",
#     "meanF[-0.0,-5.0,5.0]","sigmaF[1.0,0.0,3.0]",
#     "acmsP[60.,50.,80.]","betaP[0.05,0.01,0.08]","gammaP[0.1, -2, 2]","peakP[87.0,82.0,90.0]",
#     "acmsF[60.,50.,70.]","betaF[0.05,0.05,0.07]","gammaF[0.01, -2, 2]","peakF[87.0,82.0,90.0]",
#     ]

# # 4
# tnpParNomFit = [
#     "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.5,5.0]",
#     "meanF[0.2,0.1,5.0]","sigmaF[1.5]",
#     "acmsP[60.,50.,80.]","betaP[0.05,0.01,0.08]","gammaP[0.1, -2, 2]","peakP[87.0,82.0,90.0]",
#     "acmsF[60.,40.,80.]","betaF[0.05,0.01,0.08]","gammaF[0.01, -2, 0.1]","peakF[87.0,82.0,90.0]",
#     ]
# print("DEBUG tnpParNomFit =", tnpParNomFit)

tnpParAltSigFit = [
    "meanP[-0.0,-5.0,5.0]","sigmaP[1,0.7,6.0]","alphaP[2.0,1.2,3.5]" ,'nP[3,-5,5]',"sigmaP_2[1.5,0.5,6.0]","sosP[1,0.5,5.0]",
    "meanF[-0.0,-5.0,5.0]","sigmaF[2,0.7,8.0]","alphaF[2.0,1.2,3.5]",'nF[3,0,5]',"sigmaF_2[2.0,0.5,6.0]","sosF[1,0.5,5.0]",
    "acmsP[65.,45.,90.]","betaP[0.04,0.005,0.08]","gammaP[0.08, 0.002, 1.5]","peakP[89.0,82.0,90.0]",
    "acmsF[65.,45.,90.]","betaF[0.04,0.005,0.08]","gammaF[0.08, 0.002, 1.5]","peakF[89.0,82.0,90.0]",
    ]

# Failing-leg bkg too large in altSig: same fix as nominal (lower acmsF turn-on,
# free betaF). gammaF range already wide in altSig.
_failbkg_altsig = ("acmsF[62.,45.,72.]", "betaF[0.04,0.005,0.15]", "gammaF[0.10,0.002,1.5]")
tnpParAltSigFitByBin = {
    # 2026-09-06: bins 13/14 have exactly the pathology _failbkg_altsig cures
    # but were never added to the list -- acmsF railed at 90 and betaF on the
    # 0.08 ceiling (nominal's own range goes to 0.10), so the CMSShape turn-on
    # sat at the Z peak and its erfc flooded the low-mass end: 60-65 GeV curve
    # ran +57% / +53% above the data while 65-70 GeV was 30% short. The
    # failing background swallowed the signal -- nSigF 44%/49% below nominal --
    # which pushed the altSig systematic to +7.5% / +9.8% against nominal,
    # where altBkg and altSigBkg both sit within 2.6%.
    13: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    # --- bin14 左尾：2026-09-15 試過解放 alphaF/nF，殘差大好但效率變壞，已撤回 ---
    # 機制查清楚了（這部分是對的，值得留著）：
    # fitUtils.createWorkspaceForAltSig() 會拿 **MC 的 altSigFit 結果**覆寫訊號形狀
    # 參數並**固定成常數**。這一格被釘死的是
    #     alphaF -> 1.424   nF -> 0.183   sigmaF -> 3.203   sigmaF_2 -> 3.221
    # 而 DSCB 左尾 exp(n*(t+|alpha|)) 正由 alphaF/nF 控制，nF=0.183 是極平坦的尾巴。
    # 所以先前兩輪只調背景（_failbkg_altsig、round-2 的 _failbkg_sharp）都不可能成功：
    # 等於拿背景去補訊號形狀的缺口，只能在「60-64 灌太多」和「67-70 補不上」之間二選一。
    # 解放方法是框架自備的 preserve_params_from_mc = changed_names
    #（tnpEGM_fitter.py:455 -> fitUtils.py:510）：參數只要出現在逐 bin 覆寫裡就不被 MC 覆寫。
    #
    # 實測結果：寫進 "alphaF[1.4,0.8,4.0]" 與 "nF[0.5,0.0,5.0]" 之後
    #     log 確認「保留手動設定 alphaF / nF，不使用 MC 覆寫」
    #     殘差 60.5 GeV 的 d/model 0.192 -> 0.619（曲線 119.9 -> 37.2，資料 23）
    #     最大 |pull| 16.5 -> 4.20，Σ|pull|(60-76) 90.6 -> 34.9
    #     sosF 也從撞下界 0.5 脫離到 1.925
    # 看起來是大勝，但效率往錯方向跑：
    #     nominalFit 0.8028 / altBkgFit 0.8181 / altSigBkgFit 0.8182
    #     altSigFit  改前 0.8391（比 altBkg 高 2.6%）→ 改後 0.8763（高 **7.1%**）
    # 產率說明了原因：nSigF 12961 -> 9536、nBkgF 2055 -> 5479，總量守恆，
    # 也就是把 3425 個事件從訊號重新歸類成背景。但另外三種 fit type 都說
    # nSigF ~ 14950（failing 幾乎全是訊號），這個歸類與它們的共識相反。
    #
    # 🔴 判準：**殘差好不算數，效率與 altBkg 的一致性才是決定性的。**
    #    這一格的 round-1 當初就是為了把 altSig 的系統誤差從 +7.5%/+9.8% 壓到 2.6%，
    #    解放左尾等於把它推回原來的壞區間。
    #    要再動這一格，得先解釋「為什麼 altSig 認為 36% 的 failing 是背景，
    #    而另外三種模型認為幾乎沒有」—— 那是模型層級的分歧，不是調參能解決的。
    14: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    16: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    18: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    19: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    20: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    21: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    22: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    23: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
}
# bin18: passing CB floated left (meanP~-2.75) and undershoots the data Z peak.
# Pin meanP near the Z AND widen the core (narrow cores over-peak the broad data Z).
# bin13 additionally rails nF on its ceiling of 5 (longest possible power-law
# tail, which is what reaches down into 60-70 GeV) and sosF on its 0.5 floor.
# Round 2 (2026-09-06): _failbkg_altsig was treating the symptom. It caps acmsF
# at 72 to keep the background off the low-mass end, but the fit then rails
# there AND on betaF's ceiling. The real constraint is betaF: CMSShape is
# erfc((acms-x)*beta) * exp, so a small beta makes the turn-on gradual and the
# background leaks downward no matter where acms sits. This is a 23 GeV trigger
# leg -- its background should fall off a cliff, i.e. beta wants to be LARGE.
# Let beta go to 0.6 and give acms back the room it originally asked for.
_failbkg_sharp = ("acmsF[80.,60.,90.]", "betaF[0.20,0.02,0.60]", "gammaF[0.10,0.002,1.5]")
tnpParAltSigFitByBin[13] = params_with_updates(
    tnpParAltSigFitByBin[13],
    *_failbkg_sharp,
    "nF[1.0,0.0,3.0]",
    "sosF[0.8,0.0,3.0]",
)
# bin14 tried _failbkg_sharp too (2026-09-06 round 2) and it destroyed the
# convergence: edm went 9.2e-06 -> 4.8e+05 for no residual gain (2 slices both
# ways, 60-65 GeV -68% vs -53%). Reverted to round 1, which is _failbkg_altsig
# alone -- edm 9.2e-06, covQual 3, altSig systematic +4.5% against nominal
# (down from +9.8%). Only bin13 benefits from the sharp turn-on.

# bin21 passing: edm 1.39e+06 -- no convergence at all. acmsP=89.06 puts the
# CMSShape turn-on right at the Z peak, so its erfc lays a plateau across the
# whole low-mass end: 60-65 GeV curve 23287 vs 1985 observed (-91%), 65-70 GeV
# -81%, 70-75 GeV -40%; 12 slices past 5 sigma. sigmaP=4.31 is too broad and
# sigmaP_2 rails on its 0.5 floor. Apply the _failbkg_altsig idea to the
# passing leg -- pull the turn-on below the Z, free beta -- and narrow the core.
tnpParAltSigFitByBin[21] = params_with_updates(
    tnpParAltSigFitByBin[21],
    # Round 2's acmsP[80,60,90]/betaP[..,0.60] did converge (edm 1.4e7 -> 0.008)
    # but moved the efficiency -4.2% off nominal while the residuals stayed at
    # 12 slices, so it bought convergence with bias. Back to round 1.
    "acmsP[62.,45.,75.]",
    "betaP[0.04,0.005,0.15]",
    "gammaP[0.10,0.002,1.5]",
    "meanP[-0.5,-2.5,1.5]",
    "sigmaP[2.0,0.7,4.5]",
    "sigmaP_2[1.2,0.3,5.0]",
    "sosP[0.8,0.0,3.0]",
)

tnpParAltSigFitByBin[18] = params_with_updates(
    tnpParAltSigFitByBin[18],
    "meanP[0.0,-1.5,1.5]",
    "sigmaP[3.0,1.8,5.5]",
    "sigmaP_2[2.2,1.0,5.0]",
    "sosP[0.8,0.0,3.0]",
)

tnpParAltBkgFit = [
    "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.5,5.0]",
    "meanF[-0.0,-5.0,5.0]","sigmaF[0.9,0.5,5.0]",
    "alphaP[0.,-5.,5.]",
    "alphaF[0.,-5.,5.]",
    ]


tnpParAltSigBkgFit = [
  'meanP[-0.0, -5.0, 5.0]',
  'meanF[-0.0, -5.0, 5.0]',
  'sigmaP[0.5, 0.1, 2.0]',
  'sigmaF[0.5, 0.1, 2.0]',
  'sigmaP_2[0.5, 0.1, 2.0]',
  'sigmaF_2[0.5, 0.1, 3.0]',
  'sosP[0.10, 0.0, 1.0]',
  'sosF[0.12, 0.0, 1.0]',
  'alphaP[2.0, 1.4, 3.5]', 'nP[0.4, 0.0, 1.5]',
  'alphaF[2.0, 1.4, 3.5]', 'nF[0.4, 0.0, 1.5]',
  'alphaP_2[-0.012, -1, 0]',
  'alphaF_2[-0.014, -1, 0.05]',
]
tnpParAltSigBkgFitByBin = {
    6: params_with_updates(
        tnpParAltSigBkgFit,
        'alphaF_2[-0.014, -1, 0.]',
    ),
}

# ## 06
# tnpParAltSigBkgFit = [
#   'meanP[-0.0, -5.0, 5.0]',
#   'meanF[-0.0, -5.0, 5.0]',
#   'sigmaP[0.5, 0.1, 2.0]',
#   'sigmaF[0.5, 0.1, 2.0]',
#   'sigmaP_2[0.5, 0.1, 2.0]',
#   'sigmaF_2[0.5, 0.1, 3.0]',
#   'sosP[0.10, 0.0, 1.0]',
#   'sosF[0.12, 0.0, 1.0]',
#   'alphaP[2.0, 1.4, 3.5]', 'nP[0.4, 0.0, 1.5]',
#   'alphaF[2.0, 1.4, 3.5]', 'nF[0.4, 0.0, 1.5]',
#   'alphaP_2[-0.012, -1, 0]',
#   'alphaF_2[-0.014, -1, 0.]',
# ]


# --- 背景無約束釘住 (2026-08-21) ---
# 這些 bin 的 nBkg 被壓到接近或等於框架下界(0.5 個事件)，背景佔比 <1.4%，
# 於是背景形狀參數連半個事件都約束不了 -> Hessian 在那些方向奇異 ->
# 誤差全為 0、covQual=0。參數本身是擬合值而非初始值，代表中央值可信、壞的只有誤差。
# 已在 elid_gap_2024/2025 bin6/bin5 與 sielleg30trigger_nongap_2025 bin2/10/29 驗證:
# 釘住背景形狀後 covQual 0->3，效率變動僅 1e-5 量級。
tnpParNomFitByBin = dict(globals().get('tnpParNomFitByBin', {}))
tnpParNomFitByBin[24] = params_with_updates(
    tnpParNomFitByBin.get(24, tnpParNomFit),
    "acmsP[80.0]",
    "betaP[0.06]",
    "gammaP[0.05]",
    "peakP[89.0]",
)
tnpParAltSigBkgFitByBin = dict(globals().get('tnpParAltSigBkgFitByBin', {}))
tnpParAltSigBkgFitByBin[5] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(5, tnpParAltSigBkgFit),
    "alphaF_2[-0.02]",
)

# ---------------------------------------------------------------------------
# 2026-08-29  altBkgFit bin37 / bin38（ET 50-100，failing）
#
# 兩個都收斂良好(edm 1.5e-04 / 9.7e-04、covQual 3)且沒有任何參數撞界 —— 問題純粹是
# altBkg 的單參數 Exponential 背景描述不了資料的形狀:
#   b37  75-80 +25%  80-85 +15%  90-95 +6%  100-105 -9.5%  110-115 -9.7%
#   b38  100-105 -15%
# alphaF 分別是 -0.0088 和 +0.0142(b38 甚至是上升的指數,對背景不合物理),
# 一個自由度不足以同時描述 Z 峰兩側。改用我在 2026-08-23 加進 fitUtils 的
# 二階 Bernstein 背景(tnpAltBkgModelByBin),多兩個自由度但仍是平滑單調族。
# 訊號解析度同時給實體起點:b37 sigmaF=1.23、b38 sigmaF=1.64 偏窄(ET 50-100 的
# endcap 解析度應在 2 GeV 上下),讓它有往上的空間。
tnpAltBkgModelByBin = dict(globals().get('tnpAltBkgModelByBin', {}))
tnpAltBkgModelByBin[37] = 'bernstein2'
# b38 第二輪:bernstein2 沒有改善(100-105 -14.9% -> -15.5%)。那一格的偏差不是背景
# 彈性不足 —— 資料在 Z 峰上緣掉得比模型快(90-95 +7.8%、95-100 +0.4%、100-105 -15.5%),
# 是訊號解析度的問題:altBkg 的訊號是 MC template 摺積 Gaussian(sigmaF=1.538),
# 峰太鈍。給 sigmaF 往下的空間讓峰變利,同時升到 bernstein3 多一個自由度去刻 100-110。
tnpAltBkgModelByBin[38] = 'bernstein3'

tnpParAltBkgFitByBin = dict(globals().get('tnpParAltBkgFitByBin', {}))
for _b, _m in ((37, -0.5), (38, -1.3)):
    tnpParAltBkgFitByBin[_b] = params_with_updates(
        tnpParAltBkgFitByBin.get(_b, tnpParAltBkgFit),
        "meanF[%.1f,-5.0,3.0]" % _m,
        "sigmaF[1.8,0.5,6.0]",
    )
# b38 第二輪:把 sigmaF 的起點壓低並收窄上界,逼出更利的峰(見上面的註解)。
# 下界維持 0.3 不動,不排除比目前 1.538 更窄的解。
tnpParAltBkgFitByBin[38] = params_with_updates(
    tnpParAltBkgFitByBin[38],
    "sigmaF[1.0,0.3,2.5]",
)


# --- bin38 altSigBkgFit: failing 訊號略寬 (2026-09-07) ---
# 90-95 GeV 曲線 3399 對資料 3639 (-7%，峰頂不夠高)，100-105 GeV 1415 對 1204
# (+15%，右側太肥) —— 典型的「太寬」。該格背景只有 552 個事件，所以那 211 個
# 多出來的事件是訊號形狀給的，不是背景。
# 同時 alphaF = 1.412 +/- 1.363 貼著 1.4 下界、sosF = 0.024 +/- 0.753，兩個都
# 完全不受約束，只是開出平坦方向讓 MIGRAD 停不下來（edm 0.44、covQual 2）。
# 改法：把不受約束的 alphaF 釘死，再收 sigmaF 的上界。
tnpParAltSigBkgFitByBin = dict(globals().get('tnpParAltSigBkgFitByBin', {}))
tnpParAltSigBkgFitByBin[38] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(38, tnpParAltSigBkgFit),
    'alphaF[2.0]',
    'sigmaF[0.50, 0.10, 0.62]',
)
