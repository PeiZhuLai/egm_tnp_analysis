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
    'hza_dielleg23trigger_nongap_2026_sf': '(passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg1L1match == 1 && el_hltE23E12leg1_dR < 0.3)',
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
        'data'  : tnpSamples.Run3_2026_ele['Data_2026'].clone(),
        'mcNom' : tnpSamples.Run3_2026_ele['DY_MC_LO_2026'].clone(),
        'tagSel': tnpSamples.Run3_2026_ele['DY_MC_LO_2026'].clone(),
        'mcAlt': tnpSamples.Run3_2026_ele['DY_MC_NLO_2026'].clone(),
    }
## can add data sample easily
# samplesDef['data'].add_sample( tnpSamples.Run3_2026['Data_2026D'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2026['Data_2026E'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2026['Data_2026F'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2026['Data_2026G'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2026['Data_2026H'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2026['Data_2026I'] )


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
    samplesDef['tagSel'].rename('mcAltSel_DY_MC_LO_2026')
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
# Failing-leg CMSShape bkg too large: pull turn-on (acmsF) below the Z peak so the
# background is a smooth falling shape under the resonance, and free betaF/gammaF.
_failbkg_nom = ("acmsF[62.,45.,72.]", "betaF[0.04,0.002,0.15]", "gammaF[0.10,-0.5,1.5]")
tnpParNomFitByBin = {
    18: params_with_updates(
        tnpParNomFit,
        "meanP[-0.2,-5.0,5.0]",
        "sigmaP[1.4,0.5,4.0]",
        "acmsP[92.,65.,120.]",
        "betaP[0.05,0.002,0.12]",
        "gammaP[0.08,-0.2,1.2]",
        "peakP[89.0,84.0,93.0]",
        "meanF[-0.4,-5.0,5.0]",
        "sigmaF[2.0,0.5,5.5]",
        "acmsF[75.,45.,100.]",
        "betaF[0.06,0.002,0.14]",
        "gammaF[0.05,-0.2,0.8]",
    ),
    17: params_with_updates(tnpParNomFit, *_failbkg_nom),
    21: params_with_updates(tnpParNomFit, *_failbkg_nom),
}
# bin21: passing signal stuck narrow at init (sigmaP=0.9) -> over-peaks the data and
# misses the shoulders. Widen sigmaP (failing already handled by _failbkg_nom above).
tnpParNomFitByBin[21] = params_with_updates(
    tnpParNomFitByBin[21],
    "meanP[0.0,-2.0,2.0]",
    "sigmaP[1.8,1.2,4.0]",
)

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
# Failing-leg bkg too large in altSig: lower acmsF turn-on, free betaF.
_failbkg_altsig = ("acmsF[62.,45.,72.]", "betaF[0.04,0.005,0.15]", "gammaF[0.10,0.002,1.5]")
tnpParAltSigFitByBin = {
    20: params_with_updates(
        tnpParAltSigFit,
        "meanP[0.0,-4.0,4.0]",
        "sigmaP[1.5,0.5,4.5]",
        "sigmaP_2[1.5,0.4,4.5]",
        "sosP[0.8,0.0,3.0]",
        "acmsP[92.,65.,120.]",
        "betaP[0.05,0.002,0.12]",
        "gammaP[0.08,0.002,1.5]",
        "peakP[90.0,84.0,94.0]",
        "meanF[-0.5,-5.0,5.0]",
        "sigmaF[2.0,0.5,5.5]",
        "sigmaF_2[1.2,0.3,4.0]",
        "sosF[0.8,0.0,3.0]",
        "acmsF[88.,55.,115.]",
        "betaF[0.06,0.002,0.14]",
        "gammaF[0.06,0.002,1.0]",
        "peakF[86.0,80.0,92.0]",
    ),
    17: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    18: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    19: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    21: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    22: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
    23: params_with_updates(tnpParAltSigFit, *_failbkg_altsig),
}
# 2026-08-23 bin17: passing 訊號太窄 —— sigmaP=0.838 幾乎坐在 0.7 的地板上,
# 而資料的 Z 峰明顯較寬(80:11985 85:25969 90:19160 95:3588)。alphaP 也撞在下界 1.2。
# 另外 passing 背景只佔 0.2%,acmsP 撞上界 90 是「背景近乎為零時形狀無資料約束」的
# 必然結果,不是病徵,所以把背景形狀釘住而不是繼續放寬它。
# (bins 19/21 是相反方向的問題 —— 那兩個是 sigmaP 跑太寬,見下方。)
tnpParAltSigFitByBin[17] = params_with_updates(
    tnpParAltSigFitByBin[17],
    "meanP[0.0,-3.0,3.0]",
    "sigmaP[2.0,1.0,5.0]",
    "sigmaP_2[1.5,0.5,5.0]",
    "sosP[0.8,0.0,3.0]",
    "alphaP[2.0,0.8,3.5]",
    "acmsP[75.0]",
    "betaP[0.04]",
    "gammaP[0.05]",
)

