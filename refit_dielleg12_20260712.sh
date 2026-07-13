cd /afs/cern.ch/work/p/pelai/HZa/TnP/CMSSW_11_2_0/src
eval `scramv1 runtime -sh`
export PYTHONPATH="$CMSSW_BASE/src:$PYTHONPATH" LANG=C LC_ALL=C
cd egm_tnp_analysis
F="python3 -m egm_tnp_analysis.tnpEGM_fitter"
B=egm_tnp_analysis.etc.config.hza_ele
echo "=== refit dielleg12 fit-tune START $(date) ==="

# --- nongap_2024: altSig 33/38/55 wider ---
echo "--- nongap_2024 ---"
$F $B.settings_htoza_dielleg12trigger_nongap_2024 --flag hza_dielleg12trigger_nongap_2024_sf --doFit --altSig
$F $B.settings_htoza_dielleg12trigger_nongap_2024 --flag hza_dielleg12trigger_nongap_2024_sf --sumUp --exportJson

# --- gap_2025: bin5 nominal(data+mcNom) + altSig ---
echo "--- gap_2025 ---"
$F $B.settings_htoza_dielleg12trigger_gap_2025 --flag hza_dielleg12trigger_gap_2025_sf --doFit --fitSample mcNom
$F $B.settings_htoza_dielleg12trigger_gap_2025 --flag hza_dielleg12trigger_gap_2025_sf --doFit --fitSample data
$F $B.settings_htoza_dielleg12trigger_gap_2025 --flag hza_dielleg12trigger_gap_2025_sf --doFit --altSig
$F $B.settings_htoza_dielleg12trigger_gap_2025 --flag hza_dielleg12trigger_gap_2025_sf --sumUp --exportJson

# --- nongap_2025: altSig(10-14,18-21,23,30,39) + altSigBkg(32) ---
echo "--- nongap_2025 ---"
$F $B.settings_htoza_dielleg12trigger_nongap_2025 --flag hza_dielleg12trigger_nongap_2025_sf --doFit --altSig
$F $B.settings_htoza_dielleg12trigger_nongap_2025 --flag hza_dielleg12trigger_nongap_2025_sf --doFit --altSigBkg
$F $B.settings_htoza_dielleg12trigger_nongap_2025 --flag hza_dielleg12trigger_nongap_2025_sf --sumUp --exportJson

echo "=== refit dielleg12 END $(date) ==="
