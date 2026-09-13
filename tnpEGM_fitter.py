# -*- coding: utf-8 -*-
### python specific import
import argparse
import os
import sys
import pickle
import shutil
import tempfile
import time
from multiprocessing import Pool
import math, json


def _is_eos_path(path):
    return os.path.abspath(path).startswith('/eos/')


def _copy_file_with_retries(src, dst, attempts=3):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    last_error = None
    for attempt in range(attempts):
        try:
            shutil.copyfile(src, dst)
            return
        except OSError as err:
            last_error = err
            if attempt == attempts - 1:
                break
            time.sleep(1 + attempt)
    raise last_error


def _uses_nominal_only_sf_systematics(*tokens):
    measurement_key = " ".join(str(token or "") for token in tokens).lower()
    return "phcsev" in measurement_key


def _uses_phcsev_bkg_uncertainty(flag):
    flag_lower = str(flag or "").lower()
    return "phcsev" in flag_lower and "_bkg" in flag_lower


def _phcsev_signal_flag_for_bkg(flag):
    if "_bkg_" in flag:
        return flag.replace("_bkg_", "_", 1)
    return flag.replace("_bkg", "", 1)


parser = argparse.ArgumentParser(description='tnp EGM fitter')
parser.add_argument('--checkBins'  , action='store_true'  , help = 'check  bining definition')
parser.add_argument('--createBins' , action='store_true'  , help = 'create bining definition')
parser.add_argument('--createHists', action='store_true'  , help = 'create histograms')
parser.add_argument('--sample'     , default='all'        , help = 'create histograms (per sample, expert only)')
parser.add_argument('--fitSample'  , default=None         , help = 'choose which sample to run fits on', choices=['data', 'mcNom', 'mcAlt', 'tagSel'])
parser.add_argument('--altSig'     , action='store_true'  , help = 'alternate signal model fit')
parser.add_argument('--addGaus'    , action='store_true'  , help = 'add gaussian to alternate signal model failing probe')
parser.add_argument('--altBkg'     , action='store_true'  , help = 'alternate background model fit')
parser.add_argument('--altSigBkg'  , action='store_true'  , help = 'alternate signal and background model fit')
parser.add_argument('--doFit'      , action='store_true'  , help = 'fit sample (sample should be defined in settings.py)')
parser.add_argument('--mcSig'      , action='store_true'  , help = 'fit MC nom [to init fit parama]')
parser.add_argument('--doPlot'     , action='store_true'  , help = 'plotting')
parser.add_argument('--sumUp'      , action='store_true'  , help = 'sum up efficiencies')
parser.add_argument('--iBin'       , dest = 'binNumber'   , type = int,  default=-1, help='bin number (to refit individual bin)')
parser.add_argument('--flag'       , default = None       , help ='WP to test')
parser.add_argument('settings'     , default = "egm_tnp_analysis"       , help = 'setting file [mandatory]')
parser.add_argument('--exportJson' , action='store_true', help='export scale factors JSON (schema_version=2)')


args = parser.parse_args()

print('===> settings %s <===' % args.settings)
tnpConf = None
_settings_arg = args.settings
# --- begin: robust settings loader (replace imp) ---
import importlib
import importlib.util

settings_source = None
try:
    # Prefer explicit file path if it exists (also accepts ending with .py)
    if _settings_arg.endswith('.py') and os.path.isfile(_settings_arg):
        spec = importlib.util.spec_from_file_location('tnpConf', _settings_arg)
        if spec is None or spec.loader is None:
            raise ImportError('Could not create spec for settings file: %s' % _settings_arg)
        tnpConf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tnpConf)
        settings_source = getattr(tnpConf, '__file__', _settings_arg)
    else:
        # Treat input as module path (allow .py suffix or '/' separators)
        mod_path = _settings_arg[:-3] if _settings_arg.endswith('.py') else _settings_arg
        mod_path = mod_path.replace('/', '.')
        tnpConf = importlib.import_module(mod_path)
        settings_source = getattr(tnpConf, '__file__', 'module:' + mod_path)
    print('[tnpEGM_fitter] loaded settings module: %s' % settings_source)
except Exception as e:
    print('[tnpEGM_fitter] Failed to import settings: %s' % str(e))
    sys.exit(1)
# --- end: robust settings loader (replace imp) ---

### tnp library
CMSSW_BASE = os.getenv('CMSSW_BASE')
if CMSSW_BASE:
    _src = os.path.join(CMSSW_BASE, 'src')
    if _src not in sys.path:
        sys.path.insert(0, _src)

from egm_tnp_analysis.libPython import binUtils  as tnpBiner
from egm_tnp_analysis.libPython import rootUtils as tnpRoot


if args.flag is None:
    print('[tnpEGM_fitter] flag is MANDATORY, this is the working point as defined in the settings.py')
    sys.exit(0)
    
if not args.flag in tnpConf.flags.keys() :
    print('[tnpEGM_fitter] flag %s not found in flags definitions' % args.flag)
    print('  --> define in settings first')
    print('  In settings I found flags: ')
    print(tnpConf.flags.keys())
    sys.exit(1)

outputDirectory = '%s/%s/' % (tnpConf.baseOutDir,args.flag)

print('===>  Output directory: ')
print(outputDirectory)


