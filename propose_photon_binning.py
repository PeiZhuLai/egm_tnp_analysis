#!/usr/bin/env python3
"""Propose a coarser (nPV, et) binning for the photon CSEV measurements.

Several bins cannot be fitted at all because a leg is empty -- the extreme case
is 2023postBPixHole bin01, whose failing histogram has zero entries, so the
framework's yield range nSigF[nTot*0.9, 0.5, nTot*1.5] collapses to the single
point [0.5, 0.5] and no parameter can move. That is a binning problem; no amount
of parameter tuning creates events.

The empties are all at LOW nPV (pileup peaks near 30-40, so the first nPV slice
is always thin) and get worse with et. The binning is a rectangular product of
per-variable edge lists, so a merge can only move edges, not treat one et row
differently from another.

Strategy, cheapest change first:
  1. merge adjacent nPV slices from the low end until every (nPV, et) cell clears
     the thresholds -- this keeps the et dependence the SF is applied against
  2. only if nPV has collapsed to a single slice and cells still fail, merge et
     rows from the top down

Cell counts for a merged bin are just the sums of the cells it covers, so the
proposal is computed from the histograms already on disk -- no refit needed to
know what the merged bin would contain.
"""
import glob, os, pickle, re, sys
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

# 2026-08-23: 門檻由實測標定,不是猜的。把今天重跑的 516 個 failing 側依事件數分組,
# 統計「誤差算得出來(零誤差=0 且 covQual>=2)」的比例:
#     0-20: 58%   20-40: 59%   40-60: 60%   60-80: 50%
#    80-120: 86%  120-200: 76%  200-400: 96%  400+: 99%
# 轉折在 fail≈80,與單一 measurement 的逐 bin 觀察一致(hr9_2023postBPix: >=86 成功、<=63 失敗)。
# 先前用 30 是憑感覺,會留下一批「擬合跑得動但拿不到誤差」的格子。
MIN_FAIL = 80
MIN_PASS = 200


def counts(d, flag):
    pkl = os.path.join(d, 'bining.pkl')
    bins = pickle.load(open(pkl, 'rb'))['bins']
    hs = glob.glob(os.path.join(d, 'Data_*_%s.root' % flag))
    if not hs:
        return None
    fh = ROOT.TFile.Open(hs[0])
    cells = {}
    for b in bins:
        m = re.search(r'nPV_([\d p]+)To([\d p]+)_ph_et_([\d p]+)To([\d p]+)', b['name'])
        if not m:
            continue
        f = lambda s: float(s.replace('p', '.'))
        key = (f(m.group(1)), f(m.group(2)), f(m.group(3)), f(m.group(4)))
        hp = fh.Get('%s_Pass' % b['name'])
        hf = fh.Get('%s_Fail' % b['name'])
        cells[key] = (hp.Integral() if hp else 0.0, hf.Integral() if hf else 0.0)
    fh.Close()
    return cells


def edges(cells, idx):
    lo = sorted({k[idx] for k in cells})
    hi = sorted({k[idx + 1] for k in cells})
    return lo + [hi[-1]]


def grid_ok(cells, npv, et):
    """Sum the original cells into the proposed grid and test every cell."""
    bad = []
    for i in range(len(npv) - 1):
        for j in range(len(et) - 1):
            p = f = 0.0
            for (a, b, c, e), (cp, cf) in cells.items():
                if a >= npv[i] and b <= npv[i + 1] and c >= et[j] and e <= et[j + 1]:
                    p += cp
                    f += cf
            if f < MIN_FAIL or p < MIN_PASS:
                bad.append((npv[i], npv[i + 1], et[j], et[j + 1], p, f))
    return bad


def propose(cells):
    npv = edges(cells, 0)
    et = edges(cells, 2)
    # 1) merge nPV from the low end
    while len(npv) > 2 and grid_ok(cells, npv, et):
        trial = npv[:1] + npv[2:]          # drop the first internal edge
        if not grid_ok(cells, trial, et):
            return trial, et, 'nPV merged'
        npv = trial
    if not grid_ok(cells, npv, et):
        return npv, et, 'nPV merged'
    # 2) fall back to merging et rows from the top
    while len(et) > 2:
        et = et[:-2] + et[-1:]
        if not grid_ok(cells, npv, et):
            return npv, et, 'nPV+et merged'
    return npv, et, 'STILL BAD'


def main(pattern):
    base = '/eos/home-p/pelai/HZa/root_TnP'
    for d in sorted(glob.glob(os.path.join(base, pattern))):
        flag = os.path.basename(d)
        if any(t in flag for t in ('_bkg_', '_puup_', '_pudown_', '_summary_')):
            continue
        cells = counts(d, flag)
        if not cells:
            continue
        npv0, et0 = edges(cells, 0), edges(cells, 2)
        bad0 = grid_ok(cells, npv0, et0)
        short = flag.replace('hza_resolve_phcsev_', '').replace('_sf', '')
        if not bad0:
            print('%-24s OK  nPV=%s et=%s' % (short, npv0, et0))
            continue
        npv, et, how = propose(cells)
        bad = grid_ok(cells, npv, et)
        print('%-24s %d bad cell(s) -> %s' % (short, len(bad0), how))
        print('     現行  nPV=%s  et=%s  (%d bins)' % (npv0, et0, (len(npv0)-1)*(len(et0)-1)))
        print('     建議  nPV=%s  et=%s  (%d bins)%s' % (
            npv, et, (len(npv)-1)*(len(et)-1),
            '   仍有 %d 格不足' % len(bad) if bad else '   全部達標'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'hza_resolve_phcsev_*_sf')
