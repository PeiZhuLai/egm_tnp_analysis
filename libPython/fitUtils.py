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

def createWorkspaceForAltSig( sample, tnpBin, tnpWorkspaceParam, preserve_params_from_mc=None ):
    """
    根據 MC 參考檔案的 RooFitResult 覆寫部分參數；若缺失則保持原樣。
    為避免多程序修改同一列表，使用複本後再回傳。
    """
    # 使用複本避免 multiprocessing 共享列表被就地修改
    localParams = list(tnpWorkspaceParam)
    preserve_params_from_mc = set(preserve_params_from_mc or [])

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

    # 只有真的收斂過的 MC 擬合才能拿來覆寫參數。若 MC 擬合從未最小化，
    # RooFit 會把參數留在初始值、誤差全部歸零 —— 取它的 getVal() 等於把
    # 「初始猜測」當成擬合結果餵進 data 的 altSig，而且外觀完全正常。
    # 這正是先前 nominal 大量「假成功」的同一種模式，所以在此擋下。
    def _never_minimised(res):
        pars = res.floatParsFinal()
        n = pars.getSize()
        return bool(n) and all(pars.at(i).getError() == 0.0 for i in range(n))

    if _never_minimised(fitresP) or _never_minimised(fitresF):
        logging.warning(
            f"MC 參考擬合未收斂（參數誤差全為 0）: {tnpBin['name']} @ {fileref} "
            f"→ 不用它覆寫 altSig 參數，改用設定檔的初始值"
        )
        filemc.Close()
        return localParams

    listOfParam = ['nF','alphaF','nP','alphaP','sigmaP','sigmaF','sigmaP_2','sigmaF_2','meanGF','sigmaGF','sigFracF','meanGP','sigmaGP','sigFracP']

    # 失敗樣本參數
    fitParF = fitresF.floatParsFinal()
    for ipar in range(len(fitParF)):
        pName = fitParF[ipar].GetName()
        if pName in listOfParam:
            if pName in preserve_params_from_mc:
                logging.warning(f'保留手動設定 {pName}，不使用 MC 覆寫')
                continue
            logging.warning(f'覆寫 {pName} -> {fitParF[ipar].getVal():2.3f}')
            _removeAndAppend(pName, fitParF[ipar].getVal())

    # 通過樣本參數
    fitParP = fitresP.floatParsFinal()
    for ipar in range(len(fitParP)):
        pName = fitParP[ipar].GetName()
        if pName in listOfParam:
            if pName in preserve_params_from_mc:
                logging.warning(f'保留手動設定 {pName}，不使用 MC 覆寫')
                continue
            logging.warning(f'覆寫 {pName} -> {fitParP[ipar].getVal():2.3f}')
            _removeAndAppend(pName, fitParP[ipar].getVal())

    filemc.Close()
    return localParams

#############################################################
########## nominal fitter
#############################################################
def _applyBkgModel(lines, bkgModel=None):
    """把 nominal / altSig 的 RooCMSShape 背景換成別的模型。

    預設（None / 'cmsshape'）原封不動回傳，所以既有 measurement 一律不受影響。

    'exp' 換成單參數 RooExponential，settings 要改為提供 alphaBkgP / alphaBkgF。
    刻意不叫 alphaP/alphaF：altSig 的 alphaP 是 DSCB 的尾巴參數、altBkg 的 alphaP
    是它自己的背景斜率，兩個都會撞名（altSigBkg 用 alphaP_2 正是為了避開）。
    這是給 phcsev 用的：那批是 Z->mumugamma，m(mumugamma) 被選擇釘在 80-100 GeV，
    在一個幾乎全是峰的 20 GeV 窗裡，RooCMSShape 的 4 個參數(acms/beta/gamma/peak)
    不可能被決定，而且它的 erfc turn-on 本身就長得像一個峰，會直接冒充訊號。
    """
    if bkgModel in (None, '', 'cmsshape', 'RooCMSShape'):
        return lines
    if bkgModel in ('exp', 'exponential', 'RooExponential'):
        out = []
        for l in lines:
            if l.startswith('RooCMSShape::bkgPass'):
                out.append("Exponential::bkgPass(x, alphaBkgP)")
            elif l.startswith('RooCMSShape::bkgFail'):
                out.append("Exponential::bkgFail(x, alphaBkgF)")
            else:
                out.append(l)
        return out
    raise ValueError("unknown tnpBkgModel %r (use 'cmsshape' or 'exp')" % (bkgModel,))


