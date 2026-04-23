#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# publish_subpage.sh  (v2: default /eos/user/p/pelai/www/HZa/sfs)
#
# 用途：在 /eos/user/p/pelai/www/HZa/sfs 下生成「子頁面」
# 功能：
#   - 自動建立子頁面結構
#   - （可選）同步 fits/ 和 summary/ 檔案（僅 PNG）
#   - 自動產生 index.html
#   - 將 summary/ 內圖片與 PDF 生成圖牆
#   - 設定公開權限
#
# 環境變數：
#   FORCE_REGEN_SUB=1   強制重建子頁 index.html
#   FORCE_REGEN_HOME=1  強制重建首頁 index.html
#   FORCE_REGEN_FIT=1   強制重建 fits/index.html
#
# ------------------------------------------------------------
# 必填參數：
#   --dest <EOS放圖的相對路徑>    例如: resolve_ph_2022preEE/hza_resolve_phid_2022preEE
#   --title <頁面標題>           例如: "Efficiency / Scale Factor Measurements — hza_resolve_phid_2022preEE"
#
# 可選參數：
#   --src-fits <所有fit plots來源目錄>     例如: /eos/home-p/pelai/HZa/root_TnP/muon_2023/hzg_muid_2023/fits
#   --src-fits-prefixed <prefix:path>     例如: Nominal:/eos/.../Nominal/NUM_xxx （可重複）
#   --src-summary <Summary plots來源目錄> 例如: /eos/home-p/pelai/HZa/root_TnP/muon_2023/hzg_muid_2023/summary
#   --web-root <根路徑>         預設: /eos/user/p/pelai/www/HZa/sfs
#   --home-url <首頁URL>        預設: /HZa/sfs/
#   --section-url <錨點>        例如: "#Resolved_Custom_Photon_ID_2022preEE"
#   --summary-include <glob>    指定 summary 要同步的檔名樣式（可重複）
#   --summary-exclude <glob>    指定 summary 要排除的檔名樣式（可重複）
#   --summary-order <glob>      指定 summary 頁顯示順序（可重複；先比對先顯示）
#   --copy-pdf                  同步來源中的 PDF 到網頁目錄
#   --hide-pdf-in-html          HTML 只顯示 PNG（即使目錄中有 PDF）
#
# 範例：
# ./publish_subpage.sh \
#   --dest photon_2022preEE/hza_resolve_phidfsr_2022preEE \
#   --title "Efficiency / scale factor measurements — hza_resolve_phid_2022preEE" \
#   --src-fits /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022preEE_sf/plots \
#   --src-summary /eos/home-p/pelai/HZa/root_TnP/hza_resolve_phid_2022preEE_sf \
#   --section-url "#Resolved_Custom_Photon_ID_2022preEE"
# ------------------------------------------------------------

WEB_ROOT="/eos/user/p/pelai/www/HZa/sfs"
HOME_URL="/HZa/sfs/"
SECTION_URL=""
DEST_REL=""
ITEM_TITLE=""
TITLE=""
SRC_FITS=""
SRC_FITS_PREFIXED=()
SRC_SUMMARY=""
SUMMARY_INCLUDE_PATTERNS=()
SUMMARY_EXCLUDE_PATTERNS=()
SUMMARY_ORDER_PATTERNS=()
DID_FITS_SYNC=0
COPY_PDF=0
HIDE_PDF_IN_HTML=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --web-root)     WEB_ROOT="$2"; shift 2;;
    --home-url)     HOME_URL="$2"; shift 2;;
    --section-url)  SECTION_URL="$2"; shift 2;;
    --dest)         DEST_REL="$2"; shift 2;;
    --hometitle)    ITEM_TITLE="$2"; shift 2;;
    --title)        TITLE="$2"; shift 2;;
    --src-fits)     SRC_FITS="$2"; shift 2;;
    --src-fits-prefixed) SRC_FITS_PREFIXED+=("$2"); shift 2;;
    --src-summary)  SRC_SUMMARY="$2"; shift 2;;
    --summary-include) SUMMARY_INCLUDE_PATTERNS+=("$2"); shift 2;;
    --summary-exclude) SUMMARY_EXCLUDE_PATTERNS+=("$2"); shift 2;;
    --summary-order) SUMMARY_ORDER_PATTERNS+=("$2"); shift 2;;
    --copy-pdf)      COPY_PDF=1; shift;;
    --hide-pdf-in-html) HIDE_PDF_IN_HTML=1; shift;;
    -h|--help)
      sed -n '1,80p' "$0"; exit 0;;
    *)
      echo "未知參數：$1"; exit 1;;
  esac
