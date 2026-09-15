#!/usr/bin/env bash
# 2026-09-14：只發布昨夜真正有擬合改動的 4 個 measurement。
#
# 為什麼不直接跑 ./publish.sh electron：它一次發布 103 頁，會把其餘 99 頁的
# 時間戳全部洗掉，之後就判不出哪些是真的重做過的。昨天在 prepare 階段用
# 「fit 比 summary 新」挑出 3 個 measurement，就是同一個原則。
# 參數逐字取自 publish.sh 對應的四個區塊（--dest/--hometitle/--title/
# --src-fits/--src-summary/--section-url），沒有自己編。
#
# 首頁另外用 FORCE_REGEN_HOME=1 ./publish.sh electron 更新（若需要）。
# 預設 dry-run，實際執行要加 --go。
set -o pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GO=0; [ "${1:-}" = "--go" ] && GO=1
one(){ # one <dest> <hometitle> <title> <srcfits> <srcsummary> <section>
  if [ "$GO" -eq 0 ]; then
    echo "DRY-RUN: publish_subpage.sh --dest $1"
    echo "         --src-fits    $4"
    echo "         --src-summary $5"
    return 0
  fi
  echo "=== $1 ($(date +%T))"
  bash "${SCRIPT_DIR}/publish_subpage.sh" \
    --dest "$1" --hometitle "$2" --title "$3" \
    --src-fits "$4" --src-summary "$5" --section-url "$6"
}
B=/eos/home-p/pelai/HZa/root_TnP
one resolve_elminiIso0p15_nongap_2026/hza_elminiIso0p15_nongap_2026_sf \
    "Custom Electron miniIso0p15 Nongap 2026" \
    "Efficiency / Scale Factor Measurements — hza_elminiIso0p15_nongap_2026_sf" \
    "$B/hza_elminiIso0p15_nongap_2026_sf/plots/Data_2026" \
    "$B/hza_elminiIso0p15_nongap_2026_sf" \
    "#Resolve_Electron_miniIso0p15_nongap_2026"
one resolve_elminiIso0p1_nongap_2026/hza_elminiIso0p1_nongap_2026_sf \
    "Custom Electron miniIso0p1 Nongap 2026" \
    "Efficiency / Scale Factor Measurements — hza_elminiIso0p1_nongap_2026_sf" \
    "$B/hza_elminiIso0p1_nongap_2026_sf/plots/Data_2026" \
    "$B/hza_elminiIso0p1_nongap_2026_sf" \
    "#Resolve_Electron_miniIso0p1_nongap_2026"
one resolve_elid_nongap_lowpT_2024/hza_elid_nongap_lowpT_2024_sf \
    "Custom Electron ID Nongap Low pT 2024" \
    "Efficiency / Scale Factor Measurements — hza_elid_nongap_lowpT_2024_sf" \
    "$B/hza_elid_nongap_lowpT_2024_sf/plots/Data_2024" \
    "$B/hza_elid_nongap_lowpT_2024_sf" \
    "#Resolve_Electron_ID_nongap_lowpT_2024"
one resolve_elid_nongap_2024/hza_elid_nongap_2024_sf \
    "Custom Electron ID Nongap 2024" \
    "Efficiency / Scale Factor Measurements — hza_elid_nongap_2024_sf" \
    "$B/hza_elid_nongap_2024_sf/plots/Data_2024" \
    "$B/hza_elid_nongap_2024_sf" \
    "#Resolve_Electron_ID_nongap_2024"
[ "$GO" -eq 0 ] && echo && echo "以上為 dry-run。確認無誤後加 --go 執行。"
exit 0