####################################################################
##### Create (check) Bins
####################################################################
if args.checkBins:
    tnpBins = tnpBiner.createBins(tnpConf.biningDef,tnpConf.cutBase)
    tnpBiner.tuneCuts( tnpBins, tnpConf.additionalCuts )
    for ib in range(len(tnpBins['bins'])):
        print(tnpBins['bins'][ib]['name'])
        print('  - cut: ',tnpBins['bins'][ib]['cut'])
    sys.exit(0)
    
if args.createBins:
    if os.path.exists( outputDirectory ):
            shutil.rmtree( outputDirectory )
    os.makedirs( outputDirectory )
    tnpBins = tnpBiner.createBins(tnpConf.biningDef,tnpConf.cutBase)
    tnpBiner.tuneCuts( tnpBins, tnpConf.additionalCuts )
    pickle.dump( tnpBins, open( '%s/bining.pkl'%(outputDirectory),'wb') )
    print('created dir: %s ' % outputDirectory)
    print('bining created successfully... ')
    print('Note than any additional call to createBins will overwrite directory %s' % outputDirectory)
    sys.exit(0)

tnpBins = pickle.load( open( '%s/bining.pkl'%(outputDirectory),'rb') )


####################################################################
##### Create Histograms
####################################################################
for s in tnpConf.samplesDef.keys():
    sample =  tnpConf.samplesDef[s]
    if sample is None: continue
    setattr( sample, 'tree'     ,'%s/fitter_tree' % tnpConf.tnpTreeDir )
    setattr( sample, 'histFile' , '%s/%s_%s.root' % ( outputDirectory , sample.name, args.flag ) )

missing_sample_inputs = []
for s in tnpConf.samplesDef.keys():
    sample = tnpConf.samplesDef[s]
    if sample is None:
        continue
    for p in sample.path:
        if not os.path.exists(p):
            missing_sample_inputs.append((s, sample.name, p))

if missing_sample_inputs:
    print('[tnpEGM_fitter] Missing input ROOT files:')
    for sample_key, sample_name, path in missing_sample_inputs:
        print('  - samplesDef[%s] (%s): %s' % (sample_key, sample_name, path))
    print('[tnpEGM_fitter] Abort before histogram creation. The later "Bad numerical expression" messages come from building formulas on an empty TChain.')
    sys.exit(1)


if args.createHists:

    print(" ======== Creating Histograms ========")
    # 先嘗試正常匯入；若失敗就動態建置 C++ 擴充並重試
    try:
        from egm_tnp_analysis.libPython import histUtils as tnpHist
    except Exception as e_first:
        print('[tnpEGM_fitter] histUtils import failed: %s' % str(e_first))
        _pkg_dir = os.path.dirname(__file__)
        _builder = os.path.join(_pkg_dir, 'tools', 'build_histutils.sh')
        if os.path.exists(_builder):
            import subprocess as _sp
            print('[tnpEGM_fitter] trying on-demand build via: %s' % _builder)
            try:
                _sp.check_call(['bash', _builder], cwd=_pkg_dir)
            except _sp.CalledProcessError as _be:
                print('[tnpEGM_fitter] build script failed (rc=%s), will retry import anyway' % _be.returncode)
        else:
            print('[tnpEGM_fitter] build script not found at %s' % _builder)
        # 第二段回退：直接以絕對路徑載入 .so（包路徑）
        try:
            import glob, importlib.util as _il_util
            from importlib import machinery as _il_mach
            _lib_dir = os.path.join(_pkg_dir, 'libPython')
            _cands = sorted(glob.glob(os.path.join(_lib_dir, 'histUtils*.so')))
            if not _cands:
                raise ImportError('no histUtils*.so found under %s' % _lib_dir)
            _so_path = _cands[-1]
            _loader = _il_mach.ExtensionFileLoader('egm_tnp_analysis.libPython.histUtils', _so_path)
            _spec = _il_util.spec_from_file_location('egm_tnp_analysis.libPython.histUtils', _so_path, loader=_loader)
            tnpHist = _il_util.module_from_spec(_spec)
            _spec.loader.exec_module(tnpHist)
        except Exception as e_second:
            # 第三段回退：以頂層模組名載入，並註冊別名到封包路徑
            try:
                import glob, importlib.util as _il_util
                from importlib import machinery as _il_mach
                _lib_dir = os.path.join(_pkg_dir, 'libPython')
                _cands = sorted(glob.glob(os.path.join(_lib_dir, 'histUtils*.so')))
                if not _cands:
                    raise ImportError('no histUtils*.so found under %s' % _lib_dir)
                _so_path = _cands[-1]
                _loader = _il_mach.ExtensionFileLoader('histUtils', _so_path)
                _spec = _il_util.spec_from_file_location('histUtils', _so_path, loader=_loader)
                tnpHist = _il_util.module_from_spec(_spec)
                _spec.loader.exec_module(tnpHist)
                sys.modules['egm_tnp_analysis.libPython.histUtils'] = tnpHist
                print('[tnpEGM_fitter] loaded histUtils as top-level module and aliased into egm_tnp_analysis.libPython.histUtils')
            except Exception as e_third:
                print('[tnpEGM_fitter] histUtils still not importable after build: %s' % str(e_third))
                print('  -> Hint: 確認已在正確的 CMSSW/ROOT 環境下，亦可手動執行: tools/build_histutils.sh')
                sys.exit(1)

    # 修正：確保對 histUtils 傳遞正確型別
    def _ensure_str(v):
        if isinstance(v, bytes):
            return v.decode('utf-8', errors='ignore')
        return v
    def _ensure_bytes(v):
        if isinstance(v, str):
            return v.encode('utf-8', errors='ignore')
        return v

    class _SampleProxy:
        def __init__(self, obj, str_attrs=('tnpTree', 'name', 'path', 'histFile', 'puTree', 'weight', 'cut'),
                           bytes_attrs=('tree',)):
            self.__obj = obj
            self.__str_attrs = set(str_attrs)
            self.__bytes_attrs = set(bytes_attrs)
        def __getattr__(self, name):
            v = getattr(self.__obj, name)
            if name in self.__bytes_attrs:
                if isinstance(v, (list, tuple)):
                    return [ _ensure_bytes(x) for x in v ]
                return _ensure_bytes(v)
            if name in self.__str_attrs:
                if isinstance(v, (list, tuple)):
                    return [ _ensure_str(x) for x in v ]
                return _ensure_str(v)
            return v
        def __repr__(self):
            return "<SampleProxy of %r>" % (self.__obj,)

    def parallel_hists(sampleType):
        sample =  tnpConf.samplesDef[sampleType]
        if sample is None : return
        if sampleType == args.sample or args.sample == 'all' :
            print('creating histogram for sample ')
            sample.dump()
            var = { 'name' : 'pair_mass', 'nbins' : 80, 'min' : 50, 'max': 130 }
            if sample.mcTruth:
                var = { 'name' : 'pair_mass', 'nbins' : 80, 'min' : 50, 'max': 130 }

            # 僅將 sample.tree 轉 bytes，其他維持/確保為 str；var['name'] 維持 str
            sample_p = _SampleProxy(sample)
            var_t = dict(var)
            var_t['name'] = _ensure_str(var_t.get('name'))

            try:
                tnpHist.makePassFailHistograms(sample_p, tnpConf.flags[args.flag], tnpBins, var_t)
            except TypeError as te:
                print('[tnpEGM_fitter] makePassFailHistograms TypeError: %s' % te)
                print('  -> 檢查 sample.tree 是否為 bytes（本修正已轉換），以及 histUtils*.so 是否需要清理重建。')
                raise
    
    for k in tnpConf.samplesDef.keys(): parallel_hists(k)

    sys.exit(0)


