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
    'hza_dielleg12trigger_nongap_2025_sf': '(passHltEle23Ele12CaloIdLTrackIdLIsoVLLeg2 == 1 && el_hltE23E12leg2_dR < 0.3)',
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
   { 'var' : 'el_et' , 'type': 'float', 'bins': [7,13,16,20,30,50,100,500] },
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

# 2026-07-12 夥伴回饋: nominal bin37(et30-50) passing σ=0.9 略窄 + acmsP railed 90。略寬+解開acmsP。
tnpParNomFitByBin = {
    37: params_with_updates(
        tnpParNomFit,
        "sigmaP[1.6,0.9,4.5]",
        "acmsP[70.,45.,88.]",
    ),
}
# NOTE: bin12 (et 13-16) is background-dominated with empty failing leg -> eff~1;
# shrinking its background collapses the signal and wrongly lowers eff, so it is left
# at default (see doc/HZa/tnp_ele_fit_tuning_2026-06-28.md).

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
    (8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23),
    "meanP[-25.0,-40.0,-5.0]",
    "sigmaP[7.0,1.5,16.0]",
    "sigmaP_2[4.0,0.5,14.0]",
    "alphaP[2.0,0.8,4.5]",
    "nP[0.8,-2.0,8.0]",
    "sosP[3.0,0.2,12.0]",
    "meanF[-25.0,-40.0,-5.0]",
    "sigmaF[7.0,1.5,16.0]",
    "sigmaF_2[4.0,0.5,14.0]",
    "alphaF[2.0,0.8,4.5]",
    "nF[0.8,0.0,8.0]",
    "sosF[3.0,0.2,12.0]",
    "acmsP[52.,40.,65.]",
    "betaP[0.008,0.001,0.035]",
    "gammaP[0.02,0.001,0.35]",
    "peakP[75.0,60.0,86.0]",
    "acmsF[52.,40.,65.]",
    "betaF[0.008,0.001,0.035]",
    "gammaF[0.02,0.001,0.35]",
    "peakF[75.0,60.0,86.0]",
)
tnpParAltSigFitByBin.update({
    37: params_with_updates(
        tnpParAltSigFit,
        "meanP[0.0,-4.0,4.0]",
        "sigmaP[1.1,0.4,2.8]",
        "sigmaP_2[1.0,0.3,3.0]",
        "sosP[0.45,0.0,1.6]",
        "acmsP[92.,75.,115.]",
        "betaP[0.045,0.002,0.10]",
        "gammaP[0.06,0.002,1.0]",
        "peakP[90.0,86.0,93.0]",
    ),
    # 2026-07-12: passing bkg 太大(acmsP/peakP~90 讓 bkg turn-on 坐 Z 峰吸訊號)。綁低 + 加寬 signal。
    39: params_with_updates(
        tnpParAltSigFit,
        "meanP[0.0,-4.0,4.0]",
        "sigmaP[2.5,1.0,6.0]",
        "sigmaP_2[2.0,0.6,5.5]",
        "sosP[1.0,0.0,4.0]",
        "acmsP[62.,45.,78.]",
        "betaP[0.03,0.005,0.07]",
        "gammaP[0.06,0.002,1.0]",
        "peakP[70.0,60.0,82.0]",
    ),
})

# 2026-07-12 夥伴回饋: bins 10-14,18-21,23,30 — group 的 meanP[-25,-40,-5] 過度偏移
# (data 只微偏 ~88),導致 meanP railed 在 -5/peakP railed 75。個別 override 覆蓋 group,
# 解開 meanP 讓 signal 坐回 peak(未旗標的 8,9,15,16,17 保持 group 參數不動)。
for _b in (10, 11, 12, 13, 14, 18, 19, 20, 21, 23, 30):
    tnpParAltSigFitByBin[_b] = params_with_updates(
        tnpParAltSigFit,
        "meanP[-2.0,-12.0,5.0]",
        "sigmaP[2.5,0.7,7.0]",
        "sigmaP_2[2.0,0.5,7.0]",
        "sosP[1.0,0.0,5.0]",
        "meanF[-2.0,-12.0,5.0]",
        "sigmaF[3.0,0.7,8.0]",
        "sigmaF_2[2.0,0.5,7.0]",
        "sosF[1.0,0.0,5.0]",
        "peakP[86.0,70.0,90.0]",
        "peakF[86.0,70.0,90.0]",
    )

