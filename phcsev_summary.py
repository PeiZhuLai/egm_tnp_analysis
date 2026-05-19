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
import sys
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

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
ROOT_COLORS_HEX = (
    "#3f90da",
    "#ffa90e",
    "#bd1f01",
    "#94a4a2",
    "#832db6",
    "#a96b59",
    "#e76300",
    "#b9ac70",
    "#717581",
    "#92dadd",
    "#1a9850",
    "#4d4d4d",
)
ROOT_MARKERS = (20, 22, 21, 23, 33, 29, 43, 47, 34)
CMS_LABEL_RELPOSX = 0.12


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


def export_json_axis_name(axis_name: str) -> str:
    name = str(axis_name).strip()
    var_map = {
        "el_pt": "pt",
        "el_et": "pt",
        "el_sc_et": "pt",
        "probe_Ele_pt": "pt",
        "probe_pt": "pt",
        "ph_et": "pt",
        "ph_pt": "pt",
        "el_eta": "eta",
        "el_sc_eta": "eta",
        "probe_sc_eta": "eta",
        "ph_sc_eta": "eta",
        "ph_eta": "eta",
    }
    return var_map.get(name, name)


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


def root_axis_title(axis_name: str) -> str:
    normalized = normalize_axis_name(axis_name)
    if normalized == "eta":
        return "#eta"
    if normalized == "nvtx":
        return "N_{vtx}"
    if normalized == "pt":
        return "p_{T} [GeV]"
    return axis_name.strip()


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
        sf_fail_nom = float(_safe_divide(1.0 - nom.eff_data, 1.0 - nom.eff_mc, default=0.0))
        sf_fail_bkg = float(_safe_divide(1.0 - bkg[key].eff_data, 1.0 - bkg[key].eff_mc, default=0.0))
        sf_fail_up = float(_safe_divide(1.0 - puup[key].eff_data, 1.0 - puup[key].eff_mc, default=0.0))
        sf_fail_down = float(_safe_divide(1.0 - pudown[key].eff_data, 1.0 - pudown[key].eff_mc, default=0.0))
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
        unc_fail = compute_sf_uncertainty(
            1.0 - nom.eff_data,
            nom.eff_data_err,
            1.0 - nom.eff_mc,
            nom.eff_mc_err,
            sf_fail_nom,
            sf_fail_bkg,
            sf_fail_nom,
            sf_fail_up,
            sf_fail_down,
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
                "sf_fail": unc_fail["sf_nom"],
                "sf_fail_err": unc_fail["sf_total_err"],
                "sigma_fail_total_rel": unc_fail["sigma_total_rel"],
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


def _edges_for_rows(rows: Sequence[dict], axis_name: str, var_prefix: str) -> List[float]:
    lows = sorted({row[f"{var_prefix}_low"] for row in rows})
    last_high = max(row[f"{var_prefix}_high"] for row in rows)
    return lows + ([last_high] if lows[-1] != last_high else [])


def _multibinning_content(rows: Sequence[dict], axis_names: Sequence[str], value_name: str) -> Tuple[List[List[float]], List[float]]:
    import itertools

    axis_prefixes = {"var1": "var1", "var2": "var2"}
    edges_by_axis = {
        "var1": _edges_for_rows(rows, axis_names[0], "var1"),
        "var2": _edges_for_rows(rows, axis_names[1], "var2"),
    }
    values_by_bin = {}
    for row in rows:
        idx = (
            edges_by_axis["var1"].index(row["var1_low"]),
            edges_by_axis["var2"].index(row["var2_low"]),
        )
        values_by_bin[idx] = row[value_name]

    shape = [range(len(edges_by_axis["var1"]) - 1), range(len(edges_by_axis["var2"]) - 1)]
    content = [values_by_bin[tuple(idx)] for idx in itertools.product(*shape)]
    return [edges_by_axis[axis_prefixes["var1"]], edges_by_axis[axis_prefixes["var2"]]], content


def write_export_json(path: str, var1_name: str, var2_name: str, rows: Sequence[dict]) -> None:
    """Write the correctionlib schema-v2 JSON produced by fitter --exportJson."""

    axis_names = [export_json_axis_name(var1_name), export_json_axis_name(var2_name)]

    def _correction(name: str, content_key: str, output_description: str) -> dict:
        edges, content = _multibinning_content(rows, axis_names, content_key)
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
                "flow": "clamp",
            },
        }

    out_json = {
        "schema_version": 2,
        "description": "auto-generated photon CSEV scale factors with total uncertainty",
        "corrections": [
            _correction("sf_pass", "sf_nom", "data/MC scale factor (pass)"),
            _correction("unc_pass", "sf_total_err", "total uncertainty (pass)"),
            _correction("sf_fail", "sf_fail", "data/MC scale factor (fail)"),
            _correction("unc_fail", "sf_fail_err", "total uncertainty (fail)"),
            _correction("unc_pass_rel", "sigma_total_rel", "relative total uncertainty (pass)"),
            _correction("unc_pass_nominal_rel", "sigma_nom_rel", "relative nominal statistical uncertainty (pass)"),
            _correction("unc_pass_bkg_rel", "sigma_bkg_rel", "relative background uncertainty (pass)"),
            _correction("unc_pass_pileup_rel", "sigma_pileup_rel", "relative pileup uncertainty (pass)"),
        ],
    }
    with open(path, "w") as handle:
        json.dump(out_json, handle, indent=2)
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


