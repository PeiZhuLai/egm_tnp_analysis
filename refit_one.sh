cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
MOD="$1"; WP="$2"; shift 2
echo "=== refit $WP : $@ START $(date +%H:%M:%S) ==="
for spec in "$@"; do
  ft="${spec%%:*}"; bins="${spec#*:}"
  for b in ${bins//,/ }; do
    case "$ft" in
      nom)  $F $MOD --flag $WP --doFit --fitSample data --iBin $b ;;
      altSig) $F $MOD --flag $WP --doFit --altSig --iBin $b ;;
      altBkg) $F $MOD --flag $WP --doFit --altBkg --iBin $b ;;
      altSigBkg) $F $MOD --flag $WP --doFit --altSigBkg --iBin $b ;;
    esac
  done
done
echo "=== refit END $(date +%H:%M:%S) ==="
