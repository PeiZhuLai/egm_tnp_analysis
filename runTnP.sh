#!/bin/bash

# $1 config: etc/config/settings_pho_run2022FG.py
# $2 id
# python tnpEGM_fitter.py $1 --flag $2 --checkBins
# python tnpEGM_fitter.py $1 --flag $2 --createBins
# python tnpEGM_fitter.py $1 --flag $2 --createHists
# python tnpEGM_fitter.py $1 --flag $2 --doFit
# python tnpEGM_fitter.py $1 --flag $2 --sumUp

baseDir="/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src/egm_tnp_analysis"

# sh $baseDir/run.sh "$baseDir/etc/config/settings_resolve_pho_2022preEE.py" passingCustomCutBased
sh $baseDir/run.sh egm_tnp_analysis.etc.config.settings_resolve_pho_2022preEE passingCustomCutBased_2022preEE
# BUILD_CPP=1 sh $baseDir/run.sh egm_tnp_analysis.etc.config.settings_resolve_pho_2022preEE passingCustomCutBased_2022preEE