def _load_root_modules():
    try:
        import ROOT as rt  # type: ignore
    except Exception:
        return None, None

    repo_dir = os.path.dirname(os.path.abspath(__file__))
    lib_dir = os.path.join(repo_dir, "libPython")
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)

    cms_lumi = None
    try:
        import tdrstyle  # type: ignore
        import CMS_lumi  # type: ignore

        tdrstyle.setTDRStyle()
        cms_lumi = CMS_lumi
    except Exception as exc:
        print("[WARN] ROOT plotting loaded, but CMS style modules are unavailable: %s" % exc)

    rt.gROOT.SetBatch(True)
    try:
        rt.gROOT.ProcessLine("gErrorIgnoreLevel = 1001;")
    except Exception:
        pass
    return rt, cms_lumi


def draw_cms_lumi_shifted(cms_lumi, canvas, era: str, position: int, rel_pos_x: float = CMS_LABEL_RELPOSX) -> None:
    """Draw the CMS Preliminary label with a local horizontal offset.

    CMS_lumi.py stores label placement in module globals.  Keep the adjustment
    local to phcsev_summary by restoring the original values immediately after
    drawing.
    """

    if cms_lumi is None:
        return
    saved = {
        "cmsText": getattr(cms_lumi, "cmsText", None),
        "writeExtraText": getattr(cms_lumi, "writeExtraText", None),
        "extraText": getattr(cms_lumi, "extraText", None),
        "lumi": getattr(cms_lumi, "lumi", None),
        "relPosX": getattr(cms_lumi, "relPosX", None),
    }
    cms_lumi.cmsText = "CMS"
    cms_lumi.writeExtraText = True
    cms_lumi.extraText = "Preliminary"
    cms_lumi.lumi = ""
    cms_lumi.relPosX = rel_pos_x
    try:
        cms_lumi.CMS_lumi(canvas, era, position)
    finally:
        for name, value in saved.items():
            if value is not None:
                setattr(cms_lumi, name, value)


def _apply_cms_lumi(cms_lumi, canvas, era: str, position: int) -> None:
    draw_cms_lumi_shifted(cms_lumi, canvas, era, position)


def _row_axis_values(row: Mapping[str, float], axis_index: int) -> Tuple[float, float, float]:
    low = row[f"var{axis_index}_low"]
    high = row[f"var{axis_index}_high"]
    return low, high, 0.5 * (low + high)


def _make_root_graph(rt, rows: Sequence[dict], x_axis_index: int, y_key: str, err_key: Optional[str] = None):
    from array import array

    x_vals = []
    y_vals = []
    x_err_low = []
    x_err_high = []
    y_err_low = []
    y_err_high = []
    for row in rows:
        x_low, x_high, x_mid = _row_axis_values(row, x_axis_index)
        y_val = row[y_key]
        y_err = row[err_key] if err_key else 0.0
        x_vals.append(x_mid)
        y_vals.append(y_val)
        x_err_low.append(x_mid - x_low)
        x_err_high.append(x_high - x_mid)
        y_err_low.append(y_err)
        y_err_high.append(y_err)

    return rt.TGraphAsymmErrors(
        len(x_vals),
        array("d", x_vals),
        array("d", y_vals),
        array("d", x_err_low),
        array("d", x_err_high),
        array("d", y_err_low),
        array("d", y_err_high),
    )


