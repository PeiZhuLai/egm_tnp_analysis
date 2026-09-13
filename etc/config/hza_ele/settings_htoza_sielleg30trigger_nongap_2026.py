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
    ' )'    ') || ('
    + baseline_cut +
    '(el_sc_et < 10) && ('
    '    (abs(el_sc_eta) < 0.8   && el_hzzMVA > 0.9267)'
    ' || (abs(el_sc_eta) >= 0.8  && abs(el_sc_eta) < 1.479 && el_hzzMVA > 0.9138)'
    ' || (abs(el_sc_eta) >= 1.479 && el_hzzMVA > 0.9683)'
    ' )'    '))'
)

# flag to be Tested
flags = {
    'hza_sielleg30trigger_nongap_2026_sf': '(passHltEle30WPTightGsf == 1 && el_hltE30single_dR < 0.3)',
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
   { 'var' : 'el_et' , 'type': 'float', 'bins': [7,33,35,38,45,80,120,500] },
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
tnpParAltSigFitByBin = {
    # 2026-08-22 bin6: fail 側 sigmaF 撞上界 8.0,訊號吃掉低質量端的連續背景
    # (資料 60:2525 65:3451 70:5070 75:8679 明顯上升),擬合回報 nBkgF=209 -> 背景 0.2%,
    # 與資料矛盾。收訊號寬度 + 把背景 turn-on 拉到窗左緣以下,讓背景描述那段上升。
    6: params_with_updates(
        tnpParAltSigFit,
        "sigmaF[2.0,0.7,4.5]",
        "sigmaF_2[2.0,0.5,5.0]",
        "acmsF[58.,40.,75.]",
        "betaF[0.04,0.005,0.15]",
    ),
    13: params_with_updates(
        tnpParAltSigFit,
        "meanP[-0.2,-5.0,5.0]",
        "sigmaP[1.5,0.5,4.5]",
        "sigmaP_2[1.5,0.4,4.5]",
        "sosP[0.8,0.0,3.0]",
        "acmsP[92.,65.,120.]",
        "betaP[0.06,0.002,0.12]",
        "gammaP[0.08,0.002,1.5]",
        "peakP[90.0,84.0,94.0]",
    ),
}
     
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


# --- bin27 passing 收斂失敗 (2026-08-13) ---
# bin27 (eta -0.80..0.00, et 38-45) 的 passing 擬合停在 edm=894、covQual=1:
# sigmaP 釘在下界 0.5 而誤差 107%，nBkgP=1213±73230(誤差是值的 60 倍)，
# gammaP=0.018±1.30 — 背景形狀完全不受約束。訊號 40 萬、背景只佔 0.3%，
# 於是背景參數在沒有資料約束的方向上游走，把整個最小化帶偏；曲線在峰上
# 連續四個 bin 高於資料 13-22% (pull 50)。fail 側同設定完全正常 (edm 7e-4)。
#
# 同一個病徵在 dielleg12trigger_gap_2025 的 bin13/14 已有驗證過的處方:
# 把背景 turn-on 形狀釘成常數、只讓 meanP/sigmaP 浮動 -> edm~1e-3、covQual=3。
# 這是 2026 全部 56 個 bin 中唯一 sigmaP 撞界者，所以只覆寫這一個 bin。
tnpParNomFitByBin = dict(globals().get('tnpParNomFitByBin', {}))
tnpParNomFitByBin[27] = params_with_updates(
    tnpParNomFit,
    "meanP[0.0,-2.0,2.0]",
    "sigmaP[1.3,0.5,3.0]",
    "acmsP[60.0]",
    "betaP[0.05]",
    "gammaP[0.05,0.0,0.5]",
    "peakP[87.0]",
)


# --- bin44 passing: MIGRAD never moved (2026-09-06) ---
# meanP = 0.0001, sigmaP = 0.4990, sigmaP_2 = 0.4997 -- all three still on the
# tnpParAltSigBkgFit seeds (0.0 / 0.5 / 0.5) with errors of 0.0000, edm 0.275,
# status 3. Same signature as bin22 of the 2025 file. The peak lands left of
# the data: 80-85 GeV +37% and 85-90 GeV +36% too high, 95-100 GeV -34% too
# low. nBkgP sits on its 0.5 floor (121 events against 13711 signal) and
# alphaP_2 rails at 0, so the background contributes nothing but slack.
# Give starts near the data and open the 2.0 sigma ceilings, which are too
# tight to describe this et range.
tnpParAltSigBkgFitByBin = dict(globals().get('tnpParAltSigBkgFitByBin', {}))
tnpParAltSigBkgFitByBin[44] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(44, tnpParAltSigBkgFit),
    "meanP[0.6,-2.0,3.0]",
    "sigmaP[1.0,0.2,4.0]",
    "sigmaP_2[1.5,0.2,5.0]",
    "sosP[0.3,0.0,2.0]",
)


# --- bin06 passing：2026-09-06 嘗試後還原 ---
# 診斷是對的（nBkgP=0.5 貼在下界、acmsP 撞 90、gammaP 撞 0.002，三個背景形狀
# 參數都失去約束，訊號因此把低質量端自己吃下來），但把 mean/sigma 錨到 nominal
# 並拉回 turn-on 的做法反而更糟：meanP 撞死在新設的 -3.0 下界，效率從 0.1158
# 掉到 0.1072，離 nominal 的 0.1167 更遠（-0.8% 變成 -8.1%）。
# 這一格 passing 只有一萬三千個訊號、背景近乎為零，殘差檢定看不出差別
# （前後都是 0 個 slice 超標），效率是唯一的判準，而它變差了。維持原設定。


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
    'altBkgFit':    (0, 7),
}

tnpParAltBkgFit_addGaus = params_with_updates(tnpParAltBkgFit, *_gaus_f)
_bybin = globals().get('tnpParAltBkgFitByBin', {})
tnpParAltBkgFit_addGausByBin = {}
for _b, _sides in {0: 'f', 7: 'fp'}.items():
    _extra = _gaus_f + (_gaus_p if _sides == "fp" else ())
    tnpParAltBkgFit_addGausByBin[_b] = params_with_updates(
        _bybin.get(_b, tnpParAltBkgFit), *_extra)


# --- bin00 altBkgFit：單一指數做不出低質量的轉折 (2026-09-07) ---
# altBkg 的背景是 RooExponential，只有一個斜率參數，形狀必然是單調的 ——
# 往低質量只會一路往上爬，做不出資料在 60-70 GeV 的轉折。實測 alphaF =
# -0.0458 +/- 0.0009（自由、沒撞界），也就是說它已經盡力了，是函數族的限制。
# 殘差：60-65 GeV -56%、70-75 GeV +86%（曲線在最低端過高、緊接著又不夠）。
# 這正是 tnpAltBkgModelByBin 那個逃生口存在的理由，改用 bernstein2。
# 注意 bin07 同一個檔案用指數 + addGaus 就修好了（兩側 0 slice），所以只換這格。
tnpAltBkgModelByBin = dict(globals().get('tnpAltBkgModelByBin', {}))
tnpAltBkgModelByBin[0] = 'bernstein2'
