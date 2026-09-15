# -*- coding: utf-8 -*-
# 初始化 _mod_path 並更新 sys.path，供 tnpEGM_fitter 與 etc.* 匯入使用
import os, sys
# 以 globals() 安全檢查，避免在 Py2 觸發 NameError
if '_mod_path' not in globals() or not _mod_path:
    _mod_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    if _mod_path not in sys.path:
        sys.path.insert(0, _mod_path)
from etc.config.fit_param_utils import params_with_updates

#############################################################
########## General settings
#############################################################
# EA reference: https://indico.cern.ch/event/1204277/contributions/5064356/attachments/2538496/4369369/CutBasedPhotonID_20221031.pdf
# flag to be Tested
flags = {
    # Run3 custom ID aligned to ZaTaggerRun3.select_photons
    'hza_resolve_phid_lowpt_2023preBPix_sf': (
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
        '   && (('
        '         (abs(ph_sc_eta) > 0.0 && abs(ph_sc_eta) < 1.0)'
        '         && (ph_chIso - event_rho*0.0342898 - (event_rho*event_rho)*(-0.000103508)'
        '             < 0.316306)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 1.0 && abs(ph_sc_eta) < 1.4442)'
        '         && (ph_chIso - event_rho*0.0281424 - (event_rho*event_rho)*(-0.000031494)'
        '             < 0.316306)'
        '       ))'
        # ================= H ISO =================
        '   && (('
        '         (abs(ph_sc_eta) > 0.0 && abs(ph_sc_eta) < 1.0)'
        '         && (ph_neuIso - event_rho*0.17005 - (event_rho*event_rho)*(-0.000835)'
        '             < (0.39057 + 0.0100547*ph_et + 0.0000578332*ph_et*ph_et))'
        '       ) || ('
        '         (abs(ph_sc_eta) > 1.0 && abs(ph_sc_eta) < 1.4442)'
        '         && (ph_neuIso - event_rho*0.208571 - (event_rho*event_rho)*(-0.000905)'
        '             < (0.39057 + 0.0100547*ph_et + 0.0000578332*ph_et*ph_et))'
        '       ))'
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
        '   && (('
        '         (abs(ph_sc_eta) > 1.566 && abs(ph_sc_eta) < 2.0)'
        '         && (ph_chIso - event_rho*0.0288533 - (event_rho*event_rho)*(-0.0000666148)'
        '             < 0.292664)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.0 && abs(ph_sc_eta) < 2.2)'
        '         && (ph_chIso - event_rho*0.028789 - (event_rho*event_rho)*(-0.0000684993)'
        '             < 0.292664)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.2 && abs(ph_sc_eta) < 2.3)'
        '         && (ph_chIso - event_rho*0.0264064 - (event_rho*event_rho)*(-0.0000889189)'
        '             < 0.292664)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.3 && abs(ph_sc_eta) < 2.4)'
        '         && (ph_chIso - event_rho*0.025587 - (event_rho*event_rho)*(-0.0000590178)'
        '             < 0.292664)'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.4 && abs(ph_sc_eta) < 2.5)'
        '         && (ph_chIso - event_rho*0.0224817 - (event_rho*event_rho)*(-0.0000422712)'
        '             < 0.292664)'
        '       ))'
        # ================= H ISO =================
        '   && (('
        '         (abs(ph_sc_eta) > 1.566 && abs(ph_sc_eta) < 2.0)'
        '         && (ph_neuIso - event_rho*0.246494 - (event_rho*event_rho)*(-0.000722)'
        '             < (0.0292617 + 0.0116989*ph_et + 0.0000747603*ph_et*ph_et))'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.0 && abs(ph_sc_eta) < 2.2)'
        '         && (ph_neuIso - event_rho*0.306529 - (event_rho*event_rho)*(-0.000608)'
        '             < (0.0292617 + 0.0116989*ph_et + 0.0000747603*ph_et*ph_et))'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.2 && abs(ph_sc_eta) < 2.3)'
        '         && (ph_neuIso - event_rho*0.322673 - (event_rho*event_rho)*(-0.000750)'
        '             < (0.0292617 + 0.0116989*ph_et + 0.0000747603*ph_et*ph_et))'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.3 && abs(ph_sc_eta) < 2.4)'
        '         && (ph_neuIso - event_rho*0.315793 - (event_rho*event_rho)*(-0.000795)'
        '             < (0.0292617 + 0.0116989*ph_et + 0.0000747603*ph_et*ph_et))'
        '       ) || ('
        '         (abs(ph_sc_eta) > 2.4 && abs(ph_sc_eta) < 2.5)'
        '         && (ph_neuIso - event_rho*0.36531 - (event_rho*event_rho)*(-0.000439)'
        '             < (0.0292617 + 0.0116989*ph_et + 0.0000747603*ph_et*ph_et))'
        '       ))'
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
        'data'  : tnpSamples.Run3_2023preBPix['Data_2023preBPix'].clone(),
        'mcNom' : tnpSamples.Run3_2023preBPix['DY_MC_LO_2023preBPix'].clone(),
        'tagSel': tnpSamples.Run3_2023preBPix['DY_MC_LO_2023preBPix'].clone(),
        'mcAlt': tnpSamples.Run3_2023preBPix['DY_MC_NLO_2023preBPix'].clone(),
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
    samplesDef['tagSel'].rename('mcAltSel_DY_MC_LO_2023preBPix')
    samplesDef['tagSel'].set_cut('tag_Ele_pt > 50 && abs(tag_sc_eta) < 2.17 && ph_mva122XV1 > 0.99 && ph_r9 > 0.99')

