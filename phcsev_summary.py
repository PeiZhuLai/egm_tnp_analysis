#!/usr/bin/env python3
"""Build photon CSEV scale-factor summaries with total uncertainties.

The script reads the ``egammaEffi*.txt`` files produced by ``tnpEGM_fitter.py``
for nominal, signal+background, PU-up, and PU-down jobs, then writes per-bin
SF uncertainty summaries and comparison plots.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np


DEFAULT_BASE_DIR = "/eos/home-p/pelai/HZa/root_TnP"
DEFAULT_ERAS = (
    "2022preEE",
    "2022postEE",
    "2023preBPix",
    "2023postBPix",
    "2023postBPixHole",
    "2024",
)
DEFAULT_R9 = ("hr9", "lr9")
VARIATIONS = ("nominal", "bkg", "puup", "pudown")
EPS = 1.0e-12


@dataclass(frozen=True)
class BinKey:
    var1_low: float
    var1_high: float
    var2_low: float
    var2_high: float


@dataclass
class EffRecord:
    key: BinKey
    var1_name: str
    var2_name: str
    eff_data: float
    eff_data_err: float
    eff_mc: float
    eff_mc_err: float
    sf: float


def _as_array(value):
    return np.asarray(value, dtype=float)


def _safe_divide(numerator, denominator, default=0.0):
    numerator_arr = _as_array(numerator)
    denominator_arr = _as_array(denominator)
    out = np.full(np.broadcast_shapes(numerator_arr.shape, denominator_arr.shape), default, dtype=float)
    return np.divide(numerator_arr, denominator_arr, out=out, where=np.abs(denominator_arr) > EPS)


def _return_scalar_if_scalar(reference, value):
    if np.asarray(reference).shape == ():
        return float(np.asarray(value))
    return value


def compute_sf_uncertainty(
    eff_data,
    eff_data_err,
    eff_mc,
    eff_mc_err,
    sf_sig,
    sf_sig_bkg,
    sf_nom,
    sf_up,
    sf_down,
):
    """Compute nominal, background, pileup, and total SF uncertainties.

    All uncertainty components are relative except ``sf_nom_err`` and
    ``sf_total_err``, which are absolute errors on the scale factor. Inputs can
    be scalars or numpy-compatible arrays.
    """

    eff_data = _as_array(eff_data)
    eff_data_err = _as_array(eff_data_err)
    eff_mc = _as_array(eff_mc)
    eff_mc_err = _as_array(eff_mc_err)
    sf_sig = _as_array(sf_sig)
    sf_sig_bkg = _as_array(sf_sig_bkg)
    sf_nom = _as_array(sf_nom)
    sf_up = _as_array(sf_up)
    sf_down = _as_array(sf_down)

    rel_data = _safe_divide(eff_data_err, eff_data, default=0.0)
    rel_mc = _safe_divide(eff_mc_err, eff_mc, default=0.0)
    sigma_nom_rel = np.sqrt(rel_data * rel_data + rel_mc * rel_mc)
    sigma_nom_rel = np.where((np.abs(eff_data) > EPS) & (np.abs(eff_mc) > EPS), sigma_nom_rel, 0.0)
    sf_nom_err = sf_nom * sigma_nom_rel

    sigma_bkg_rel = _safe_divide(np.abs(sf_sig - sf_sig_bkg), sf_sig, default=0.0)
    sigma_pileup_rel = _safe_divide(
        np.abs(sf_up - sf_nom) + np.abs(sf_down - sf_nom),
        2.0 * sf_nom,
        default=0.0,
    )

    sigma_total_rel = np.sqrt(
        sigma_bkg_rel * sigma_bkg_rel
        + sigma_pileup_rel * sigma_pileup_rel
        + sigma_nom_rel * sigma_nom_rel
    )
    sigma_total_rel = np.where(np.abs(sf_nom) > EPS, sigma_total_rel, 0.0)
    sf_total_err = sf_nom * sigma_total_rel

    return {
        "sf_nom": _return_scalar_if_scalar(sf_nom, sf_nom),
        "sf_nom_err": _return_scalar_if_scalar(sf_nom, sf_nom_err),
        "sigma_nom_rel": _return_scalar_if_scalar(sf_nom, sigma_nom_rel),
        "sigma_bkg_rel": _return_scalar_if_scalar(sf_nom, sigma_bkg_rel),
        "sigma_pileup_rel": _return_scalar_if_scalar(sf_nom, sigma_pileup_rel),
        "sigma_total_rel": _return_scalar_if_scalar(sf_nom, sigma_total_rel),
        "sf_total_err": _return_scalar_if_scalar(sf_nom, sf_total_err),
    }


def normalize_axis_name(axis_name: str) -> str:
    lowered = axis_name.strip().lower()
    if "eta" in lowered:
        return "eta"
    if "npv" in lowered or "nvtx" in lowered or "vertex" in lowered:
        return "nvtx"
    if lowered in ("pt", "et", "ph_et", "el_et") or lowered.endswith("_pt") or lowered.endswith("_et"):
        return "pt"
    return lowered


def axis_title(axis_name: str) -> str:
    normalized = normalize_axis_name(axis_name)
    if normalized == "eta":
        return "eta"
    if normalized == "nvtx":
        return "N_{vtx}"
    if normalized == "pt":
        return "p_{T} [GeV]"
    return axis_name.strip()


def axis_file_token(axis_name: str) -> str:
    normalized = normalize_axis_name(axis_name)
    if normalized == "eta":
        return "Eta"
    if normalized == "nvtx":
        return "Nvtx"
    if normalized == "pt":
        return "Pt"
    return axis_name.strip().replace(" ", "")


def measurement_flag(r9: str, era: str, variation: str = "nominal") -> str:
    middle = f"{r9}_{era}" if variation == "nominal" else f"{r9}_{variation}_{era}"
    return f"hza_resolve_phcsev_{middle}_sf"


def summary_flag(r9: str, era: str) -> str:
    return f"hza_resolve_phcsev_{r9}_summary_{era}_sf"


def find_efficiency_file(base_dir: str, flag: str) -> str:
    candidates = (
        os.path.join(base_dir, flag, "egammaEffi.txt"),
        os.path.join(base_dir, flag, "egammaLowptEffi.txt"),
        os.path.join(base_dir, flag, "egammaEffi_postBPixHole.txt"),
        os.path.join(base_dir, flag, "egammaLowptEffi_postBPixHole.txt"),
    )
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(
        "No efficiency text file found for %s. Tried: %s" % (flag, ", ".join(candidates))
    )


def _rounded_key(values: Sequence[float]) -> Tuple[float, float, float, float]:
    return tuple(round(float(value), 6) for value in values)  # type: ignore[return-value]


def read_efficiency_file(path: str) -> Tuple[str, str, Dict[Tuple[float, float, float, float], EffRecord]]:
    var1_name = "var1"
    var2_name = "var2"
    records: Dict[Tuple[float, float, float, float], EffRecord] = {}

    with open(path) as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("###"):
                header = line.lstrip("#").split(":", 1)
                if len(header) == 2:
                    name = header[0].strip().lower()
                    value = header[1].strip()
                    if name == "var1":
                        var1_name = value
                    elif name == "var2":
                        var2_name = value
                continue

            fields = line.split()
            if len(fields) < 8:
                continue
            try:
                values = [float(field) for field in fields[:8]]
            except ValueError:
                continue

            key_values = _rounded_key(values[:4])
            eff_data = values[4]
            eff_data_err = values[5]
            eff_mc = values[6]
            eff_mc_err = values[7]
            sf = float(_safe_divide(eff_data, eff_mc, default=0.0))
            records[key_values] = EffRecord(
                key=BinKey(*key_values),
                var1_name=var1_name,
                var2_name=var2_name,
                eff_data=eff_data,
                eff_data_err=eff_data_err,
                eff_mc=eff_mc,
                eff_mc_err=eff_mc_err,
                sf=sf,
            )

    if not records:
        raise ValueError("No efficiency records parsed from %s" % path)

    return var1_name, var2_name, records


def build_summary_records(
    nominal: Mapping[Tuple[float, float, float, float], EffRecord],
    bkg: Mapping[Tuple[float, float, float, float], EffRecord],
    puup: Mapping[Tuple[float, float, float, float], EffRecord],
    pudown: Mapping[Tuple[float, float, float, float], EffRecord],
) -> List[dict]:
    rows: List[dict] = []
    common_keys = sorted(set(nominal).intersection(bkg, puup, pudown))
    missing = {
        "bkg": len(set(nominal) - set(bkg)),
        "puup": len(set(nominal) - set(puup)),
        "pudown": len(set(nominal) - set(pudown)),
    }
    if any(missing.values()):
        print("[WARN] Missing matched bins relative to nominal:", missing)

    for key in common_keys:
        nom = nominal[key]
        unc = compute_sf_uncertainty(
            nom.eff_data,
            nom.eff_data_err,
            nom.eff_mc,
            nom.eff_mc_err,
            nom.sf,
            bkg[key].sf,
            nom.sf,
            puup[key].sf,
            pudown[key].sf,
        )
        rows.append(
            {
                "var1_low": nom.key.var1_low,
                "var1_high": nom.key.var1_high,
                "var2_low": nom.key.var2_low,
                "var2_high": nom.key.var2_high,
                "eff_data": nom.eff_data,
                "eff_data_err": nom.eff_data_err,
                "eff_mc": nom.eff_mc,
                "eff_mc_err": nom.eff_mc_err,
                "sf_sig": nom.sf,
                "sf_sig_bkg": bkg[key].sf,
                "sf_nom": unc["sf_nom"],
                "sf_up": puup[key].sf,
                "sf_down": pudown[key].sf,
                "sf_nom_err": unc["sf_nom_err"],
                "sigma_nom_rel": unc["sigma_nom_rel"],
                "sigma_bkg_rel": unc["sigma_bkg_rel"],
                "sigma_pileup_rel": unc["sigma_pileup_rel"],
                "sigma_total_rel": unc["sigma_total_rel"],
                "sf_total_err": unc["sf_total_err"],
            }
        )

    return rows


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_csv(path: str, rows: Sequence[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_txt(path: str, var1_name: str, var2_name: str, rows: Sequence[dict]) -> None:
    with open(path, "w") as handle:
        handle.write("### var1 : %s\n" % var1_name)
        handle.write("### var2 : %s\n" % var2_name)
        handle.write(
            "### columns : var1_low var1_high var2_low var2_high eff_data eff_data_err "
            "eff_mc eff_mc_err sf_nom sf_total_err sigma_total_rel sigma_nom_rel "
            "sigma_bkg_rel sigma_pileup_rel sf_sig_bkg sf_up sf_down\n"
        )
        for row in rows:
            handle.write(
                "%+8.5f\t%+8.5f\t%+8.5f\t%+8.5f\t"
                "%5.5f\t%5.5f\t%5.5f\t%5.5f\t"
                "%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\t%5.5f\n"
                % (
                    row["var1_low"],
                    row["var1_high"],
                    row["var2_low"],
                    row["var2_high"],
                    row["eff_data"],
                    row["eff_data_err"],
                    row["eff_mc"],
                    row["eff_mc_err"],
                    row["sf_nom"],
                    row["sf_total_err"],
                    row["sigma_total_rel"],
                    row["sigma_nom_rel"],
                    row["sigma_bkg_rel"],
                    row["sigma_pileup_rel"],
                    row["sf_sig_bkg"],
                    row["sf_up"],
                    row["sf_down"],
                )
            )


def write_json(path: str, metadata: Mapping[str, object], rows: Sequence[dict]) -> None:
    with open(path, "w") as handle:
        json.dump({"metadata": metadata, "bins": list(rows)}, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _setup_matplotlib():
    mpl_config = os.path.join(os.environ.get("TMPDIR", "/tmp"), "phcsev_summary_mpl")
    os.makedirs(mpl_config, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", mpl_config)
    os.environ.setdefault("XDG_CACHE_HOME", mpl_config)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _row_axis_values(row: Mapping[str, float], axis_index: int) -> Tuple[float, float, float]:
    low = row[f"var{axis_index}_low"]
    high = row[f"var{axis_index}_high"]
    return low, high, 0.5 * (low + high)


def plot_axis_comparisons(
    out_dir: str,
    tag: str,
    var1_name: str,
    var2_name: str,
    rows: Sequence[dict],
    x_axis_kind: str,
) -> None:
    if not rows:
        return

    axes = {normalize_axis_name(var1_name): (1, var1_name), normalize_axis_name(var2_name): (2, var2_name)}
    if x_axis_kind not in axes:
        print("[WARN] Cannot draw SFvs%s for %s; axes are %s and %s" % (x_axis_kind, tag, var1_name, var2_name))
        return

    plt = _setup_matplotlib()
    x_axis_index, x_axis_name = axes[x_axis_kind]
    other_axis_index = 2 if x_axis_index == 1 else 1
    other_axis_name = var2_name if x_axis_index == 1 else var1_name

    groups: Dict[Tuple[float, float], List[dict]] = {}
    for row in rows:
        other_low, other_high, _ = _row_axis_values(row, other_axis_index)
        groups.setdefault((other_low, other_high), []).append(row)

    plots = (
        (
            "compare_sig_bkg",
            (("signal fit", "sf_sig", None), ("signal+background fit", "sf_sig_bkg", None)),
            "SF comparison: signal vs signal+background",
        ),
        (
            "compare_pileup",
            (("PU down", "sf_down", None), ("nominal", "sf_nom", None), ("PU up", "sf_up", None)),
            "SF comparison: PU variations",
        ),
        (
            "total_uncertainty",
            (("nominal total uncertainty", "sf_nom", "sf_total_err"),),
            "SF with total uncertainty",
        ),
    )

    for suffix, series, title in plots:
        fig, ax = plt.subplots(figsize=(9.0, 6.5))
        for group_key, group_rows in sorted(groups.items()):
            group_rows = sorted(group_rows, key=lambda row: _row_axis_values(row, x_axis_index)[2])
            x = np.array([_row_axis_values(row, x_axis_index)[2] for row in group_rows], dtype=float)
            xerr = np.array(
                [0.5 * (_row_axis_values(row, x_axis_index)[1] - _row_axis_values(row, x_axis_index)[0]) for row in group_rows],
                dtype=float,
            )
            group_label = "%g-%g %s" % (group_key[0], group_key[1], axis_title(other_axis_name))
            for label, y_key, err_key in series:
                y = np.array([row[y_key] for row in group_rows], dtype=float)
                yerr = np.array([row[err_key] for row in group_rows], dtype=float) if err_key else None
                full_label = "%s, %s" % (group_label, label)
                ax.errorbar(x, y, xerr=xerr, yerr=yerr, marker="o", linestyle="-", capsize=2.0, label=full_label)

        ax.axhline(1.0, color="black", linestyle="--", linewidth=1.0)
        ax.set_xlabel(axis_title(x_axis_name))
        ax.set_ylabel("Scale factor")
        ax.set_title(title)
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=7, ncol=1)
        fig.tight_layout()
        out_path = os.path.join(out_dir, "HZa_SFvs%s_%s_%s.png" % (axis_file_token(x_axis_name), suffix, tag))
        fig.savefig(out_path, dpi=160)
        plt.close(fig)


def plot_2d_summary(out_dir: str, tag: str, var1_name: str, var2_name: str, rows: Sequence[dict], value_key: str, title: str) -> None:
    if not rows:
        return
    plt = _setup_matplotlib()
    x_edges = sorted({row["var1_low"] for row in rows}.union({row["var1_high"] for row in rows}))
    y_edges = sorted({row["var2_low"] for row in rows}.union({row["var2_high"] for row in rows}))
    z = np.full((len(y_edges) - 1, len(x_edges) - 1), np.nan)
    x_lookup = {edge: idx for idx, edge in enumerate(x_edges[:-1])}
    y_lookup = {edge: idx for idx, edge in enumerate(y_edges[:-1])}
    for row in rows:
        z[y_lookup[row["var2_low"]], x_lookup[row["var1_low"]]] = row[value_key]

    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    mesh = ax.pcolormesh(np.array(x_edges), np.array(y_edges), z, shading="flat")
    fig.colorbar(mesh, ax=ax)
    for row in rows:
        ax.text(
            0.5 * (row["var1_low"] + row["var1_high"]),
            0.5 * (row["var2_low"] + row["var2_high"]),
            "%.3f" % row[value_key],
            ha="center",
            va="center",
            fontsize=7,
        )
    ax.set_xlabel(axis_title(var1_name))
    ax.set_ylabel(axis_title(var2_name))
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "HZa_2D_%s_%s.png" % (value_key, tag)), dpi=160)
    plt.close(fig)


def write_root(path: str, var1_name: str, var2_name: str, rows: Sequence[dict]) -> bool:
    try:
        import ROOT as rt  # type: ignore
    except Exception as exc:
        print("[WARN] PyROOT is not available; skip ROOT output (%s)." % exc)
        return False

    x_edges = sorted({row["var1_low"] for row in rows}.union({row["var1_high"] for row in rows}))
    y_edges = sorted({row["var2_low"] for row in rows}.union({row["var2_high"] for row in rows}))
    x_arr = np.array(x_edges, dtype=float)
    y_arr = np.array(y_edges, dtype=float)
    root_file = rt.TFile(path, "RECREATE")

    hist_specs = (
        ("EGamma_SF2D_total", "SF with total uncertainty", "sf_nom", "sf_total_err"),
        ("EGamma_SF2D_nominal_stat", "SF with nominal statistical uncertainty", "sf_nom", "sf_nom_err"),
        ("EGamma_SF2D_total_rel", "Relative total uncertainty", "sigma_total_rel", None),
        ("EGamma_SF2D_bkg_rel", "Relative background uncertainty", "sigma_bkg_rel", None),
        ("EGamma_SF2D_pileup_rel", "Relative pileup uncertainty", "sigma_pileup_rel", None),
        ("EGamma_SF2D_nominal_rel", "Relative nominal statistical uncertainty", "sigma_nom_rel", None),
    )
    for name, title, content_key, error_key in hist_specs:
        hist = rt.TH2F(
            name,
            "%s;%s;%s" % (title, axis_title(var1_name), axis_title(var2_name)),
            len(x_edges) - 1,
            x_arr,
            len(y_edges) - 1,
            y_arr,
        )
        for row in rows:
            xbin = hist.GetXaxis().FindBin(0.5 * (row["var1_low"] + row["var1_high"]))
            ybin = hist.GetYaxis().FindBin(0.5 * (row["var2_low"] + row["var2_high"]))
            hist.SetBinContent(xbin, ybin, row[content_key])
            if error_key is not None:
                hist.SetBinError(xbin, ybin, row[error_key])
        hist.Write(name, rt.TObject.kOverwrite)

    root_file.Close()
    return True


def process_one(base_dir: str, output_base_dir: str, r9: str, era: str, make_plots: bool, make_root: bool) -> Optional[str]:
    flags = {variation: measurement_flag(r9, era, variation) for variation in VARIATIONS}
    paths = {variation: find_efficiency_file(base_dir, flag) for variation, flag in flags.items()}

    parsed = {variation: read_efficiency_file(path) for variation, path in paths.items()}
    var1_name, var2_name, nominal_records = parsed["nominal"]
    for variation in ("bkg", "puup", "pudown"):
        if parsed[variation][0] != var1_name or parsed[variation][1] != var2_name:
            raise ValueError(
                "Axis mismatch for %s %s %s: nominal=(%s,%s), %s=(%s,%s)"
                % (r9, era, variation, var1_name, var2_name, variation, parsed[variation][0], parsed[variation][1])
            )

    rows = build_summary_records(
        nominal_records,
        parsed["bkg"][2],
        parsed["puup"][2],
        parsed["pudown"][2],
    )
    if not rows:
        raise ValueError("No matched bins found across nominal, bkg, puup, and pudown inputs.")

    out_flag = summary_flag(r9, era)
    out_dir = os.path.join(output_base_dir, out_flag)
    ensure_dir(out_dir)

    metadata = {
        "r9": r9,
        "era": era,
        "var1": var1_name,
        "var2": var2_name,
        "inputs": paths,
        "formula": "sqrt(background^2 + pileup^2 + nominal_stat^2)",
    }
    write_csv(os.path.join(out_dir, "phcsev_summary.csv"), rows)
    write_txt(os.path.join(out_dir, "egammaEffi_summary.txt"), var1_name, var2_name, rows)
    write_json(os.path.join(out_dir, "phcsev_summary.json"), metadata, rows)

    if make_plots:
        plot_axis_comparisons(out_dir, out_flag, var1_name, var2_name, rows, "eta")
        plot_axis_comparisons(out_dir, out_flag, var1_name, var2_name, rows, "nvtx")
        plot_2d_summary(out_dir, out_flag, var1_name, var2_name, rows, "sf_nom", "Nominal scale factor")
        plot_2d_summary(out_dir, out_flag, var1_name, var2_name, rows, "sf_total_err", "Absolute total SF uncertainty")
        plot_2d_summary(out_dir, out_flag, var1_name, var2_name, rows, "sigma_total_rel", "Relative total SF uncertainty")

    if make_root:
        write_root(os.path.join(out_dir, "%s.root" % out_flag), var1_name, var2_name, rows)

    print("[OK] %s: wrote %d bin(s) to %s" % (out_flag, len(rows), out_dir))
    return out_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize photon CSEV SF total uncertainties.")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR, help="Directory containing run_job output folders.")
    parser.add_argument("--output-base-dir", default=None, help="Directory for summary output folders. Defaults to --base-dir.")
    parser.add_argument("--eras", nargs="+", default=list(DEFAULT_ERAS), help="Eras to process.")
    parser.add_argument("--r9", nargs="+", default=list(DEFAULT_R9), choices=list(DEFAULT_R9), help="R9 categories to process.")
    parser.add_argument("--no-plots", action="store_true", help="Write tables only.")
    parser.add_argument("--no-root", action="store_true", help="Do not attempt PyROOT output.")
    parser.add_argument("--allow-missing", action="store_true", help="Skip missing input groups instead of failing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_base_dir = args.output_base_dir or args.base_dir
    failures = []
    written = []

    for r9 in args.r9:
        for era in args.eras:
            try:
                out_dir = process_one(
                    args.base_dir,
                    output_base_dir,
                    r9,
                    era,
                    make_plots=not args.no_plots,
                    make_root=not args.no_root,
                )
                if out_dir:
                    written.append(out_dir)
            except Exception as exc:
                message = "%s %s: %s" % (r9, era, exc)
                if args.allow_missing:
                    print("[WARN]", message)
                    failures.append(message)
                    continue
                raise

    print("Wrote %d summary directory/directories." % len(written))
    if failures:
        print("Skipped %d group(s)." % len(failures))
    return 0 if written or args.allow_missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