####################################################################
##### Actual Fitter
####################################################################
sampleToFit = tnpConf.samplesDef['data']
sampleMC = tnpConf.samplesDef.get('mcNom', None)

if args.fitSample is not None:
    # --fitSample should choose the actual sample being fitted
    sampleToFit = tnpConf.samplesDef[args.fitSample]
    # data fits still need an MC reference for line-shape templates
    if args.fitSample == 'data':
        sampleMC = tnpConf.samplesDef.get('mcNom', None)
    else:
        sampleMC = sampleToFit
elif args.mcSig:
    sampleToFit = tnpConf.samplesDef['mcNom']
    sampleMC = sampleToFit

if sampleMC is None:
    print('[tnpEGM_fitter, prelim checks]: MC sample not available... check your settings')
    sys.exit(1)
for s in tnpConf.samplesDef.keys():
    sample =  tnpConf.samplesDef[s]
    if sample is None: continue
    setattr( sample, 'mcRef'     , sampleMC )
    setattr( sample, 'nominalFit', '%s/%s_%s.nominalFit.root' % ( outputDirectory , sample.name, args.flag ) )
    setattr( sample, 'altSigFit' , '%s/%s_%s.altSigFit.root'  % ( outputDirectory , sample.name, args.flag ) )
    setattr( sample, 'altBkgFit' , '%s/%s_%s.altBkgFit.root'  % ( outputDirectory , sample.name, args.flag ) )
    setattr( sample, 'altSigBkgFit' , '%s/%s_%s.altSigBkgFit.root'  % ( outputDirectory , sample.name, args.flag ) )
    setattr( sample, 'diagnosticsSettingsTag', args.settings )
    setattr( sample, 'diagnosticsFlag', args.flag )

pool = None

def _current_fit_type():
    fit_type = 'nominalFit'
    if args.altSig:
        fit_type = 'altSigFit'
    if args.altBkg:
        fit_type = 'altBkgFit'
    if args.altSigBkg:
        fit_type = 'altSigBkgFit'
    return fit_type

def _workspace_param_name(param):
    param = str(param).strip()
    if '[' not in param:
        return None
    return param.split('[', 1)[0].strip()

def _changed_param_names(base_attr, override_params):
    base_by_name = {}
    for item in getattr(tnpConf, base_attr):
        name = _workspace_param_name(item)
        if name:
            base_by_name[name] = str(item)

    changed = set()
    for item in override_params:
        name = _workspace_param_name(item)
        if name and name in base_by_name and str(item) != base_by_name[name]:
            changed.add(name)
    return changed

