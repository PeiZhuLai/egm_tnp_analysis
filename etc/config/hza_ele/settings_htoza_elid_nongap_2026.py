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
    'hza_elid_nongap_2026_sf': (
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
   { 'var' : 'el_et' , 'type': 'float', 'bins': [15,20,35,50,100] },
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
_nongap_nominal_fail_falling = (
    "acmsF[55.,35.,75.]",
    "betaF[0.02,0.001,0.08]",
    "gammaF[0.03,-0.2,0.4]",
)
_nongap_nominal_fail_turn68 = (
    "acmsF[68.,58.,78.]",
    "betaF[0.04,0.005,0.08]",
    "gammaF[0.03,-0.1,0.3]",
)
tnpParNomFitByBin = {
    0: params_with_updates(
        tnpParNomFit,
        "meanP[-2.2,-5.0,5.0]",
        "meanF[-2.5,-5.0,1.0]",
        "sigmaF[3.2,0.8,4.6]",
        "acmsP[75.,40.,100.]",
        "betaP[0.05,0.002,0.12]",
        "gammaP[0.08,0.002,2.]",
        *_nongap_nominal_fail_falling,
    ),
    2: params_with_updates(
        tnpParNomFit,
        "meanF[-2.5,-5.0,1.0]",
        "sigmaF[3.0,0.8,4.2]",
        *_nongap_nominal_fail_falling,
    ),
    3: params_with_updates(
        tnpParNomFit,
        "meanP[-0.4,-5.0,5.0]",
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[2.8,0.8,4.0]",
        "acmsP[75.,40.,100.]",
        "betaP[0.05,0.002,0.12]",
        "gammaP[0.08,0.002,2.]",
        *_nongap_nominal_fail_falling,
    ),
    5: params_with_updates(
        tnpParNomFit,
        "meanP[-0.6,-5.0,5.0]",
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.0,0.8,4.2]",
        "acmsP[75.,40.,100.]",
        "betaP[0.05,0.002,0.12]",
        "gammaP[0.08,0.002,2.]",
        *_nongap_nominal_fail_falling,
    ),
    6: params_with_updates(
        tnpParNomFit,
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.2,0.8,4.5]",
        *_nongap_nominal_fail_falling,
    ),
    7: params_with_updates(
        tnpParNomFit,
        "meanP[-2.2,-5.0,2.0]",
        "sigmaP[3.0,1.0,6.0]",
        "meanF[-2.6,-5.0,1.0]",
        "sigmaF[2.2,0.8,3.8]",
        "acmsP[75.,45.,95.]",
        "betaP[0.04,0.002,0.12]",
        "gammaP[0.06,-0.1,0.8]",
        *_nongap_nominal_fail_falling,
    ),
    8: params_with_updates(
        tnpParNomFit,
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.2,1.0,4.8]",
        "acmsF[62.,55.,70.]",
        "betaF[0.02,0.002,0.06]",
        "gammaF[0.02,-0.05,0.2]",
    ),
    9: params_with_updates(
        tnpParNomFit,
        # failing signal floated too wide (sigmaF~3.3) and too far left (meanF~-3.2),
        # overshooting the rising edge and peaking left of the data. Tighten the
        # smearing and keep meanF nearer the Z so the peak lands at ~89.
        "meanF[-1.0,-2.6,1.0]",
        "sigmaF[2.0,0.8,2.7]",
        *_nongap_nominal_fail_turn68,
    ),
    10: params_with_updates(
        tnpParNomFit,
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    11: params_with_updates(
        tnpParNomFit,
        "meanF[-1.8,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    12: params_with_updates(
        tnpParNomFit,
        "meanF[-1.8,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    13: params_with_updates(
        tnpParNomFit,
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    14: params_with_updates(
        tnpParNomFit,
        "meanF[-2.6,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    15: params_with_updates(
        tnpParNomFit,
        "meanP[-1.6,-5.0,2.0]",
        "sigmaP[2.4,0.8,5.0]",
        "meanF[-2.8,-5.0,1.0]",
        "sigmaF[2.8,0.8,4.8]",
        "acmsP[82.,60.,95.]",
        "betaP[0.035,0.002,0.09]",
        "gammaP[0.04,-0.1,0.7]",
        "acmsF[66.,55.,78.]",
        "betaF[0.035,0.003,0.08]",
        "gammaF[0.02,-0.1,0.4]",
    ),
    24: params_with_updates(
        tnpParNomFit,
        "meanP[-1.0,-5.0,5.0]",
        "sigmaP[3.2,1.0,7.0]",
        "meanF[2.0,-3.0,5.0]",
        "sigmaF[2.5,0.8,4.0]",
        "acmsP[85.,60.,100.]",
        "betaP[0.04,0.002,0.12]",
        "gammaP[0.03,-0.2,0.7]",
        "acmsF[75.,50.,95.]",
        "betaF[0.04,0.002,0.12]",
        "gammaF[0.05,-0.2,0.8]",
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
_nongap_altsig_fail_falling = (
    "acmsF[55.,35.,75.]",
    "betaF[0.02,0.001,0.08]",
    "gammaF[0.03,0.001,0.80]",
)
_nongap_altsig_fail_turn68 = (
    "acmsF[68.,58.,78.]",
    "betaF[0.03,0.001,0.08]",
    "gammaF[0.03,0.001,0.80]",
)
tnpParAltSigFitByBin = {
    # --- bin01 failing：2026-09-13 試過抬地板，失敗，已撤回 ---
    # 症狀是 sigmaF / sigmaF_2 / sosF 三個同時停在下界（0.7 / 0.5 / 0.5），
    # 有效寬度只有 左 0.860 / 右 0.707 GeV —— 端蓋、et 15-20 做不到這種解析度。
    # 我把地板抬到 1.0 / 0.8 / 0.8（以同格已收斂的 nominalFit sigmaF=1.59 當錨點），
    # 結果擬合**在新地板上全部重新撞界**，而且多拖了 alphaF / betaF / nF 三個下去，
    # 從 3 個撞界變成 6 個。它仍然要更窄。
    # 決定性的證據是產率對 nominalFit 的一致性（nominal nSigF = 2792.7）：
    #     改前 nSigF =  2271   差 19%
    #     改後 nSigF = 11562   差 314%
    # 也就是說，抬地板只是換來一個「看起來寬一點、但和其他 fit type 更不一致」的解。
    # 這和 phid_lowpt_2023preBPix b07 是同一種錯誤：擬合往某個方向頂界時，
    # 用移動界線去逼它，得到的是偏差不是修正。
    # 真正的病灶在別處 —— failing 側背景是訊號的 5.4 倍（nBkgF 12156 / nSigF 2271），
    # 訊號被壓成針是背景主導下的退化解。要動就要動背景模型，不是訊號寬度。
    0: params_with_updates(
        tnpParNomFit,
        "meanP[-2.2,-5.0,5.0]",
        "meanF[-2.5,-5.0,1.0]",
        "sigmaF[3.2,0.8,4.6]",
        "acmsP[75.,40.,100.]",
        "betaP[0.05,0.002,0.12]",
        "gammaP[0.08,0.002,2.]",
        *_nongap_nominal_fail_falling,
    ),
    2: params_with_updates(
        tnpParNomFit,
        "meanF[-2.5,-5.0,1.0]",
        "sigmaF[3.0,0.8,4.2]",
        *_nongap_nominal_fail_falling,
    ),
    3: params_with_updates(
        tnpParNomFit,
        "meanP[-0.4,-5.0,5.0]",
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[2.8,0.8,4.0]",
        "acmsP[75.,40.,100.]",
        "betaP[0.05,0.002,0.12]",
        "gammaP[0.08,0.002,2.]",
        *_nongap_nominal_fail_falling,
    ),
    5: params_with_updates(
        tnpParNomFit,
        "meanP[-0.6,-5.0,5.0]",
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.0,0.8,4.2]",
        "acmsP[75.,40.,100.]",
        "betaP[0.05,0.002,0.12]",
        "gammaP[0.08,0.002,2.]",
        *_nongap_nominal_fail_falling,
    ),
    6: params_with_updates(
        tnpParNomFit,
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.2,0.8,4.5]",
        *_nongap_nominal_fail_falling,
    ),
    7: params_with_updates(
        tnpParNomFit,
        "meanP[-2.2,-5.0,2.0]",
        "sigmaP[3.0,1.0,6.0]",
        "meanF[-2.6,-5.0,1.0]",
        "sigmaF[2.2,0.8,3.8]",
        "acmsP[75.,45.,95.]",
        "betaP[0.04,0.002,0.12]",
        "gammaP[0.06,-0.1,0.8]",
        *_nongap_nominal_fail_falling,
    ),
    8: params_with_updates(
        tnpParNomFit,
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.2,1.0,4.8]",
        "acmsF[62.,55.,70.]",
        "betaF[0.02,0.002,0.06]",
        "gammaF[0.02,-0.05,0.2]",
    ),
    9: params_with_updates(
        tnpParNomFit,
        # failing signal floated too wide (sigmaF~3.3) and too far left (meanF~-3.2),
        # overshooting the rising edge and peaking left of the data. Tighten the
        # smearing and keep meanF nearer the Z so the peak lands at ~89.
        "meanF[-1.0,-2.6,1.0]",
        "sigmaF[2.0,0.8,2.7]",
        *_nongap_nominal_fail_turn68,
    ),
    10: params_with_updates(
        tnpParNomFit,
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    11: params_with_updates(
        tnpParNomFit,
        "meanF[-1.8,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    12: params_with_updates(
        tnpParNomFit,
        "meanF[-1.8,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    13: params_with_updates(
        tnpParNomFit,
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    14: params_with_updates(
        tnpParNomFit,
        "meanF[-2.6,-5.0,1.0]",
        "sigmaF[2.4,0.8,3.6]",
        *_nongap_nominal_fail_turn68,
    ),
    15: params_with_updates(
        tnpParNomFit,
        "meanP[-1.6,-5.0,2.0]",
        "sigmaP[2.4,0.8,5.0]",
        "meanF[-2.8,-5.0,1.0]",
        "sigmaF[2.8,0.8,4.8]",
        "acmsP[82.,60.,95.]",
        "betaP[0.035,0.002,0.09]",
        "gammaP[0.04,-0.1,0.7]",
        "acmsF[66.,55.,78.]",
        "betaF[0.035,0.003,0.08]",
        "gammaF[0.02,-0.1,0.4]",
    ),
    24: params_with_updates(
        tnpParNomFit,
        "meanP[-1.0,-5.0,5.0]",
        "sigmaP[3.2,1.0,7.0]",
        "meanF[2.0,-3.0,5.0]",
        "sigmaF[2.5,0.8,4.0]",
        "acmsP[85.,60.,100.]",
        "betaP[0.04,0.002,0.12]",
        "gammaP[0.03,-0.2,0.7]",
        "acmsF[75.,50.,95.]",
        "betaF[0.04,0.002,0.12]",
        "gammaF[0.05,-0.2,0.8]",
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
_nongap_altsig_fail_falling = (
    "acmsF[55.,35.,75.]",
    "betaF[0.02,0.001,0.08]",
    "gammaF[0.03,0.001,0.80]",
)
_nongap_altsig_fail_turn68 = (
    "acmsF[68.,58.,78.]",
    "betaF[0.03,0.001,0.08]",
    "gammaF[0.03,0.001,0.80]",
)
tnpParAltSigFitByBin = {
    # --- bin01 failing 訊號被壓成一根針 (2026-09-13) ---
    # sigmaF / sigmaF_2 / sosF **三個同時停在自己的下界**（0.7 / 0.5 / 0.5），
    # 有效寬度 sqrt(sigma^2+sos^2) 只有 左 0.860 / 右 0.707 GeV。端蓋、et 15-20
    # 的電子做不到這種解析度，這是退化解不是物理。
    # 成因是 failing 側背景主導：nBkgF=12156 是 nSigF=2271 的 5.4 倍，擬合把訊號
    # 縮成窄峰去貼某個凸起，其餘全交給背景。acmsF 還釘在天花板 90（誤差 25.4，
    # 完全未定），alphaF 也停在 1.2。
    # 同一格已收斂的 nominalFit 給 sigmaF=1.59，拿它當錨點把地板抬起來，
    # 並讓 acmsF 有往上走的空間。
    1: params_with_updates(
        tnpParAltSigFit,
        "meanF[-1.7,-5.0,5.0]",
        "sigmaF[1.8,1.0,8.0]",
        "sigmaF_2[1.6,0.8,6.0]",
        "alphaF[2.0,0.8,4.5]",
        "nF[0.5,0.0,5.0]",
        "sosF[1.0,0.8,5.0]",
        "acmsF[75.,45.,115.]",
        "betaF[0.02,0.001,0.10]",
        "gammaF[0.03,0.001,1.0]",
    ),
    0: params_with_updates(
        tnpParAltSigFit,
        "meanP[-2.0,-5.0,5.0]",
        "sigmaP[4.0,1.0,6.0]",
        "sigmaP_2[1.5,0.4,4.0]",
        "alphaP[1.8,0.8,4.0]",
        "nP[0.8,0.0,6.0]",
        "sosP[1.5,0.0,4.0]",
        "meanF[-1.8,-4.0,2.0]",
        "sigmaF[3.2,1.0,5.0]",
        "sigmaF_2[0.7,0.3,2.0]",
        "alphaF[1.4,1.0,3.0]",
        "nF[0.4,0.0,3.0]",
        "sosF[0.5,0.0,2.0]",
        "acmsP[85.,25.,110.]",
        "betaP[0.04,0.001,0.10]",
        "gammaP[0.08,0.001,2.0]",
        *_nongap_altsig_fail_falling,
    ),
    3: params_with_updates(
        tnpParAltSigFit,
        "meanF[-0.5,-4.0,3.0]",
        "sigmaF[4.0,1.0,7.0]",
        "sigmaF_2[1.6,0.4,5.5]",
        "sosF[1.2,0.0,4.5]",
        "alphaF[1.6,0.8,4.0]",
        "nF[0.6,0.0,5.0]",
        "acmsF[55.,30.,75.]",
        "betaF[0.055,0.005,0.12]",
        "gammaF[0.035,0.001,0.60]",
    ),
    8: params_with_updates(
        tnpParAltSigFit,
        "meanP[-2.1,-5.0,5.0]",
        "sigmaP[4.0,1.5,8.0]",
        "sigmaP_2[2.0,0.5,8.0]",
        "alphaP[1.8,0.8,4.0]",
        "nP[1.0,0.0,8.0]",
        "sosP[1.5,0.2,6.0]",
        "meanF[-2.0,-5.0,5.0]",
        "sigmaF[7.0,1.5,12.0]",
        "sigmaF_2[1.0,0.3,8.0]",
        "alphaF[2.0,0.8,4.0]",
        "nF[1.0,0.0,8.0]",
        "sosF[2.5,0.2,10.0]",
        "acmsP[75.,35.,100.]",
        "betaP[0.04,0.002,0.12]",
        "gammaP[0.08,0.002,2.0]",
        "acmsF[75.,35.,100.]",
        "betaF[0.04,0.002,0.12]",
        "gammaF[0.08,0.002,2.0]",
    ),
    6: params_with_updates(
        tnpParAltSigFit,
        "meanP[-1.8,-5.0,3.0]",
        "sigmaP[3.2,0.8,6.5]",
        "sigmaP_2[1.2,0.3,5.0]",
        "sosP[1.2,0.0,5.0]",
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[3.8,1.2,6.5]",
        "sigmaF_2[0.8,0.3,2.5]",
        "alphaF[1.4,1.0,3.0]",
        "nF[0.4,0.0,3.0]",
        "sosF[1.2,0.0,3.0]",
        "acmsP[75.,40.,100.]",
        "betaP[0.035,0.002,0.10]",
        "gammaP[0.06,0.002,1.2]",
        *_nongap_altsig_fail_falling,
    ),
    7: params_with_updates(
        tnpParAltSigFit,
        "meanP[-2.2,-5.0,2.0]",
        "sigmaP[4.5,1.5,9.0]",
        "sigmaP_2[2.0,0.5,8.0]",
        "alphaP[1.8,0.8,4.0]",
        "nP[0.8,0.0,8.0]",
        "sosP[1.5,0.2,6.0]",
        "meanF[-2.0,-5.0,2.0]",
        "sigmaF[6.0,1.5,11.0]",
        "sigmaF_2[1.0,0.3,8.0]",
        "alphaF[1.6,0.8,4.0]",
        "nF[0.8,0.0,8.0]",
        "sosF[2.0,0.2,8.0]",
        "acmsP[75.,35.,100.]",
        "betaP[0.04,0.002,0.12]",
        "gammaP[0.08,0.002,2.0]",
        *_nongap_altsig_fail_falling,
    ),
    9: params_with_updates(
        tnpParAltSigFit,
        "meanF[-2.5,-5.0,1.0]",
        "sigmaF[3.5,1.2,5.5]",
        "sigmaF_2[0.8,0.3,2.0]",
        "alphaF[1.4,1.0,3.0]",
        "nF[0.4,0.0,3.0]",
        "sosF[1.2,0.0,3.0]",
        *_nongap_altsig_fail_turn68,
    ),
    10: params_with_updates(
        tnpParAltSigFit,
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[3.5,1.2,5.5]",
        "sigmaF_2[0.8,0.3,2.0]",
        "alphaF[1.4,1.0,3.0]",
        "nF[0.4,0.0,3.0]",
        "sosF[1.0,0.0,3.0]",
        *_nongap_altsig_fail_turn68,
    ),
    13: params_with_updates(
        tnpParAltSigFit,
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.8,1.2,5.8]",
        "sigmaF_2[0.8,0.3,2.0]",
        "alphaF[1.4,1.0,3.0]",
        "nF[0.4,0.0,3.0]",
        "sosF[1.2,0.0,3.0]",
        *_nongap_altsig_fail_turn68,
    ),
    14: params_with_updates(
        tnpParAltSigFit,
        "meanF[-2.8,-5.0,1.0]",
        "sigmaF[3.5,1.2,5.5]",
        "sigmaF_2[0.8,0.3,2.0]",
        "alphaF[1.4,1.0,3.0]",
        "nF[0.4,0.0,3.0]",
        "sosF[1.2,0.0,3.0]",
        *_nongap_altsig_fail_turn68,
    ),
}
     
tnpParAltBkgFit = [
    "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.5,5.0]",
    "meanF[-0.0,-5.0,5.0]","sigmaF[0.9,0.5,5.0]",
    "alphaP[0.,-5.,5.]",
    "alphaF[0.,-5.,5.]",
    ]
tnpParAltBkgFitByBin = {
    0: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-2.5,-5.0,1.0]",
        "sigmaP[2.0,0.7,4.0]",
        "alphaP[-0.02,-0.12,0.02]",
        "meanF[-3.4,-5.0,0.0]",
        "sigmaF[2.8,0.8,3.8]",
        "alphaF[-0.02,-0.10,0.01]",
    ),
    3: params_with_updates(
        tnpParAltBkgFit,
        "meanF[-1.2,-3.0,1.0]",
        "sigmaF[1.5,0.6,2.8]",
        "alphaF[-0.015,-0.08,0.04]",
    ),
    4: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-0.4,-5.0,5.0]",
        "sigmaP[1.1,0.6,3.0]",
        "alphaP[-0.03,-5.,5.]",
        "meanF[-0.20,-2.0,1.5]",
        "sigmaF[1.20,0.6,5.0]",
        "alphaF[-0.015,-0.08,0.04]",
    ),
    5: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-0.65,-5.0,5.0]",
        "sigmaP[1.5,0.8,4.5]",
        "alphaP[-0.04,-5.,5.]",
        "meanF[-1.1,-5.0,5.0]",
        "sigmaF[1.9,0.8,5.0]",
        "alphaF[-0.03,-5.,5.]",
    ),
    11: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-0.6,-5.0,5.0]",
        "sigmaP[1.6,0.6,4.0]",
        "alphaP[-0.01,-0.08,0.03]",
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.2,1.0,5.5]",
        "alphaF[-0.02,-0.12,0.01]",
    ),
    12: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-0.6,-5.0,5.0]",
        "sigmaP[1.6,0.6,4.0]",
        "alphaP[-0.01,-0.08,0.03]",
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[3.2,1.0,5.5]",
        "alphaF[-0.02,-0.12,0.01]",
    ),
    15: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-2.0,-5.0,1.0]",
        "sigmaP[2.4,0.8,5.0]",
        "alphaP[-0.03,-0.20,0.]",
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[3.0,1.0,6.0]",
        "alphaF[-0.03,-0.20,0.]",
    ),
    31: params_with_updates(
        tnpParAltBkgFit,
        "meanP[-0.8,-5.0,5.0]",
        "sigmaP[1.8,0.8,6.0]",
        "alphaP[-0.1,-5.,5.]",
        "meanF[1.5,-5.0,8.0]",
        "sigmaF[8.0,2.0,18.0]",
        "alphaF[0.1,-5.,5.]",
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
    # bins 24/31 (et 50-100 endcap): high-pT resolution larger than the default
    # sigmaP cap (2.0), so the passing CB core rails at 2.0 and over-peaks the data.
    # Raise the core caps. (Only the passing leg was flagged; leave the failing/bkg
    # at default so the high-mass plateau stays covered.)
    24: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[2.5, 0.8, 4.5]',
        'sigmaP_2[2.0, 0.6, 4.5]',
        'sosP[0.8, 0.0, 3.0]',
    ),
    31: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[2.5, 0.8, 4.5]',
        'sigmaP_2[2.0, 0.6, 4.5]',
        'sosP[0.8, 0.0, 3.0]',
    ),
    # bin02: failing-leg signal core railed right (meanF~+3.8) and bkg exponential
    # turned up at high mass. Same recipe as bin04: pin meanF near Z, widen core,
    # forbid the exponential upturn.
    2: params_with_updates(
        tnpParAltSigBkgFit,
        'meanF[-0.5, -3.0, 1.5]',
        'sigmaF[0.8, 0.2, 2.5]',
        'sigmaF_2[1.0, 0.1, 3.0]',
        'sosF[0.2, 0.0, 1.0]',
        'alphaF_2[-0.04, -0.15, 0.]',
    ),
    4: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[0.5, 0.1, 1.5]',
        'sigmaP_2[0.6, 0.1, 2.0]',
        'sosP[0.15, 0.0, 0.8]',
        'alphaP_2[-0.04, -0.12, 0.]',
        'meanF[-0.8, -3.0, 1.5]',
        'sigmaF[0.8, 0.2, 2.5]',
        'sigmaF_2[0.9, 0.1, 3.0]',
        'sosF[0.2, 0.0, 1.0]',
        'alphaF_2[-0.04, -0.15, 0.]',
    ),
    6: params_with_updates(
        tnpParAltSigBkgFit,
        'meanF[0.0, -3.0, 2.0]',
        'sigmaF[0.8, 0.2, 1.8]',
        'sigmaF_2[0.5, 0.1, 1.5]',
        'sosF[0.2, 0.0, 0.8]',
        'alphaF[2.2, 1.4, 3.5]',
        'nF[0.4, 0.0, 1.2]',
        'alphaF_2[-0.05, -0.2, -0.005]',
    ),
    10: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[0.8, 0.2, 2.5]',
        'sigmaP_2[1.0, 0.1, 3.0]',
        'sosP[0.2, 0.0, 1.0]',
        'alphaP_2[-0.01, -0.08, 0.]',
        'meanF[0.4, -2.0, 2.0]',
        'sigmaF[0.8, 0.2, 2.5]',
        'sigmaF_2[0.8, 0.1, 3.0]',
        'sosF[0.25, 0.0, 1.0]',
        'alphaF_2[-0.01, -0.08, 0.]',
    ),
    20: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[0.7, 0.2, 2.5]',
        'sigmaP_2[1.1, 0.1, 3.0]',
        'sosP[0.2, 0.0, 1.0]',
        'alphaP_2[-0.006, -0.06, 0.]',
        'sigmaF[0.55, 0.15, 1.4]',
        'sigmaF_2[0.75, 0.1, 1.8]',
        'sosF[0.08, 0.0, 0.5]',
        'alphaF_2[-0.008, -0.08, 0.]',
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