done

if [[ -z "$DEST_REL" || -z "$TITLE" ]]; then
  echo "❌ 缺少必要參數 --dest 或 --title"
  exit 1
fi

# 追加：防止 WEB_ROOT 為空造成 HOME_INDEX 失效
if [[ -z "${WEB_ROOT:-}" ]]; then
  echo "❌ WEB_ROOT 為空，請提供 --web-root"
  exit 1
fi

DEST_DIR="${WEB_ROOT%/}/${DEST_REL%/}"
FITSD="${DEST_DIR}/fits"
SUMMD="${DEST_DIR}/summary"

echo ">>> 目的地：${DEST_DIR}"
mkdir -p "$FITSD" "$SUMMD"

# 同步來源（如果提供）
if [[ "${#SRC_FITS_PREFIXED[@]}" -gt 0 ]]; then
  DID_FITS_SYNC=1
  echo ">>> 同步 fits/ 來源（檔名前綴模式）"
  # 前綴模式下先清理舊的 PNG，避免與舊版（未加前綴）檔名混用
  find "${FITSD}" -type f -iname '*.png' -delete
  for spec in "${SRC_FITS_PREFIXED[@]:-}"; do
    prefix="${spec%%:*}"
    src="${spec#*:}"
    if [[ -z "${prefix}" || -z "${src}" || "${src}" == "${spec}" ]]; then
      echo "⚠️ 跳過無效 --src-fits-prefixed 參數：${spec}"
      continue
    fi
    if [[ ! -d "${src}" ]]; then
      echo "⚠️ fits 來源不存在（跳過 ${prefix}）：${src}"
      continue
    fi
    echo ">>> 同步 fits 來源 [${prefix}]：${src}"
    while IFS= read -r -d '' f; do
      rel="${f#${src%/}/}"
      case "${rel}" in
        *1p44To1p57*|*m1p57Tom1p44*) continue ;;
      esac
      rel_dir="$(dirname "${rel}")"
      base="$(basename "${rel}")"
      out_dir="${FITSD}/${rel_dir}"
      mkdir -p "${out_dir}"
      cp -f "${f}" "${out_dir}/${prefix}_${base}"
    done < <(
      if [[ "$COPY_PDF" == "1" ]]; then
        find "${src}" -type f \( -iname '*.png' -o -iname '*.pdf' \) -print0
      else
        find "${src}" -type f -iname '*.png' -print0
      fi
    )
  done
elif [[ -n "${SRC_FITS}" && -d "${SRC_FITS}" ]]; then
  DID_FITS_SYNC=1
  echo ">>> 同步 fits/ 來源（僅 PNG）：${SRC_FITS}"
  fits_rsync_args=(
    -avL
    "--include=*/"
    "--exclude=**1p44To1p57**"
    "--exclude=**m1p57Tom1p44**"
    "--include=*.png"
  )
  if [[ "$COPY_PDF" == "1" ]]; then
    fits_rsync_args+=("--include=*.pdf")
  fi
  fits_rsync_args+=("--exclude=*")
  rsync "${fits_rsync_args[@]}" "${SRC_FITS%/}/" "${FITSD}/"
elif [[ -n "${SRC_FITS}" ]]; then
  echo "⚠️ fits 來源不存在：${SRC_FITS}"
fi