def _addgaus_for_bin(bin_index):
    """Whether this bin gets the extra shoulder Gaussian on the failing leg.

    --addGaus used to be all or nothing, and a full comparison showed that is the
    wrong granularity: turning it on for every bin improved 699 fits and made 1766
    worse. The recipe helps exactly where the failing leg really is "narrow peak +
    shoulder" -- elsewhere the extra component has nothing to describe and only
    costs a degree of freedom. So let the settings name the bins that need it:

        addGausBins = (18, 19, 20, 21)                  # same for every fit type
        addGausBins = {'nominalFit': (18, 19),          # or per fit type
                       'altSigFit' : (18, 19, 20, 21)}

    --addGaus stays as a global override, which is what the exploratory runs used.
    """
    if args.addGaus:
        return True
    spec = getattr(tnpConf, 'addGausBins', None)
    if not spec:
        return False
    if isinstance(spec, dict):
        spec = spec.get(_current_fit_type(), spec.get('all', ()))
    return bin_index in set(spec)


def _fit_mass_range():
    """settings 的 fitMassRange = (lo, hi)；沒設回 None（沿用 60-120）。"""
    fr = getattr(tnpConf, 'fitMassRange', None)
    return (float(fr[0]), float(fr[1])) if fr and len(fr) == 2 else None


def _bkg_model():
    """settings 的 tnpBkgModel（None/'cmsshape' 預設，或 'exp'）；給 nominal 與 altSig。"""
    return getattr(tnpConf, 'tnpBkgModel', None)


def _altbkg_model_for_bin(bin_index, tnp_bin):
    """Per-bin background model for the alternate-background fit.

    Settings files may define

        tnpAltBkgModelByBin = { 3: 'bernstein2', 4: 'bernstein2' }

    keyed by bin index or by bin name. Absent -- which is the case for every
    measurement unless it opts in -- the fit keeps its single-parameter
    RooExponential and nothing changes.
    """
    spec = getattr(tnpConf, 'tnpAltBkgModelByBin', None)
    if not spec:
        return None
    model = spec.get(bin_index)
    if model is None:
        model = spec.get(str(bin_index))
    if model is None:
        model = spec.get(tnp_bin['name'])
    if model:
        print('[tnpEGM_fitter] altBkg background model %r for bin %s (%s)'
              % (model, bin_index, tnp_bin['name']))
    return model


def _resolve_fit_params(base_attr, bin_index, tnp_bin, return_changed_names=False):
    params = list(getattr(tnpConf, base_attr))
    override_map = getattr(tnpConf, '%sByBin' % base_attr, None)
    if not override_map:
        if return_changed_names:
            return params, set()
        return params

    override = None
    if bin_index in override_map:
        override = override_map[bin_index]
    elif str(bin_index) in override_map:
        override = override_map[str(bin_index)]
    elif tnp_bin['name'] in override_map:
        override = override_map[tnp_bin['name']]

    if override:
        print('[tnpEGM_fitter] override %s for bin %s (%s)' % (base_attr, bin_index, tnp_bin['name']))
        params = list(override)
        if return_changed_names:
            return params, _changed_param_names(base_attr, params)
        return params
    if return_changed_names:
        return params, set()
    return params

if  args.doFit:
    print(" ======== Fitting ========")
    sampleToFit.dump()
    def parallel_fit(ib):
        if (args.binNumber >= 0 and ib == args.binNumber) or args.binNumber < 0:
            tnp_bin = tnpBins['bins'][ib]
            use_gaus = _addgaus_for_bin(ib)
            if args.altSig and not use_gaus:
                fit_params, changed_names = _resolve_fit_params('tnpParAltSigFit', ib, tnp_bin, return_changed_names=True)
                tnpRoot.histFitterAltSig(
                    sampleToFit,
                    tnp_bin,
                    fit_params,
                    bin_index=ib,
                    preserve_params_from_mc=changed_names,
                    fitRange=_fit_mass_range(),
                    bkgModel=_bkg_model(),
                )
            elif args.altSig and use_gaus:
                fit_params, changed_names = _resolve_fit_params('tnpParAltSigFit_addGaus', ib, tnp_bin, return_changed_names=True)
                tnpRoot.histFitterAltSig(
                    sampleToFit,
                    tnp_bin,
                    fit_params,
                    1,
                    bin_index=ib,
                    preserve_params_from_mc=changed_names,
                    fitRange=_fit_mass_range(),
                    bkgModel=_bkg_model(),
                )
            elif args.altBkg and use_gaus:
                fit_params = _resolve_fit_params('tnpParAltBkgFit_addGaus', ib, tnp_bin)
                tnpRoot.histFitterAltBkg(  sampleToFit, tnp_bin, fit_params, 1, bin_index=ib,
                                           bkgModel=_altbkg_model_for_bin(ib, tnp_bin), fitRange=_fit_mass_range() )
            elif args.altBkg:
                fit_params = _resolve_fit_params('tnpParAltBkgFit', ib, tnp_bin)
                tnpRoot.histFitterAltBkg(  sampleToFit, tnp_bin, fit_params, bin_index=ib,
                                           bkgModel=_altbkg_model_for_bin(ib, tnp_bin), fitRange=_fit_mass_range() )
            elif args.altSigBkg and use_gaus:
                fit_params = _resolve_fit_params('tnpParAltSigBkgFit_addGaus', ib, tnp_bin)
                tnpRoot.histFitterAltSigBkg(  sampleToFit, tnp_bin, fit_params, 1, bin_index=ib, fitRange=_fit_mass_range() )
            elif args.altSigBkg:
                fit_params = _resolve_fit_params('tnpParAltSigBkgFit', ib, tnp_bin)
                tnpRoot.histFitterAltSigBkg(  sampleToFit, tnp_bin, fit_params, bin_index=ib, fitRange=_fit_mass_range() )
            elif use_gaus:
                fit_params = _resolve_fit_params('tnpParNomFit_addGaus', ib, tnp_bin)
                tnpRoot.histFitterNominal( sampleToFit, tnp_bin, fit_params, 1, bin_index=ib, fitRange=_fit_mass_range(), bkgModel=_bkg_model() )
            else:
                fit_params = _resolve_fit_params('tnpParNomFit', ib, tnp_bin)
                tnpRoot.histFitterNominal( sampleToFit, tnp_bin, fit_params, bin_index=ib, fitRange=_fit_mass_range(), bkgModel=_bkg_model() )
    # Pool() with no argument uses every core the machine has, which is not what
    # was asked for: on a batch worker the job holds one requested CPU but forks
    # ~13 ROOT processes (a 2.6 h job reported 33.5 h of CPU), and on a shared
    # login node it is how a handful of measurements turn into 200 processes.
    # The memory a job appears to need is likewise N processes' worth, not one
    # fit's. Take it from TNP_NPROC so the submit file and the code agree.
    _nproc = int(os.environ.get('TNP_NPROC', '0')) or len(os.sched_getaffinity(0))
    print('===> fitting %d bins with %d parallel processes' % (len(tnpBins['bins']), _nproc))
    pool = Pool(processes=_nproc)
    pool.map(parallel_fit, range(len(tnpBins['bins'])))

    args.doPlot = True
     