def histFitterNominal( sample, tnpBin, tnpWorkspaceParam, isaddGaus=0, bin_index=None, fitRange=None, bkgModel=None ):

    tnpWorkspaceFunc = [
        "Gaussian::sigResPass(x,meanP,sigmaP)",
        "Gaussian::sigResFail(x,meanF,sigmaF)",
        "RooCMSShape::bkgPass(x, acmsP, betaP, gammaP, peakP)",
        "RooCMSShape::bkgFail(x, acmsF, betaF, gammaF, peakF)",
        ]
    tnpWorkspaceFunc = _applyBkgModel(tnpWorkspaceFunc, bkgModel)
    ## optional 2nd Gaussian on the FAILING signal to absorb the low-mass (FSR/DY)
    ## shoulder: pdfFail = sigFracF*(template⊗Gauss) + (1-sigFracF)*sigGaussFail, both
    ## counted as signal (nSigF). Needs meanGF/sigmaGF in the param list (config).
    if isaddGaus==1:
        tnpWorkspaceFunc += [ "Gaussian::sigGaussFail(x,meanGF,sigmaGF)", ]
        if not any(str(_p).startswith("sigFracF") for _p in tnpWorkspaceParam):
            tnpWorkspaceFunc += [ "sigFracF[0.5,0.0,1.0]", ]
    tnpWorkspaceFunc += _passShoulderLines( tnpWorkspaceParam )

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
    # 擬合範圍：預設沿用 histFitter.C 寫死的 60-120；settings 設了 fitMassRange 才收窄。
    if fitRange:
        fitter.setFitRange( float(fitRange[0]), float(fitRange[1]) )
    
    ## generated Z LineShape
    if isaddGaus==1:
        ## addGaus 模式: PASSING 用 MC template(Pass,乾淨隔離電子峰,無 shoulder,配 data 峰形最好);
        ## FAILING 用通用 gen-level lineshape(無 template 過量 shoulder)+ sigGaussFail 補真實 shoulder。
        fileP = rt.TFile(sample.mcRef.histFile,'read')
        histZLineShapeP = fileP.Get('%s_Pass'%tnpBin['name'])
        fileG = rt.TFile('etc/inputs/ZeeGenLevel.root','read')
        histZLineShapeF = fileG.Get('Mass')
        fitter.setZLineShapes(histZLineShapeP,histZLineShapeF)
        fileP.Close()
        fileG.Close()
    else:
        ## for high pT change the failing spectra to any probe to get statistics
        fileTruth  = rt.TFile(sample.mcRef.histFile,'read')
        histZLineShapeP = fileTruth.Get('%s_Pass'%tnpBin['name'])
        histZLineShapeF = fileTruth.Get('%s_Fail'%tnpBin['name'])
        if ptMin( tnpBin ) > minPtForSwitch:
            histZLineShapeF = fileTruth.Get('%s_Pass'%tnpBin['name'])
        fitter.setZLineShapes(histZLineShapeP,histZLineShapeF)
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
def histFitterAltSig(
    sample,
    tnpBin,
    tnpWorkspaceParam,
    isaddGaus=0,
    bin_index=None,
    preserve_params_from_mc=None,
    fitRange=None,
    bkgModel=None,
):

    tnpWorkspacePar = createWorkspaceForAltSig(
        sample,
        tnpBin,
        tnpWorkspaceParam,
        preserve_params_from_mc=preserve_params_from_mc,
    )

    tnpWorkspaceFunc = [
        "tailLeft[1]",
        "RooCBExGaussShapeTNP::sigResPass(x,meanP,expr('sqrt(sigmaP*sigmaP+sosP*sosP)',{sigmaP,sosP}),alphaP,nP, expr('sqrt(sigmaP_2*sigmaP_2+sosP*sosP)',{sigmaP_2,sosP}),tailLeft)",
        "RooCBExGaussShapeTNP::sigResFail(x,meanF,expr('sqrt(sigmaF*sigmaF+sosF*sosF)',{sigmaF,sosF}),alphaF,nF, expr('sqrt(sigmaF_2*sigmaF_2+sosF*sosF)',{sigmaF_2,sosF}),tailLeft)",
        "RooCMSShape::bkgPass(x, acmsP, betaP, gammaP, peakP)",
        "RooCMSShape::bkgFail(x, acmsF, betaF, gammaF, peakF)",
        ]
    tnpWorkspaceFunc = _applyBkgModel(tnpWorkspaceFunc, bkgModel)
    if isaddGaus==1:
        tnpWorkspaceFunc += [ "Gaussian::sigGaussFail(x,meanGF,sigmaGF)", ]
        # 原本這裡有 `sample.isMC and` 的守衛：設計上 data 的 sigFracF 應該由
        # createWorkspaceForAltSig 從 MC 參考檔搬過來（它會 append 成 sigFracF[值]）。
        # 但只要 MC 參考檔是在還沒開 addGaus 的時候擬合的，裡面就沒有 sigFracF，
        # data 端於是誰都沒建立它，histFitter.C 的
        #   SUM::pdfFail(expr('sigFracF*nSigF',...)...)
        # 建不起來 —— RooFit 只印兩行 ERROR，然後**安靜地退回沒有 shoulder 的
        # pdf**：擬合照跑、return 0、結果和沒加 gaus 時逐位元相同。
        # (2026-09-07 實測 elminiIso0p15_gap_2024 bin02：MC 參考檔是 8/6 產的，
        #  加了 addGaus 之後 nSigP/nSigF/meanF/sigmaF 四個數字完全沒變。)
        # 拿掉守衛之後：MC 有提供就照用（下面的 not any(...) 會擋掉重複建立，
        # 既有行為逐位元不變），沒提供才讓 data 自己浮動 —— 總比 pdf 靜默壞掉好。
        if not any(str(_p).startswith("sigFracF") for _p in tnpWorkspaceParam):
            tnpWorkspaceFunc += [ "sigFracF[0.5,0.0,1.0]", ]
    tnpWorkspaceFunc += _passShoulderLines( tnpWorkspaceParam )

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
    # 擬合範圍：預設沿用 histFitter.C 寫死的 60-120；settings 設了 fitMassRange 才收窄。
    if fitRange:
        fitter.setFitRange( float(fitRange[0]), float(fitRange[1]) )
    
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
            'preserved_params_from_mc': sorted(preserve_params_from_mc or []),
        },
    )



