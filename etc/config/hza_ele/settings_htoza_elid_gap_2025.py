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

# flag to be Tested
flags = {
    'hza_elid_gap_2025_sf': (
        '('
        + baseline_cut +
        '('
        # ele Et > 10 region
        '((el_sc_et > 10) && ('
        '    (abs(el_sc_eta) < 0.8   && el_hzzMVA > 0.3527)'
        ' || (abs(el_sc_eta) >= 0.8  && abs(el_sc_eta) < 1.479 && el_hzzMVA > 0.2601)'
        ' || (abs(el_sc_eta) >= 1.479 && el_hzzMVA > -0.4954)'
        ' ))'
        ' || '
        # ele Et < 10 region
        '((el_sc_et < 10) && ('
        '    (abs(el_sc_eta) < 0.8   && el_hzzMVA > 0.9267)'
        ' || (abs(el_sc_eta) >= 0.8  && abs(el_sc_eta) < 1.479 && el_hzzMVA > 0.9138)'
        ' || (abs(el_sc_eta) >= 1.479 && el_hzzMVA > 0.9683)'
        ' ))'
        ')'
        ')'
    ),
}

# /eos/cms/store/group/phys_egamma/ec/nkasarag/EGM_comm/TnP_samples/2022/sim/DY_NLO/merged_Run3Summer22MiniAODv4-130X_mcRun3_2022_realistic_v5-v2.root
baseOutDir = '/eos/home-p/pelai/HZa/root_TnP/'

#############################################################
########## samples definition  - preparing the samples
#############################################################
### samples are defined in etc/inputs/tnpSampleDef.py
### not: you can setup another sampleDef File in inputs
import etc.inputs.tnpSampleDef as tnpSamples
tnpTreeDir = 'tnpEleIDs'

samplesDef = {
        'data'  : tnpSamples.Run3_2025_ele['Data_2025'].clone(),
        'mcNom' : tnpSamples.Run3_2025_ele['DY_MC_LO_2025'].clone(),
        'tagSel': tnpSamples.Run3_2025_ele['DY_MC_LO_2025'].clone(),
        'mcAlt': tnpSamples.Run3_2025_ele['DY_MC_NLO_2025'].clone(),
    }
## can add data sample easily
# samplesDef['data'].add_sample( tnpSamples.Run3_2025['Data_2025D'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2025['Data_2025E'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2025['Data_2025F'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2025['Data_2025G'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2025['Data_2025H'] )
# samplesDef['data'].add_sample( tnpSamples.Run3_2025['Data_2025I'] )


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
    samplesDef['tagSel'].rename('mcAltSel_DY_MC_LO_2025')
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
   { 'var' : 'el_sc_eta' , 'type': 'float', 'bins': [-1.566,-1.4442, 0.0, 1.4442, 1.566] },
   { 'var' : 'el_et' , 'type': 'float', 'bins': [7,35,100] },
]

