# egm_tnp_analysis 腳本地圖

2026-09-12 整理。根目錄原本有 114 個 `.sh` / 36 個 `.py`，其中 87 個 `.sh` 是 2026-07
之間「使用者回報 N 格要調 → 新長一個一次性腳本」留下的。現在根目錄只放**還會再用到的
東西**，一次性的全部移到 `archive/oneshots_2026/`。

## 日常入口

| 想做的事 | 用這個 |
|---|---|
| 重擬合 + 重畫某幾格 | **`./tnp_refit.sh`** |
| 重跑整個 miniIso measurement（含 createHists / sumUp） | `1_run_miniiso.sh`（`0_launch_miniiso.sh` 幫你進 container） |
| 送 condor 逐格擬合 | `condor_fit/*.sub` → `condor_fit_worker*.sh` |
| 發布到 web area | `publish.sh` / `publish_subpage.sh` |

### `tnp_refit.sh` — 取代所有 `wrap_*` / `rerun_*` / `refit_*` / `run_*batch*`

```bash
./tnp_refit.sh elminiIso0p15_nongap_2024:altSig:18,19,20,21
./tnp_refit.sh -j 4 phid_lowpt_2023preBPix:nominal:7 phid_lowpt_2022preEE:nominal:3
./tnp_refit.sh -n elminiIso0p15_nongap_2025:nominal:all      # dry-run 只看檢查表
./tnp_refit.sh -f joblist.txt                                 # 一行一個 job
```

`<config>:<fitType>:<bins>`。config 寫別名即可，會在 `etc/config/hza_ele` 與
`etc/config/isoMyCorr` 兩處解析；`bins` 可以是 `all`。

它做了幾件舊腳本沒做、而且都是被實際的 bug 逼出來的事：

- **執行前印出每個 job 的 settings 路徑、flag、baseOutDir**。曾經有 29 條 joblist 解析到
  `settings_*_eoscms.py`，那個變體的 `baseOutDir` 指向另一棵樹，27 個 job 回 rc=0 卻把
  結果寫到錯的地方，只有逐 ProcId 比對才發現。baseOutDir 印出來就當場看得見。
- **flag 從 settings 的 `flags` 讀出來**，不是手打；一個 config 有多個 flag 就中止。
- **別名解析到多個 config 就中止並列出候選**，不猜。
- **開跑前先 `import egm_tnp_analysis`**。PYTHONPATH 設錯時 78 個 summary 曾在 2 分鐘內
  全滅，而每個 job 的 rc 看起來都正常。
- 併行度硬上限 6（lxplus 前台規定），逐格 status 檔，畫圖階段對 EOS 暫時性錯誤重試 3 次。

## `--addGaus`：不要下全域旗標

`--addGaus` 會把 failing 的 shoulder Gaussian 強加到**每一格**。完整比對量過：全開改善
699 個擬合、弄壞 1766 個 —— 那個成分只在 failing 真的是「窄峰 + shoulder」時有東西可
描述，其他格子只是白花一個自由度。

正常的路是 settings 檔自己的 `addGausBins`（可逐 fit type、逐 bin），
`tnpEGM_fitter._addgaus_for_bin()` 不需要任何旗標就會讀它：

```python
addGausBins = {'altSigFit': (18, 19, 20, 21)}   # 或 addGausBins = (18, 19, 20, 21)
```

`1_run_miniiso.sh` 在 2026-09-12 之前每一行 doFit 都帶 `--addGaus`，已經移除。
`condor_fit_worker.sh` 的 `TNP_ADDGAUS=1` 保留，但只給探索性 A/B 用。

## 診斷工具（判斷「改好了沒」的順序）

| 工具 | 回答什麼 |
|---|---|
| `fit_residuals.py <fit.root> --side pass\|fail\|both` | **最重要**：從存下來的 canvas 直接比對資料點與曲線，每 5 GeV 一段給 pull。參數撞界、edm 大都**不等於**形狀錯；只有這個看得出來 |
| `dump_one_fit.py <fit.root> <tag> [--full]` | 一個擬合的浮動參數、撞界標記、eff、edm、covQual |
| `verify_fits.py` | 殘差 slice + sigmaG + sigFrac + nSig/nBkg 誤差，一行一格 |
| `scan_railed_bkg.py` | 全掃 `nBkgF` 貼在下界的格子 |
| `audit_fits.py` / `judge_fits*.py` / `audit_coverage.py` | 批次健康度與覆蓋率 |
| `find_missing_fits.py` / `scan_unfitted.py` | 哪些格子根本沒擬合到 |

**驗收判準不能只看殘差。** 有一次殘差乾淨（0 slice）但 `sigmaGF` 漲到 12.4 GeV 變成寬
pedestal 去吃背景，`nSigF` 誤差從 484 膨脹到 1728、效率掉 2.4 個點。所以每次都要一起看：
殘差 slice 數、`sigmaGF` 有沒有變大到像 pedestal、`sigFracF` 有沒有退化到 0 或 1、
`nSig`/`nBkg` 誤差有沒有膨脹、以及**效率有沒有離開其他三種擬合的共識帶**。

## 一個一定要記得的坑

`dump_one_fit.py` 刻意設計成**一個檔案一個 process**。同一個 ROOT session 開多個
RooFitResult 檔會透過 TProcessID/TRef 互相串線，安靜地報出別的檔案的參數值
（看過 nSigP 從 6.4e5 變成 2.3e9）。不要為了快而把它改成迴圈開檔。

## `archive/oneshots_2026/`

保留成**紀錄**，不是可執行的入口。裡面很多腳本用 `cd "$(dirname "$BASH_SOURCE")"`
或相對路徑呼叫根目錄的 sibling，搬過去之後直接跑會失敗。要復現當時的某次操作，
看內容、用 `tnp_refit.sh` 重寫成 job 即可。