#############################################################
########## alternate background fitter
#############################################################
def _passShoulderLines( tnpWorkspaceParam ):
    """Passing-leg shoulder Gaussian, opt-in from the settings file.

    The shoulder component existed only on the failing leg. But the low-mass tail
    it describes comes from the MC template, and the same template feeds both legs,
    so a bin whose failing leg needs it can need it on the passing leg too.
    Measured on elid_nongap_2026 bin08 (eta -2.50..-2.00, ET 20-35): the passing
    residuals carry the same structure as the failing ones -- 60-65 GeV -50%,
    70-75 GeV +65%, 7 slices past 5 sigma.

    Opt-in by design: the lines are emitted only when the settings declared meanGP,
    so every existing configuration is untouched (verified bit-for-bit on b12,
    nSigP 364838.3434 -> 364838.3433). histFitter.C likewise builds the three-way
    pdfPass only when sigGaussPass exists.
    """
    if not any(str(_p).startswith("meanGP") for _p in tnpWorkspaceParam):
        return []
    lines = [ "Gaussian::sigGaussPass(x,meanGP,sigmaGP)" ]
    if not any(str(_p).startswith("sigFracP") for _p in tnpWorkspaceParam):
        lines += [ "sigFracP[0.5,0.0,1.0]" ]
    return lines


