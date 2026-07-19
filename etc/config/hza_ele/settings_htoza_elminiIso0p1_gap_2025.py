# -*- coding: utf-8 -*-
import os, sys
if '_mod_path' not in globals() or not _mod_path:
    _mod_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    if _mod_path not in sys.path:
        sys.path.insert(0, _mod_path)
from etc.config.fit_param_utils import params_for_bins, params_with_updates

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
    '&& ( (passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg2 == 1 && el_hltE23E12leg2_dR < 0.3 && pair_lead_el_sc_et > 15 ) || (passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg1L1match == 1 && el_hltE23E12leg1_dR < 0.3 && pair_lead_el_sc_et > 25 ) || (passHltEle30WPTightGsf == 1 && el_hltE30single_dR < 0.3 && pair_lead_el_sc_et > 35))'
    ') || ('
    + baseline_cut +
    '(el_sc_et < 10) && ('
    '    (abs(el_sc_eta) < 0.8   && el_hzzMVA > 0.9267)'
    ' || (abs(el_sc_eta) >= 0.8  && abs(el_sc_eta) < 1.479 && el_hzzMVA > 0.9138)'
    ' || (abs(el_sc_eta) >= 1.479 && el_hzzMVA > 0.9683)'
    ' )'
    '&& ( (passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg2 == 1 && el_hltE23E12leg2_dR < 0.3 && pair_lead_el_sc_et > 15 ) || (passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg1L1match == 1 && el_hltE23E12leg1_dR < 0.3 && pair_lead_el_sc_et > 25 ) || (passHltEle30WPTightGsf == 1 && el_hltE30single_dR < 0.3 && pair_lead_el_sc_et > 35))'
    '))'
)