if [[ -n "${SRC_SUMMARY}" && -d "${SRC_SUMMARY}" ]]; then
  echo ">>> 同步 summary/ 來源（僅 PNG）：${SRC_SUMMARY}"
  summary_rsync_args=(
    -avL
    --delete
    "--include=*/"
  )
  if [[ "${#SUMMARY_INCLUDE_PATTERNS[@]}" -gt 0 ]]; then
    for pat in "${SUMMARY_INCLUDE_PATTERNS[@]:-}"; do
      summary_rsync_args+=("--include=${pat}")
    done
  else
    # 預設維持原有 electron/photon 行為
    summary_rsync_args+=(
      "--include=HZa_SF2D_hza_*.png"
      "--include=**/HZa_SF2D_hza_*.png"
      "--include=HZa_SFvseta_*.png"
      "--include=**/HZa_SFvseta_*.png"
      "--include=HZa_SFvsabsEta_*.png"
      "--include=**/HZa_SFvsabsEta_*.png"
      "--include=HZa_SFvsabseta_*.png"
      "--include=**/HZa_SFvsabseta_*.png"
      "--include=HZa_SFvsnVtx_hza_resolve_phcsev_*.png"
      "--include=**/HZa_SFvsnVtx_hza_resolve_phcsev_*.png"
      "--include=pelai_SFvsnVtx_hza_resolve_phcsev_*.png"
      "--include=**/pelai_SFvsnVtx_hza_resolve_phcsev_*.png"
      "--include=HZa_SFvspT_*.png"
      "--include=**/HZa_SFvspT_*.png"
    )
  fi
  for pat in "${SUMMARY_EXCLUDE_PATTERNS[@]:-}"; do
    summary_rsync_args+=("--exclude=${pat}")
  done
  summary_rsync_args+=("--exclude=*")
  rsync "${summary_rsync_args[@]}" "${SRC_SUMMARY%/}/" "${SUMMD}/"
  if [[ "$COPY_PDF" == "1" ]]; then
    echo ">>> 額外同步 summary PDF：${SRC_SUMMARY}"
    rsync -avL --delete \
      --include='*/' \
      --include='*.pdf' \
      --exclude='*' \
      "${SRC_SUMMARY%/}/" "${SUMMD}/"
  fi
elif [[ -n "${SRC_SUMMARY}" ]]; then
  echo "⚠️ summary 來源不存在：${SRC_SUMMARY}"
fi

if [[ -n "${SRC_FITS}" ]]; then
  fit_file_count="$(
    find "${FITSD}" -type f \( -iname '*.png' -o -iname '*.pdf' \) | wc -l | tr -d ' '
  )"
  if [[ "${fit_file_count}" == "0" ]]; then
    echo "⚠️ fits/ 目前沒有任何已同步檔案：${FITSD}"
  fi
fi

if [[ -n "${SRC_SUMMARY}" ]]; then
  summary_file_count="$(
    find "${SUMMD}" -type f \( -iname '*.png' -o -iname '*.pdf' \) | wc -l | tr -d ' '
  )"
  if [[ "${summary_file_count}" == "0" ]]; then
    echo "⚠️ summary/ 目前沒有任何符合條件的檔案：${SUMMD}"
  fi
fi

INDEX="${DEST_DIR}/index.html"
FORCE_REGEN_SUB="${FORCE_REGEN_SUB:-0}"
FORCE_REGEN_HOME="${FORCE_REGEN_HOME:-0}"
FORCE_REGEN_FIT="${FORCE_REGEN_FIT:-0}"  # 新增：控制是否強制重建 fits/index.html
if [[ ! -f "$INDEX" || "$FORCE_REGEN_SUB" == "1" ]]; then
  echo ">>> 生成 Sub-page index.html"
  cat > "$INDEX" <<HTML
