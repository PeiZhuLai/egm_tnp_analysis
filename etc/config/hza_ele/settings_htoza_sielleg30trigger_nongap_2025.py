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
    'hza_sielleg30trigger_nongap_2025_sf': '(passHltEle30WPTightGsf == 1 && el_hltE30single_dR < 0.3)',
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


# --- bin2/10/29 passing Hessian 奇異 (2026-08-20) ---
# 三個 bin 的 nBkgP 都停在框架給的下界 0.5 個事件(nBkgP[nTot*0.1, 0.5, nTot*1.5])，
# 背景佔比 0.00%。背景形狀參數 acmsP/betaP/gammaP 因此連半個事件都約束不了，
# Hessian 在那三個方向奇異 -> 誤差全為 0、covQual=0。參數本身是擬合值(不是初始值)，
# 所以中央值可信、壞掉的只有誤差 —— 與 elid_gap_2024/2025 bin6/bin5 同型，
# 那兩個釘住背景後 covQual 0->3 而效率只動 1e-5。
tnpParAltSigFitByBin = dict(globals().get('tnpParAltSigFitByBin', {}))
for _b in (2, 10, 29):
    tnpParAltSigFitByBin[_b] = params_with_updates(
        tnpParAltSigFitByBin.get(_b, tnpParAltSigFit),
        "acmsP[80.0]",
        "betaP[0.06]",
        "gammaP[0.05]",
        "peakP[89.0]",
    )

# ---------------------------------------------------------------------------
# 2026-08-29  使用者標記的三個 bin（altSigBkg b22 fail / altSig b00 fail / altSig b02 pass）
#
# b22 (altSigBkgFit, |eta| 1.57-2.00, ET 35-38, failing)
#   edm 3.7e+07、covQual 2 —— 根本沒收斂。meanF = -2.5e-07、sigmaF = 0.49997、
#   sigmaF_2 = 0.50001 三個都逐位元停在 tnpParAltSigBkgFit 的種子(0.0 / 0.5 / 0.5)，
#   只有 alpha/n/sos/產率動過。0.5 GeV 的解析度對 |eta| 1.57-2.0 不可能。
#   資料峰在 85-90(43916)，模型峰偏高(90-95 曲線 34619 對資料 26531，+30% 在 80-85)。
#   給接近資料的起點,並把 sigma 的上界從 2.0/3.0 開到 6.0(原上界對這個 |eta| 太窄)。
tnpParAltSigBkgFitByBin = dict(globals().get('tnpParAltSigBkgFitByBin', {}))
tnpParAltSigBkgFitByBin[22] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(22, tnpParAltSigBkgFit),
    "meanF[-3.0,-8.0,2.0]",
    "sigmaF[2.5,0.8,6.0]",
    "sigmaF_2[2.0,0.6,6.0]",
    "sosF[0.5,0.0,3.0]",
)

tnpParAltSigFitByBin = dict(globals().get('tnpParAltSigFitByBin', {}))

# b00 (altSigFit, eta -2.50..-2.00, ET 7-33, failing)
#   sigmaF_2 撞下界 0.5、alphaF 撞上界 3.5、gammaF 撞下界。第二個高斯本來要當寬尾,
#   卻塌到跟核心(sigmaF=4.87)重疊 -> 尾巴不足:65-70 +94%、70-75 +87%(資料遠多於曲線),
#   峰區反而過剩(85-90 -8%、90-95 -13%)。
#   修法:把 sigmaF_2 的下界抬到核心之上,強迫它只能當寬尾;同時解開撞界的 alphaF/gammaF。
tnpParAltSigFitByBin[0] = params_with_updates(
    tnpParAltSigFitByBin.get(0, tnpParAltSigFit),
    "sigmaF[4.0,1.0,10.0]",
    "sigmaF_2[9.0,4.0,20.0]",
    "sosF[1.0,0.1,5.0]",
    "alphaF[2.5,1.2,6.0]",
    "nF[3.0,0.0,10.0]",
    "gammaF[0.02,-0.2,1.5]",
)

# b02 (altSigFit, eta -1.57..-0.80, ET 7-33, passing)
#   與 b00 反向:核心 sigmaP=5.77 逼近上界 6、nP 撞上界 5、sosP 撞下界 0.5,
#   結果尾巴過肥 —— 60-65 -68%、65-70 -47%、105-110 -25%、115-120 -29%(曲線都比資料高)。
#   sosP 想再往下卻被 0.5 的下界擋住,nP 想再往上卻被 5 擋住:兩個方向都被關住。
#   把 sosP 下界放到 0.05、nP 上界開到 10,並讓 sigmaP 有往下的空間。
#   ⚠️ 背景已由檔案上方的 (2,10,29) 迴圈釘死(nBkgP 停在框架下界 0.5 個事件),
#      那組 acmsP/betaP/gammaP/peakP 必須保留 —— 這裡是在它之上再疊訊號參數。
tnpParAltSigFitByBin[2] = params_with_updates(
    tnpParAltSigFitByBin.get(2, tnpParAltSigFit),
    "sigmaP[2.5,0.7,6.0]",
    "sigmaP_2[1.0,0.3,6.0]",
    "sosP[0.5,0.05,3.0]",
    "alphaP[2.5,1.2,6.0]",
    "nP[3.0,0.0,10.0]",
)

