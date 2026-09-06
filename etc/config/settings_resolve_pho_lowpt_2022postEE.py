# -*- coding: utf-8 -*-
# 初始化 _mod_path 並更新 sys.path，供 tnpEGM_fitter 與 etc.* 匯入使用
import os, sys
from etc.config.fit_param_utils import params_with_updates
# 以 globals() 安全檢查，避免在 Py2 觸發 NameError
if '_mod_path' not in globals() or not _mod_path:
    _mod_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    if _mod_path not in sys.path:
        sys.path.insert(0, _mod_path)

#############################################################
########## General settings
#############################################################
# EA reference: https://indico.cern.ch/event/1204277/contributions/5064356/attachments/2538496/4369369/CutBasedPhotonID_20221031.pdf
# flag to be Tested
flags = {
    # Run3 custom ID aligned to ZaTaggerRun3.select_photons
    'hza_resolve_phid_lowpt_2022postEE_sf': (
        # pT + acceptance
        '(ph_et > 10) && ((abs(ph_sc_eta) < 1.4442) || (abs(ph_sc_eta) > 1.566 && abs(ph_sc_eta) < 2.5))'
        ' && ('
        # ================= EB block =================
        # ================= H/E =================
        '  (abs(ph_sc_eta) < 1.4442'
        '   && (('
        '         (abs(ph_sc_eta) > 0.0 && abs(ph_sc_eta) < 1.0)'
        '         && (ph_hoe - event_rho*0.00198598 - (event_rho*event_rho)*(-0.0000115014)'
        '             < 0.0417588)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 1.0 && abs(ph_sc_eta) < 1.4442)'
        '         && (ph_hoe - event_rho*0.208571 - (event_rho*event_rho)*(-0.0000115014)'
        '             < 0.0417588)'
        '       ))'
        # ================= Ch ISO =================
        '   && (ph_chIso < 0.316306)'
        # ================= H ISO =================
        '   && (ph_neuIso < (0.39057 + 0.0100547*ph_et + 0.0000578332*ph_et*ph_et))'
        '  )'
        '  ||'
        # ================= EE block =================
        # ================= H/E =================
        '  (abs(ph_sc_eta) > 1.566 && abs(ph_sc_eta) < 2.5'
        '   && (('
        '         (abs(ph_sc_eta) > 1.566 && abs(ph_sc_eta) < 2.0)'
        '         && (ph_hoe - event_rho*0.00302416 - (event_rho*event_rho)*(-0.0000151973)'
        '             < 0.00254267)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.0 && abs(ph_sc_eta) < 2.2)'
        '         && (ph_hoe - event_rho*0.306529 - (event_rho*event_rho)*(-0.0000149651)'
        '             < 0.00254267)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.2 && abs(ph_sc_eta) < 2.3)'
        '         && (ph_hoe - event_rho*0.322673 - (event_rho*event_rho)*(-0.0000147232)'
        '             < 0.00254267)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.3 && abs(ph_sc_eta) < 2.4)'
        '         && (ph_hoe - event_rho*0.315793 - (event_rho*event_rho)*(-0.0000213958)'
        '             < 0.00254267)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.4 && abs(ph_sc_eta) < 2.5)'
        '         && (ph_hoe - event_rho*0.36531 - (event_rho*event_rho)*(-0.0000280795)'
        '             < 0.00254267)'
        '       ))'
        # ================= Ch ISO =================
        '   && (ph_chIso < 0.292664)'
        # ================= H ISO =================
        '   && (ph_neuIso < (0.0292617 + 0.0116989*ph_et + 0.0000747603*ph_et*ph_et))'
        '  )'
        ' )'
        # electron veto
        # ' && (ph_passElectronVeto == 1)'
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
tnpTreeDir = 'tnpPhoIDs'

samplesDef = {
        'data'  : tnpSamples.Run3_2022postEE['Data_2022postEE'].clone(),
        'mcNom' : tnpSamples.Run3_2022postEE['DY_MC_LO_2022postEE'].clone(),
        'tagSel': tnpSamples.Run3_2022postEE['DY_MC_LO_2022postEE'].clone(),
        'mcAlt': tnpSamples.Run3_2022postEE['DY_MC_NLO_2022postEE'].clone(),
    }


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
    samplesDef['tagSel'].rename('mcAltSel_DY_MC_LO_2022postEE')
    samplesDef['tagSel'].set_cut('tag_Ele_pt > 50 && ph_mva122XV1 > 0.99 && ph_r9 > 0.99')

## set MC weight, simple way (use tree weight) 
# weightName = 'totWeight'
# if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_weight(weightName)
# if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_weight(weightName)
# if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_weight(weightName)

## set MC weight, can use several pileup rw for different data taking 
mcNom_puFile = '/eos/cms/store/group/phys_egamma/ec/nkasarag/EGM_comm/TnP_samples/2022/sim/DY_LO/puTree/mcRun3_130X_2022_realistic_postEE_LO_pho.pu.puTree.root'
mcAlt_puFile = '/eos/cms/store/group/phys_egamma/ec/nkasarag/EGM_comm/TnP_samples/2022/sim/DY_NLO/puTree/mcRun3_130X_2022_realistic_postEE_pho.pu.puTree.root'
weightName = 'weights_data_Run2022EFG.totWeight'
if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_weight(weightName)
if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_weight(weightName)
if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_weight(weightName)
if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_puTree(mcNom_puFile)
if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_puTree(mcAlt_puFile)
if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_puTree(mcNom_puFile)

#############################################################
########## bining definition  [can be nD bining]
#############################################################
biningDef = [
   { 'var' : 'ph_sc_eta' , 'type': 'float', 'bins': [-2.5,-2.0,-1.566,-1.4442, 0.0, 1.4442, 1.566, 2.0, 2.5] },
   { 'var' : 'ph_et' , 'type': 'float', 'bins': [10,20] }
]

#############################################################
########## Cuts definition for all samples
#############################################################
### cut
cutBase   = 'tag_Ele_pt > 35 && abs(tag_sc_eta) < 2.17'

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
    "meanF[-0.0,-3.0,5.0]","sigmaF[2.0,0.5,5.0]",
    "acmsP[60.,50.,80.]","betaP[0.05,0.01,0.08]","gammaP[0.1, -2, 2]","peakP[87.0,82.0,90.0]",
    "acmsF[60.,35.,80.]","betaF[0.05,0.01,0.08]","gammaF[0.1, 0.02, 2]","peakF[87.0,82.0,90.0]",
    ]

# # 4
# tnpParNomFit = [
#     "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.5,5.0]",
#     "meanF[0.2,0.1,5.0]","sigmaF[1.5]",
#     "acmsP[60.,50.,80.]","betaP[0.05,0.01,0.08]","gammaP[0.1, -2, 2]","peakP[87.0,82.0,90.0]",
#     "acmsF[60.,40.,80.]","betaF[0.05,0.01,0.08]","gammaF[0.01, -2, 0.1]","peakF[87.0,82.0,90.0]",
#     ]
# print("DEBUG tnpParNomFit =", tnpParNomFit)

tnpParAltSigFit = [
    "meanP[-0.0,-5.0,5.0]",
    "sigmaP[4.0, 3.0, 8.0]",
    "sigmaP_2[0.5, 0.5, 6.0]",
    "alphaP[2.0,1.2,3.5]" ,
    "nP[3,-5,5]",
    "sosP[1,0.5,5.0]",
    "meanF[-0.0,-5.0,5.0]",
    "sigmaF[4.5, 3.0, 8.0]",
    "sigmaF_2[0.5, 0.5, 6.0]",
    "alphaF[2.0,1.2,3.5]",
    "nF[3,0,5]",
    "sosF[1,0.5,5.0]",
    "acmsP[60.,50.,75.]","betaP[0.04,0.01,0.06]","gammaP[0.1, 0.005, 1]","peakP[89.0,82.0,90.0]",
    "acmsF[60.,40.,75.]","betaF[0.04,0.01,0.06]","gammaF[0.1, 0.01, 1]","peakF[89.0,82.0,90.0]",
    ]
     
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

# ## 00
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
#   'alphaF_2[-0.04, -1, -0.03]',
# ]

# ---------------------------------------------------------------------------
# 2026-08-29  nominalFit bin04 / bin06 failing（ET 10-20，背景約 89%）
#
# 兩格都是 covQual=0（Hessian 奇異）且四個參數同時撞界:
#   b04  acmsF=35 撞**下**界   betaF=0.01 撞下界  gammaF=0.02 撞下界  sigmaF=5 撞**上**界
#   b06  acmsF=80 撞**上**界   betaF=0.01 撞下界  gammaF=0.02 撞下界  sigmaF=5 撞上界
# 共通點是 sigmaF 撐到上界 5 —— 訊號被拉到最寬去描述低 pT endcap 光子的爛解析度,
# 背景的三個形狀參數只好往界上跑去補償。acmsF 一個往下一個往上,代表它是被迫的、
# 不是資料要的。四個方向都被關住時 Hessian 必然奇異。
# 只放寬撞界那一側:sigmaF 上界 5->10、betaF 下界 0.01->0.002、gammaF 下界 0.02->-0.5、
# acmsF 兩側都開(因為兩格撞的方向相反)。
tnpParNomFitByBin = dict(globals().get('tnpParNomFitByBin', {}))
for _b in (4, 6):
    tnpParNomFitByBin[_b] = params_with_updates(
        tnpParNomFitByBin.get(_b, tnpParNomFit),
        "sigmaF[3.0,0.5,10.0]",
        "acmsF[60.,25.,95.]",
        "betaF[0.03,0.002,0.30]",
        "gammaF[0.05,-0.5,2.0]",
    )