def _concat_bin_files(target, pattern):
    """Gather the per-bin result files into the measurement-level file.

    This used to be `hadd -f`, which goes through TFileMerger and crashes
    non-deterministically on these files: repeating the same 28-file merge eight
    times aborted twice reading from EOS and three times reading from a local
    copy, so it is the merger, not the storage. os.system() hid the failure, and
    the truncated output only surfaced later as the plotting step dereferencing a
    null canvas.

    There is nothing to merge in the first place -- every object is named after
    its own bin, so this is a pure concatenation. Copying the keys ourselves is
    deterministic, and a missing or unreadable input now raises instead of
    quietly producing a short file.
    """
    import glob as _glob
    import ROOT as rt
    sources = sorted(_glob.glob(pattern))
    if not sources:
        raise RuntimeError('no per-bin files matching %s' % pattern)
    out = rt.TFile.Open(target, 'RECREATE')
    if not out or out.IsZombie():
        raise RuntimeError('cannot open %s for writing' % target)
    nobj = 0
    for src in sources:
        fin = rt.TFile.Open(src)
        if not fin or fin.IsZombie():
            out.Close()
            raise RuntimeError('cannot read %s' % src)
        for key in fin.GetListOfKeys():
            obj = key.ReadObj()
            if not obj:
                fin.Close(); out.Close()
                raise RuntimeError('unreadable object %s in %s' % (key.GetName(), src))
            out.cd()
            obj.Write(key.GetName(), rt.TObject.kOverwrite)
            nobj += 1
        fin.Close()
    out.Close()
    print('===> merged %d per-bin files (%d objects) into %s' % (len(sources), nobj, target))
    return len(sources), nobj


####################################################################
##### dumping plots
####################################################################
if  args.doPlot:
    fileName = sampleToFit.nominalFit
    fitType  = _current_fit_type()
    if fitType == 'altSigFit':
        fileName = sampleToFit.altSigFit
    if fitType == 'altBkgFit':
        fileName = sampleToFit.altBkgFit
    if fitType == 'altSigBkgFit':
        fileName = sampleToFit.altSigBkgFit
        
    _concat_bin_files(fileName, fileName.replace('.root', '-*.root'))

    plottingDir = '%s/plots/%s/%s' % (outputDirectory,sampleToFit.name,fitType)
    if not os.path.exists( plottingDir ):
        os.makedirs( plottingDir )
    _pkg_dir = os.path.dirname(__file__)
    shutil.copy(os.path.join(_pkg_dir, 'etc', 'inputs', 'index.php.listPlots'),
                os.path.join(plottingDir, 'index.php'))

    for ib in range(len(tnpBins['bins'])):
        if (args.binNumber >= 0 and ib == args.binNumber) or args.binNumber < 0:
            tnpRoot.histPlotter( fileName, tnpBins['bins'][ib], plottingDir )

    summaryPath = tnpRoot.build_fit_diagnostics_summary(sampleToFit, fitType, tnpBins['bins'], args.binNumber)
    print(' ===> Fit diagnostics summary saved in <=======')
    print(summaryPath)
    print(' ===> Plots saved in <=======')
    if pool is not None:
        pool.close()
        pool.join()
#    print 'localhost/%s/' % plottingDir