<!doctype html>
<html lang="en" id="top">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Summary Plots</title>
<style>
  :root{--mx:22px}
  html,body{margin:0;padding:0}
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;background:#fff}
  header{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:14px var(--mx);z-index:10}
  header h1{margin:0;font-size:1.2rem}
  main{max-width:1200px;margin:0 auto;padding:18px var(--mx) 28px}
  p{line-height:1.55;margin:0 0 12px}
  .muted{color:#666}
  a{color:#0b5bd3;text-decoration:none}
  a:hover{text-decoration:underline}

  /* 卡片網格：每個卡片最小寬度從 260px → 340px */
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(1000px,1fr));gap:20px}

  /* 卡片外觀：圓角更大、邊距更寬 */
  .card{border:1px solid #e0e0e0;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.06);min-height:600px;}

  /* 圖片區塊高度加大 */
  .card img{width:100%;height:580px;object-fit:contain;background:#fafafa}

  /* 檔名文字加大 */
  .name{font-size:1.05rem;padding:12px 14px;border-top:1px solid #eee;word-break:break-all}

  /* PDF 卡片的中央文字也放大並配合圖片高度 */
  .pdf{display:flex;align-items:center;justify-content:center;height:320px;background:#fafafa;font-size:1.1rem}

  .toplink{position:fixed;right:16px;bottom:16px;background:#0b5bd3;color:#fff;padding:8px 12px;border-radius:999px;text-decoration:none}
  .caption{color:#555;font-size:.92rem;margin-top:8px}
  nav.breadcrumb{margin:8px 0 0;font-size:1.3rem}
</style>

<header>
  <h1>${TITLE}</h1>
  <nav class="breadcrumb">
    <a href="${HOME_URL}">← Back to Home</a>
  </nav>
</header>

<main>
  <p class="muted">This page was auto-generated. Last updated: <span id="ts"></span></p>

  <h2>All fit plots can be found <a href="fits/">here</a>.</h2>

  <h2>Summary Plots</h2>

  <div class="grid">
    <!-- AUTO SUMMARY START -->
    <!-- AUTO SUMMARY END -->
  </div>

</main>

<a class="toplink" href="#top">Back to Top</a>

<script>
  document.getElementById('ts').textContent = new Date().toLocaleString();
</script>
</html>
HTML
else
  echo ">>> 使用既有 index.html（將更新卡片區塊）"
fi

# 生成卡片清單
TMP_CARDS="$(mktemp)"

# 先切到目的目錄，下面的相對路徑才會對
cd "$DEST_DIR"

python3 - "$TMP_CARDS" "$HIDE_PDF_IN_HTML" "${SUMMARY_ORDER_PATTERNS[@]:-}" <<'PY'
import fnmatch
import html
import pathlib
import sys

cards_path = pathlib.Path(sys.argv[1])
hide_pdf_in_html = sys.argv[2] == "1"
order_patterns = [p for p in sys.argv[3:] if p]
summary_dir = pathlib.Path("summary")
if not summary_dir.exists():
    cards_path.write_text("")
    raise SystemExit(0)

suffixes = {".png"} if hide_pdf_in_html else {".png", ".pdf"}
files = sorted(
    str(p).replace("\\", "/")
    for p in summary_dir.rglob("*")
    if p.is_file() and p.suffix.lower() in suffixes
)

# Photon CSEV pages: prefer the nVtx summary card over the legacy SFvsEta card,
# while still keeping any SFvsabsEta summary plots.
has_hza_nvtx = any(
    fnmatch.fnmatch(fpath, "summary/HZa_SFvsnVtx_hza_resolve_phcsev_*")
    for fpath in files
)
has_legacy_pelai_nvtx = any(
    fnmatch.fnmatch(fpath, "summary/pelai_SFvsnVtx_hza_resolve_phcsev_*")
    for fpath in files
)
if has_hza_nvtx or has_legacy_pelai_nvtx:
    legacy_eta_patterns = (
        "summary/HZa_SFvseta_hza_resolve_phcsev_*",
        "summary/HZa_SFvsEta_hza_resolve_phcsev_*",
    )
    abs_eta_patterns = (
        "summary/HZa_SFvsabsEta_hza_resolve_phcsev_*",
        "summary/HZa_SFvsabseta_hza_resolve_phcsev_*",
    )
    files = [
        fpath
        for fpath in files
        if not any(fnmatch.fnmatch(fpath, pattern) for pattern in legacy_eta_patterns)
        and not (has_hza_nvtx and fnmatch.fnmatch(fpath, "summary/pelai_SFvsnVtx_hza_resolve_phcsev_*"))
    ]
    if not order_patterns:
        nvtx_pattern = "summary/HZa_SFvsnVtx_hza_resolve_phcsev_*" if has_hza_nvtx else "summary/pelai_SFvsnVtx_hza_resolve_phcsev_*"
        order_patterns = [
            "summary/HZa_SF2D_hza_resolve_phcsev_*",
            *abs_eta_patterns,
            nvtx_pattern,
            "summary/HZa_SFvspT_hza_resolve_phcsev_*",
        ]

ordered = []
remaining = files.copy()

for pattern in order_patterns:
    candidate_patterns = [pattern]
    if "/" not in pattern:
        candidate_patterns.append(f"summary/{pattern}")
    matched = []
    for fpath in remaining:
        if any(fnmatch.fnmatch(fpath, pat) for pat in candidate_patterns):
            matched.append(fpath)
    for m in matched:
        ordered.append(m)
        remaining.remove(m)

files = ordered + remaining
lines = []
for name in files:
    esc = html.escape(name)
    if name.lower().endswith(".pdf"):
        lines.append(
            f'<a class="card" href="{esc}"><div class="pdf">📄 {esc}</div>'
            f'<div class="name">{esc}</div></a>'
        )
    else:
        lines.append(
            f'<a class="card" href="{esc}"><img loading="lazy" src="{esc}" alt="{esc}">'
            f'<div class="name">{esc}</div></a>'
        )

cards_path.write_text("\n".join(lines))
PY

# 插入卡片至佔位符
python3 - "$INDEX" "$TMP_CARDS" <<'PY'
import re, sys, pathlib
index_path = pathlib.Path(sys.argv[1])
cards_path = pathlib.Path(sys.argv[2])
html = index_path.read_text()
cards = cards_path.read_text()
replacement = "<!-- AUTO SUMMARY START -->\n" + cards
if cards:
    replacement += "\n"
replacement += "    <!-- AUTO SUMMARY END -->"

if "<!-- AUTO SUMMARY START -->" in html and "<!-- AUTO SUMMARY END -->" in html:
    html = re.sub(
        r"<!-- AUTO SUMMARY START -->.*?<!-- AUTO SUMMARY END -->",
        replacement,
        html,
        count=1,
        flags=re.S,
    )
elif "<!-- AUTO SUMMARY -->" in html:
    html = re.sub(r"<!-- AUTO SUMMARY -->", replacement, html, count=1)
else:
    html = re.sub(
        r"(<div class=\"grid\">\s*).*?(\s*</div>\s*</main>)",
        r"\1" + replacement + r"\2",
        html,
        count=1,
        flags=re.S,
    )
index_path.write_text(html)
print("index.html updated.")
PY

# ---- 更新首頁 (WEB_ROOT/index.html) ----
HOME_INDEX="${WEB_ROOT%/}/index.html"
NEW_ITEM="<li><a href=\"./${DEST_REL%/}/\">${ITEM_TITLE}</a></li>"
HOME_ITEMS_TMP="$(mktemp)"

if [[ -f "$HOME_INDEX" && "$FORCE_REGEN_HOME" == "1" ]]; then
  python3 - "$HOME_INDEX" "$HOME_ITEMS_TMP" <<'PY'
import pathlib
import re
import sys

home = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
html = home.read_text()

match = re.search(
    r'<ul[^>]*class="[^"]*\bauto-list\b[^"]*"[^>]*>(.*?)</ul>',
    html,
    flags=re.S | re.I,
)
if not match:
    match = re.search(r"<ul[^>]*>(.*?)</ul>", html, flags=re.S | re.I)

items = []
seen = set()
if match:
    for item in re.findall(r"<li\b.*?</li>", match.group(1), flags=re.S | re.I):
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            items.append(cleaned)

out.write_text("\n".join(items))
PY
fi

if [[ ! -f "$HOME_INDEX" || "$FORCE_REGEN_HOME" == "1" ]]; then
  echo ">>> 建立首頁 ${HOME_INDEX}"
  cat > "$HOME_INDEX" <<HTML
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>HZa SF</title>
<style>
  ul.auto-list li a {
    font-size: 1.5rem;     /* 可以改成 18px 或更大 */
    font-weight: 500;      /* 稍微加粗，可選 */
  }
  .center { text-align: center; }
  .center ul { display: inline-block; text-align: left; }
  li {
    margin-bottom: 16px;  /* 控制項目間距，單位可改為 px/em/rem */
  }
</style>
<div class="center">
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
  <h2>
  Welcome to the \(H \to Z\gamma \to \ell\ell\gamma\) and
  \(H \to Za \to \ell\ell\gamma\gamma\) (\(\ell = e, \mu\))
  efficiency and scale factor measurement
  </h2>
  <h2>The same electron and muon selection criteria are used in both analyses.</h2>
  <h2>Photon-related efficiency and scale factors are only considered in the H&rarr;Za analysis.</h2>
  <h2>
    Links to the lepton scale factor measurement fits and results for the Run 3 2024+2025+2026 \(H \to Z\gamma \to \ell\ell\gamma\) analysis (\(\ell = e,\mu\)).<br>
  </h2>
  <h2>
    Links to the photon-related scale factor measurement fits and results for the Run 3 2022+2023+2024 \(H \to Za \to \ell\ell\gamma\gamma\) analysis (\(\ell = e,\mu\)).<br>
  </h2>
  <h2>
    Presentations will be given to the MUO POG
    <a href="https://indico.cern.ch/event/XXXXXXX" target="_blank">muon presentation</a>
    and to the EGM POG
    <a href="https://indico.cern.ch/event/ELECTRON_ID" target="_blank">electron presentation</a>
    and
    <a href="https://indico.cern.ch/event/PHOTON_ID" target="_blank">photon presentation</a>.
    (Left the space for the future)<br>
  </h2>
  <h2>See below links for plots.</h2>
  <ul class="auto-list">
    <!-- AUTO LIST START -->
$(sed 's/^/    /' "$HOME_ITEMS_TMP")
    <!-- AUTO LIST END -->
  </ul>
</div>
</html>
HTML
fi  # 補上遺漏的 fi，避免腳本語法錯誤

python3 - "$HOME_INDEX" "$NEW_ITEM" <<'PY'
import html as html_lib
import pathlib
import re
import sys

home = pathlib.Path(sys.argv[1])
item = sys.argv[2].strip()
if not home.exists():
    print(f">>> 首頁檔案不存在：{home}")
    sys.exit(1)
html = home.read_text()

# 新增：若舊版首頁缺少 auto-list class，自動補上
if 'class="auto-list"' not in html:
    html = re.sub(r"<ul(\s*)>", r"<ul class=\"auto-list\">", html, count=1)

def normalize_label(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()

def split_items(body: str):
    return [frag.strip() for frag in re.findall(r"<li\b.*?</li>", body, flags=re.S | re.I)]

anchor_match = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', item, flags=re.S | re.I)
new_href = anchor_match.group(1).strip() if anchor_match else ""
new_label = normalize_label(anchor_match.group(2)) if anchor_match else normalize_label(item)

def matches(existing_item: str) -> bool:
    match = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', existing_item, flags=re.S | re.I)
    if not match:
        return False
    href = match.group(1).strip()
    label = normalize_label(match.group(2))
    if new_href and href == new_href:
        return True
    if new_label and label == new_label:
        return True
    return False

def merge_items(existing_items):
    merged = []
    inserted = False
    for entry in existing_items:
        if matches(entry):
            if not inserted:
                merged.append(item)
                inserted = True
            continue
        merged.append(entry)
    if not inserted:
        merged.append(item)
    return merged

def render_body(items):
    if not items:
        return "\n    "
    return "\n" + "\n".join(f"    {entry}" for entry in items) + "\n    "

if "<!-- AUTO LIST START -->" in html and "<!-- AUTO LIST END -->" in html:
    match = re.search(
        r"(<!-- AUTO LIST START -->)(.*?)(<!-- AUTO LIST END -->)",
        html,
        flags=re.S,
    )
    if not match:
        print(">>> 找不到 AUTO LIST 區塊，略過首頁更新")
        sys.exit(1)
    items = merge_items(split_items(match.group(2)))
    html = html[: match.start(2)] + render_body(items) + html[match.end(2) :]
elif "<!-- AUTO LIST -->" in html:
    html = html.replace(
        "<!-- AUTO LIST -->",
        f"<!-- AUTO LIST START -->\n    {item}\n    <!-- AUTO LIST END -->",
        1,
    )
else:
    m = re.search(
        r'(<ul[^>]*class="[^"]*\bauto-list\b[^"]*"[^>]*>)(.*?)(</ul>)',
        html,
        flags=re.IGNORECASE | re.S,
    )
    if m:
        items = merge_items(split_items(m.group(2)))
        html = html[: m.start(2)] + render_body(items) + html[m.end(2) :]
    else:
        html += f"\n<ul class=\"auto-list\">\n  {item}\n</ul>\n"
home.write_text(html)
print(">>> 首頁已更新")
PY

rm -f "$HOME_ITEMS_TMP"
rm -f "$TMP_CARDS"

# 建立 fits 目錄 index.html 的函式（僅 PNG）
build_fits_index() {
  local dir="$1"
  local out="${dir}/index.html"
  # 新增：若檔案存在且未強制重建則略過
  if [[ -f "$out" && "$FORCE_REGEN_FIT" != "1" && "$DID_FITS_SYNC" != "1" ]]; then
    echo ">>> fits/index.html 已存在（跳過，設 FORCE_REGEN_FIT=1 可強制重建）"
    return 0
  fi
  if [[ ! -d "$dir" ]]; then
    echo "⚠️ fits 目錄不存在：$dir"
    return 1
  fi
  local tmp_cards
  tmp_cards="$(mktemp)"

  (
    cd "$dir"
    # 只抓 PNG；若無檔案，後續補一個空白提示
    # 用 -print -quit 避免在 pipefail 下因 grep -q 提前結束而被誤判為失敗。
    if ! find . -type f -iname '*.png' -print -quit | LC_ALL=C grep -q .; then
      cat > "$tmp_cards" <<'EMPTY'
<div class="card">
  <div class="pdf" style="height:240px;font-size:1rem">No PNG files found.</div>
  <div class="name">—</div>
</div>
EMPTY
    else
      python3 - "$tmp_cards" <<'PY'
import sys, html, pathlib
cards_path = pathlib.Path(sys.argv[1])
root = pathlib.Path(".")
pngs = sorted(
    str(p.relative_to(root)).replace("\\", "/")
    for p in root.rglob("*")
    if p.is_file() and p.suffix.lower() == ".png"
)
lines=[]
for raw in pngs:
    if not raw.strip(): continue
    name = raw.strip()
    esc = html.escape(name)
    lines.append(f'<a class="card" href="./{esc}">'
                 f'<img loading="lazy" src="./{esc}" alt="{esc}">'
                 f'<div class="name">{esc}</div></a>')
cards_path.write_text("\n".join(lines))
PY
    fi
  ) || { echo "❌ 無法列出 PNG"; rm -f "$tmp_cards"; return 1; }

  cat > "$out" <<HTML
<!doctype html>
<html lang="en" id="top">
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fit plots</title>
<style>
  :root{--mx:22px} html,body{margin:0;padding:0}
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;background:#fff}
  header{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:14px var(--mx);z-index:10}
  header h1{margin:0;font-size:1.1rem}
  main{max-width:1400px;margin:0 auto;padding:18px var(--mx) 34px}
  a{color:#0b5bd3;text-decoration:none} a:hover{text-decoration:underline}
  nav.breadcrumb{font-size:1.1rem;margin:0 0 12px}
  
  /* 卡片網格：每個卡片最小寬度從 260px → 340px */
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(1000px,1fr));gap:10px}

  /* 卡片外觀：圓角更大、邊距更寬 */
  .card{border:1px solid #e0e0e0;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.06);min-height:800px;line-height:0;margin:0;}

  /* 圖片區塊高度加大 */
  .card img{width:103%;height:780px;object-fit:contain;object-position:center;background:#fafafa;margin:0;padding:0;}

  /* 檔名文字加大 */
  .name{font-size:1.05rem;padding:5px 6px;border-top:1px solid #eee;word-break:break-all;}

  /* PDF 卡片的中央文字也放大並配合圖片高度 */
  .pdf{display:flex;align-items:center;justify-content:center;height:320px;background:#fafafa;font-size:1.1rem}

  .toplink{position:fixed;right:16px;bottom:16px;background:#0b5bd3;color:#fff;padding:8px 12px;border-radius:999px;text-decoration:none}
  .caption{color:#555;font-size:.92rem;margin-top:8px}
  nav.breadcrumb{margin:8px 0 0;font-size:1.3rem}

</style>
<header>
  <h1>Fit Plots</h1>
  <nav class="breadcrumb">
    <a href="../">← Back to Previous Page</a>
  </nav>
</header>
<main>
  <div class="grid">
$(cat "$tmp_cards")
  </div>
</main>
<a class="toplink" href="#top">Back to Top</a>
</html>
HTML

  if [[ ! -s "$out" ]]; then
    echo "❌ 生成 ${out} 失敗"
    rm -f "$tmp_cards"
    return 1
  fi
  rm -f "$tmp_cards"
  echo "✅ 已生成 ${out}"
}

rm -f "$TMP_CARDS"

# 重新建立 fits/index.html
build_fits_index "$FITSD"

HOME_PATH="/${HOME_URL#/}"
HOME_PATH="${HOME_PATH%/}/"
DEST_PATH="${DEST_REL%/}/"
echo "🌐 網址：https://pelai.web.cern.ch${HOME_PATH}${DEST_PATH}"
echo "🏠 首頁：https://pelai.web.cern.ch${HOME_PATH}"