# bins 19/21: passing CB core ran away wide (sigmaP railed at 6) and under-peaked the
# sharp data Z. Cap sigmaP lower and pin meanP near the Z so a sharper core is found.
for _b in (19, 21):
    tnpParAltSigFitByBin[_b] = params_with_updates(
        tnpParAltSigFitByBin[_b],
        "meanP[0.0,-2.0,2.0]",
        "sigmaP[2.0,0.8,4.0]",
        "sigmaP_2[1.0,0.4,3.0]",
        "sosP[0.6,0.0,3.0]",
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
    # bin39 (et 50-100 endcap): high-pT resolution exceeds the default sigmaP cap
    # (2.0), so the passing CB core rails at 2.0 and over-peaks the data. Raise caps.
    39: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[2.5, 0.8, 4.5]',
        'sigmaP_2[2.0, 0.6, 4.5]',
        'sosP[0.8, 0.0, 3.0]',
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

# ---------------------------------------------------------------------------
# 2026-08-29  altSigBkgFit bin40（eta -2.50..-2.00, ET 100-500, failing）
#   使用者:"weird peak at 60 GeV"
#
# failing 側總共只有 ~40 個事件(nSigF=38.1、nBkgF=1.85)。alphaF_2 = -0.3874,
# exp(-0.387*m) 在 60-130 GeV 內從 e^-23 掉到 e^-50 —— 背景整包塌到質量窗左緣,
# 圖上就是那個 60 GeV 的怪峰。與 2026-08-28 在 muon Mu17leg 上修掉的 alphaP=-2.48
# 完全同源:預設範圍 [-1, 0.05] 對這個質量尺度等於沒有約束,而 40 個事件根本約束不了
# 背景形狀,擬合就往角落跑。
# sigmaF_2 也撞上界 3(訊號想更寬)。
#
# 修法:把 alphaF_2 收到物理範圍。同 measurement 其他 bin 的 alphaF_2 落在 -0.014
# 附近(base 的種子),取 [-0.06, 0.0] 涵蓋它並排除 -0.39 那個解;sigmaF_2 上界開到 6。
tnpParAltSigBkgFitByBin = dict(globals().get('tnpParAltSigBkgFitByBin', {}))
# 第二輪:只換一個界沒有用。alphaF_2 從 -0.387 移到 -0.06 之後又貼死在新的下界 ——
# failing 側總共 40 個事件、其中背景只有 3.6 個,背景形狀沒有任何資料可以約束,
# 給它什麼界它就往哪個界跑。這種情況要把形狀**釘死**(常數),不是換一個界,
# 否則背景會一直去追雜訊。值取 base 的種子 -0.014(同 measurement 其他 bin 的量級)。
# sigmaF 同時也塌到下界、sosF 貼 0 -> 訊號只剩窄成分;給核心一個物理下限 0.6。
tnpParAltSigBkgFitByBin[40] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(40, tnpParAltSigBkgFit),
    "alphaF_2[-0.014]",
    "sigmaF[1.5,0.6,4.0]",
    "sigmaF_2[3.0,1.0,8.0]",
    "sosF[0.3,0.0,2.0]",
)