def _format_root_overlay_bin_label(axis_name: str, low: float, high: float) -> str:
    normalized = normalize_axis_name(axis_name)
    if normalized == "eta":
        return "%g <|#eta|< %g" % (low, high)
    if normalized == "pt":
        return "%g <p_{T}< %g GeV" % (low, high)
    if normalized == "nvtx":
        return "%g <N_{vtx}< %g" % (low, high)
    return "%s in [%g, %g)" % (root_axis_title(axis_name), low, high)


def plot_axis_comparisons(
    out_dir: str,
    tag: str,
    var1_name: str,
    var2_name: str,
    rows: Sequence[dict],
    x_axis_kind: str,
    warn_missing: bool = True,
) -> None:
    if not rows:
        return

    axes = {normalize_axis_name(var1_name): (1, var1_name), normalize_axis_name(var2_name): (2, var2_name)}
    if x_axis_kind not in axes:
        if warn_missing:
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
            (("sig", "sf_sig", None), ("sig+bkg", "sf_sig_bkg", None)),
            "",
        ),
        (
            "compare_pileup",
            (("puDown", "sf_down", None), ("nominal", "sf_nom", None), ("puUp", "sf_up", None)),
            "",
        ),
        (
            "total_uncertainty",
            (("", "sf_nom", "sf_total_err"),),
            "",
        ),
        (
            "nominal",
            (("nominal", "sf_nom", "sf_nom_err"),),
            "",
        ),
    )

    if plot_axis_comparisons_root(
        out_dir,
        tag,
        era_from_tag(tag),
        x_axis_index,
        x_axis_name,
        other_axis_index,
        other_axis_name,
        groups,
        plots,
    ):
        return

    for suffix, series, title in plots:
        needs_extra_x_title_space = normalize_axis_name(x_axis_name) == "pt"
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
        if needs_extra_x_title_space:
            ax.set_xlabel(axis_title(x_axis_name), labelpad=14)
        else:
            ax.set_xlabel(axis_title(x_axis_name))
        ax.set_ylabel("Scale factor")
        ax.set_title(title)
        ax.grid(True, alpha=0.25)
        legend_fontsize = 6 if suffix == "compare_pileup" and normalize_axis_name(x_axis_name) == "nvtx" else 7
        ax.legend(fontsize=legend_fontsize, ncol=1)
        fig.tight_layout()
        if needs_extra_x_title_space:
            fig.subplots_adjust(bottom=0.16)
        out_path = os.path.join(out_dir, "HZa_SFvs%s_%s_%s.png" % (axis_file_token(x_axis_name), suffix, tag))
        fig.savefig(out_path, dpi=160)
        plt.close(fig)


def era_from_tag(tag: str) -> str:
    for era in DEFAULT_ERAS:
        if era in tag:
            return era
    return ""