# ---------------------------------------------------------------------------
# 2026-08-29 b02 第二輪。第一輪(放寬 sosP/nP/alphaP)參數確實變了
#   alphaP 3.44->5.44、nP 5.0->0.01、sosP 0.503->0.332
# 但殘差**逐位元不變** —— 走的是 CB 尾巴 alpha/n 的簡併方向(nP->0 時冪次尾退化成
# 常數平台,與 alphaP 往外移等價),形狀完全沒動。真正卡住的是另外兩個:
#   sigmaP  = 5.77 貼在上界 6      核心寬到 5.8 GeV(|eta| 0.80-1.57 的 passing 電子
#                                  解析度應在 1.5-2.5 GeV)
#   nBkgP   = 0.5  停在框架下界    背景被上方 (2,10,29) 那組覆寫釘死形狀後,
#                                  擬合乾脆把它的產率設成零
# 後果:60-70 與 100-120 兩端曲線都比資料高(-68%/-47% 與 -25%/-29%),
# 因為沒有背景可用,只能讓訊號的尾巴撐滿整個窗。
#
# 第二輪換方向:把背景放開(但限制在合理的 turn-on 範圍),同時把核心壓回物理值。
# 背景一旦能描述兩端,nBkgP 就會離開下界,訊號尾巴也不必再被拉長。
# ⚠️ 這會取代 (2,10,29) 迴圈對 bin2 釘死背景的做法 —— 那組原本是為了修 Hessian 奇異,
#    而奇異的成因正是 nBkgP 卡在下界。若重跑後 covQual 掉回 0,代表背景仍撐不起來,
#    那就要退回釘死並接受形狀偏差。
tnpParAltSigFitByBin = dict(globals().get('tnpParAltSigFitByBin', {}))
tnpParAltSigFitByBin[2] = params_with_updates(
    tnpParAltSigFitByBin.get(2, tnpParAltSigFit),
    "sigmaP[2.0,0.8,4.5]",
    "sigmaP_2[1.2,0.4,5.0]",
    "sosP[0.8,0.05,3.0]",
    "alphaP[2.0,1.2,4.0]",
    "nP[2.0,0.3,10.0]",
    "acmsP[72.,55.,88.]",
    "betaP[0.05,0.01,0.25]",
    "gammaP[0.05,-0.1,0.6]",
    "peakP[89.0]",
)


# --- bin52 passing: MIGRAD never moved (2026-09-06) ---
# meanP = -0.0045 +/- 0.0000 and sigmaP = 0.8992 +/- 0.0001, i.e. still on the
# seed with no error, edm 8.55, status -1, covQual 1. The peak therefore sits
# left of the data: 85-90 GeV curve 11658 vs 9660 observed (+17%), 90-95 GeV
# 22663 vs 24486 (-8%), 95-100 GeV +17% the other way.
# The passing background is 8 events out of 42556, so acmsP/betaP/peakP are
# unconstrained and merely open a flat direction the minimizer cannot leave.
# Same cure bin27 of the 2026 file documents: pin the turn-on shape to
# constants and let only meanP/sigmaP float, with meanP started to the right.
tnpParNomFitByBin = dict(globals().get('tnpParNomFitByBin', {}))
tnpParNomFitByBin[52] = params_with_updates(
    tnpParNomFitByBin.get(52, tnpParNomFit),
    "meanP[0.3,-2.0,2.5]",
    "sigmaP[0.9,0.4,3.0]",
    "acmsP[60.0]",
    "betaP[0.05]",
    "gammaP[0.05,0.0,0.5]",
    "peakP[87.0]",
)


# --- bin42 altBkgFit: failing 訊號略寬 (2026-09-07) ---
# sigmaF = 2.599 是自由參數、沒壓界、edm 1.45e-05、covQual 3，也就是真的極小值，
# 只改初值不會動；要收窄必須收上界。峰太胖的證據：85-90 GeV 曲線 2748 對資料
# 2474 (-10%)、90-95 GeV 3542 對 3754 (+6%)，低質量 75-80 GeV 還缺 48%
# （訊號吃掉了本來該給背景的份）。nominalFit 同格 sigmaF = 1.818。
tnpParAltBkgFitByBin = dict(globals().get('tnpParAltBkgFitByBin', {}))
tnpParAltBkgFitByBin[42] = params_with_updates(
    tnpParAltBkgFitByBin.get(42, tnpParAltBkgFit),
    "sigmaF[2.0,0.5,2.3]",
)
