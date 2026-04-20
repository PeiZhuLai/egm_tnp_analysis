import ROOT as rt
rt.gROOT.LoadMacro('./libCpp/histFitter.C+')
rt.gROOT.LoadMacro('./libCpp/RooCBExGaussShapeTNP.cc+')
rt.gROOT.LoadMacro('./libCpp/RooCMSShape.cc+')
rt.gROOT.SetBatch(1)

from ROOT import tnpFitter

import re
import math
import os
import json
import ctypes
from array import array
from datetime import datetime, timezone
import logging
logging.basicConfig(level=logging.WARNING, format='[fitUtils] %(message)s')

minPtForSwitch = 70

def ptMin( tnpBin ):
    ptmin = 1
    if tnpBin['name'].find('pt_') >= 0:
        ptmin = float(tnpBin['name'].split('pt_')[1].split('p')[0])
    elif tnpBin['name'].find('et_') >= 0:
        ptmin = float(tnpBin['name'].split('et_')[1].split('p')[0])
    return ptmin

def _safe_float(value):
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out

def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def _jsonable(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)

def _integral_and_error(hist, bin1, bin2):
    try:
        err = array('d', [0.0])
        integral = hist.IntegralAndError(bin1, bin2, err)
        return float(integral), float(err[0])
    except TypeError:
        err = ctypes.c_double(0.0)
        integral = hist.IntegralAndError(bin1, bin2, err)
        return float(integral), float(err.value)

def _histogram_summary(hist, fit_min=60.0, fit_max=120.0):
    if not hist:
        return None

    axis = hist.GetXaxis()
    full_bin1 = 1
    full_bin2 = axis.GetNbins()
    fit_bin1 = axis.FindFixBin(fit_min)
    fit_bin2 = axis.FindFixBin(fit_max)
    if axis.GetBinLowEdge(fit_bin2) >= fit_max and fit_bin2 > fit_bin1:
        fit_bin2 -= 1

    integral_full, integral_full_err = _integral_and_error(hist, full_bin1, full_bin2)
    integral_fit, integral_fit_err = _integral_and_error(hist, fit_bin1, fit_bin2)
    maximum_bin = hist.GetMaximumBin()

    return {
        'entries': _safe_float(hist.GetEntries()),
        'integral_full': integral_full,
        'integral_full_error': integral_full_err,
        'integral_fit_window': integral_fit,
        'integral_fit_window_error': integral_fit_err,
        'mean': _safe_float(hist.GetMean()),
        'rms': _safe_float(hist.GetRMS()),
        'maximum_bin_center': _safe_float(axis.GetBinCenter(maximum_bin)),
        'maximum_bin_content': _safe_float(hist.GetBinContent(maximum_bin)),
        'fit_window': {
            'min': fit_min,
            'max': fit_max,
            'bin1': fit_bin1,
            'bin2': fit_bin2,
        },
    }

def _parse_workspace_parameter(raw_value):
    parsed = {'raw': raw_value}
    if not isinstance(raw_value, str):
        return parsed

    match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$', raw_value.strip())
    if not match:
        return parsed

    name = match.group(1)
    payload = [item.strip() for item in match.group(2).split(',') if item.strip()]
    parsed['name'] = name
    parsed['tokens'] = payload
    if len(payload) >= 1:
        parsed['value'] = _safe_float(payload[0])
    if len(payload) >= 2:
        parsed['min'] = _safe_float(payload[1])
    if len(payload) >= 3:
        parsed['max'] = _safe_float(payload[2])
    return parsed

def _workspace_overrides(requested, effective):
    requested_map = {}
    effective_map = {}

    for raw_value in requested:
        parsed = _parse_workspace_parameter(raw_value)
        name = parsed.get('name')
        if name:
            requested_map[name] = parsed

    for raw_value in effective:
        parsed = _parse_workspace_parameter(raw_value)
        name = parsed.get('name')
        if name:
            effective_map[name] = parsed

    overrides = []
    for name in sorted(set(requested_map.keys()) | set(effective_map.keys())):
        before = requested_map.get(name)
        after = effective_map.get(name)
        if before == after:
            continue
        overrides.append({
            'name': name,
            'requested': before,
            'effective': after,
        })
    return overrides