def plot_axis_comparisons_root(
    out_dir: str,
    tag: str,
    era: str,
    x_axis_index: int,
    x_axis_name: str,
    other_axis_index: int,
    other_axis_name: str,
    groups: Mapping[Tuple[float, float], List[dict]],
    plots: Sequence[Tuple[str, Sequence[Tuple[str, str, Optional[str]]], str]],
) -> bool:
    rt, cms_lumi = _load_root_modules()
    if rt is None:
        return False

    line_styles = (rt.kSolid, rt.kDashed, rt.kDotted, rt.kDashDotted)

    for suffix, series, title in plots:
        graphs = []
        legend_entries = []
        y_min = 1.0e9
        y_max = -1.0e9

        for gi, (group_key, group_rows) in enumerate(sorted(groups.items())):
            group_rows = sorted(group_rows, key=lambda row: _row_axis_values(row, x_axis_index)[2])
            color = rt.TColor.GetColor(ROOT_COLORS_HEX[gi % len(ROOT_COLORS_HEX)])
            for si, (series_label, y_key, err_key) in enumerate(series):
                graph = _make_root_graph(rt, group_rows, x_axis_index, y_key, err_key)
                graph.SetLineColor(color)
                graph.SetMarkerColor(color)
                graph.SetMarkerStyle(ROOT_MARKERS[(gi + si) % len(ROOT_MARKERS)])
                graph.SetMarkerSize(1.1)
                graph.SetLineStyle(line_styles[si % len(line_styles)])
                graph.SetLineWidth(4)
                for point_idx in range(graph.GetN()):
                    y_val = graph.GetPointY(point_idx)
                    y_min = min(y_min, y_val - graph.GetErrorYlow(point_idx))
                    y_max = max(y_max, y_val + graph.GetErrorYhigh(point_idx))
                graphs.append(graph)
                legend_entries.append(
                    (
                        graph,
                        "%s, %s"
                        % (
                            _format_root_overlay_bin_label(other_axis_name, group_key[0], group_key[1]),
                            series_label,
                        ),
                    )
                )

        if not graphs:
            continue

        out_stem = os.path.join(out_dir, "HZa_SFvs%s_%s_%s" % (axis_file_token(x_axis_name), suffix, tag))
        needs_extra_x_title_space = normalize_axis_name(x_axis_name) == "pt"
        canvas = rt.TCanvas(out_stem, out_stem, 900, 800)
        canvas.SetRightMargin(0.05)
        if needs_extra_x_title_space:
            canvas.SetBottomMargin(0.16)
        if normalize_axis_name(x_axis_name) == "pt":
            canvas.SetLogx()

        mg = rt.TMultiGraph()
        for graph in graphs:
            mg.Add(graph, "P")

        mg.Draw("A")
        mg.GetXaxis().SetTitle(root_axis_title(x_axis_name))
        if needs_extra_x_title_space:
            mg.GetXaxis().SetTitleOffset(1.2)
        mg.GetYaxis().SetTitle("Scale Factor")
        x_edges = sorted(
            {row[f"var{x_axis_index}_low"] for group in groups.values() for row in group}.union(
                {row[f"var{x_axis_index}_high"] for group in groups.values() for row in group}
            )
        )
        if x_edges:
            mg.GetXaxis().SetLimits(x_edges[0], x_edges[-1])
            mg.GetXaxis().SetRangeUser(x_edges[0], x_edges[-1])
        if normalize_axis_name(x_axis_name) == "pt":
            mg.GetXaxis().SetMoreLogLabels()
            mg.GetXaxis().SetNoExponent()

        if y_min < 1.0e8:
            span = max(y_max - y_min, 0.02)
            margin = max(0.02, 0.2 * span)
            mg.GetYaxis().SetRangeUser(max(0.0, y_min - margin), y_max + margin*4.5)
        else:
            mg.GetYaxis().SetRangeUser(0.8, 1.2)

        line = rt.TLine(x_edges[0], 1.0, x_edges[-1], 1.0) if x_edges else None
        if line is not None:
            line.SetLineStyle(rt.kDashed)
            line.SetLineWidth(4)
            line.Draw()

        if len(legend_entries) < 3:
            legend = rt.TLegend(0.32, 0.72, 0.92, 0.93)
        else:
            legend = rt.TLegend(0.32, 0.62, 0.92, 0.93)
        legend.SetNColumns(1 if len(legend_entries) < 7 else 2)
        legend.SetTextFont(42)
        if suffix == "compare_pileup" and normalize_axis_name(x_axis_name) == "nvtx":
            legend.SetTextSize(0.022)
        else:
            legend.SetTextSize(0.025 if len(legend_entries) > 12 else 0.029)
        legend.SetBorderSize(0)
        legend.SetFillStyle(0)
        for graph, label in legend_entries:
            legend.AddEntry(graph, label, "lp")
        legend.Draw()

        try:
            latex = rt.TLatex()
            latex.SetNDC()
            latex.SetTextFont(42)
            latex.SetTextSize(0.035)
            latex.DrawLatex(0.18, 0.94, str(title))
        except TypeError:
            pass

        _apply_cms_lumi(cms_lumi, canvas, era, 11)
        canvas.Modified()
        canvas.Update()
        canvas.Print(out_stem + ".png")
        canvas.Print(out_stem + ".pdf")

    return True


def plot_2d_summary(out_dir: str, tag: str, var1_name: str, var2_name: str, rows: Sequence[dict], value_key: str, title: str) -> None:
    if not rows:
        return
    if plot_2d_summary_root(out_dir, tag, era_from_tag(tag), var1_name, var2_name, rows, value_key, title):
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
    ax.set_xlabel(axis_title(var1_name), labelpad=15)
    ax.set_ylabel(axis_title(var2_name))
    ax.set_title(title)
    fig.subplots_adjust(bottom=0.15)
    fig.savefig(os.path.join(out_dir, "HZa_2D_%s_%s.png" % (value_key, tag)), dpi=160)
    plt.close(fig)