# --- bin00 low-mass shoulder, both legs (2026-09-06) ---
# et 7-25 GeV endcap probes: the data carries a genuine bump at 65-75 GeV from
# FSR/bremsstrahlung and mismeasured low-pT electrons. A single exponential can
# only fall, so the fit cannot put it there -- passing runs +33% / +61% short
# at 65-70 / 70-75 GeV, failing +56% / +53%, while 60-65 and 80-85 are
# over-predicted on both legs.
# Worse, the fit compensates by dragging the whole peak left: meanP = -3.06 and
# meanF = -3.83 GeV of "resolution" shift, and the failing leg does not
# converge at all (edm 2.8e+04). So the shoulder is corrupting the peak
# position, not just the tail.
# altBkgFit is the fit whose job is to swap the background model, and Bernstein
# has the freedom to build the shoulder. Order 3 on both legs (nongap_2024 uses
# order 2 for a milder version of this on its bins 3/4).
tnpAltBkgModelByBin = {
    0: {'pass': 'bernstein3', 'fail': 'bernstein3'},
}


# ============================================================================
# addGaus：failing（必要時 passing）訊號加一個 shoulder Gaussian  (2026-09-07)
# ----------------------------------------------------------------------------
# 適用症狀：模板 conv Gaussian 做不出「窄峰 + 低質量 shoulder」的形狀，於是把
# sigmaF 撐寬去湊 shoulder，結果峰頂與 shoulder 兩邊都對不上，而且參數會撞界。
# 加一個第二成分後 sigmaF 可以回到窄值，兩個區域同時對上。
#
# ⚠️ sigmaG 的上界必須收窄（<= 9 GeV）。上界放到 20 時第二成分會退化成寬平台，
#    把背景整段吃進訊號：elid_nongap_2026 bin11/bin12 實測 sigmaGF 12.4 GeV、
#    nSigF 27879+/-484 -> 46534+/-1728、nBkgF 41912 -> 23257，效率 0.9073 ->
#    0.8830，離其他三種擬合更遠。殘差在那種狀態下反而是乾淨的（0 slice），
#    所以驗收不能只看殘差，要一併看 sigmaG 大小與 nSig/nBkg 的誤差有沒有脹起來。
#    健康的 shoulder 是 sigmaG 約 5-6.5 GeV、效率只動 0.5% 以內。
_gaus_f = ("meanGF[74.0,60.0,88.0]", "sigmaGF[5.0,2.0,9.0]")
_gaus_p = ("meanGP[74.0,60.0,88.0]", "sigmaGP[5.0,2.0,9.0]")

addGausBins = {
    'altBkgFit':    (0, 7, 8, 15),
    'altSigBkgFit': (0, 8, 15, 22, 23),
    'altSigFit':    (14, 15, 16, 18, 21, 23),
}

tnpParAltBkgFit_addGaus = params_with_updates(tnpParAltBkgFit, *_gaus_f)
_bybin = globals().get('tnpParAltBkgFitByBin', {})
tnpParAltBkgFit_addGausByBin = {}
for _b, _sides in {0: 'fp', 7: 'fp', 8: 'fp', 15: 'fp'}.items():
    _extra = _gaus_f + (_gaus_p if _sides == "fp" else ())
    tnpParAltBkgFit_addGausByBin[_b] = params_with_updates(
        _bybin.get(_b, tnpParAltBkgFit), *_extra)

tnpParAltSigBkgFit_addGaus = params_with_updates(tnpParAltSigBkgFit, *_gaus_f)
_bybin_asb = globals().get('tnpParAltSigBkgFitByBin', {})
tnpParAltSigBkgFit_addGausByBin = {}
for _b, _sides in {0: 'fp', 8: 'fp', 15: 'fp', 22: 'f', 23: 'fp'}.items():
    _extra = _gaus_f + (_gaus_p if _sides == "fp" else ())
    tnpParAltSigBkgFit_addGausByBin[_b] = params_with_updates(
        _bybin_asb.get(_b, tnpParAltSigBkgFit), *_extra)

tnpParAltSigFit_addGaus = params_with_updates(tnpParAltSigFit, *_gaus_f)
_bybin_as = globals().get('tnpParAltSigFitByBin', {})
tnpParAltSigFit_addGausByBin = {}
for _b, _sides in {14: 'f', 15: 'fp', 16: 'fp', 18: 'f', 21: 'f', 23: 'fp'}.items():
    _extra = _gaus_f + (_gaus_p if _sides == "fp" else ())
    tnpParAltSigFit_addGausByBin[_b] = params_with_updates(
        _bybin_as.get(_b, tnpParAltSigFit), *_extra)