def _altBkgShapeLines( bkgModel, tnpWorkspaceParam ):
    """Background pdf lines for the alternate-background fit.

    Default stays the single-parameter RooExponential this fit has always used --
    passing bkgModel=None reproduces the previous behaviour exactly.

    'bernsteinN' is the escape hatch for bins where one exponential parameter
    provably cannot describe the failing spectrum. Measured on
    elid_nongap_2024 altBkg bin03/bin04 (et 15-20): the data falls only 23% over
    60->80 GeV but by a factor 5 over 90->115. A single exponential must split the
    difference -- alphaF settled at -0.0332, which is far too steep at low mass and
    far too flat at high mass -- and the failing signal width then rails at its
    upper bound trying to make up the shortfall. A Bernstein polynomial adds the
    second shape degree of freedom while staying a genuinely *different* model from
    the nominal RooCMSShape, so the alternate-background systematic still means
    something. (Switching those bins to CMSShape would make altBkg identical to
    nominal and the systematic would collapse to zero.)

    Bernstein coefficients are non-negative by construction, so the pdf cannot go
    negative the way a free polynomial would.
    """
    if not bkgModel:
        return [
            "Exponential::bkgPass(x, alphaP)",
            "Exponential::bkgFail(x, alphaF)",
            ]

    # A bare string applies to both legs; a dict switches one leg only. Usually only
    # the failing leg needs it -- the passing background is a couple of percent and
    # its exponential is fine, so there is no reason to disturb a working fit.
    if isinstance(bkgModel, dict):
        per_side = {'P': bkgModel.get('pass'), 'F': bkgModel.get('fail')}
    else:
        per_side = {'P': bkgModel, 'F': bkgModel}

    lines = []
    coeffs = {}
    for side in ('P', 'F'):
        long_side = 'Pass' if side == 'P' else 'Fail'
        model = per_side.get(side)
        if not model:
            lines.append('Exponential::bkg%s(x, alpha%s)' % (long_side, side))
            continue
        model = str(model).strip().lower()
        if not model.startswith('bernstein'):
            raise ValueError('unknown altBkg background model: %s' % model)
        try:
            order = int(model[len('bernstein'):])
        except ValueError:
            raise ValueError('bernstein model needs an order, e.g. bernstein2: %s' % model)
        if order < 1 or order > 6:
            raise ValueError('bernstein order out of range (1-6): %s' % model)
        names = []
        for i in range(order + 1):
            name = 'b%s%d' % (side, i)
            names.append(name)
            # Only declare a coefficient the settings file has not already provided,
            # so a per-bin tune can narrow the range the same way it does for any
            # other parameter.
            if not any(str(_p).startswith('%s[' % name) for _p in tnpWorkspaceParam):
                coeffs[name] = '%s[0.5,0.,20.]' % name
        lines.append('Bernstein::bkg%s(x, {%s})' % (long_side, ', '.join(names)))
    return [coeffs[k] for k in sorted(coeffs)] + lines


def histFitterAltBkg( sample, tnpBin, tnpWorkspaceParam, isaddGaus=0, bin_index=None, bkgModel=None, fitRange=None ):

    tnpWorkspaceFunc = [
        "Gaussian::sigResPass(x,meanP,sigmaP)",
        "Gaussian::sigResFail(x,meanF,sigmaF)",
        ] + _altBkgShapeLines( bkgModel, tnpWorkspaceParam )
    if isaddGaus==1:
        tnpWorkspaceFunc += [ "Gaussian::sigGaussFail(x,meanGF,sigmaGF)", ]
        if not any(str(_p).startswith("sigFracF") for _p in tnpWorkspaceParam):
            tnpWorkspaceFunc += [ "sigFracF[0.5,0.0,1.0]", ]
    tnpWorkspaceFunc += _passShoulderLines( tnpWorkspaceParam )

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
    # 擬合範圍：預設沿用 histFitter.C 寫死的 60-120；settings 設了 fitMassRange 才收窄。
    if fitRange:
        fitter.setFitRange( float(fitRange[0]), float(fitRange[1]) )