# --- bin04 failing background: exponential -> Bernstein (2026-09-06) ---
# The failing peak sat ~0.7-0.8 GeV left of the converged nominalFit solution
# and sigmaF railed at its 2.8 ceiling, with nSigF running 34-45%% above
# nominal -- the signal was broadening to patch a background shape the model
# cannot make. A single exponential has one slope, but this bin's background
# falls slowly below the Z and steeply above it (2025 data: 60->80 GeV drops
# 1.28x, 95->120 GeV drops 2.78x), so the residual keeps the same signature
# whatever the signal does: -10%% at 60-65, +9%% at 70-80, -12%% at 115-120.
# Tightening sigmaF (first attempt) only moved the peak 0.22 GeV right and
# made the residuals worse -- the peak position is a symptom, not the cause.
# nongap_2024 already fixed exactly this on its own bins 3/4; reuse it here.
# alphaF is left in place: no pdf uses it under Bernstein, and it is harmless.
tnpAltBkgModelByBin = {
    4: {'fail': 'bernstein2'},
}

# --- 70-75 GeV shoulder：模板的低質量尾巴太小 (2026-09-07) ---
# 症狀：三個用「MC 模板 ⊗ Gaussian」的擬合在**同一質量區同號**失敗，而同格用解析
# DSCB 的 altSigFit 明顯較好。以 bin08 failing 為例：
#   nominalFit   60-65 -31%  70-75 +27%   3 個 slice 超過 5 sigma
#   altBkgFit    60-65 -25%  70-75 +34%   6 個
#   altSigBkgFit 60-65 -26%  70-75 +20%   3 個
#   altSigFit    60-65 -0.0% 70-75 +3.5%  0 個   <-- 不吃模板
# 三個模板型擬合各自扭曲別的東西去補（altBkg 的 sigmaF 撞死上界 5.0、meanF 拉到
# -3.75；nominal 的 acmsF 撞 70、betaF 撞 0.06；altSigBkg 的 alphaF 撞 1.4 下界），
# 三個不同參數撞界指向同一件事：函數族做不出那個形狀，放寬邊界只會撞下一個。
#
# 驗證（bin08 altBkgFit failing，2026-09-07）：
#   60-65 -24.8% -> -1.9% ; 70-75 +34.2% -> -1.6% ; 80-85 -18.1% -> -0.6%
#   6 個 slice -> 0 ; sigmaF 5.000(撞界) -> 4.300(自由) ; 效率 0.7852 -> 0.7897
#   meanGF 74.40+/-0.25、sigmaGF 5.42+/-0.23、sigFracF 0.678+/-0.015
#   全部落在內部極小值，sigFracF 誤差只有 2% —— 第二個成分是被資料決定的，不是硬湊。
#
# ⚠️ addGaus 不能全開：全開會讓 699 個 fit 變好、1766 個變壞（見 tnpEGM_fitter.py
#    的 _addgaus_for_bin 註解）。只在 failing 真的是「窄峰 + shoulder」時才有用。
#
# passing 側（bin08/bin15 的 altBkgFit）用同一機制的對稱版本：低質量尾來自同一份
# 模板，兩條腿都會受影響。bin08 passing 實測 60-65 -50%、70-75 +65%、7 個 slice。
# 由設定宣告 meanGP/sigmaGP 才啟用，未宣告的組態逐位元不變（已驗證 b12）。
_gaus_f = ("meanGF[70.0,55.0,88.0]", "sigmaGF[8.0,2.0,20.0]")
_gaus_p = ("meanGP[70.0,55.0,88.0]", "sigmaGP[8.0,2.0,20.0]")

