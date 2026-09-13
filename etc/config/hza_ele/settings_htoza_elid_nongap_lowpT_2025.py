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
    'hza_elid_nongap_lowpT_2025_sf': (
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
   { 'var' : 'el_sc_eta' , 'type': 'float', 'bins': [-2.5, -1.566, -1.4442, 0.0, 1.4442, 1.566, 2.5] },
   { 'var' : 'el_et' , 'type': 'float', 'bins': [7,15] },
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
_lowpt_nominal_tail_common = (
    "acmsP[60.,25.,95.]",
    "betaP[0.06,0.001,0.12]",
    "gammaP[0.05,-2,2.]",
    "acmsF[55.,30.,80.]",
    "betaF[0.02,0.001,0.08]",
    "gammaF[0.03,-0.2,0.4]",
)
tnpParNomFitByBin = {
    0: params_with_updates(
        tnpParNomFit,
        "meanP[-2.0,-5.0,5.0]",
        "sigmaP[1.8,0.5,3.0]",
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.0,0.8,4.5]",
        *_lowpt_nominal_tail_common,
    ),
    5: params_with_updates(
        tnpParNomFit,
        "meanP[-2.0,-5.0,5.0]",
        "sigmaP[1.9,0.5,3.0]",
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[3.2,0.8,4.8]",
        *_lowpt_nominal_tail_common,
    ),
    2: params_with_updates(
        tnpParNomFit,
        "meanP[-0.6,-3.0,2.0]",
        "sigmaP[1.5,0.7,3.0]",
        "acmsP[72.,50.,90.]",
        "betaP[0.045,0.005,0.10]",
        "gammaP[0.08,-0.2,0.5]",
        "peakP[87.0,85.0,90.0]",
        "meanF[-0.3,-2.5,2.0]",
        "sigmaF[1.2,0.4,2.8]",
        "acmsF[88.,65.,105.]",
        "betaF[0.006,0.001,0.04]",
        "gammaF[0.06,-0.1,0.5]",
        "peakF[87.0,85.0,89.0]",
    ),
    3: params_with_updates(
        tnpParNomFit,
        "meanP[-0.6,-3.0,2.0]",
        "sigmaP[1.4,0.7,3.0]",
        "acmsP[65.,45.,85.]",
        "betaP[0.052,0.005,0.10]",
        "gammaP[0.07,-0.2,0.5]",
        "peakP[87.0,85.0,90.0]",
        "meanF[-0.2,-2.5,2.0]",
        "sigmaF[0.8,0.35,2.5]",
        "acmsF[48.,35.,70.]",
        "betaF[0.006,0.001,0.04]",
        "gammaF[0.05,-0.1,0.5]",
        "peakF[87.0,85.0,89.0]",
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
_lowpt_altsig_tail_common = (
    "acmsP[85.,25.,110.]",
    "betaP[0.05,0.001,0.10]",
    "gammaP[0.06,0.001,1.5]",
    "acmsF[55.,30.,80.]",
    "betaF[0.02,0.001,0.08]",
    "gammaF[0.03,0.001,0.80]",
)
tnpParAltSigFitByBin = {
    0: params_with_updates(
        tnpParAltSigFit,
        "meanP[-1.6,-5.0,5.0]",
        "sigmaP[4.8,1.0,7.0]",
        "sigmaP_2[1.2,0.3,4.0]",
        "alphaP[2.5,0.8,4.5]",
        "nP[0.8,0.0,8.0]",
        "sosP[1.5,0.0,4.0]",
        "meanF[-1.0,-4.0,2.0]",
        "sigmaF[3.8,1.2,5.5]",
        "sigmaF_2[0.6,0.3,1.5]",
        "alphaF[1.4,1.0,3.0]",
        "nF[0.4,0.0,3.0]",
        "sosF[0.5,0.0,1.5]",
        *_lowpt_altsig_tail_common,
    ),
    5: params_with_updates(
        tnpParAltSigFit,
        "meanP[-1.3,-5.0,5.0]",
        "sigmaP[4.8,1.0,7.0]",
        "sigmaP_2[1.5,0.3,4.0]",
        "alphaP[2.0,0.8,4.5]",
        "nP[0.8,0.0,8.0]",
        "sosP[1.5,0.0,4.0]",
        # failing Z bump is narrow: sigmaF was railing at its 1.0 floor and sigmaF_2 at
        # its 1.5 ceiling. Loosen both so the core/second components sit off the bounds.
        "meanF[-0.5,-2.5,1.0]",
        "sigmaF[1.4,0.5,3.5]",
        "sigmaF_2[1.5,0.5,4.0]",
        "alphaF[1.6,1.0,3.0]",
        "nF[0.4,0.0,3.0]",
        "sosF[0.4,0.0,1.5]",
        # NOTE: tried raising acmsF to lift the bkg at m=60, but a higher CMSShape
        # turn-on moves the bkg peak to ~95 and collapses the sig/bkg split (eff
        # 0.48->0.15). The low bkg at 60 is driven by the signal CB low-side tail, not
        # acmsF, so this is left at the (stable) original turn-on.
        "acmsF[45.,30.,60.]",
        "betaF[0.01,0.001,0.05]",
        "gammaF[0.02,0.001,0.30]",
    ),
}
     
tnpParAltBkgFit = [
    "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.5,5.0]",
    "meanF[-0.0,-5.0,5.0]","sigmaF[0.9,0.5,5.0]",
    "alphaP[0.,-5.,5.]",
    "alphaF[0.,-5.,5.]",
    ]
tnpParAltBkgFitByBin = {
    5: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-2.8,-5.0,0.5]",
        "sigmaP[2.2,0.8,4.5]",
        "alphaP[-0.05,-0.20,0.00]",
        "meanF[-1.5,-4.0,1.5]",
        "sigmaF[2.2,0.8,3.8]",
        "alphaF[-0.02,-0.50,-0.01]",
    ),
}
tnpParAltBkgFitByBin['bin05_el_sc_eta_1p57To2p50_el_et_7p00To15p00'] = tnpParAltBkgFitByBin[5]


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
    # bin00: failing-leg signal core railed right (meanF~+4.9) and over-narrow, with
    # the bkg exponential turning up at high mass. Pin meanF near the Z, widen the
    # core, and forbid the exponential upturn (alphaF_2 max 0).
    #
    # 2026-09-12：上面那次「放寬核心」現在變成病因。sigmaF 被壓滿在 2.0 上界
    # （1.9927 +/- 0.0009），訊號因此吃掉約 113,000 個其他擬合視為背景的事件：
    #   nSigF 160426 對 nominal 47466 / altBkg 47352（altSig 31586）
    #   效率  0.3434 對 0.6320 / 0.6352 / 0.7139  —— 差快一倍，明顯離群
    #   edmF  6.95e+05，covQual 2：根本沒收斂
    # 同時 nF = 0.0007 撞 0 下界、alphaF = 1.444 +/- 1.071 貼著 1.4 下界且誤差
    # 比可動範圍還大 —— 那兩個參數只是開出平坦方向讓 MIGRAD 停不下來。
    # 這格背景占九成以上（nBkgF ~ 567k 對 nSigF ~ 47k），訊號一旦能變寬就會
    # 往背景裡長，所以收上界之外還要把不受約束的尾巴參數釘死。
    0: params_with_updates(
        tnpParAltSigBkgFit,
        # 第三輪試過把 meanF 放寬成 [-5, 1]（理由是 nominal/altBkg 的 meanF 都是
        # -3.2，而 [-2,2] 把它排除在外），結果**大幅變壞**，已撤銷：
        #   nSigF 74001 -> 362521、效率 0.5314 -> 0.1880、edm 0.055 -> 8.93e+08、
        #   殘差 6 -> 11 個 slice；meanF 沒有去 -3.2，而是停在 +0.573，參數誤差
        #   全是 1e-4 量級（MIGRAD 沒動）。
        # 教訓：nominal/altBkg 是模板擬合，meanF 是「模板的位移」；altSigBkg 是
        # 解析 DSCB，meanF 是「峰位本身」。兩者不同義，不能拿前者的數值當後者的
        # 目標值。要跨擬合比對只能比 nSigF / 效率這種物理量。
        'meanF[0.0, -2.0, 2.0]',
        # 第二輪（2026-09-12）：只收 sigmaF 的上界沒有用。RooCBExGaussShapeTNP 收到的
        # 寬度是 sqrt(sigmaF^2 + sosF^2)，所以 sigmaF 被壓到 1.4 上界之後，sosF 立刻
        # 從 0.616 跑到 1.0 上界把寬度補回來：
        #   有效寬度 sqrt(1.9927^2+0.616^2)=2.086 -> sqrt(1.4^2+1.0^2)=1.72
        # 方向對了（nSigF 160426 -> 78996、edm 6.95e+05 -> 0.052、covQual 2 -> 3），
        # 但兩個參數同時撞上界表示擬合還想更寬，所以 sosF 的上界要一起收。
        'sigmaF[0.9, 0.2, 1.3]',
        'sigmaF_2[0.8, 0.3, 1.6]',
        'sosF[0.2, 0.0, 0.5]',
        'alphaF[2.0]',
        'nF[0.4, 0.05, 1.5]',
        'alphaF_2[-0.02, -1, 0.]',
    ),
    5: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[0.35, 0.1, 1.5]',
        'sigmaP_2[0.25, 0.1, 1.5]',
        'sosP[0.05, 0.0, 1.0]',
        'alphaP[2.0, 0.8, 4.0]',
        'nP[0.3, 0.0, 2.0]',
        'alphaP_2[-0.03, -1, 0.05]',
    ),
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


# --- bin02 passing：2026-09-06 嘗試後還原 ---
# 診斷成立：altSig 的 sigmaP = 5.531 對照 nominalFit 的 1.442 寬了 3.8 倍，
# acmsP 撞 90 上界、nP 撞 5，5 個 slice 超過 5 sigma。
# 但把核心釘回 nominal 的解析度之後，殘差確實變好（5 -> 0 個 slice，covQual 2 -> 3），
# 效率卻走反方向：0.7811 -> 0.8047，而 nominal 是 0.7357。同一格的 altBkg 是
# +0.1%、altSigBkg 是 +0.5%，只有 altSig 離群，我的修改讓它從 +6.2% 變成 +9.4%。
# 而且 sigmaP 停在新設的 3.0 上界，也就是那個效率是被界擋出來的，不是自由極小值。
# 殘差不是這裡的判準——這格 passing 有 16 萬個事件，殘差對形狀很敏感，但
# alternate-signal 的用途是產生系統誤差，離群才是問題。維持原設定。