# flag to be Tested
flags = {
    'hza_elminiIso0p1_gap_2025_sf': '(el_miniPFRelIso_all < 0.1)',
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
   { 'var' : 'el_sc_eta' , 'type': 'float', 'bins': [-1.566,-1.4442, 0.0, 1.4442, 1.566] },
   { 'var' : 'el_et' , 'type': 'float', 'bins': [7,35,500] },
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

# bin01/02 (et 7-35, barrel, high-stat passing Z, eff<1): the PASSING fit stalls
# (edm~3e4, status -1, signal params frozen) because the pass-leg bkg CMSShape
# turn-on acmsP rails at upper bound 90 (the Z peak). The FAILING legs already fit
# well, so only the pass leg is pinned: fix the pass bkg turn-on shape
# (acmsP/betaP/peakP) to constants and let meanP/sigmaP float -> converges.
# Failing params untouched. (bin01 eta -1.44..0, bin02 eta 0..1.44.)
_lowet_pin_bkg = (
    "meanP[0.0,-3.0,3.0]",
    "sigmaP[1.5,0.5,4.0]",
    "acmsP[60.0]",
    "betaP[0.05]",
    "gammaP[0.05,0.0,0.5]",
    "peakP[87.0]",
)
tnpParNomFitByBin = {
    1: params_with_updates(tnpParNomFit, *_lowet_pin_bkg),
    2: params_with_updates(tnpParNomFit, *_lowet_pin_bkg),
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
tnpParAltSigFitByBin = params_for_bins(
    tnpParAltSigFit,
    (1, 2),
    "sigmaP[2.5,0.7,7.0]",
    "sigmaP_2[1.2,0.5,5.0]",
    "sosP[0.8,0.2,4.0]",
    "sigmaF[2.8,0.8,7.0]",
    "sigmaF_2[1.2,0.5,5.0]",
    "sosF[0.8,0.2,4.0]",
    "acmsP[88.,70.,95.]",
    "betaP[0.02,0.001,0.06]",
    "gammaP[0.02,0.001,0.5]",
    "acmsF[88.,70.,95.]",
    "betaF[0.02,0.001,0.06]",
    "gammaF[0.02,0.001,0.5]",
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


# --- altSig --addGaus 變體 (2026-07-14) ---
# altSig 解析 DSCB 平滑、undershoots failing 的真實 78 shoulder(FSR/DY prompt ee 失隔離)。
# 加第二 Gaussian(sigGaussFail, meanGF~77)補上; pdfFail=sigFracF*DSCB+(1-sigFracF)*Gauss,
# 兩者都算 nSigF(signal),物理上正確(那批確是 Z->ee 電子失隔離)。保留各 bin 現有調參。
_gaus_pars = ["meanGF[77.0,73.0,81.0]", "sigmaGF[4.0,2.0,8.0]"]
tnpParAltSigFit_addGaus = tnpParAltSigFit + _gaus_pars
tnpParAltSigFit_addGausByBin = {k: (list(v) + _gaus_pars) for k, v in tnpParAltSigFitByBin.items()}

# --- gap crack (bin0 η-1.57~-1.44, bin3 η+1.44~+1.57) altSig 專屬 (2026-07-16) ---
# crack 低統計、failing 譜寬又亂(主峰~85 broad + 低質量 shoulder~74)。base meanF 撞界 -5
# (bin0 eff 離群高 0.9515)、sosF 撞界 0.5(bin3 DSCB 過寬 undershoot 主峰)。放寬 meanF/sosF
# 下界並讓 addGaus 第二 Gaussian 往更低質量 catch shoulder(收窄 altSig systematic band)。
_crack_altsig = params_with_updates(
    tnpParAltSigFit,
    "meanF[-3.0,-8.0,1.0]",
    "sigmaF[2.5,1.0,6.0]",
    "sigmaF_2[3.5,1.0,8.0]",
    "sosF[0.6,0.05,3.0]",
) + ["meanGF[73.0,66.0,80.0]", "sigmaGF[5.0,2.5,11.0]"]
for _cb in (0, 3):
    tnpParAltSigFit_addGausByBin[_cb] = _crack_altsig



# --- altSigBkg --addGaus 變體 (2026-07-15) ---
# altSigBkg 的 signal 也是解析 DSCB(RooCBExGaussShapeTNP) → 同 altSig,加第二 Gaussian
# (sigGaussFail, meanGF~77)補 failing 的真實 FSR/DY shoulder。保留各 bin 現有調參。
tnpParAltSigBkgFit_addGaus = tnpParAltSigBkgFit + _gaus_pars
tnpParAltSigBkgFit_addGausByBin = {k: (list(v) + _gaus_pars) for k, v in tnpParAltSigBkgFitByBin.items()}


# --- nominal + altBkg --addGaus 全套解析變體 (2026-07-15) ---
# fitUtils isaddGaus: signal=通用 gen-level lineshape ⊗ Gaussian(平滑,無 template shoulder)
# + sigGaussFail 補真實 shoulder。nominal=CMSShape bkg(pin acmsP 防 rail); altBkg=Exp bkg。
# bimodal(中央 et20-35: 18-21): 窄 sigmaF + pin failing bkg + shoulder Gaussian。
# high-ET 中央(34-37,42-45): 窄 sigmaF,Gaussian 自動關。
_gs = ["meanGF[77.0,73.0,81.0]", "sigmaGF[3.5,2.0,6.0]"]
_pass_nom = ("meanP[-0.0,-3.0,3.0]", "sigmaP[1.5,0.5,4.0]", "acmsP[60.0]", "betaP[0.05]", "gammaP[0.05,0.0,0.5]")
_pass_ab  = ("meanP[-0.0,-3.0,3.0]", "sigmaP[1.5,0.5,4.0]")
tnpParNomFit_addGaus = params_with_updates(tnpParNomFit, *_pass_nom) + _gaus_pars
tnpParNomFit_addGausByBin = {}
_nom_bimodal = params_with_updates(tnpParNomFit, "meanF[0.0,-3.0,3.0]","sigmaF[1.0,0.5,2.2]","acmsF[58.0]","betaF[0.10]","gammaF[0.0,-0.03,0.05]","acmsP[60.0]","betaP[0.05]","gammaP[0.05,0.0,0.5]") + _gs
_nom_highet  = params_with_updates(tnpParNomFit, "meanF[0.0,-2.5,2.5]","sigmaF[1.0,0.5,2.5]","acmsP[60.0]","betaP[0.05]","gammaP[0.05,0.0,0.5]") + _gaus_pars
for _b in (18,19,20,21): tnpParNomFit_addGausByBin[_b] = _nom_bimodal
for _b in (16,17,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47): tnpParNomFit_addGausByBin[_b] = _nom_highet
tnpParAltBkgFit_addGaus = params_with_updates(tnpParAltBkgFit, *_pass_ab) + _gaus_pars
tnpParAltBkgFit_addGausByBin = {}
_ab_bimodal = params_with_updates(tnpParAltBkgFit, "meanF[0.0,-3.0,3.0]","sigmaF[1.0,0.5,2.2]","alphaF[-0.02,-0.1,0.02]") + _gs
_ab_highet  = params_with_updates(tnpParAltBkgFit, "meanF[0.0,-2.5,2.5]","sigmaF[1.0,0.5,2.5]","alphaF[-0.02,-0.1,0.005]") + _gaus_pars
for _b in (18,19,20,21): tnpParAltBkgFit_addGausByBin[_b] = _ab_bimodal
for _b in (16,17,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47): tnpParAltBkgFit_addGausByBin[_b] = _ab_highet