####################################################################
##### dumping egamma txt file 
####################################################################
if args.sumUp:
    sampleToFit.dump()
    info = {
        'data'        : sampleToFit.histFile,
        'dataNominal' : sampleToFit.nominalFit,
        'dataAltSig'  : sampleToFit.altSigFit ,
        'dataAltBkg'  : sampleToFit.altBkgFit ,
        'dataAltSigBkg'  : sampleToFit.altSigBkgFit ,
        'mcNominal'   : sampleToFit.mcRef.histFile,
        'mcAlt'       : None,
        'tagSel'      : None
        }

    nominalOnlySFSystematics = _uses_nominal_only_sf_systematics(
        args.flag,
        settings_source,
        outputDirectory,
    )
    if nominalOnlySFSystematics:
        info['dataAltSig'] = None
        info['dataAltBkg'] = None
        info['dataAltSigBkg'] = None
        print('[sumUp] phcsev detected: using only nominal Data/MC for SF uncertainties.')

    if not nominalOnlySFSystematics and not tnpConf.samplesDef['mcAlt' ] is None:
       info['mcAlt'    ] = tnpConf.samplesDef['mcAlt' ].histFile
    # if not tnpConf.samplesDef['tagSel'] is None:
    #     info['tagSel'   ] = tnpConf.samplesDef['tagSel'].histFile

    effis = None
    flag = args.flag

    is_lowpt = "lowpt" in flag
    is_postBPixHole = "2023postBPixHole" in flag

    if is_postBPixHole and is_lowpt:
        effFileName = f"{outputDirectory}/egammaLowptEffi_postBPixHole.txt"

    elif is_postBPixHole and not is_lowpt:
        effFileName = f"{outputDirectory}/egammaEffi_postBPixHole.txt"

    elif not is_postBPixHole and is_lowpt:
        effFileName = f"{outputDirectory}/egammaLowptEffi.txt"

    else:
        effFileName = f"{outputDirectory}/egammaEffi.txt"

    sfStageDir = None
    sfStageOutputDirectory = None
    effFileNameForSFProduction = effFileName
    if _is_eos_path(effFileName):
        sfStageDir = tempfile.mkdtemp(prefix='egm_tnp_sf_')
        sfStageOutputDirectory = os.path.join(
            sfStageDir,
            os.path.basename(os.path.normpath(outputDirectory)) or args.flag
        )
        os.makedirs(sfStageOutputDirectory, exist_ok=True)
        effFileNameForSFProduction = os.path.join(
            sfStageOutputDirectory,
            os.path.basename(effFileName)
        )
        print('[tnpEGM_fitter] staging scale-factor text/plots locally: %s' % sfStageOutputDirectory)

    fOut = open( effFileNameForSFProduction,'w')
    
    # 用來組合 JSON 的暫存
    _jsonRecords = []
    _var1_name = None
    _var2_name = None

    def _json_var_name(name):
        name = str(name).strip()
        var_map = {
            'el_pt': 'pt',
            'el_et': 'pt',
            'el_sc_et': 'pt',
            'probe_Ele_pt': 'pt',
            'probe_pt': 'pt',
            'ph_et': 'pt',
            'ph_pt': 'pt',
            'el_eta': 'eta',
            'el_sc_eta': 'eta',
            'probe_sc_eta': 'eta',
            'ph_sc_eta': 'eta',
            'ph_eta': 'eta',
        }
        return var_map.get(name, name)

    def _range_key(ranges):
        return tuple(
            (axis, round(float(lo), 6), round(float(hi), 6))
            for axis, (lo, hi) in sorted(ranges.items())
        )

    def _read_sf_by_bin(eff_path):
        sf_by_bin = {}
        raw_var1 = 'var1'
        raw_var2 = 'var2'

        with open(eff_path) as eff_file:
            for line in eff_file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('###'):
                    header_fields = line.lstrip('#').split(':', 1)
                    if len(header_fields) == 2:
                        header_name = header_fields[0].strip().lower()
                        header_value = _json_var_name(header_fields[1].strip())
                        if header_name == 'var1':
                            raw_var1 = header_value
                        elif header_name == 'var2':
                            raw_var2 = header_value
                    continue

                fields = line.split()
                if len(fields) < 8:
                    continue
                try:
                    ranges = {
                        raw_var1: (float(fields[0]), float(fields[1])),
                        raw_var2: (float(fields[2]), float(fields[3])),
                    }
                    eff_data = float(fields[4])
                    eff_mc = float(fields[6])
                except ValueError:
                    continue

                sf_pass = eff_data / eff_mc if eff_mc > 0 else 1.0
                eff_data_fail = 1.0 - eff_data
                eff_mc_fail = 1.0 - eff_mc
                sf_fail = eff_data_fail / eff_mc_fail if eff_mc_fail > 0 else 1.0
                sf_by_bin[_range_key(ranges)] = {
                    'sf_pass': sf_pass,
                    'sf_fail': sf_fail,
                }

        return sf_by_bin

    def _apply_phcsev_bkg_uncertainties():
        if not _uses_phcsev_bkg_uncertainty(args.flag):
            return

        signal_flag = _phcsev_signal_flag_for_bkg(args.flag)
        signal_eff_path = os.path.join(
            tnpConf.baseOutDir,
            signal_flag,
            os.path.basename(effFileName),
        )

        if not os.path.exists(signal_eff_path):
            print(
                '[exportJson] WARNING: cannot apply phcsev bkg uncertainty; '
                'missing signal efficiency file: %s' % signal_eff_path
            )
            return

        signal_sf_by_bin = _read_sf_by_bin(signal_eff_path)
        updated = 0
        missing = 0
        for rec in _jsonRecords:
            signal_sf = signal_sf_by_bin.get(_range_key(rec['ranges']))
            if signal_sf is None:
                missing += 1
                continue

            sf_sig = signal_sf['sf_pass']
            sf_sig_plus_bkg = rec['sf_pass']
            if sf_sig > 0:
                rec['unc_pass'] = abs(sf_sig - sf_sig_plus_bkg) / sf_sig

            sf_fail_sig = signal_sf['sf_fail']
            sf_fail_sig_plus_bkg = rec['sf_fail']
            if sf_fail_sig > 0:
                rec['unc_fail'] = abs(sf_fail_sig - sf_fail_sig_plus_bkg) / sf_fail_sig

            updated += 1

        print(
            '[exportJson] phcsev bkg uncertainty from %s: updated %d bin(s), missing %d bin(s).'
            % (signal_eff_path, updated, missing)
        )

    for ib in range(len(tnpBins['bins'])):
        effis = tnpRoot.getAllEffi( info, tnpBins['bins'][ib] )

        ### formatting assuming 2D bining -- to be fixed        
        v1Range = tnpBins['bins'][ib]['title'].split(';')[1].split('<')
        v2Range = tnpBins['bins'][ib]['title'].split(';')[2].split('<')
        if ib == 0 :
            astr = '### var1 : %s' % v1Range[1]
            print(astr)
            fOut.write( astr + '\n' )
            astr = '### var2 : %s' % v2Range[1]
            print(astr)
            fOut.write( astr + '\n' )
            
        astr =  '%+8.5f\t%+8.5f\t%+8.5f\t%+8.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f' % (
            float(v1Range[0]), float(v1Range[2]),
            float(v2Range[0]), float(v2Range[2]),
            effis['dataNominal'][0],effis['dataNominal'][1],
            effis['mcNominal'  ][0],effis['mcNominal'  ][1],
            effis['dataAltBkg' ][0],
            effis['dataAltSig' ][0],
            effis['mcAlt' ][0],
            # effis['tagSel'][0],
            effis['dataAltSigBkg' ][0],
            )
        print(astr)
        fOut.write( astr + '\n' )

        # 取得變數名稱 (首次)
        if _var1_name is None: _var1_name = v1Range[1] if len(v1Range) > 1 else 'var1'
        if _var2_name is None: _var2_name = v2Range[1] if len(v2Range) > 1 else 'var2'
        # 正規化變數命名（映射 ph_et -> pt；ph_sc_eta -> eta）
        if _var1_name is not None:
            _var1_name = _var1_name.strip()
            _var1_name = _json_var_name(_var1_name)
        if _var2_name is not None:
            _var2_name = _var2_name.strip()
            _var2_name = _json_var_name(_var2_name)
        # 效率與不確定度
        # JSON 的中心 data 效率必須與圖 (libPython/efficiencyUtils.py:efficiency.mean)
        # 完全一致：取 nominal + altBkg + altSig + altSigBkg 四個 data fit 效率的平均，
        # 而非只用 nominal。這樣 sf_pass = mean(data)/nominal(mc) 就會等於 EGM2D/SFvseta
        # 圖上畫的 SF。缺席的 alt fit 由 getAllEffi 回傳 -1，需與 efficiencyUtils 相同地
        # 排除（>=0 才納入）；nominal 一律納入。
        _data_effs = [effis['dataNominal'][0]]
        for _alt_key in ('dataAltBkg', 'dataAltSig', 'dataAltSigBkg'):
            _alt_eff = effis[_alt_key][0]
            if _alt_eff >= 0:
                _data_effs.append(_alt_eff)
        eff_data = sum(_data_effs) / len(_data_effs)
        unc_data = effis['dataNominal'][1]
        eff_mc  , unc_mc   = effis['mcNominal'  ][0], effis['mcNominal'  ][1]
        # 保護除以零
        if eff_mc <= 0: 
            sf_pass = 1.0
            unc_pass = 0.0
        else:
            sf_pass = eff_data / eff_mc
            # 誤差傳播: f = A/B
            unc_pass = math.sqrt( (unc_data/eff_mc)**2 + (eff_data*unc_mc/(eff_mc**2))**2 )
        # Fail 區 (互補)
        eff_data_fail = 1.0 - eff_data
        eff_mc_fail   = 1.0 - eff_mc
        if eff_mc_fail <= 0:
            sf_fail = 1.0
            unc_fail = 0.0
        else:
            sf_fail = eff_data_fail / eff_mc_fail
            # f = (1-A)/(1-B) -> 對 A, B 的偏微分做近似 (線性誤差傳播)
            # df/dA = -1/(1-B), df/dB = (1-A)/(1-B)^2
            dfdA = -1.0 / max(1e-12, (1 - eff_mc))
            dfdB = (1 - eff_data) / max(1e-12, (1 - eff_mc)**2)
            unc_fail = math.sqrt( (dfdA * unc_data)**2 + (dfdB * unc_mc)**2 )
        _jsonRecords.append({
            'ranges': {
                _var1_name: (float(v1Range[0]), float(v1Range[2])),
                _var2_name: (float(v2Range[0]), float(v2Range[2])),
            },
            'effdata': eff_data,
            'systdata': unc_data,
            'effmc': eff_mc,
            'systmc': unc_mc,
            'sf_pass': sf_pass,
            'unc_pass': unc_pass,
            'sf_fail': sf_fail,
            'unc_fail': unc_fail,
        })

    fOut.close()
    if sfStageDir is not None:
        _copy_file_with_retries(effFileNameForSFProduction, effFileName)

    print('Effis saved in file : ',  effFileName)
    # 同樣加入回退匯入，避免 PyROOT 攔截
    try:
        from egm_tnp_analysis.libPython import EGammaID_scaleFactors as egm_sf
    except Exception:
        import importlib.util as _il_util
        _pkg_dir = os.path.dirname(__file__)
        _sf_path = os.path.join(_pkg_dir, 'libPython', 'EGammaID_scaleFactors.py')
        _spec = _il_util.spec_from_file_location('egm_tnp_analysis.libPython.EGammaID_scaleFactors', _sf_path)
        egm_sf = _il_util.module_from_spec(_spec)
        _spec.loader.exec_module(egm_sf)
    egm_sf.doEGM_SFs(effFileNameForSFProduction,sampleToFit.lumi)
    if sfStageDir is not None:
        for sfOutputName in os.listdir(sfStageOutputDirectory):
            sfOutputPath = os.path.join(sfStageOutputDirectory, sfOutputName)
            if not os.path.isfile(sfOutputPath):
                continue
            _copy_file_with_retries(sfOutputPath, os.path.join(outputDirectory, sfOutputName))
        shutil.rmtree(sfStageDir)

    if args.exportJson:
        _apply_phcsev_bkg_uncertainties()

        def _edges_for(axis):
            lows = sorted({rec['ranges'][axis][0] for rec in _jsonRecords})
            last_high = max(rec['ranges'][axis][1] for rec in _jsonRecords)
            return lows + ([last_high] if lows[-1] != last_high else [])

        def _content_for(axis_names, value_name):
            import itertools
            edges_by_axis = {axis: _edges_for(axis) for axis in axis_names}
            values_by_bin = {}
            for rec in _jsonRecords:
                idx = tuple(edges_by_axis[axis].index(rec['ranges'][axis][0]) for axis in axis_names)
                values_by_bin[idx] = rec[value_name]
            shape = [range(len(edges_by_axis[axis]) - 1) for axis in axis_names]
            return [values_by_bin[tuple(idx)] for idx in itertools.product(*shape)]

        def _correction(name, axis_names, edges, content, output_description):
            return {
                "name": name,
                "version": 1,
                "inputs": [
                    {"name": axis, "type": "real", "description": axis}
                    for axis in axis_names
                ],
                "output": {"name": "sf", "type": "real", "description": output_description},
                "data": {
                    "nodetype": "multibinning",
                    "inputs": axis_names,
                    "edges": edges,
                    "content": content,
                    "flow": "clamp"
                }
            }

        axis_names = [_var1_name, _var2_name]
        export_mode = getattr(tnpConf, 'exportJsonFormat', None)
        if export_mode is None:
            flag_lower = args.flag.lower()
            export_mode = 'efficiency' if (
                'trigger' in flag_lower or 'trig' in flag_lower or 'miniiso' in flag_lower
            ) else 'sf'

        if export_mode == 'efficiency' and set(['pt', 'eta']).issubset(set(axis_names)):
            axis_names = ['pt', 'eta'] + [axis for axis in axis_names if axis not in ('pt', 'eta')]

        edges = [_edges_for(axis) for axis in axis_names]

        if export_mode == 'efficiency':
            out_json = {
                "schema_version": 2,
                "description": "",
                "corrections": [
                    _correction("effdata", axis_names, edges, _content_for(axis_names, "effdata"), "data eff"),
                    _correction("systdata", axis_names, edges, _content_for(axis_names, "systdata"), "data unc"),
                    _correction("effmc", axis_names, edges, _content_for(axis_names, "effmc"), "MC eff"),
                    _correction("systmc", axis_names, edges, _content_for(axis_names, "systmc"), "MC unc"),
                ]
            }
        else:
            axis_names = [_var1_name, _var2_name]
            edges = [_edges_for(axis) for axis in axis_names]
            sf_pass = _content_for(axis_names, "sf_pass")
            unc_pass = _content_for(axis_names, "unc_pass")
            sf_fail = _content_for(axis_names, "sf_fail")
            unc_fail = _content_for(axis_names, "unc_fail")
            out_json = {
                "schema_version": 2,
                "description": "auto-generated scale factors",
                "corrections": [
                    _correction("sf_pass", axis_names, edges, sf_pass, "data/MC scale factor (pass)"),
                    _correction("unc_pass", axis_names, edges, unc_pass, "uncertainty (pass)"),
                    _correction("sf_fail", axis_names, edges, sf_fail, "data/MC scale factor (fail)"),
                    _correction("unc_fail", axis_names, edges, unc_fail, "uncertainty (fail)"),
                ]
            }
        _json_path = os.path.join(outputDirectory, f'{args.flag}.json')
        with open(_json_path, 'w') as jf:
            json.dump(out_json, jf, indent=2)
        print('[exportJson] JSON written:', _json_path)