# ⚠️ sigmaGF 的上界 20 太鬆，會讓第二個成分從「shoulder」退化成「寬平台」，
#    把背景整段吃進訊號。bin11/bin12 的 altBkgFit 中招（2026-09-07）：
#      sigmaGF 12.36 / 12.68 GeV、sigFracF 0.33、meanGF 81.8
#      nSigF 27879+/-484 -> 46534+/-1728，nBkgF 41912+/-499 -> 23257+/-1722
#      （誤差脹 3.5 倍且兩者完全反相關 = 訊號/背景已經分不開）
#      效率 0.9073 -> 0.8830，離其他三種擬合更遠，altBkg 系統誤差反而翻倍
#    殘差是乾淨的（0 slice），所以殘差本身抓不到這個病 —— 判準是 sigmaGF 的大小
#    與 nSigF/nBkgF 的誤差有沒有脹起來。健康的 shoulder：bin08 sigmaGF 5.42、
#    bin15 6.47，效率只動 0.5%。因此 b11/b12 改用收窄版本。
_gaus_f_narrow = ("meanGF[74.0,60.0,88.0]", "sigmaGF[5.0,2.0,9.0]")

addGausBins = {
    'nominalFit':   (8, 15),
    # bin12 已撤回（原本是 (8, 11, 12, 15)）：加了 shoulder 之後 sigFracF 撞到
    # 1.0 上界 —— 第二個高斯把模板訊號整個取代掉，sigmaGF 3.88+/-4.31 完全不受
    # 約束、sigmaF 5.25 貼著 5.5 天花板，failing 殘差反而從乾淨變成 6 個 slice。
    # bin11 收窄後 OK（效率 0.9065 對未加時的 0.9073），bin12 就是不適用。
    'altBkgFit':    (8, 11, 15),
    'altSigBkgFit': (8, 15),
    'altSigFit':    (15,),
}