#    fitter.setFitRange(65,115)

    ## generated Z LineShape
    if isaddGaus==1:
        ## addGaus 模式: PASSING 用 MC template(乾淨峰); FAILING 用通用 lineshape + sigGaussFail 補 shoulder。
        fileP = rt.TFile(sample.mcRef.histFile,'read')
        histZLineShapeP = fileP.Get('%s_Pass'%tnpBin['name'])
        fileG = rt.TFile('etc/inputs/ZeeGenLevel.root','read')
        histZLineShapeF = fileG.Get('Mass')
        fitter.setZLineShapes(histZLineShapeP,histZLineShapeF)
        fileP.Close()
        fileG.Close()
    else:
        ## for high pT change the failing spectra to any probe to get statistics
        fileTruth = rt.TFile(sample.mcRef.histFile,'read')
        histZLineShapeP = fileTruth.Get('%s_Pass'%tnpBin['name'])
        histZLineShapeF = fileTruth.Get('%s_Fail'%tnpBin['name'])
        if ptMin( tnpBin ) > minPtForSwitch:
            histZLineShapeF = fileTruth.Get('%s_Pass'%tnpBin['name'])
        fitter.setZLineShapes(histZLineShapeP,histZLineShapeF)
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
def histFitterAltSigBkg( sample, tnpBin, tnpWorkspaceParam, isaddGaus=0, bin_index=None, fitRange=None):


    tnpWorkspaceFunc = [
        "tailLeft[1]",
        "RooCBExGaussShapeTNP::sigResPass(x,meanP,expr('sqrt(sigmaP*sigmaP+sosP*sosP)',{sigmaP,sosP}),alphaP,nP, expr('sqrt(sigmaP_2*sigmaP_2+sosP*sosP)',{sigmaP_2,sosP}),tailLeft)",
        "RooCBExGaussShapeTNP::sigResFail(x,meanF,expr('sqrt(sigmaF*sigmaF+sosF*sosF)',{sigmaF,sosF}),alphaF,nF, expr('sqrt(sigmaF_2*sigmaF_2+sosF*sosF)',{sigmaF_2,sosF}),tailLeft)",
        "Exponential::bkgPass(x, alphaP_2)",
        "Exponential::bkgFail(x, alphaF_2)",
        ]
    ## optional 2nd Gaussian on FAILING signal to absorb the low-mass FSR/DY shoulder
    ## (altSigBkg 的 signal 是解析 DSCB,與 altSig 同 → addGaus 有效)。需 meanGF/sigmaGF in config.
    if isaddGaus==1:
        tnpWorkspaceFunc += [ "Gaussian::sigGaussFail(x,meanGF,sigmaGF)", ]
        if not any(str(_p).startswith("sigFracF") for _p in tnpWorkspaceParam):
            tnpWorkspaceFunc += [ "sigFracF[0.5,0.0,1.0]", ]
    tnpWorkspaceFunc += _passShoulderLines( tnpWorkspaceParam )

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
    # 擬合範圍：預設沿用 histFitter.C 寫死的 60-120；settings 設了 fitMassRange 才收窄。
    if fitRange:
        fitter.setFitRange( float(fitRange[0]), float(fitRange[1]) )
#    fitter.setFitRange(65,115)


    ## generated Z LineShape
    ## for high pT change the failing spectra to any probe to get statistics
    if isaddGaus==1:
        ## addGaus 模式(2026-07-18): PASSING 用 MC template Pass(乾淨隔離電子峰,勿動 passing);
        ## FAILING 用 generic gen-level(無 template FSR shoulder),讓 addGaus sigGaussFail 乾淨做
        ## failing shoulder。template FSR shoulder>data → DSCB 尾 overshoot+starve 主峰;此組合解之。
        ## (2026-07-18b 修正: 原先 pass+fail 都用 generic 會壞 passing peak,改回 pass=template)
        fileP = rt.TFile(sample.mcRef.histFile,'read')
        histZLineShapeP = fileP.Get('%s_Pass'%tnpBin['name'])
        fileG = rt.TFile('etc/inputs/ZeeGenLevel.root','read')
        histZLineShapeF = fileG.Get('Mass')
        fitter.setZLineShapes(histZLineShapeP,histZLineShapeF)
        fileP.Close(); fileG.Close()
    else:
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
    fitter.setWorkspace( workspace, isaddGaus )

    title = tnpBin['title'].replace(';',' - ')
    title = title.replace('probe_sc_eta','#eta_{SC}')
    title = title.replace('probe_Ele_pt','p_{T}')
    fitter.fits(sample.mcTruth,sample.isMC,title, isaddGaus)
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
