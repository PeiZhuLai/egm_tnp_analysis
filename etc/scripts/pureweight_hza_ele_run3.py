# -*- coding: utf-8 -*-
# DRAFT — HZa Run3 electron-trigger TnP PU-reweighter driver (py2, run under cmssw-el7 + cmsenv)
#
# 目的：為「這批 2024/2025 電子 TnP MC ntuple」重產列數對齊的 puTree，
#       取代 config 目前誤用的 2023 preBPIX puTree。
#
# 用法（在 egm_tnp_analysis/ 根目錄）：
#   cmssw-el7                      # 進 SLC7 container
#   cd .../CMSSW_11_2_0/src && cmsenv
#   cd egm_tnp_analysis
#   python etc/scripts/pureweight_hza_ele_run3.py
#
# ★ 執行前必須先在 libPython/puReweighter.py 設定好（見下方說明）：
#   - puMCscenario / puMC   : Run3 2024(2025) MC truePU 參考（現缺，需補或改成從 MC 樹自建）
#   - puDataEpoch           : 指到 2024/2025 data pileup root（含 'pileup' 直方圖）
#   friend tree 名 = 'weights_<epochKey>'，config 的 weightName 要對應。

import etc.inputs.tnpSampleDef as tnpSamples
from libPython.tnpClassUtils import mkdir
import libPython.puReweighter as pu

puType = 0  # 0 = reweight vs truePU（標準）

# 對齊 MC ntuple 的 puTree 輸出目錄（與 MC 同區）
dirout = '/eos/project/h/htozg-dy-privatemc/pelai/root_merged_eTnP_ntuple/PU_Trees/'
mkdir(dirout)

# nominal = LO(madgraph)；alt = NLO(amcatnlo)。2025 config 目前沿用同一批 2024 MC 檔，
# 故其實只有 2 個實體 MC 檔（LO、NLO）需各產一次 puTree；2025 靠 puDataEpoch 裡的
# weights_data_Run2025 friend tree 區分。若 2025 換成獨立 MC 檔，再加對應 job。
jobs = [
    (tnpSamples.Run3_2024_ele, 'DY_MC_LO_2024'),   # nominal 用
    (tnpSamples.Run3_2024_ele, 'DY_MC_NLO_2024'),  # alt 用
]

for sdict, sName in jobs:
    sample = sdict[sName].clone()
    if sample is None or not sample.isMC:
        print('skip', sName); continue
    sample.set_tnpTree('tnpEleTrig/fitter_tree')                       # 電子 trigger 樹
    sample.set_puTree(dirout + '%s.pu.puTree.root' % sample.name)      # 輸出（覆蓋舊）
    sample.dump()
    pu.reweight(sample, puType)                                        # 逐事件算 PUweight/totWeight