tnpParNomFit_addGaus = params_with_updates(tnpParNomFit, *_gaus_f)
# bin15 改用收窄版：寬版（sigmaGF 上界 20）會讓 sigGaussFail 跑到 nan，
# 連帶 bkgFail 的歸一化積分變成 0，整個 fit 直接掛掉（2026-09-07 實測）。
tnpParNomFit_addGausByBin = {
    b: params_with_updates(tnpParNomFitByBin.get(b, tnpParNomFit),
                           *(_gaus_f_narrow if b == 15 else _gaus_f))
    for b in (8, 15)
}

# altBkg：bin08 與 bin15 兩側都加 shoulder
tnpParAltBkgFit_addGaus = params_with_updates(tnpParAltBkgFit, *_gaus_f)
tnpParAltBkgFit_addGausByBin = {}
for _b in (8, 11, 15):
    _base = _gaus_f_narrow if _b == 11 else _gaus_f
    _extra = _base + (_gaus_p if _b in (8, 15) else ())
    tnpParAltBkgFit_addGausByBin[_b] = params_with_updates(
        tnpParAltBkgFitByBin.get(_b, tnpParAltBkgFit), *_extra)

tnpParAltSigBkgFit_addGaus = params_with_updates(tnpParAltSigBkgFit, *_gaus_f)
tnpParAltSigBkgFit_addGausByBin = {
    b: params_with_updates(tnpParAltSigBkgFitByBin.get(b, tnpParAltSigBkgFit), *_gaus_f)
    for b in (8, 15)
}

tnpParAltSigFit_addGaus = params_with_updates(tnpParAltSigFit, *_gaus_f)
tnpParAltSigFit_addGausByBin = {
    15: params_with_updates(tnpParAltSigFitByBin.get(15, tnpParAltSigFit), *_gaus_f),
}
