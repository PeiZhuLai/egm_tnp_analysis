# -*- coding: utf-8 -*-
# 初始化 _mod_path 並更新 sys.path，供 tnpEGM_fitter 與 etc.* 匯入使用
import os, sys
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
    'hza_resolve_phcsev_hr9_2022preEE_sf': (
        # electron veto
        ' (ph_passElectronVeto > 0.5)'
    ),
}

# /eos/cms/store/group/phys_egamma/ec/nkasarag/EGM_comm/TnP_samples/2022/sim/DY_NLO/merged_Run3Summer22MiniAODv4-130X_mcRun3_2022_realistic_v5-v2.root
baseOutDir = '/eos/home-p/pelai/HZa/root_TnP'

#############################################################
########## samples definition  - preparing the samples
#############################################################
### samples are defined in etc/inputs/tnpSampleDef.py
### not: you can setup another sampleDef File in inputs
import etc.inputs.tnpSampleDef as tnpSamples
tnpTreeDir = 'tnpPhoIDs'

samplesDef = {
        'data'  : tnpSamples.Run3_2022preEE_zmmg['Data_2022preEE'].clone(),
        'mcNom' : tnpSamples.Run3_2022preEE_zmmg['DY_MC_NLO_2022preEE'].clone(),
        'tagSel': tnpSamples.Run3_2022preEE_zmmg['DY_MC_NLO_2022preEE'].clone(),
        'mcAlt': tnpSamples.Run3_2022preEE_zmmg['DY_MC_NLO_2022preEE'].clone(),
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
    samplesDef['tagSel'].rename('mcAltSel_DY_MC_NLO_2022preEE')
    # samplesDef['tagSel'].set_cut('tag_Ele_pt > 35 && abs(tag_sc_eta) < 2.17')

## set MC weight, simple way (use tree weight) 
# weightName = 'totWeight'
# if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_weight(weightName)
# if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_weight(weightName)
# if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_weight(weightName)

## zmmg ntuples already carry the final event weight in-tree
weightName = 'totWeight'
if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_weight(weightName)
if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_weight(weightName)
if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_weight(weightName)

#############################################################
########## bining definition  [can be nD bining]
#############################################################
biningDef = [
# 2026-08-29 重新分箱:判準改為 **data 的 failing 側 >= 300 個事件**。
# 舊分箱(2026-08-23)用的是 MC 側(2022/2023)或 data 總量(2024)的統計量,
# 沒有把 failing 側單獨當約束 —— 但 CSEV 的 failing 只佔 2-24%,效率誤差完全由它決定。
# 實測 74 個 bin 有 42 個(57%) failing < 300,擬合有 7 個自由參數、每個分不到 15 個事件,
# Hessian 必然奇異(covQual=0),逐格調參是在調雜訊。
# bkg/puup/pudown 三個變體必須與 nominal 同分箱,否則系統誤差無法對照。
   { 'var' : 'event_nPV' , 'type': 'float', 'bins': [10,100] },
#    { 'var' : 'ph_sc_eta' , 'type': 'float', 'bins': [-2.5,-1.566,-1.4442,0.0,1.4442,1.566,2.5] },
#    { 'var' : 'ph_sc_abseta' , 'type': 'float', 'bins': [0.0,1.4442,1.566,2.5] },
   { 'var' : 'ph_et' , 'type': 'float', 'bins': [10,80] },
]

#############################################################
########## Cuts definition for all samples
#############################################################
### cut
cutBase   = 'ph_r9 > 0.96'
# cutBase   = ''

# can add addtionnal cuts for some bins (first check bin number using tnpEGM --checkBins)
additionalCuts = { 
}

#### or remove any additional cut (default)
additionalCuts = None

#############################################################
########## fitting params to tune fit by hand if necessary
#############################################################
tnpParNomFit = [
    "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
    "meanF[-0,-8,5]","sigmaF[0.9,0.2,8]",
    "acmsP[60,50,95]","betaP[0.05,0.01,0.4]","gammaP[0.1,-2,0.03]","peakP[87.0,82.0,90.0]",
    "acmsF[60,50,95]","betaF[0.05,0.01,0.4]","gammaF[0.1,-2,2]","peakF[87.0,82.0,90.0]",
    ]

# # 0
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[-0,-8,5]","sigmaF[0.9,0.2,8]",
#     "acmsP[60,50,95]","betaP[0.05,0.01,0.4]","gammaP[0.1,-2,0.03]","peakP[87.0,82.0,90.0]",
#     "acmsF[60,50,95]","betaF[0.05,0.01,0.4]","gammaF[0.1,-2,2]","peakF[87.0,82.0,90.0]",
#     ]

# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[0.2,-8,5]","sigmaF[1.5]",
#     "acmsP[60,50,95]","betaP[0.05,0.01,0.4]","gammaP[0.1,-2,2]","peakP[87.0,82.0,90.0]",
#     "acmsF[60,40,95]","betaF[0.05,0.005,0.4]","gammaF[0.01,-2,1]","peakF[87.0,82.0,90.0]",
#     ]

# # 4
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[0.2,-8,5]","sigmaF[1.5]",
#     "acmsP[60,50,95]","betaP[0.05,0.01,0.4]","gammaP[0.1,-2,2]","peakP[87.0,82.0,90.0]",
#     "acmsF[60,40,95]","betaF[0.05,0.005,0.4]","gammaF[0.01,-2,1]","peakF[87.0,82.0,90.0]",
#     ]

# # 5
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[0.2,-8,5]","sigmaF[1.5]",
#     "acmsP[60,50,95]","betaP[0.05,0.01,0.4]","gammaP[0.1,-2,2]","peakP[87.0,82.0,90.0]",
#     "acmsF[60,40,95]","betaF[0.05,0.005,0.4]","gammaF[0.01,-2,1]","peakF[87.0,82.0,90.0]",
#     ]

# 9
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[0.2,-8,5]","sigmaF[1.5]",
#     "acmsP[60,50,95]","betaP[0.05,0.005,0.4]","gammaP[0.1,-2,2]","peakP[87.0,82.0,90.0]",
#     "acmsF[60,40,95]","betaF[0.05,0.005,0.4]","gammaF[0.01,-2,0.1]","peakF[87.0,82.0,90.0]",
#     ]

# # 15
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[-0,-8,5]","sigmaF[1,0,8]",
#     "acmsP[60,50,95]","betaP[0.05,0.01,0.4]","gammaP[0.1,-2,2]","peakP[87.0,82.0,90.0]",
#     "acmsF[60,50,95]","betaF[0.05,0.05,0.4]","gammaF[0.01,-2,2]","peakF[87.0,82.0,90.0]",
#     ]

# # # 24
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[-0,-8,5]","sigmaF[1,0,8]",
#     "acmsP[60,50,95]","betaP[0.01,0.01,0.4]","gammaP[0.1,-2,2]","peakP[87.0,82.0,91.0]",
#     "acmsF[60,50,95]","betaF[0.05,0.01,0.4]","gammaF[0.1,-2,2]","peakF[87.0,82.0,90.0]",
#     ]

# # 25
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[-0,-8,5]","sigmaF[1,0,8]",
#     "acmsP[60,50,95]","betaP[0.01,0.01,0.4]","gammaP[0.1,-2,2]","peakP[87.0,82.0,91.0]",
#     "acmsF[60,50,95]","betaF[0.05,0.01,0.4]","gammaF[0.1,-2,2]","peakF[87.0,82.0,90.0]",
#     ]

# # 26
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[-0,-8,5]","sigmaF[1,0,8]",
#     "acmsP[60,50,95]","betaP[0.01,0.01,0.4]","gammaP[0.1,-2,2]","peakP[87.0,82.0,91.0]",
#     "acmsF[60,50,95]","betaF[0.05,0.01,0.4]","gammaF[0.1,-2,2]","peakF[87.0,82.0,90.0]",
#     ]

# # 30
# tnpParNomFit = [
#     "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
#     "meanF[-0,-8,5]","sigmaF[0.9,0.2,8]",
#     "acmsP[60,50,95]","betaP[0.05,0.01,0.4]","gammaP[-0.1,-2,2]","peakP[87.0,82.0,92.0]",
#     "acmsF[60,50,95]","betaF[0.05,0.01,0.4]","gammaF[0.1,-2,2]","peakF[87.0,82.0,90.0]",
#     ]

tnpParAltSigFit = [
    "meanP[-0,-8,5]",
    "sigmaP[1,0.2,8]",
    "alphaP[2.0,1.2,3.5]" ,
    "nP[3,-5,5]",
    "sigmaP_2[1.5,0.5,6.0]",
    "sosP[1,0.5,5.0]",
    "meanF[-0,-8,5]",
    "sigmaF[2,0.2,8]",
    "alphaF[2.0,1.2,3.5]",
    "nF[3,0,5]",
    "sigmaF_2[2.0,0.5,6.0]",
    "sosF[1,0.5,5.0]",
    "acmsP[60,50,95]","betaP[0.04,0.01,0.4]","gammaP[0.1,-0.5,1]","peakP[89.0,82.0,90.0]",
    "acmsF[60,50,95]","betaF[0.04,0.01,0.4]","gammaF[0.1,-0.5,1]","peakF[89.0,82.0,90.0]",
    ]

tnpParAltBkgFit = [
    "meanP[-0,-8,5]","sigmaP[0.9,0.2,8]",
    "meanF[-0,-8,5]","sigmaF[0.9,0.2,8]",
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
  'alphaP[2.0, 1.4, 3.5]', 'nP[1.0, 0.0, 15.0]',
  'alphaF[2.0, 1.4, 3.5]', 'nF[1.0, 0.0, 20.0]',
  'alphaP_2[-0.012, -1, 0]',
  'alphaF_2[-0.014, -1, 0.05]',
]

# 2026-08-30 放寬 CMSShape / 解析度的窗。重新分箱後每格的 failing 事件數由
# 10-300 提升到 300-2000,參數終於由資料決定 —— 結果 60 格裡有 55 格撞界,
# 而且是同一組:acmsP/F 與 betaP/F 撞**上**界(60/60 與 58/60)、gammaF 撞**下**界(30)、
# sigmaF 撞上界(12)、sigmaP 撞下界(6)、meanF 撞下界(4)。
# 這些窗是舊統計量下手調出來的(有的被收到 acmsF 上界 75、sigmaF 上界 2.1),
# 統計量增加 6 倍後就綁不住了。只開撞界那一側,另一側一律不動 ——
# 不要把最佳解排除在範圍外(這個錯誤在 2026-08 已經犯過三次)。
