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
    'hza_elid_nongap_2025_sf': (
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
        # 2026-08-23: betaF/gammaF/sigmaF 三個同時撞界(0.08↑ / 0.001↓ / 6.5↑),edm 1.31e+10。
        # gammaF 撞下界代表 CMSShape 的指數項想要更平甚至上翹;fail 資料平滑下降
        # (15850->2850)看不到 Z bump,背景 72.8%。只放寬撞界那側;betaF/gammaF 的覆寫寫在
        # *_nongap_altsig_fail_falling 之後(params_with_updates 後者覆蓋前者),
        # 不動那個被多個 bin 共用的 tuple。
        "sigmaF[4.5,1.2,11.0]",
        "sigmaF_2[0.8,0.3,2.5]",
        "alphaF[1.4,1.0,3.0]",
        "nF[0.8,0.5,3.0]",
        "sosF[1.2,0.0,3.0]",
        "acmsP[75.,40.,100.]",
        "betaP[0.035,0.002,0.10]",
        "gammaP[0.06,0.002,1.2]",
        *_nongap_altsig_fail_falling,
        "betaF[0.05,0.001,0.30]",
        "gammaF[0.01,-0.05,0.80]",
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
    # 2026-08-23 bin30。第一輪我把 sigmaF 上界從 5.0 放寬到 10.0(它在 4.812,96% 位置),
    # edm 確實從 1.03e+06 掉到 2.89e-06,但背景佔比同時從 47.4% 崩到 6.7% —— 訊號變寬之後
    # 直接吃掉了高質量端 ~2350/5GeV 的平台。**那個方向是錯的**:這個 bin 的病不是訊號被
    # 上界卡住,而是訊號本來就想變寬去吃背景,所以該收不該放。
    # 第二輪:把 sigmaF 收在 et 50-100、|eta| 1.57-2.00 的合理解析度範圍內(~1.5-3 GeV),
    # 迫使高質量端的平台由背景描述。
    # (alphaF=+0.029「上升」的指數是合理的:et 50-100 的 failing probe 本來就把低質量端
    #  切掉,資料 60:442 -> 90:4555 -> 平台 ~2350,背景確實隨質量上升,不強迫它遞減。)
    30: params_with_updates(
        tnpParAltBkgFit,
        "meanF[-0.7,-5.0,5.0]",
        "sigmaF[2.0,1.0,3.5]",
    ),
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
        # 2026-09-06 failing peak sat 0.77 GeV left of where it belongs.
        # sigmaF railed at its 2.8 ceiling and meanF never left its -1.3
        # start, ending at -1.3067 against nominalFit's -0.5351. The signal
        # was broadening to eat background: nSigF=56832 vs nominal 39267
        # (+45%). Same failure bin30 documents above -- the cure is to TIGHTEN
        # sigmaF, not release it. Anchor both at the converged nominal
        # solution (sigmaF=1.136 +/- 0.172, meanF=-0.535).
        "meanF[-0.55,-2.0,1.5]",
        "sigmaF[1.14,0.6,5.0]",
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
    # 2026-08-23 bin30: edm 1.34e+07。sigmaF=0.344 GeV 對 et 50-100、|eta| 1.57-2.00 的
    # 電子是不可能的解析度,那是尖峰;搭配 nF=0.21(CB 冪次尾巴在 n->0 時趨近水平)讓訊號
    # 吃掉高質量端 ~2350/5GeV 的平台,nSigF 因此被灌到 20735(fail 總數 28624 的 72%),
    # 但資料的 Z 峰超出量只有 ~5000-8000。抬 sigmaF 與 nF 的地板到物理值。
    30: params_with_updates(
        tnpParAltSigBkgFit,
        'meanF[-0.2, -4.0, 3.0]',
        'sigmaF[1.8, 1.0, 5.0]',
        'sigmaF_2[1.5, 0.5, 5.0]',
        'sosF[0.4, 0.0, 1.0]',
        'nF[0.8, 0.5, 3.0]',
    ),
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


# --- failing 背景 turn-on 調整 (2026-08-20) ---
# 與 elid_gap_2024 altSigFit bin02 同型的病徵：failing 側的 CMSShape turn-on 撞界，
# 背景無法覆蓋 failing spectrum，訊號的寬度參數因此被擠到界上去補背景該做的事。
# 那個 bin 修好後 acmsF 90->45.5、sosF 由下界 0.5 脫離到 1.29、背景佔比 22%->78%，
# 證實因果是「背景缺位擠壓訊號」而非訊號模型不足。這裡只放寬撞界的那一側。
# bin01: 同上，另有 sigmaF_2 也撞下界
tnpParAltSigFitByBin = dict(globals().get('tnpParAltSigFitByBin', {}))
tnpParAltSigFitByBin[1] = params_with_updates(
    tnpParAltSigFitByBin.get(1, tnpParAltSigFit),
    "acmsF[65.,45.,80.]",
    "betaF[0.04,0.005,0.25]",
)


# --- 背景無約束釘住 (2026-08-21) ---
# 這些 bin 的 nBkg 被壓到接近或等於框架下界(0.5 個事件)，背景佔比 <1.4%，
# 於是背景形狀參數連半個事件都約束不了 -> Hessian 在那些方向奇異 ->
# 誤差全為 0、covQual=0。參數本身是擬合值而非初始值，代表中央值可信、壞的只有誤差。
# 已在 elid_gap_2024/2025 bin6/bin5 與 sielleg30trigger_nongap_2025 bin2/10/29 驗證:
# 釘住背景形狀後 covQual 0->3，效率變動僅 1e-5 量級。
tnpParAltSigFitByBin = dict(globals().get('tnpParAltSigFitByBin', {}))
tnpParAltSigFitByBin[17] = params_with_updates(
    tnpParAltSigFitByBin.get(17, tnpParAltSigFit),
    "acmsP[80.0]",
    "betaP[0.06]",
    "gammaP[0.05]",
    "peakP[89.0]",
)


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