#############################################################
########## Cuts definition for all samples
#############################################################
### cut
cutBase   = 'tag_Ele_pt > 40 && abs(tag_sc_eta) < 2.17 && (tag_Ele_q + el_q) == 0'

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
_gap_nominal_low_common = (
    "acmsP[80.,25.,120.]",
    "betaP[0.05,0.001,0.15]",
    "gammaP[0.05,-2,2.]",
    "acmsF[55.,30.,80.]",
    "betaF[0.02,0.001,0.08]",
    "gammaF[0.03,-0.2,0.4]",
)
_gap_nominal_high_common = (
    "acmsP[80.,25.,120.]",
    "betaP[0.05,0.001,0.15]",
    "gammaP[0.03,-2,2.]",
    "acmsF[60.,35.,85.]",
    "betaF[0.02,0.001,0.08]",
    "gammaF[0.03,-0.2,0.4]",
)
tnpParNomFitByBin = {
    0: params_with_updates(
        tnpParNomFit,
        "meanP[-0.9,-5.0,5.0]",
        "sigmaP[1.8,0.5,3.0]",
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[3.0,0.8,4.5]",
        *_gap_nominal_low_common,
    ),
    1: params_with_updates(
        tnpParNomFit,
        "meanF[-1.0,-5.0,1.0]",
        "sigmaF[3.0,1.0,4.5]",
        "acmsF[50.,25.,70.]",
        "betaF[0.01,0.0005,0.05]",
        "gammaF[0.02,-0.1,0.3]",
    ),
    2: params_with_updates(
        tnpParNomFit,
        "meanP[-0.5,-5.0,5.0]",
        "sigmaP[1.4,0.5,2.5]",
        "meanF[-1.2,-5.0,1.0]",
        "sigmaF[3.0,1.0,4.5]",
        "acmsF[52.,25.,72.]",
        "betaF[0.01,0.0005,0.05]",
        "gammaF[0.02,-0.1,0.3]",
    ),
    3: params_with_updates(
        tnpParNomFit,
        "meanP[-0.9,-5.0,5.0]",
        "sigmaP[1.7,0.5,3.0]",
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[3.0,0.8,4.5]",
        *_gap_nominal_low_common,
    ),
    5: params_with_updates(
        tnpParNomFit,
        "meanP[-0.2,-5.0,5.0]",
        "sigmaP[1.1,0.5,2.0]",
        "meanF[-0.4,-3.0,1.0]",
        "sigmaF[1.8,0.8,3.0]",
        *_gap_nominal_high_common,
    ),
    6: params_with_updates(
        tnpParNomFit,
        "meanP[-0.2,-5.0,5.0]",
        "sigmaP[1.1,0.5,2.0]",
        "meanF[-0.4,-3.0,1.0]",
        "sigmaF[1.8,0.8,3.0]",
        *_gap_nominal_high_common,
    ),
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
tnpParAltSigFitByBin = {
    0: params_with_updates(
        tnpParAltSigFit,
        "meanP[-1.2,-5.0,5.0]",
        "sigmaP[4.0,0.8,7.0]",
        "sigmaP_2[1.5,0.3,4.0]",
        "alphaP[1.8,0.8,4.0]",
        "nP[0.8,0.0,8.0]",
        "sosP[1.0,0.0,4.0]",
        "meanF[-2.0,-5.0,3.0]",
        "sigmaF[5.0,0.8,8.0]",
        "sigmaF_2[1.5,0.3,4.0]",
        "alphaF[1.8,0.8,4.0]",
        "nF[1.0,0.0,8.0]",
        "sosF[1.5,0.0,4.0]",
        "acmsP[90.,25.,120.]",
        "betaP[0.05,0.001,0.10]",
        "gammaP[0.06,0.001,1.0]",
        "acmsF[75.,20.,110.]",
        "betaF[0.04,0.001,0.10]",
        "gammaF[0.06,0.001,1.0]",
    ),
}
     
tnpParAltBkgFit = [
    "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.5,5.0]",
    "meanF[-0.0,-5.0,5.0]","sigmaF[0.9,0.5,5.0]",
    "alphaP[0.,-5.,5.]",
    "alphaF[0.,-5.,5.]",
    ]
tnpParAltBkgFitByBin = {
    1: params_with_updates(
        tnpParAltBkgFit,
        "meanF[-0.8,-3.0,1.0]",
        "sigmaF[2.4,0.8,4.0]",
        "alphaF[-0.05,-1.,1.]",
    ),
    3: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-0.95,-5.0,5.0]",
        "sigmaP[1.9,0.8,6.0]",
        "alphaP[0.05,-5.,5.]",
    ),
    4: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-0.35,-5.0,5.0]",
        "sigmaP[1.8,0.8,4.0]",
        "alphaP[0.01,-5.,5.]",
        "meanF[-0.4,-5.0,5.0]",
        "sigmaF[2.2,0.8,6.0]",
        "alphaF[0.03,-5.,5.]",
    ),
}


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
    # 2026-08-23 bin2: sigmaF 撞在 0.1 GeV 的下界 —— 電子質量解析度不可能是 0.1 GeV。
    # 解析度被壓成近乎 delta 之後,gen-level Z lineshape 的輻射尾巴就直接去描述那條連續譜,
    # nSigF 被灌到 1,305,846(佔 fail 總數 3,256,376 的 40%),背景 46.5%,edm 8.3e+08。
    # 資料的 fail 譜是單調下降(60:339443 -> 115:56553,比值 6.0),只有 85 有個約 13 萬的
    # 小 bump —— 真正的 failing 訊號量遠小於擬合宣稱的。
    # 把 sigmaF 地板抬到物理值、上界放寬(failing bump 本來就寬),並比照本檔 bin0 的先例
    # 把 alphaF_2 限制成真正遞減(原上界 0.05 允許背景往上翹)。
    # 純指數描述整條 fail 譜需要 alpha ~ -0.033,落在新範圍內、不會排除最佳解。
    2: params_with_updates(
        tnpParAltSigBkgFit,
        'meanF[-0.5, -4.0, 2.0]',
        'sigmaF[1.5, 0.8, 5.0]',
        'sigmaF_2[2.0, 0.5, 5.0]',
        'sosF[0.2, 0.0, 1.0]',
        'nF[0.4, 0.0, 3.0]',
        'alphaF_2[-0.03, -0.20, -0.002]',
    ),
    0: params_with_updates(
        tnpParAltSigBkgFit,
        'meanF[-1.0, -4.0, 2.0]',
        'sigmaF[2.0, 0.3, 3.5]',
        'sigmaF_2[0.4, 0.1, 1.2]',
        'sosF[0.2, 0.0, 0.8]',
        'alphaF[2.4, 1.4, 3.5]',
        'nF[0.2, 0.0, 1.0]',
        'alphaF_2[-0.05, -0.2, -0.005]',
    ),
    # 2026-08-30 bin6:上一輪把 alphaF_2 鎖成 [-0.15, -0.005](整段都是負的,背景只能遞減)
    # 反而變成這一格的病因。這一格的 fail 譜是**單調上升**的:
    #   60-65 資料 6143 -> 115-120 資料 23238(3.8 倍)
    # 背景無法上升,擬合只好把 alphaF_2 貼死在最靠近 0 的 -0.005 => 幾乎水平的背景
    #   60-65 曲線 14385 / 65-70 14136 / 70-75 14306
    # 於是低質量端曲線是資料的 2.3 倍(-57%)、高質量端只有資料的 2/3(+74%)。
    # sigmaF_2 同時撞上界 2.5 —— 訊號的寬成分被迫去補高質量端。
    # 修法:讓 alphaF_2 的上界跨過 0(資料要的是上升的背景),並放寬被連累的 sigmaF_2。
    # 下界維持 -0.20 不動,不排除「其實該遞減」的解。
    # ⚠️ 這一格的遞減限制與 bin0/bin2 是各自獨立的覆寫,那兩格不受影響。
    6: params_with_updates(
        tnpParAltSigBkgFit,
        'meanF[-0.8, -3.0, 1.0]',
        'sigmaF[0.5, 0.1, 2.0]',
        'sigmaF_2[1.5, 0.2, 5.0]',
        'sosF[0.15, 0.0, 0.8]',
        'alphaF[2.4, 1.4, 3.5]',
        'nF[0.6, 0.0, 1.5]',
        'alphaF_2[0.005, -0.20, 0.06]',
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


# --- bin5 passing Hessian 奇異 (2026-08-20) ---
# passing 側的參數確實移動過(acmsP、sigmaP 都是擬合值而非初始值)、edm 也降到個位數，
# 但誤差全為 0、covQual=0 —— 是 Hessian 算不出來，不是 MIGRAD 沒跑。
# 原因: nBkgP/nSigP 只有 0.8% (高 et 35-100 的 barrel，Z 峰乾淨、背景幾乎不存在)，
# 背景形狀參數 acmsP/betaP/gammaP 沒有任何資料能約束，Hessian 在那些方向奇異。
# fail 側同設定 covQual=3 完全正常，排除設定本身的問題。
# 與 sielleg30trigger_nongap_2026 bin27 同型(那次 edm 894 -> 2.3e-4、covQual 1 -> 3)，
# 沿用同一處方: 釘住 passing 背景 turn-on，只讓 meanP/sigmaP 浮動。
tnpParNomFitByBin = dict(globals().get('tnpParNomFitByBin', {}))
tnpParNomFitByBin[5] = params_with_updates(
    tnpParNomFitByBin.get(5, tnpParNomFit),
    "meanP[0.0,-2.0,2.0]",
    "sigmaP[1.0,0.5,3.0]",
    "acmsP[52.0]",
    "betaP[0.006]",
    "gammaP[0.0,-0.05,0.05]",
    "peakP[87.0]",
)
