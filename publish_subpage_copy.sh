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
# ------------------------------------------------------------
# 必填參數：
#   --dest <EOS放圖的相對路徑>    例如: resolve_ph_2022preEE/hza_resolve_phid_2022preEE
#   --title <頁面標題>           例如: "Efficiency / Scale Factor Measurements — hza_resolve_phid_2022preEE"
#
# 可選參數：
#   --src-fits <所有fit plots來源目錄>     例如: /eos/home-p/pelai/HZa/root_TnP/muon_2023/hzg_muid_2023/fits
#   --src-summary <Summary plots來源目錄> 例如: /eos/home-p/pelai/HZa/root_TnP/muon_2023/hzg_muid_2023/summary
#   --web-root <根路徑>         預設: /eos/user/p/pelai/www/HZa/sfs
#   --home-url <首頁URL>        預設: /HZa/sfs/
#   --section-url <錨點>        例如: "#Resolved_Custom_Photon_ID_2022preEE"
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
SRC_SUMMARY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --web-root)     WEB_ROOT="$2"; shift 2;;
    --home-url)     HOME_URL="$2"; shift 2;;
    --section-url)  SECTION_URL="$2"; shift 2;;
    --dest)         DEST_REL="$2"; shift 2;;
    --hometitle)    ITEM_TITLE="$2"; shift 2;;
    --title)        TITLE="$2"; shift 2;;
    --src-fits)     SRC_FITS="$2"; shift 2;;
    --src-summary)  SRC_SUMMARY="$2"; shift 2;;
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
if [[ -n "${SRC_FITS}" && -d "${SRC_FITS}" ]]; then
  echo ">>> 同步 fits/ 來源（僅 PNG）：${SRC_FITS}"
  rsync -avL --include='*/' --include='*.png' --exclude='*' "${SRC_FITS%/}/" "${FITSD}/"
fi
if [[ -n "${SRC_SUMMARY}" && -d "${SRC_SUMMARY}" ]]; then
  echo ">>> 同步 summary/ 來源（僅 PNG）：${SRC_SUMMARY}"
  rsync -avL --delete \
    --include='*/' \
    --include=**/HZa_{SF2D_hza,SFvseta,SFvspT}_*.png \
    --exclude='*' \
    "${SRC_SUMMARY%/}/" "${SUMMD}/"
fi

INDEX="${DEST_DIR}/index.html"
FORCE_REGEN_SUB="${FORCE_REGEN_SUB:-0}"
if [[ ! -f "$INDEX" || "$FORCE_REGEN_SUB" == "1" ]]; then
  echo ">>> 生成 Sub-page index.html"
  cat > "$INDEX" <<HTML
<!doctype html>
<html lang="en" id="top">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${TITLE}</title>
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
  nav.breadcrumb{margin:8px 0 0;font-size:.92rem}
</style>

<header>
  <h1>${TITLE}</h1>
  <nav class="breadcrumb">
    <a href="${HOME_URL}">← Back to home</a>
  </nav>
</header>

<main>
  <p class="muted">This page was auto-generated. Last updated: <span id="ts"></span></p>

  <h2>All fit plots can be found <a href="fits/" target="_blank">here</a>.</h2>

  <h2>Summary plots</h2>

  <div class="grid">
    <!-- AUTO SUMMARY -->
  </div>

</main>

<a class="toplink" href="#top">Back to top</a>

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