def make_root_2d_hist(rt, hist_name: str, var1_name: str, var2_name: str, rows: Sequence[dict], value_key: str, title: str):
    x_edges = sorted({row["var1_low"] for row in rows}.union({row["var1_high"] for row in rows}))
    y_edges = sorted({row["var2_low"] for row in rows}.union({row["var2_high"] for row in rows}))
    x_arr = np.array(x_edges, dtype=float)
    y_arr = np.array(y_edges, dtype=float)
    hist = rt.TH2F(
        hist_name,
        "%s;%s;%s" % (title, root_axis_title(var1_name), root_axis_title(var2_name)),
        len(x_edges) - 1,
        x_arr,
        len(y_edges) - 1,
        y_arr,
    )
    for row in rows:
        xbin = hist.GetXaxis().FindBin(0.5 * (row["var1_low"] + row["var1_high"]))
        ybin = hist.GetYaxis().FindBin(0.5 * (row["var2_low"] + row["var2_high"]))
        hist.SetBinContent(xbin, ybin, row[value_key])
    style_root_2d_hist(hist)
    return hist


def style_root_2d_hist(hist) -> None:
    hist.SetMarkerSize(1.8)
    hist.GetYaxis().SetTitleFont(42)
    hist.GetYaxis().SetLabelFont(42)
    hist.GetYaxis().SetTitleSize(0.06)
    hist.GetYaxis().SetLabelSize(0.05)
    hist.GetYaxis().SetTitleOffset(1.2)
    hist.GetXaxis().SetTitleFont(42)
    hist.GetXaxis().SetLabelFont(42)
    hist.GetXaxis().SetTitleSize(0.06)
    hist.GetXaxis().SetLabelSize(0.05)
    hist.GetXaxis().SetTitleOffset(1.1)
    hist.GetXaxis().SetLabelOffset(0.01)
    hist.GetZaxis().SetTitleFont(42)
    hist.GetZaxis().SetLabelFont(42)
    hist.GetZaxis().SetTitleSize(0.055)
    hist.GetZaxis().SetLabelSize(0.05)
    hist.GetZaxis().SetTitleOffset(0.75)


def plot_2d_pair_summary(
    out_dir: str,
    tag: str,
    var1_name: str,
    var2_name: str,
    rows: Sequence[dict],
) -> None:
    if not rows:
        return
    if plot_2d_pair_summary_root(out_dir, tag, era_from_tag(tag), var1_name, var2_name, rows):
        return

    plt = _setup_matplotlib()
    x_edges = sorted({row["var1_low"] for row in rows}.union({row["var1_high"] for row in rows}))
    y_edges = sorted({row["var2_low"] for row in rows}.union({row["var2_high"] for row in rows}))

    def _matrix(value_key: str):
        z = np.full((len(y_edges) - 1, len(x_edges) - 1), np.nan)
        x_lookup = {edge: idx for idx, edge in enumerate(x_edges[:-1])}
        y_lookup = {edge: idx for idx, edge in enumerate(y_edges[:-1])}
        for row in rows:
            z[y_lookup[row["var2_low"]], x_lookup[row["var1_low"]]] = row[value_key]
        return z

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 6.0))
    for ax, value_key, title in (
        (axes[0], "sf_nom", "e/gamma scale factors"),
        (axes[1], "sf_total_err", "e/gamma uncertainties"),
    ):
        mesh = ax.pcolormesh(np.array(x_edges), np.array(y_edges), _matrix(value_key), shading="flat")
        fig.colorbar(mesh, ax=ax)
        ax.set_xlabel(axis_title(var1_name))
        ax.set_ylabel(axis_title(var2_name))
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "HZa_SF2D_%s.png" % tag), dpi=160)
    plt.close(fig)