def _get_fit_result(rootfile, key):
    obj = rootfile.Get(key)
    if not obj:
        return None
    if hasattr(obj, 'floatParsFinal'):
        return obj
    try:
        casted = rt.RooFitResult._cast_(obj)
        if casted and hasattr(casted, 'floatParsFinal'):
            return casted
    except Exception:
        pass
    return None

def _roofit_arglist_to_list(arglist):
    if not arglist:
        return []

    parameters = []
    for idx in range(arglist.getSize()):
        par = arglist[idx]
        entry = {
            'name': par.GetName(),
        }
        if hasattr(par, 'getVal'):
            entry['value'] = _safe_float(par.getVal())
        if hasattr(par, 'getError'):
            entry['error'] = _safe_float(par.getError())
        if hasattr(par, 'getMin'):
            entry['min'] = _safe_float(par.getMin())
        if hasattr(par, 'getMax'):
            entry['max'] = _safe_float(par.getMax())
        if hasattr(par, 'isConstant'):
            entry['isConstant'] = bool(par.isConstant())
        parameters.append(entry)
    return parameters

def _find_parameter(parameters, name):
    for parameter in parameters:
        if parameter.get('name') == name:
            return parameter
    return None

def _roofit_result_summary(fit_result):
    if fit_result is None:
        return None

    summary = {
        'status': _safe_int(fit_result.status()) if hasattr(fit_result, 'status') else None,
        'covQual': _safe_int(fit_result.covQual()) if hasattr(fit_result, 'covQual') else None,
        'edm': _safe_float(fit_result.edm()) if hasattr(fit_result, 'edm') else None,
        'minNll': _safe_float(fit_result.minNll()) if hasattr(fit_result, 'minNll') else None,
        'numInvalidNLL': _safe_int(fit_result.numInvalidNLL()) if hasattr(fit_result, 'numInvalidNLL') else None,
        'floatParsInit': _roofit_arglist_to_list(fit_result.floatParsInit()) if hasattr(fit_result, 'floatParsInit') else [],
        'floatParsFinal': _roofit_arglist_to_list(fit_result.floatParsFinal()) if hasattr(fit_result, 'floatParsFinal') else [],
    }
    return summary

def _fit_quality_flag(summary):
    if not summary:
        return 'missing'
    status = summary.get('status')
    cov_qual = summary.get('covQual')
    if status == 0 and cov_qual is not None and cov_qual >= 2:
        return 'ok'
    return 'check'

def _efficiency_from_fit_results(pass_summary, fail_summary):
    if not pass_summary or not fail_summary:
        return None

    n_sig_p = _find_parameter(pass_summary.get('floatParsFinal', []), 'nSigP')
    n_sig_f = _find_parameter(fail_summary.get('floatParsFinal', []), 'nSigF')
    if not n_sig_p or not n_sig_f:
        return None

    n_p = n_sig_p.get('value')
    n_f = n_sig_f.get('value')
    e_p = n_sig_p.get('error') or 0.0
    e_f = n_sig_f.get('error') or 0.0
    if n_p is None or n_f is None:
        return None

    denom = n_p + n_f
    if denom <= 0:
        return {
            'nSigP': n_sig_p,
            'nSigF': n_sig_f,
            'efficiency': None,
            'efficiency_error': None,
        }

    efficiency = n_p / denom
    efficiency_error = math.sqrt(n_p * n_p * e_f * e_f + n_f * n_f * e_p * e_p) / (denom * denom)
    return {
        'nSigP': n_sig_p,
        'nSigF': n_sig_f,
        'efficiency': efficiency,
        'efficiency_error': efficiency_error,
    }