# 2026-07-12 夥伴回饋: altSig bin38(endcap et30-50) passing 太窄 -> widen(同33/38/55)。
tnpParAltSigFitByBin[38] = params_with_updates(
    tnpParAltSigFit,
    "meanP[0.0,-3.0,3.0]",
    "sigmaP[3.0,1.5,7.0]",
    "sigmaP_2[2.2,0.8,6.0]",
    "sosP[1.0,0.0,4.0]",
    "acmsP[80.,45.,89.9]",
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
    # 2026-07-12: bin32 signal core σ railed 在 0.1 下限(塌成尖刺,全靠CB尾)。抬高 σ floor(far endcap ~2)。
    32: params_with_updates(
        tnpParAltSigBkgFit,
        'sigmaP[1.8, 0.8, 5.0]',
        'sigmaF[1.8, 0.8, 5.0]',
        'sigmaP_2[1.5, 0.5, 5.0]',
        'sigmaF_2[1.5, 0.5, 5.0]',
        'sosP[0.5, 0.0, 3.0]',
        'sosF[0.5, 0.0, 3.0]',
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


# --- bin15 passing:meanP 被鎖在 -5 以下 (2026-08-28) ---
# meanP 死貼上界 -5、acmsP 撞上界 65、betaP 撞上界 0.035,edm=8.6。
# 與 dielleg12trigger_nongap_2026 的 bin08/09/15/16/17 是同一個 bug 家族:
# meanP 的範圍假設 passing 峰大幅下移,但資料的峰就在 85-90
# (638 667 927 1870 3814 5665 3708 911 ...),最佳解在 -5 之外。
# 2026 那批放寬後收斂在 meanP = -1.5 ~ -2.6,沿用同一組已驗證的參數。
tnpParAltSigFitByBin = dict(globals().get('tnpParAltSigFitByBin', {}))
tnpParAltSigFitByBin[15] = params_with_updates(
    tnpParAltSigFitByBin.get(15, tnpParAltSigFit),
    "meanP[-2.0,-12.0,5.0]",
    "sigmaP[2.5,0.7,7.0]",
    "sigmaP_2[2.0,0.5,7.0]",
    "sosP[1.0,0.0,5.0]",
    "acmsP[60.,40.,85.]",
    "betaP[0.02,0.001,0.10]",
)


# --- bin41 failing: converged but pinned on three bounds (2026-09-06) ---
# edm 6.5e-04 and covQual 3, yet sigmaF sits exactly on the 2.0 ceiling of
# tnpParAltSigBkgFit, alphaF on its 1.4 floor and sosF at 0. The peak comes out
# 10% low at 90-95 GeV. Same cell (eta -2.00..-1.57, ET 50-100) and same +10%
# as bin33 of dielleg23_nongap_2025. Open the three bounds it is against.
tnpParAltSigBkgFitByBin = dict(globals().get('tnpParAltSigBkgFitByBin', {}))
tnpParAltSigBkgFitByBin[41] = params_with_updates(
    tnpParAltSigBkgFitByBin.get(41, tnpParAltSigBkgFit),
    "sigmaF[1.8,0.3,5.0]",
    "sigmaF_2[0.8,0.2,4.0]",
    "alphaF[2.0,1.0,4.0]",
    "sosF[0.3,0.0,2.0]",
    "nF[0.8,0.0,3.0]",
)


# --- bin41 failing nominalFit：covQual 1，峰頂低 12% (2026-09-06) ---
# edm 3.13、covQual 1 —— 沒有收斂。acmsF = 45.46 +/- 6.28 貼在 45 的下界，
# 也就是 CMSShape 的 turn-on 被推到質量窗之外，背景於是在整個範圍近乎平坦，
# 而 gammaF 走到 -0.0286（負值＝往高質量端爬）。
# 結果是 90-95 GeV 資料 3875 對曲線 3470（+12%，唯一超過 5 sigma 的 slice）：
# 峰頂不夠高。訊號 sigmaF = 1.720 對這個 eta/ET 偏寬，收窄可以把峰拉起來。
# 同一格的 altSigBkgFit 在 2026-09-06 早先也是 90-95 +10%，同一個病。
tnpParNomFitByBin = dict(globals().get('tnpParNomFitByBin', {}))
tnpParNomFitByBin[41] = params_with_updates(
    tnpParNomFitByBin.get(41, tnpParNomFit),
    # 第二輪 (2026-09-06)：第一輪把 edm 從 3.13 壓到 0.69，但 covQual 仍是 1，
    # sigmaF 也幾乎沒動（1.7203 -> 1.7202）。原因是 acmsF 停在 48 的下界而誤差
    # 高達 26.7 —— CMSShape 的 turn-on 被推到質量窗（60 GeV）之外，erfc 在整個
    # 窗內幾乎恆為 1，acmsF 與 betaF 因此完全簡併。那個平坦方向讓共變異數矩陣
    # 無法正定，也讓 sigmaF 找不到乾淨的極小值。
    # 兩個都釘成常數（值取第一輪停下來的位置），把自由度還給 mean/sigma 與產率。
    # gammaF 維持可負：這格的背景是真的往高質量端上升（60-65 GeV 只有 50 個事件，
    # 115-120 有 519 個），不要強迫它遞減。
    "meanF[-1.8,-4.0,1.0]",
    "sigmaF[1.5,0.5,2.6]",
    "acmsF[50.]",
    "betaF[0.073]",
    "gammaF[-0.029,-0.3,0.2]",
)


# ============================================================================
# addGaus：訊號加一個第二成分  (2026-09-07)
# ----------------------------------------------------------------------------
# 兩種症狀都適用，差別在第二個高斯落在哪裡：
#   (a) 「窄峰 + 低質量 shoulder」——模板 conv Gaussian 做不出這個形狀，於是把
#       sigma 撐寬去湊 shoulder，兩邊都對不上。高斯落在 75-83 GeV。
#   (b) 「shoulder 太肥、峰太瘦」——曲線在 70-80 GeV 高出資料 ~20%、85-95 GeV
#       又低 ~15%。模板本身的低質量尾巴比資料多，收 sigma 沒用（那段不是平滑
#       出來的）。加了第二成分後模板權重被 sigFrac 壓下去，缺的峰由高斯補回。
#       高斯落在 85-92 GeV，所以 meanG 的上界要開到 95。
#
# ⚠️ sigmaG 上界必須 <= 9 GeV。放到 20 時第二成分會退化成寬平台把背景吃進訊號：
#    elid_nongap_2026 bin11/12 實測 sigmaGF 12.4 GeV、nSigF 27879+/-484 ->
#    46534+/-1728、nBkgF 41912 -> 23257，效率 0.9073 -> 0.8830。那個狀態下殘差
#    反而是乾淨的（0 slice），所以驗收要一併看 sigmaG 與 nSig/nBkg 的誤差。
# ⚠️ meanG 的上界一度開到 95，讓第二個成分可以坐到 Z 峰上當「第二個峰」。
#    兩份證據說那樣不行（2026-09-07）：
#    (a) elminiIso0p15_gap_2024 bin02 altSigFit 的 meanGF 跑到 92.57（貼著 95），
#        60-65 GeV 殘差惡化到 -49%，比不加 gaus 還糟。
#    (b) elminiIso0p15_gap_2024/2026 的 nominalFit bin02 直接 sigGaussFail = -nan
#        整個擬合掛掉（和 elid_nongap_2026 nominal bin15 同一種死法）。
#    收回 shoulder 區間，並把 sigmaG 的下限抬到 2.5 避免退化成尖刺。
_gaus_f = ("meanGF[77.0,70.0,86.0]", "sigmaGF[5.0,2.5,9.0]")
_gaus_p = ("meanGP[77.0,70.0,86.0]", "sigmaGP[5.0,2.5,9.0]")

addGausBins = {
    'altBkgFit':    (21,),
    'altSigBkgFit': (21,),
}

tnpParAltBkgFit_addGaus = params_with_updates(tnpParAltBkgFit, *_gaus_f)
_bb0 = globals().get('tnpParAltBkgFitByBin', {})
tnpParAltBkgFit_addGausByBin = {}
for _b, _sides in {21: 'f'}.items():
    _extra = _gaus_f + (_gaus_p if _sides == "fp" else ())
    tnpParAltBkgFit_addGausByBin[_b] = params_with_updates(_bb0.get(_b, tnpParAltBkgFit), *_extra)

tnpParAltSigBkgFit_addGaus = params_with_updates(tnpParAltSigBkgFit, *_gaus_f)
_bb1 = globals().get('tnpParAltSigBkgFitByBin', {})
tnpParAltSigBkgFit_addGausByBin = {}
for _b, _sides in {21: 'f'}.items():
    _extra = _gaus_f + (_gaus_p if _sides == "fp" else ())
    tnpParAltSigBkgFit_addGausByBin[_b] = params_with_updates(_bb1.get(_b, tnpParAltSigBkgFit), *_extra)


# --- bin16 altSigFit passing：訊號偏左 (2026-09-07) ---
# 和 2026-07-12 夥伴回饋修掉的 bins 10-14,18-21,23,30 是同一個病：group 參數
# meanP[-25,-40,-5] 的「上界」就是 -5，fit 想往右卻只能停在那裡。實測 meanP =
# -5.0000 +/- 0.0008 撞界，連帶 acmsP 撞 65、betaP 撞 0.035、alphaP 撞 4.5、
# nP 撞 8.0、sigmaP 撞 1.5 下界、sosF 撞 0.2 下界 —— 六個參數同時撞界，是整組
# 範圍設錯而不是單一參數的問題。當時只改了被點名的 bin，16 留在原 group。
# 殘差：70-75 +24%、80-85 -12%、90-95 +14%、95-100 -15%（峰位整體偏左）。
tnpParAltSigFitByBin[16] = params_with_updates(
    tnpParAltSigFit,
    "meanP[-2.0,-12.0,5.0]",
    "sigmaP[2.5,0.7,7.0]",
    "sigmaP_2[2.0,0.5,7.0]",
    "sosP[1.0,0.0,5.0]",
    "meanF[-2.0,-12.0,5.0]",
    "sigmaF[3.0,0.7,8.0]",
    "sigmaF_2[2.0,0.5,7.0]",
    "sosF[1.0,0.0,5.0]",
    "peakP[86.0,70.0,90.0]",
    "peakF[86.0,70.0,90.0]",
)

# --- bin26 altSigFit passing：訊號太寬、低質量尾巴太彎 (2026-09-07) ---
# sigmaP = 5.336 貼著 6.0 天花板，其他三個擬合同格的 passing 寬度是 1.20 /
# 1.81 / 0.25，altSig 明顯離群；效率也是 0.8643 對其他三個的 0.828/0.821/0.820。
# 殘差：60-65 -62%（曲線比資料高 16700 個事件）、65-70 -28%、85-90 +15%、
# 95-100 -20%、100-105 -24% —— 峰被攤平、兩側尾巴撐太開。
# nBkgP = 36737 +/- 4685（誤差 13%）也偏大，是被寬訊號逼出來的。
tnpParAltSigFitByBin[26] = params_with_updates(
    tnpParAltSigFit,
    "sigmaP[1.8,0.7,3.0]",
    "sigmaP_2[1.2,0.4,3.0]",
    "sosP[1.0,0.3,3.0]",
    "acmsP[65.,45.,80.]",
)
