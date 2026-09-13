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
    'hza_dielleg23trigger_nongap_2025_sf': '(passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg1L1match == 1 && el_hltE23E12leg1_dR < 0.3)',
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
# 2026-08-29  使用者標記的兩個 bin
#
# b33 (altSigBkgFit, eta -2.00..-1.57, ET 50-100, failing)
#   sigmaF=0.161、sigmaF_2 撞下界 0.1、sosF 撞下界 0、alphaF 撞下界 1.4,edm 1.2e+02。
#   訊號核心塌成 0.16 GeV —— 對 endcap 不可能。病根是 tnpParAltSigBkgFit 的種子
#   (sigma 0.5、範圍下界 0.1)離真實解析度太遠,似然面在那附近平坦,MIGRAD 走不出去。
#   給實體起點並把上界從 2.0/3.0 開到 6.0。
tnpParAltSigBkgFitByBin = dict(globals().get('tnpParAltSigBkgFitByBin', {}))
tnpParAltSigBkgFitByBin[33] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(33, tnpParAltSigBkgFit),
    "meanF[-1.5,-6.0,3.0]",
    "sigmaF[2.0,0.8,6.0]",
    "sigmaF_2[2.0,0.6,6.0]",
    "sosF[0.5,0.0,3.0]",
    "alphaF[2.0,1.2,4.0]",
)

# ---------------------------------------------------------------------------
# 2026-09-06  b23 / b24 / b33
#
# b23 (eta 2.00..2.50, ET 27-35) and b24 (eta -2.50..-2.00, ET 35-50):
#   the same collapse b33 hit on 08-29, now on BOTH legs. Every sigma sits on
#   the 0.1 floor of tnpParAltSigBkgFit (b23: sigmaP/sigmaP_2/sigmaF/sigmaF_2
#   all four; b24: three of four) with alpha on its 1.4 floor and sos at 0 --
#   the signal has degenerated into the unsmeared MC template. 0.1 GeV is not
#   a resolution any endcap electron has.
#   The data says the opposite: b24 passing runs +27..+33% short of the model
#   across 100-120 GeV and -30% at 75-80 (11 slices past 5 sigma), b23 failing
#   is +17% at 80-85 and +17% at 95-100 while 85-90 matches -- both want a
#   WIDER core, yet the minimizer walked to the narrow bound and stopped
#   (b24 passing edm 53.2). Give physical starts and lift the floor off 0.1.
#
# b33 failing: the 08-29 override widened the sigmas but the fit still does not
#   converge (edm 35.2). sosF now rails at 0 and nF presses its 1.5 ceiling,
#   and the peak is 10% too low at 90-95 -- this one wants a NARROWER core, so
#   start it lower and open the two bounds it is pinned against.
_endcap_widen = (
    "sigmaP[1.5,0.5,6.0]", "sigmaP_2[1.5,0.5,6.0]", "sosP[0.4,0.0,3.0]",
    "alphaP[2.0,1.2,4.0]", "nP[0.6,0.0,3.0]", "meanP[-0.3,-3.0,2.0]",
    "sigmaF[1.5,0.5,6.0]", "sigmaF_2[1.5,0.5,6.0]", "sosF[0.4,0.0,3.0]",
    "alphaF[2.0,1.2,4.0]", "nF[0.6,0.0,3.0]", "meanF[-0.3,-3.0,2.0]",
)
tnpParAltSigBkgFitByBin[23] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(23, tnpParAltSigBkgFit), *_endcap_widen)
tnpParAltSigBkgFitByBin[24] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(24, tnpParAltSigBkgFit), *_endcap_widen)
tnpParAltSigBkgFitByBin[33] = params_with_updates(
    tnpParAltSigBkgFitByBin[33],
    "sigmaF[1.8,0.5,5.0]",
    "sigmaF_2[1.0,0.3,5.0]",
    "sosF[0.3,0.0,3.0]",
    "nF[1.0,0.0,4.0]",
)

# b18 (altSigFit, eta -1.57..-0.80, ET 27-35, failing)
#   edm 5.2e+07(沒收斂)。三個參數同時撞在上界:
#     sigmaF = 7.914  [0.7, 8]      訊號想更寬
#     acmsF  = 72     [45, 72]      背景 turn-on 想更高
#     betaF  = 0.15   [0.005, 0.15] turn-on 想更陡
#   上界 72 / 0.15 是先前 _failbkg_altsig 那組覆寫收窄過的,現在三個方向全被關住,
#   擬合無處可去。只放寬撞界那一側,下界一律不動(不要重蹈把最佳解排除在外的錯)。
tnpParAltSigFitByBin = dict(globals().get('tnpParAltSigFitByBin', {}))
tnpParAltSigFitByBin[18] = params_with_updates(
    tnpParAltSigFitByBin.get(18, tnpParAltSigFit),
    "sigmaF[6.0,0.7,14.0]",
    "acmsF[75.,45.,95.]",
    "betaF[0.10,0.005,0.60]",
)


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
    'altSigFit':    (12, 13, 15, 21, 22),
}

tnpParAltSigFit_addGaus = params_with_updates(tnpParAltSigFit, *_gaus_f)
_bybin = globals().get('tnpParAltSigFitByBin', {})
tnpParAltSigFit_addGausByBin = {}
for _b, _sides in {12: 'f', 13: 'f', 15: 'f', 21: 'f', 22: 'f'}.items():
    _extra = _gaus_f + (_gaus_p if _sides == "fp" else ())
    tnpParAltSigFit_addGausByBin[_b] = params_with_updates(
        _bybin.get(_b, tnpParAltSigFit), *_extra)


# --- bins 13/21/22 altSigFit：failing 背景在低質量端爬太快 (2026-09-07) ---
# 直接證據是 acmsF 和 betaF 同時撞到各自的「上界」：
#   b13 acmsF 89.98/[45,90]、betaF 0.0800/[0.005,0.08]
#   b21 acmsF 71.9999/[45,72]、betaF 0.1500/[0.005,0.15]
#   b22 acmsF 72.0000/[45,72]、betaF 0.1500/[0.005,0.15]
# RooCMSShape 是 erfc((acms-x)*beta) * exp(-(x-peak)*gamma)：acms 是 turn-on 的
# 位置、beta 是它的陡度。兩個都撞上界＝擬合想要「更高、更陡的低質量截止」，
# 但範圍不讓它去。把天花板打開就是使用者看到的那個問題的直接解。
# 這幾個參數不在 listOfParam 裡，所以在 data fit 是自由浮動（不會被 MC 值蓋掉），
# 改範圍才會真的生效。
for _b in (21, 22):
    tnpParAltSigFitByBin[_b] = params_with_updates(
        tnpParAltSigFitByBin.get(_b, tnpParAltSigFit),
        "acmsF[72.,45.,88.]",
        "betaF[0.15,0.005,0.60]",
    )
tnpParAltSigFitByBin[13] = params_with_updates(
    tnpParAltSigFitByBin.get(13, tnpParAltSigFit),
    "acmsF[85.,45.,96.]",
    "betaF[0.08,0.005,0.60]",
)

# ⚠️ 13/21/22 同時在 addGausBins['altSigFit'] 裡，實際取用的是
#    tnpParAltSigFit_addGausByBin（它在上面就已經從當時的 tnpParAltSigFitByBin
#    拷貝好了）。上面那段只改 tnpParAltSigFitByBin 不會傳過去，必須重建。
for _b in (13, 21, 22):
    tnpParAltSigFit_addGausByBin[_b] = params_with_updates(
        tnpParAltSigFitByBin[_b], *_gaus_f)