find "summary" -type f \( -iname '*.png' -o -iname '*.pdf' \) \
| LC_ALL=C sort \
| awk '
  {
    n=$0; ext=tolower(n);
    gsub(/^\.\//,"",n);
    if (ext ~ /\.pdf$/) {
      printf("<a class=\"card\" href=\"%s\" target=\"_blank\"><div class=\"pdf\">📄 %s</div><div class=\"name\">%s</div></a>\n", n, n, n);
    } else {
      printf("<a class=\"card\" href=\"%s\" target=\"_blank\"><img loading=\"lazy\" src=\"%s\" alt=\"%s\"><div class=\"name\">%s</div></a>\n", n, n, n, n);
    }
  }' > "$TMP_CARDS"

# 插入卡片至佔位符
python3 - "$INDEX" "$TMP_CARDS" <<'PY'
import re, sys, pathlib
index_path = pathlib.Path(sys.argv[1])
cards_path = pathlib.Path(sys.argv[2])
html = index_path.read_text()
cards = cards_path.read_text()
html = re.sub(r"<!-- AUTO SUMMARY -->", cards, html, count=1)
index_path.write_text(html)
print("index.html updated.")
PY

# ---- 更新首頁 (WEB_ROOT/index.html) ----
HOME_INDEX="${WEB_ROOT%/}/index.html"
NEW_ITEM="<li><a href=\"./${DEST_REL%/}/\">${ITEM_TITLE}</a></li>"

FORCE_REGEN_HOME="${FORCE_REGEN_HOME:-0}"
if [[ ! -f "$HOME_INDEX" || "$FORCE_REGEN_HOME" == "1" ]]; then
  echo ">>> 建立首頁 ${HOME_INDEX}"
  cat > "$HOME_INDEX" <<HTML
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>/HZa/sf</title>
<style>
  .center { text-align: center; }
  .center ul { display: inline-block; text-align: left; }
</style>
<div class="center">
  <h2>Welcome to H -> Za -> ll gamma gamma Efficiency / Scale Factors Measurement</h2>
  <p>
    This page contains links to the scale factor measurement fits and results for the Run 3 2022+2023+2024 Higgs to Za analysis.<br>
    Presentations will be given to the MUO POG
    <a href="https://indico.cern.ch/event/XXXXXXX" target="_blank">here</a>
    and to the EGM POG
    <a href="https://indico.cern.ch/event/YYYYYYY" target="_blank">here</a>.
    (Left the space for the future)<br>
    See below links for plots.
  </p>
  <ul>
    <!-- AUTO LIST -->
  </ul>
</div>
</html>
HTML
fi  # 補上遺漏的 fi，避免腳本語法錯誤

python3 - "$HOME_INDEX" "$NEW_ITEM" <<'PY'
import sys, pathlib, re
home = pathlib.Path(sys.argv[1])
item = sys.argv[2].strip()
if not home.exists():
    print(f">>> 首頁檔案不存在：{home}")
    sys.exit(1)
html = home.read_text()
if re.search(re.escape(item), html):
    print(">>> 首頁已包含此條目，略過新增")
    sys.exit(0)
if "<!-- AUTO LIST -->" in html:
    html = html.replace("<!-- AUTO LIST -->", f"<!-- AUTO LIST -->\n  {item}", 1)
else:
    m = re.search(r"</ul>", html, flags=re.IGNORECASE)
    if m:
        pos = m.start()
        html = html[:pos] + f"  {item}\n" + html[pos:]
    else:
        html += f"\n<ul>\n  {item}\n</ul>\n"
home.write_text(html)
print(">>> 首頁已更新")
PY

rm -f "$TMP_CARDS"

# 建立 fits 目錄 index.html 的函式（僅 PNG）
build_fits_index() {
  local dir="$1"
  local out="${dir}/index.html"
  if [[ ! -d "$dir" ]]; then
    echo "⚠️ fits 目錄不存在：$dir"
    return 1
  fi
  local tmp_cards
  tmp_cards="$(mktemp)"

  (
    cd "$dir"
    # 只抓 PNG；若無檔案，後續補一個空白提示
    mapfile -t pngs < <(find . -type f -iname '*.png' | LC_ALL=C sort)
    if [[ "${#pngs[@]}" -eq 0 ]]; then
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
lines=[]
for p in sys.stdin:
    pass  # (使用 mapfile 方式，此段不讀)
# 重新列舉，保持排序
import subprocess
pngs = subprocess.check_output(["bash","-lc","find . -type f -iname '*.png' | LC_ALL=C sort"]).decode().strip().splitlines()
for raw in pngs:
    if not raw.strip(): continue
    name = raw.strip().lstrip('./')
    esc = html.escape(name)
    lines.append(f'<a class="card" href="./{esc}" target="_blank">'
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
<title>Fit plots (PNG only)</title>
<style>
  :root{--mx:22px} html,body{margin:0;padding:0}
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;background:#fff}
  header{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:14px var(--mx);z-index:10}
  header h1{margin:0;font-size:1.1rem}
  main{max-width:1400px;margin:0 auto;padding:18px var(--mx) 34px}
  a{color:#0b5bd3;text-decoration:none} a:hover{text-decoration:underline}
  nav.breadcrumb{font-size:.85rem;margin:0 0 12px}
  
  /* 卡片網格：每個卡片最小寬度從 260px → 340px */
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(500px,1fr));gap:20px}

  /* 卡片外觀：圓角更大、邊距更寬 */
  .card{border:1px solid #e0e0e0;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.06);min-height:400px;}

  /* 圖片區塊高度加大 */
  .card img{width:100%;height:380px;object-fit:contain;background:#fafafa}

  /* 檔名文字加大 */
  .name{font-size:1.05rem;padding:12px 14px;border-top:1px solid #eee;word-break:break-all}

  /* PDF 卡片的中央文字也放大並配合圖片高度 */
  .pdf{display:flex;align-items:center;justify-content:center;height:320px;background:#fafafa;font-size:1.1rem}

  .name{font-size:.85rem;padding:10px 12px;border-top:1px solid #eee;word-break:break-all}
</style>
<header>
  <h1>Fit plots</h1>
  <nav class="breadcrumb">
    <a href="../">← Back to previous page</a>
  </nav>
</header>
<main>
  <div class="grid">
$(cat "$tmp_cards")
  </div>
</main>
<a class="toplink" href="#top">Back to top</a>
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

echo "🌐 網址：https://pelai.web.cern.ch/HZa/sfs/${DEST_REL}/"
echo "🏠 首頁：https://pelai.web.cern.ch/HZa/sfs/"