def _sanitize_path_component(value, default='unknown'):
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    text = re.sub(r'[^A-Za-z0-9._-]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('._-')
    return text or default

def _diagnostics_dir(sample, fit_type):
    flag_tag = _sanitize_path_component(getattr(sample, 'diagnosticsFlag', None), 'flag')
    sample_tag = _sanitize_path_component(sample.name, 'sample')
    fit_tag = _sanitize_path_component(fit_type, 'fit')
    return os.path.join(os.getcwd(), 'fit_diagnostics', flag_tag, sample_tag, fit_tag)

def _diagnostics_file(sample, fit_type, tnpBin):
    return os.path.join(_diagnostics_dir(sample, fit_type), '%s.json' % tnpBin['name'])

def _write_fit_diagnostics(sample, tnpBin, fit_type, fit_output_root, workspace_requested,
                           workspace_effective, workspace_functions, hist_pass_summary,
                           hist_fail_summary,
                           fit_metadata=None):
    os.makedirs(_diagnostics_dir(sample, fit_type), exist_ok=True)

    fit_result_pass = None
    fit_result_fail = None
    root_error = None
    rootfile = rt.TFile(fit_output_root, 'read')
    if not rootfile or rootfile.IsZombie():
        root_error = 'could_not_open_fit_output'
    else:
        fit_result_pass = _roofit_result_summary(_get_fit_result(rootfile, '%s_resP' % tnpBin['name']))
        fit_result_fail = _roofit_result_summary(_get_fit_result(rootfile, '%s_resF' % tnpBin['name']))
        rootfile.Close()

    payload = {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'fit_type': fit_type,
        'sample': {
            'name': sample.name,
            'isMC': bool(sample.isMC),
            'mcTruth': bool(sample.mcTruth),
            'histFile': getattr(sample, 'histFile', None),
            'mcRefHistFile': getattr(getattr(sample, 'mcRef', None), 'histFile', None),
            'fitOutputRoot': getattr(sample, fit_type, None),
            'fitOutputBinRoot': fit_output_root,
        },
        'bin': {
            'index': fit_metadata.get('bin_index') if fit_metadata else None,
            'name': tnpBin.get('name'),
            'title': tnpBin.get('title'),
            'cut': tnpBin.get('cut'),
            'vars': _jsonable(tnpBin.get('vars')),
        },
        'workspace': {
            'requested_raw': list(workspace_requested),
            'requested_parsed': [_parse_workspace_parameter(item) for item in workspace_requested],
            'effective_raw': list(workspace_effective),
            'effective_parsed': [_parse_workspace_parameter(item) for item in workspace_effective],
            'overrides': _workspace_overrides(workspace_requested, workspace_effective),
            'functions': list(workspace_functions),
        },
        'histograms': {
            'pass': hist_pass_summary,
            'fail': hist_fail_summary,
        },
        'fit_result': {
            'pass': fit_result_pass,
            'fail': fit_result_fail,
            'pass_quality': _fit_quality_flag(fit_result_pass),
            'fail_quality': _fit_quality_flag(fit_result_fail),
            'root_read_error': root_error,
        },
        'derived': _efficiency_from_fit_results(fit_result_pass, fit_result_fail),
        'fit_metadata': _jsonable(fit_metadata or {}),
    }

    diagnostics_path = _diagnostics_file(sample, fit_type, tnpBin)
    with open(diagnostics_path, 'w', encoding='utf-8') as handle:
        json.dump(_jsonable(payload), handle, indent=2, sort_keys=True)
        handle.write('\n')

    return diagnostics_path

def build_fit_diagnostics_summary(sample, fit_type, tnp_bins, selected_bin=-1):
    diagnostics_dir = _diagnostics_dir(sample, fit_type)
    os.makedirs(diagnostics_dir, exist_ok=True)

    entries = []
    for bin_index, tnpBin in enumerate(tnp_bins):
        if selected_bin >= 0 and bin_index != selected_bin:
            continue

        diagnostics_path = _diagnostics_file(sample, fit_type, tnpBin)
        entry = {
            'bin_index': bin_index,
            'bin_name': tnpBin.get('name'),
            'diagnostic_file': diagnostics_path,
            'present': os.path.exists(diagnostics_path),
        }

        if entry['present']:
            with open(diagnostics_path, 'r', encoding='utf-8') as handle:
                payload = json.load(handle)
            fit_result = payload.get('fit_result', {})
            derived = payload.get('derived', {}) or {}
            histograms = payload.get('histograms', {}) or {}
            hist_pass = histograms.get('pass', {}) or {}
            hist_fail = histograms.get('fail', {}) or {}
            pass_raw = hist_pass.get('integral_full', hist_pass.get('raw_integral'))
            fail_raw = hist_fail.get('integral_full', hist_fail.get('raw_integral'))
            pass_fit_window = hist_pass.get('integral_fit_window', hist_pass.get('fit_window_integral'))
            fail_fit_window = hist_fail.get('integral_fit_window', hist_fail.get('fit_window_integral'))
            pass_zero_stat = (pass_raw or 0) <= 0 and (pass_fit_window or 0) <= 0
            fail_zero_stat = (fail_raw or 0) <= 0 and (fail_fit_window or 0) <= 0
            attention_reasons = []

            if pass_zero_stat:
                attention_reasons.append('pass_zero_stat')
            if fail_zero_stat:
                attention_reasons.append('fail_zero_stat')
            if not fit_result.get('pass'):
                attention_reasons.append('missing_pass_fit_result')
            elif fit_result.get('pass_quality') != 'ok' and not pass_zero_stat:
                attention_reasons.append('bad_pass_fit')
            if not fit_result.get('fail'):
                attention_reasons.append('missing_fail_fit_result')
            elif fit_result.get('fail_quality') != 'ok' and not fail_zero_stat:
                attention_reasons.append('bad_fail_fit')

            entry.update({
                'pass_status': fit_result.get('pass', {}).get('status') if fit_result.get('pass') else None,
                'pass_covQual': fit_result.get('pass', {}).get('covQual') if fit_result.get('pass') else None,
                'fail_status': fit_result.get('fail', {}).get('status') if fit_result.get('fail') else None,
                'fail_covQual': fit_result.get('fail', {}).get('covQual') if fit_result.get('fail') else None,
                'pass_quality': fit_result.get('pass_quality'),
                'fail_quality': fit_result.get('fail_quality'),
                'efficiency': derived.get('efficiency'),
                'efficiency_error': derived.get('efficiency_error'),
                'nSigP': (derived.get('nSigP') or {}).get('value'),
                'nSigF': (derived.get('nSigF') or {}).get('value'),
                'hist_stats': {
                    'pass': {
                        'integral_full': pass_raw,
                        'integral_fit_window': pass_fit_window,
                    },
                    'fail': {
                        'integral_full': fail_raw,
                        'integral_fit_window': fail_fit_window,
                    },
                },
                'zero_stat_like': pass_zero_stat or fail_zero_stat,
                'attention_reasons': attention_reasons,
                'tuning_candidate': any(
                    reason in ('bad_pass_fit', 'bad_fail_fit', 'missing_pass_fit_result', 'missing_fail_fit_result')
                    for reason in attention_reasons
                ),
            })
            entry['needs_attention'] = bool(attention_reasons)
        else:
            entry['needs_attention'] = True
            entry['attention_reasons'] = ['missing_diagnostic']
            entry['zero_stat_like'] = False
            entry['tuning_candidate'] = True

        entries.append(entry)

    summary_path = os.path.join(diagnostics_dir, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as handle:
        json.dump({
            'sample': sample.name,
            'fit_type': fit_type,
            'selected_bin': selected_bin,
            'entries': entries,
        }, handle, indent=2, sort_keys=True)
        handle.write('\n')

    return summary_path

def createWorkspaceForAltSig( sample, tnpBin, tnpWorkspaceParam ):
    """
    根據 MC 參考檔案的 RooFitResult 覆寫部分參數；若缺失則保持原樣。
    為避免多程序修改同一列表，使用複本後再回傳。
    """
    # 使用複本避免 multiprocessing 共享列表被就地修改
    localParams = list(tnpWorkspaceParam)

    def _removeAndAppend(paramName, value):
        x = re.compile('%s.*?' % paramName)
        # 將 filter 結果轉成 list 再處理
        listToRM = list(filter(x.match, localParams))
        for old in listToRM:
            localParams.remove(old)
        localParams.append('%s[%2.3f]' % (paramName, value))

    # high pT 處理 tailLeft
    cbNList = ['tailLeft']
    ptmin = ptMin(tnpBin)
    if ptmin >= 35:
        for par in cbNList:
            x = re.compile('%s.*?' % par)
            listToRM = list(filter(x.match, localParams))
            for old in listToRM:
                logging.warning(f'remove {old}')
                localParams.remove(old)
            localParams.append('tailLeft[-1]')

    if sample.isMC:
        return localParams

    fileref = getattr(sample.mcRef, 'altSigFit', None)
    if not fileref or not os.path.exists(fileref):
        logging.warning(f'參考檔不存在或未設定: {fileref}')
        return localParams

    filemc = rt.TFile(fileref, 'read')
    if not filemc or filemc.IsZombie():
        logging.warning(f'無法開啟參考檔: {fileref}')
        return localParams

    # 安全取得 RooFitResult
    def _getFitResult(objName):
        obj = filemc.Get(objName)
        if not obj or not hasattr(obj, 'floatParsFinal'):
            logging.warning(f'缺少 RooFitResult 或型別不符: {objName}')
            return None
        return obj

    fitresP = _getFitResult(f"{tnpBin['name']}_resP")
    fitresF = _getFitResult(f"{tnpBin['name']}_resF")
    if not fitresP or not fitresF:
        filemc.Close()
        return localParams

    listOfParam = ['nF','alphaF','nP','alphaP','sigmaP','sigmaF','sigmaP_2','sigmaF_2','meanGF','sigmaGF','sigFracF']

    # 失敗樣本參數
    fitParF = fitresF.floatParsFinal()
    for ipar in range(len(fitParF)):
        pName = fitParF[ipar].GetName()
        if pName in listOfParam:
            logging.warning(f'覆寫 {pName} -> {fitParF[ipar].getVal():2.3f}')
            _removeAndAppend(pName, fitParF[ipar].getVal())

    # 通過樣本參數
    fitParP = fitresP.floatParsFinal()
    for ipar in range(len(fitParP)):
        pName = fitParP[ipar].GetName()
        if pName in listOfParam:
            logging.warning(f'覆寫 {pName} -> {fitParP[ipar].getVal():2.3f}')
            _removeAndAppend(pName, fitParP[ipar].getVal())

    filemc.Close()
    return localParams

#############################################################
########## nominal fitter
#############################################################
def histFitterNominal( sample, tnpBin, tnpWorkspaceParam, bin_index=None ):
        
    tnpWorkspaceFunc = [
        "Gaussian::sigResPass(x,meanP,sigmaP)",
        "Gaussian::sigResFail(x,meanF,sigmaF)",
        "RooCMSShape::bkgPass(x, acmsP, betaP, gammaP, peakP)",
        "RooCMSShape::bkgFail(x, acmsF, betaF, gammaF, peakF)",
        ]

    tnpWorkspace = []
    tnpWorkspace.extend(tnpWorkspaceParam)
    tnpWorkspace.extend(tnpWorkspaceFunc)
    
    ## init fitter
    infile = rt.TFile( sample.histFile, "read")
    hP = infile.Get('%s_Pass' % tnpBin['name'] )
    hF = infile.Get('%s_Fail' % tnpBin['name'] )
    if hP:
        hP.SetDirectory(0)
    if hF:
        hF.SetDirectory(0)
    hP_summary = _histogram_summary(hP)
    hF_summary = _histogram_summary(hF)
    fitter = tnpFitter( hP, hF, tnpBin['name'] )
    infile.Close()

    ## setup
    fitter.useMinos()
    rootpath = sample.nominalFit.replace('.root', '-%s.root' % tnpBin['name'])
    rootfile = rt.TFile(rootpath,'update')
    fitter.setOutputFile( rootfile )
    
    ## generated Z LineShape
    ## for high pT change the failing spectra to any probe to get statistics
    fileTruth  = rt.TFile(sample.mcRef.histFile,'read')
    histZLineShapeP = fileTruth.Get('%s_Pass'%tnpBin['name'])
    histZLineShapeF = fileTruth.Get('%s_Fail'%tnpBin['name'])
    if ptMin( tnpBin ) > minPtForSwitch: 
        histZLineShapeF = fileTruth.Get('%s_Pass'%tnpBin['name'])
#        fitter.fixSigmaFtoSigmaP()
    fitter.setZLineShapes(histZLineShapeP,histZLineShapeF)

    fileTruth.Close()

    ### set workspace
    workspace = rt.vector("string")()
    for iw in tnpWorkspace:
        workspace.push_back(iw)
    fitter.setWorkspace( workspace )

    title = tnpBin['title'].replace(';',' - ')
    title = title.replace('probe_sc_eta','#eta_{SC}')
    title = title.replace('probe_Ele_pt','p_{T}')
    fitter.fits(sample.mcTruth,sample.isMC,title)
    rootfile.Close()
    _write_fit_diagnostics(
        sample,
        tnpBin,
        'nominalFit',
        rootpath,
        tnpWorkspaceParam,
        tnpWorkspaceParam,
        tnpWorkspaceFunc,
        hP_summary,
        hF_summary,
        {
            'bin_index': bin_index,
            'fit_range': {'min': 60.0, 'max': 120.0},
            'fail_hist_uses_pass_hist': False,
            'truth_fail_template_uses_pass_hist': bool(ptMin(tnpBin) > minPtForSwitch),
            'truth_template_source': sample.mcRef.histFile,
        },
    )



#############################################################
########## alternate signal fitter
#############################################################
def histFitterAltSig( sample, tnpBin, tnpWorkspaceParam, isaddGaus=0, bin_index=None ):

    tnpWorkspacePar = createWorkspaceForAltSig( sample,  tnpBin, tnpWorkspaceParam )

    tnpWorkspaceFunc = [
        "tailLeft[1]",
        "RooCBExGaussShapeTNP::sigResPass(x,meanP,expr('sqrt(sigmaP*sigmaP+sosP*sosP)',{sigmaP,sosP}),alphaP,nP, expr('sqrt(sigmaP_2*sigmaP_2+sosP*sosP)',{sigmaP_2,sosP}),tailLeft)",
        "RooCBExGaussShapeTNP::sigResFail(x,meanF,expr('sqrt(sigmaF*sigmaF+sosF*sosF)',{sigmaF,sosF}),alphaF,nF, expr('sqrt(sigmaF_2*sigmaF_2+sosF*sosF)',{sigmaF_2,sosF}),tailLeft)",
        "RooCMSShape::bkgPass(x, acmsP, betaP, gammaP, peakP)",
        "RooCMSShape::bkgFail(x, acmsF, betaF, gammaF, peakF)",
        ]
    if isaddGaus==1:
        tnpWorkspaceFunc += [ "Gaussian::sigGaussFail(x,meanGF,sigmaGF)", ]
        if sample.isMC:
            tnpWorkspaceFunc += [ "sigFracF[0.5,0.0,1.0]", ]

    tnpWorkspace = []
    tnpWorkspace.extend(tnpWorkspacePar)
    tnpWorkspace.extend(tnpWorkspaceFunc)
        
    ## init fitter
    infile = rt.TFile( sample.histFile, "read")
    hP = infile.Get('%s_Pass' % tnpBin['name'] )
    hF = infile.Get('%s_Fail' % tnpBin['name'] )
    ## for high pT change the failing spectra to passing probe to get statistics 
    ## MC only: this is to get MC parameters in data fit!
    if sample.isMC and ptMin( tnpBin ) > minPtForSwitch:     
        hF = infile.Get('%s_Pass' % tnpBin['name'] )
    if hP:
        hP.SetDirectory(0)
    if hF:
        hF.SetDirectory(0)
    hP_summary = _histogram_summary(hP)
    hF_summary = _histogram_summary(hF)
    fitter = tnpFitter( hP, hF, tnpBin['name'] )
#    fitter.fixSigmaFtoSigmaP()
    infile.Close()

    ## setup
    rootpath = sample.altSigFit.replace('.root', '-%s.root' % tnpBin['name'])
    rootfile = rt.TFile(rootpath,'update')
    fitter.setOutputFile( rootfile )
    
    ## generated Z LineShape
    fileTruth = rt.TFile('etc/inputs/ZeeGenLevel.root','read')
    histZLineShape = fileTruth.Get('Mass')
    fitter.setZLineShapes(histZLineShape,histZLineShape)
    fileTruth.Close()

    ### set workspace
    workspace = rt.vector("string")()
    for iw in tnpWorkspace:
        workspace.push_back(iw)
    fitter.setWorkspace( workspace, isaddGaus )

    title = tnpBin['title'].replace(';',' - ')
    title = title.replace('probe_sc_eta','#eta_{SC}')
    title = title.replace('probe_Ele_pt','p_{T}')
    fitter.fits(sample.mcTruth,sample.isMC,title, isaddGaus)

    rootfile.Close()
    _write_fit_diagnostics(
        sample,
        tnpBin,
        'altSigFit',
        rootpath,
        tnpWorkspaceParam,
        tnpWorkspacePar,
        tnpWorkspaceFunc,
        hP_summary,
        hF_summary,
        {
            'bin_index': bin_index,
            'fit_range': {'min': 60.0, 'max': 120.0},
            'fail_hist_uses_pass_hist': bool(sample.isMC and ptMin(tnpBin) > minPtForSwitch),
            'truth_fail_template_uses_pass_hist': False,
            'truth_template_source': 'etc/inputs/ZeeGenLevel.root',
            'add_gaussian_fail_component': bool(isaddGaus),
        },
    )



#############################################################
########## alternate background fitter
#############################################################
def histFitterAltBkg( sample, tnpBin, tnpWorkspaceParam, bin_index=None ):

    tnpWorkspaceFunc = [
        "Gaussian::sigResPass(x,meanP,sigmaP)",
        "Gaussian::sigResFail(x,meanF,sigmaF)",
        "Exponential::bkgPass(x, alphaP)",
        "Exponential::bkgFail(x, alphaF)",
        ]

    tnpWorkspace = []
    tnpWorkspace.extend(tnpWorkspaceParam)
    tnpWorkspace.extend(tnpWorkspaceFunc)
            
    ## init fitter
    infile = rt.TFile(sample.histFile,'read')
    hP = infile.Get('%s_Pass' % tnpBin['name'] )
    hF = infile.Get('%s_Fail' % tnpBin['name'] )
    if hP:
        hP.SetDirectory(0)
    if hF:
        hF.SetDirectory(0)
    hP_summary = _histogram_summary(hP)
    hF_summary = _histogram_summary(hF)
    fitter = tnpFitter( hP, hF, tnpBin['name'] )
    infile.Close()

    ## setup
    rootpath = sample.altBkgFit.replace('.root', '-%s.root' % tnpBin['name'])
    rootfile = rt.TFile(rootpath,'update')
    fitter.setOutputFile( rootfile )
#    fitter.setFitRange(65,115)

    ## generated Z LineShape
    ## for high pT change the failing spectra to any probe to get statistics
    fileTruth = rt.TFile(sample.mcRef.histFile,'read')
    histZLineShapeP = fileTruth.Get('%s_Pass'%tnpBin['name'])
    histZLineShapeF = fileTruth.Get('%s_Fail'%tnpBin['name'])
    if ptMin( tnpBin ) > minPtForSwitch: 
        histZLineShapeF = fileTruth.Get('%s_Pass'%tnpBin['name'])
#        fitter.fixSigmaFtoSigmaP()
    fitter.setZLineShapes(histZLineShapeP,histZLineShapeF)
    fileTruth.Close()

    ### set workspace
    workspace = rt.vector("string")()
    for iw in tnpWorkspace:
        workspace.push_back(iw)
    fitter.setWorkspace( workspace )

    title = tnpBin['title'].replace(';',' - ')
    title = title.replace('probe_sc_eta','#eta_{SC}')
    title = title.replace('probe_Ele_pt','p_{T}')
    fitter.fits(sample.mcTruth,sample.isMC,title)
    rootfile.Close()
    _write_fit_diagnostics(
        sample,
        tnpBin,
        'altBkgFit',
        rootpath,
        tnpWorkspaceParam,
        tnpWorkspaceParam,
        tnpWorkspaceFunc,
        hP_summary,
        hF_summary,
        {
            'bin_index': bin_index,
            'fit_range': {'min': 60.0, 'max': 120.0},
            'fail_hist_uses_pass_hist': False,
            'truth_fail_template_uses_pass_hist': bool(ptMin(tnpBin) > minPtForSwitch),
            'truth_template_source': sample.mcRef.histFile,
        },
    )


#############################################################
########## alternate signal+background fitter
#############################################################
def histFitterAltSigBkg( sample, tnpBin, tnpWorkspaceParam, bin_index=None):


    tnpWorkspaceFunc = [
        "tailLeft[1]",
        "RooCBExGaussShapeTNP::sigResPass(x,meanP,expr('sqrt(sigmaP*sigmaP+sosP*sosP)',{sigmaP,sosP}),alphaP,nP, expr('sqrt(sigmaP_2*sigmaP_2+sosP*sosP)',{sigmaP_2,sosP}),tailLeft)",
        "RooCBExGaussShapeTNP::sigResFail(x,meanF,expr('sqrt(sigmaF*sigmaF+sosF*sosF)',{sigmaF,sosF}),alphaF,nF, expr('sqrt(sigmaF_2*sigmaF_2+sosF*sosF)',{sigmaF_2,sosF}),tailLeft)",
        "Exponential::bkgPass(x, alphaP_2)",
        "Exponential::bkgFail(x, alphaF_2)",
        ]

    tnpWorkspace = []
    tnpWorkspace.extend(tnpWorkspaceParam)
    tnpWorkspace.extend(tnpWorkspaceFunc)
            
    ## init fitter
    infile = rt.TFile(sample.histFile,'read')
    hP = infile.Get('%s_Pass' % tnpBin['name'] )
    hF = infile.Get('%s_Fail' % tnpBin['name'] )
    if hP:
        hP.SetDirectory(0)
    if hF:
        hF.SetDirectory(0)
    hP_summary = _histogram_summary(hP)
    hF_summary = _histogram_summary(hF)
    fitter = tnpFitter( hP, hF, tnpBin['name'] )
    infile.Close()
    
    ## setup
    rootpath = sample.altSigBkgFit.replace('.root', '-%s.root' % tnpBin['name'])
    rootfile = rt.TFile(rootpath,'update')
    fitter.setOutputFile( rootfile )
#    fitter.setFitRange(65,115)


    ## generated Z LineShape
    ## for high pT change the failing spectra to any probe to get statistics
    fileTruth = rt.TFile(sample.mcRef.histFile,'read')
    histZLineShapeP = fileTruth.Get('%s_Pass'%tnpBin['name'])
    histZLineShapeF = fileTruth.Get('%s_Fail'%tnpBin['name'])
    if ptMin( tnpBin ) > minPtForSwitch: 
        histZLineShapeF = fileTruth.Get('%s_Pass'%tnpBin['name'])
#        fitter.fixSigmaFtoSigmaP()
    fitter.setZLineShapes(histZLineShapeP,histZLineShapeF)
    fileTruth.Close()

    ### set workspace
    workspace = rt.vector("string")()
    for iw in tnpWorkspace:
        workspace.push_back(iw)
    fitter.setWorkspace( workspace )

    title = tnpBin['title'].replace(';',' - ')
    title = title.replace('probe_sc_eta','#eta_{SC}')
    title = title.replace('probe_Ele_pt','p_{T}')
    fitter.fits(sample.mcTruth,sample.isMC,title)
    rootfile.Close()
    _write_fit_diagnostics(
        sample,
        tnpBin,
        'altSigBkgFit',
        rootpath,
        tnpWorkspaceParam,
        tnpWorkspaceParam,
        tnpWorkspaceFunc,
        hP_summary,
        hF_summary,
        {
            'bin_index': bin_index,
            'fit_range': {'min': 60.0, 'max': 120.0},
            'fail_hist_uses_pass_hist': False,
            'truth_fail_template_uses_pass_hist': bool(ptMin(tnpBin) > minPtForSwitch),
            'truth_template_source': sample.mcRef.histFile,
        },
    )
