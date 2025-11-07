#!/bin/bash
echo $PWD
echo "Setting environment"

workdir="$(pwd)"
cmssw_path="$CMSSW_BASE/src";
cd $cmssw_path; cmsenv; cd $workdir
export PYTHONPATH=$workdir;
# make

# $1 config: etc/config/settings_pho_run2022FG.py
# $2 id

baseDir="/afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src/egm_tnp_analysis"

python $baseDir/tnpEGM_fitter.py $1 --flag $2 --checkBins
python $baseDir/tnpEGM_fitter.py $1 --flag $2 --createBins
python $baseDir/tnpEGM_fitter.py $1 --flag $2 --createHists
python $baseDir/tnpEGM_fitter.py $1 --flag $2 --doFit
python $baseDir/tnpEGM_fitter.py $1 --flag $2 --sumUp