## set MC weight, simple way (use tree weight) 
# weightName = 'totWeight'
# if not samplesDef['mcNom' ] is None: samplesDef['mcNom' ].set_weight(weightName)
# if not samplesDef['mcAlt' ] is None: samplesDef['mcAlt' ].set_weight(weightName)
# if not samplesDef['tagSel'] is None: samplesDef['tagSel'].set_weight(weightName)

## set MC weight, can use several pileup rw for different data taking 
mcNom_puFile = '/eos/cms/store/group/phys_egamma/ec/tnpTuples/Prompt2023/pileupReweightingFiles/preBPIX/DY_madgraph_pho.pu.puTree.root'
mcAlt_puFile = '/eos/cms/store/group/phys_egamma/ec/tnpTuples/Prompt2023/pileupReweightingFiles/preBPIX/DY_amcatnloext_pho.pu.puTree.root'
weightName = 'weights_data_Run2023C.totWeight'
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
   { 'var' : 'ph_et' , 'type': 'float', 'bins': [10,20] },
#    { 'var' : 'ph_et' , 'type': 'float', 'bins': [10,20,35,50,80] },
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
    "meanP[-0.0,-5.0,5.0]","sigmaP[0.9,0.4,2.87]",
    "meanF[-0.0,-2.6,5.0]","sigmaF[1.0,0.5,2.1]",
    "acmsP[60.,39.,80.]","betaP[0.05,0.01,0.09]","gammaP[0.1, -2, 2]","peakP[87.0,82.0,90.0]",
    "acmsF[60.,35.,75.]","betaF[0.05,0.01,0.11]","gammaF[0.1, 0.02, 2]","peakF[87.0,82.0,90.0]",
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
    "acmsF[60.,35.,75.]","betaF[0.04,0.01,0.06]","gammaF[0.1, 0.02, 1]","peakF[89.0,82.0,90.0]",
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
  'alphaP_2[-0.020, -1, 0]',
  'alphaF_2[-0.014, -1, 0.05]',
]


# --- bin07 nominalFit：failing 訊號要窄一點 → **已撤銷** (2026-09-12) ---
# 試過把 sigmaF 的地板從 0.5 降到 0.15（它本來就撞在 0.5 的下界，看起來是地板擋住）。
# 結果變壞，已還原：
#     sigmaF   0.5003 -> 0.150（撞新地板，換了個界線撞而已）
#     殘差      0 slice -> **3 slice**（75-80 GeV -6%、115-120 +10%、60-65 +5%）
#     效率      0.8651 -> 0.8807（+1.6 點）
# 關鍵證據是效率的方向：改前的 0.8651 幾乎正好等於 altBkg 的 0.8653（同一個訊號模型、
# 只換背景），改完反而被推離到 0.8807。也就是說原本那個「撞下界」是對的答案被邊界
# **恰好**框住，不是被邊界擋住。
#
# 教訓：參數撞界有兩種，要分清楚。
#   (a) 擬合想去界線外面 —— 放寬會改善（如 2023postBPix bin06 的 sigmaF 撞上界 5.0）。
#   (b) 最佳值本來就落在界線附近 —— 放寬只會讓它滑進一個更差的區域。
# 分辨方法不是看「撞不撞界」，而是看殘差與「同訊號模型的 altBkg 給什麼效率」。
# 這格改前殘差就已經是 0 slice，(b) 的訊號其實一開始就寫在那裡了。
#
# 使用者觀察到的「視覺上偏寬」是真的，但那個寬度來自 MC 模板本身而不是 sigmaF 的卷積，
# 所以調 sigmaF 動不到它。
#
# --- 2026-09-15 第二次被回報，補上決定性證據 ---
# 拿 **MC 自己的擬合**當對照（同一格 nominalFit 的 DY_MC_LO）：
#     Data  sigmaF = 0.5017 +- 0.1722   撞下界，誤差 34%（4233 個訊號事件約束不住）
#     MC    sigmaF = 0.5000 +- 0.0093   撞下界，誤差 1.9%（約束得很好）
# MC 是拿模板去配自己產生的分布，它**仍然要最小的卷積** —— 模板本身已經和想要的
# 寬度一樣寬甚至更寬。卷積只能加寬不能收窄，所以兩邊都往下界跑。
# 這從第二個獨立方向確認了「寬度來自模板」。
#
# 現在的擬合品質（2026-09-15 量測）：最大 |pull| = 3.8（80.5 GeV）、
# 全範圍 d/model 0.92-1.08、沒有任何 slice 超過 5 sigma。這個擬合是好的。
#
# 換函數（addGaus）也不適用：tnpEGM_fitter._addgaus_for_bin 的說明寫明那是給
# 「窄峰 + 肩膀」結構用的，而這一格的 failing 是單調下降的背景（佔 85-99%）
# 加一個 4.6% 的小凸起，多一個自由度沒東西可描述。全開的實測是改善 699 / 變差 1766。
#
# 🔴 結論：**這一格不要再動了。**三個方向都試過或排除：收 sigmaF（實測變壞）、
#    放寬 sigmaF（方向相反且 MC 對照顯示無效）、換函數（結構不符）。
#    唯一還沒試的是「擾動後重跑」（2026-09-14 在 elid_nongap_2024 b12 上意外發現
#    egm 的擬合會從輸出檔既有結果起跳，可藉此跳出壞盆地），但那格的殘差本來就差，
#    這一格沒有。
