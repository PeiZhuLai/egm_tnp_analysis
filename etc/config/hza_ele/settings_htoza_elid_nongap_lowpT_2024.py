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
    'hza_elid_nongap_lowpT_2024_sf': (
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
    # bin00 is the mirror of bin05 and showed the same railed, over-wide failing-leg Z
    # bump (sigmaF at its 4.5 upper bound). Both bins are averaged into the same |eta|
    # point, so they get the same capped smearing.
    0: params_with_updates(
        tnpParNomFit,
        "meanP[-2.0,-5.0,5.0]",
        "sigmaP[1.8,0.5,3.0]",
        "meanF[-2.2,-5.0,1.0]",
        "sigmaF[2.0,0.8,3.0]",
        *_lowpt_nominal_tail_common,
    ),
    # bin05: sigmaF railed at its 4.8 upper bound, giving a far too wide failing-leg Z
    # bump that overshoots the data between 78 and 95 GeV. Cap the extra smearing at a
    # physical level (the passing leg needs only ~1.8 GeV) so the bump stays narrow.
    5: params_with_updates(
        tnpParNomFit,
        "meanP[-2.0,-5.0,5.0]",
        "sigmaP[1.9,0.5,3.0]",
        "meanF[-2.0,-5.0,1.0]",
        "sigmaF[2.0,0.8,3.0]",
        *_lowpt_nominal_tail_common,
    ),
    # bin02: default fit fell into a bad min (meanF~+3.2, sigmaF railed at 5 -> the
    # failing-leg Z bump over-wide and right-shifted). Use the same low-pT recipe as
    # bins 0/5: meanF pulled negative, sigmaF capped, low acmsF turn-on.
    2: params_with_updates(
        tnpParNomFit,
        "meanP[-1.5,-5.0,5.0]",
        "sigmaP[1.6,0.5,3.0]",
        "meanF[-1.0,-4.0,1.5]",
        "sigmaF[2.6,1.6,4.0]",
        *_lowpt_nominal_tail_common,
    ),
    # bin03 is the mirror of bin02 and showed the same bad minimum with the default
    # parameters (meanF railed at +5.0, sigmaF railed at 5.0 -> over-wide, right-shifted
    # failing-leg Z bump). Use the bin02 recipe, with a slightly lower sigmaF floor so
    # the fit can reach the narrow width preferred by the data.
    3: params_with_updates(
        tnpParNomFit,
        "meanP[-1.5,-5.0,5.0]",
        "sigmaP[1.6,0.5,3.0]",
        "meanF[-1.0,-4.0,1.5]",
        "sigmaF[2.0,0.8,3.5]",
        *_lowpt_nominal_tail_common,
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
        # --- failing 側 2026-09-13 ---
        # 先看 EDM：4.12e+09。這個擬合根本沒收斂，那些 1e-4 的「誤差」沒有意義。
        # 症狀來自範圍把解關在外面：acmsF 釘死在天花板 60（誤差 0.0009），而同一格的
        # nominalFit 的 acmsF 卻撞在它自己的地板 30 —— 兩個擬合對背景 turn-on 的位置
        # 完全不同意，而且兩邊都撞界。alphaF 2.917 也貼著天花板 3.0。
        # 有效寬度 sqrt(sigma^2+sos^2)：左 2.611、右 sqrt(1.156^2+0.380^2)=1.217。
        # 高質量側那個 1.217 被 sigmaF_2 的天花板 1.5 卡住，所以峰的右翼特別尖。
        # 修法：acmsF 兩邊都放開讓它找內部解、alphaF 與 sigmaF_2 的天花板抬高、
        # sosF 的上界從 1.0 放到 3.0（它是加在正交方向的解析度底限，不是開關）。
        "meanF[-0.8,-3.0,1.0]",
        "sigmaF[3.5,1.0,6.0]",
        "sigmaF_2[1.6,0.5,5.0]",
        "alphaF[2.0,1.0,4.5]",
        "nF[0.4,0.0,3.0]",
        "sosF[0.8,0.0,3.0]",
        "acmsF[60.,30.,95.]",
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
_lowpt_altsigbkg_endcap_fail = (
    # Endcap failing leg: without these the DSCB tail exponent nF runs into 0, so the
    # power-law tails absorb the falling continuum and the efficiency comes out far
    # below the nominal fit. Pin the mean near the Z peak, keep the core narrow and the
    # tail exponent away from 0, and force the exponential background to fall.
    'meanF[-1.0, -4.0, 1.0]',
    'sigmaF[1.5, 0.5, 3.0]',
    'sigmaF_2[1.0, 0.3, 3.0]',
    'sosF[0.2, 0.0, 1.0]',
    'alphaF[2.5, 1.4, 3.5]',
    'nF[1.5, 0.5, 5.0]',
    'alphaF_2[-0.03, -1, 0.]',
)
tnpParAltSigBkgFitByBin = {
    # bin00 is the mirror of bin05 and had the same failing-leg pathology
    # (nF railed at 0, nSigF ~ 8e4, eff = 0.4995 against a nominal 0.6732).
    0: params_with_updates(
        tnpParAltSigBkgFit,
        *_lowpt_altsigbkg_endcap_fail,
    ),
    # bin05: the failing leg first railed alphaF_2 at its +0.05 upper bound, i.e. a
    # *rising* exponential background, which let the DSCB absorb the whole falling
    # continuum (nSigF ~ 6.4e5, eff = 0.114, fit status 3).
    5: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[0.35, 0.1, 1.5]',
        'sigmaP_2[0.25, 0.1, 1.5]',
        'sosP[0.05, 0.0, 1.0]',
        'alphaP[2.0, 0.8, 4.0]',
        'nP[0.3, 0.0, 2.0]',
        'alphaP_2[-0.03, -1, 0.05]',
        *_lowpt_altsigbkg_endcap_fail,
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