def plot_2d_pair_summary_root(
    out_dir: str,
    tag: str,
    era: str,
    var1_name: str,
    var2_name: str,
    rows: Sequence[dict],
) -> bool:
    rt, cms_lumi = _load_root_modules()
    if rt is None:
        return False

    rt.gStyle.SetPalette(1)
    rt.gStyle.SetPaintTextFormat("1.3f")
    rt.gStyle.SetOptTitle(1)

    hist_sf = make_root_2d_hist(
        rt,
        "h2_scaleFactorsEGamma_%s" % tag,
        var1_name,
        var2_name,
        rows,
        "sf_nom",
        "e/#gamma scale factors",
    )
    hist_err = make_root_2d_hist(
        rt,
        "h2_uncertaintiesEGamma_%s" % tag,
        var1_name,
        var2_name,
        rows,
        "sf_total_err",
        "e/#gamma uncertainties",
    )

    dmin = 1.0 - hist_sf.GetMinimum()
    dmax = hist_sf.GetMaximum() - 1.0
    dall = max(dmin, dmax)
    hist_sf.SetMinimum(1.0 - dall)
    hist_sf.SetMaximum(1.0 + dall)
    hist_err.SetMinimum(0.0)
    hist_err.SetMaximum(min(hist_err.GetMaximum(), 0.2))

    out_stem = os.path.join(out_dir, "HZa_SF2D_%s" % tag)
    canvas = rt.TCanvas("canScaleFactor_%s" % tag, "canScaleFactor", 900, 600)
    canvas.Divide(2, 1)
    canvas.GetPad(1).SetRightMargin(0.18)
    canvas.GetPad(1).SetLeftMargin(0.16)
    canvas.GetPad(1).SetTopMargin(0.10)
    canvas.GetPad(1).SetBottomMargin(0.13)
    canvas.GetPad(2).SetRightMargin(0.18)
    canvas.GetPad(2).SetLeftMargin(0.16)
    canvas.GetPad(2).SetTopMargin(0.10)
    canvas.GetPad(2).SetBottomMargin(0.13)
    canvas.cd(1)
    hist_sf.DrawCopy("colz TEXT45")
    canvas.cd(2)
    hist_err.DrawCopy("colz TEXT45")

    # For specific summary tags, manually draw CMS label shifted to the right
    if "hza_resolve_phcsev" in tag:
        latex = rt.TLatex()
        latex.SetNDC()
        latex.SetTextFont(61)
        latex.SetTextSize(0.06)
        latex.DrawLatex(0.35, 0.95, "CMS")
        latex.SetTextFont(52)
        latex.SetTextSize(0.045)
        latex.DrawLatex(0.59, 0.95, "Preliminary")
    else:
        draw_cms_lumi_shifted(cms_lumi, canvas, era, 0, rel_pos_x=CMS_LABEL_RELPOSX)
    canvas.Modified()
    canvas.Update()
    canvas.Print(out_stem + ".png")
    canvas.Print(out_stem + ".pdf")
    return True


def plot_2d_summary_root(
    out_dir: str,
    tag: str,
    era: str,
    var1_name: str,
    var2_name: str,
    rows: Sequence[dict],
    value_key: str,
    title: str,
) -> bool:
    rt, cms_lumi = _load_root_modules()
    if rt is None:
        return False

    hist_name = "HZa_2D_%s_%s" % (value_key, tag)
    hist = make_root_2d_hist(
        rt,
        hist_name,
        var1_name,
        var2_name,
        rows,
        value_key,
        title,
    )

    out_stem = os.path.join(out_dir, hist_name)
    canvas = rt.TCanvas(hist_name, hist_name, 900, 600)
    canvas.SetRightMargin(0.18)
    canvas.SetLeftMargin(0.16)
    canvas.SetTopMargin(0.10)
    canvas.SetBottomMargin(0.13)
    rt.gStyle.SetPalette(1)
    rt.gStyle.SetPaintTextFormat("1.3f")
    rt.gStyle.SetOptTitle(0)
    if "err" in value_key or "sigma" in value_key:
        hist.SetMinimum(0.0)
    hist.Draw("colz TEXT45")

    # Draw title at top right corner
    latex = rt.TLatex()
    latex.SetNDC()
    latex.SetTextFont(42)
    latex.SetTextSize(0.04)
    latex.SetTextAlign(31)  # Right align
    latex.DrawLatex(0.97, 0.95, title)

    _apply_cms_lumi(cms_lumi, canvas, era, 0)
    canvas.Modified()
    canvas.Update()
    canvas.Print(out_stem + ".png")
    canvas.Print(out_stem + ".pdf")
    return True


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
    write_export_json(os.path.join(out_dir, "%s.json" % out_flag), var1_name, var2_name, rows)

    if make_plots:
        available_axes = []
        for axis_name in (var1_name, var2_name):
            axis_kind = normalize_axis_name(axis_name)
            if axis_kind not in available_axes:
                available_axes.append(axis_kind)
        for axis_kind in available_axes:
            plot_axis_comparisons(out_dir, out_flag, var1_name, var2_name, rows, axis_kind, warn_missing=False)
        plot_2d_pair_summary(out_dir, out_flag, var1_name, var2_name, rows)
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
    parser.add_argument("--no-root", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--write-root", action="store_true", help="Also write the summary ROOT histogram file.")
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
                    make_root=args.write_root,
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
