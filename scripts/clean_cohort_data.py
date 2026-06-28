#!/usr/bin/env python3
"""Reproducible cleaning pipeline for the BGA neuropsychological cohort.

This script regenerates the three derived cohort files from the single raw
source file, following the rules documented in ``data/README_cleaning.md``:

    data/BGA_merged_all_20260208.csv                          (raw, 105 x 74)
        |  Stage 1  build_cleaned()
        v
    data/BGA_merged_all_20260208_cleaned.csv                  (105 x 82)
        |  Stage 2  build_for_analysis()
        v
    data/BGA_merged_all_20260208_cleaned_for_analysis.csv     (105 x 68)
        |  Stage 3  build_blinded()
        v
    data/BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv  (105 x 64)

The transforms were reverse-engineered from, and validated cell-for-cell
against, the committed derived files. Run with ``--verify`` (default) to
confirm value-level equivalence with the committed copies.

Provenance
----------
Stage 1 reproduces the original cleaning cell of
``MyStuff/01_data_exploration_20260311.ipynb`` (the notebook named in
``data/README_cleaning.md``): blank/whitespace -> NA, ``Education`` coerced to
numeric, ``HandPref`` "Right+ left" -> "Ambidextrous", and the eight QC flags
(identical column groups and definitions). Stages 2-3 (the analysis extract and
the blinded release) were applied downstream of that notebook; they are
consolidated here so the full raw -> cleaned -> for_analysis -> blinded chain is
reproducible from a single documented script.

Notes on fidelity
-----------------
* The committed ``..._cleaned.csv`` is written in a cosmetically *padded*
  ``"; "`` layout (aligned columns). That padding is a later re-save; the
  original notebook wrote plain ``to_csv(sep=";")`` exactly as this script does.
  Verification therefore compares *values* (numeric/string), not raw bytes.
* ``data/README_cleaning.md`` also mentions a separate ``..._analysis_ready.csv``
  with ``use_*`` mask columns. That variant is **legacy**: the March-16 workflow
  no longer constructs it (see ``notebooks/04_cleaned_data_results.ipynb``),
  and the deterministic pipeline reads ``..._cleaned_for_analysis.csv`` instead,
  so it is intentionally not produced here.

Usage
-----
    python scripts/clean_cohort_data.py                 # regenerate + verify
    python scripts/clean_cohort_data.py --out-dir data/reproduced
    python scripts/clean_cohort_data.py --write-inplace # overwrite data/*.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DATA = _REPO_ROOT / "data"

RAW_FILE = "BGA_merged_all_20260208.csv"
CLEANED_FILE = "BGA_merged_all_20260208_cleaned.csv"
ANALYSIS_FILE = "BGA_merged_all_20260208_cleaned_for_analysis.csv"
BLINDED_FILE = "BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv"

SEP = ";"

# --------------------------------------------------------------------------- #
# Column groups (instrument blocks)
# --------------------------------------------------------------------------- #
BIS_ITEMS = [f"BIS_Q{i}_BL" for i in range(1, 7)]
FSS_ITEMS = [f"FSS_Q{i}_BL" for i in range(1, 14)]            # all 13 FSS items
HADS_ITEMS = [f"HADS_Q{i}_BL" for i in range(1, 15)]
CPT_COLS = [
    "CPT_Detectability", "CPT_Omissions", "CPT_Commissions", "CPT_Perseverations",
    "CPT_HRT", "CPT_HRT_SD", "CPT_HRT_Block_Change", "CPT_HRT_ISI_Change",
    "CPT_Variability",
]
# The 12 RBANS raw subtests (in the order used by the analysis file: the two
# Recall items first, then the two Recognition items).
RBANS_SUBTESTS = [
    "RBANS_Wordlist", "RBANS_History", "RBANS_Figure", "RBANS_Line",
    "RBANS_Naming", "RBANS_Fluency", "RBANS_Digitspan", "RBANS_Coding",
    "RBANS_WordlistRecall", "RBANS_HistoryRecall",
    "RBANS_WordlistRecognition", "RBANS_FigureRecognition",
]
# The 5 RBANS domain index scores + the recorded composite used for the audit.
RBANS_INDEX_5 = [
    "RBANS_Memory_Index", "RBANS_Visuoaspatial_Index", "RBANS_Verbalskills_Index",
    "RBANS_Attention_Index", "RBANS_Recall_Index",
]
RBANS_DROP_FOR_ANALYSIS = RBANS_INDEX_5 + ["RBANS_Sum_Index", "RBANS_Fullscale"]

# Eight QC flag columns, in committed file order.
FLAG_COLUMNS = [
    "flag_missing_bis_block",
    "flag_missing_fatigue_block",
    "flag_missing_hads_block",
    "flag_missing_cpt_block",
    "flag_missing_rbans_block",
    "flag_hc_with_ibs_sss",
    "flag_rbans_sum_mismatch",
    "flag_tfs_vs_13_item_sum_mismatch",
]

# Metadata columns removed when blinding.
BLINDED_DROP = ["Education", "HandPref", "Mothertounge", "TestAdmin"]

# Final column order of the analysis file (drops RBANS indices + flags, inserts
# RBANS_Sum_Raw before TFS_Chalder).
FOR_ANALYSIS_COLUMNS = (
    ["Subject", "Gender", "TestAge", "Education", "Mothertounge", "HandPref",
     "TestAdmin", "Group", "IBStype", "IBS_SSS"]
    + BIS_ITEMS + CPT_COLS + FSS_ITEMS
    + ["HADS_Anxiety", "HADS_Depression"] + HADS_ITEMS
    + RBANS_SUBTESTS + ["RBANS_Sum_Raw", "TFS_Chalder"]
)
BLINDED_COLUMNS = [c for c in FOR_ANALYSIS_COLUMNS if c not in BLINDED_DROP]


# --------------------------------------------------------------------------- #
# Small formatting helpers
# --------------------------------------------------------------------------- #
def _fmt_float(token: str) -> str:
    """Coerce a raw string token to a float string (e.g. ``"12"`` -> ``"12.0"``).

    Empty / missing tokens are preserved as empty strings.
    """
    token = (token or "").strip()
    if token == "":
        return ""
    return str(float(token))


def _series_sum(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Row-wise sum across ``cols`` (numeric coercion, ``min_count=1``)."""
    num = pd.concat([pd.to_numeric(df[c], errors="coerce") for c in cols], axis=1)
    return num.sum(axis=1, min_count=1)


def _all_blank(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """True where *every* column in ``cols`` is blank for the row."""
    blank = df[cols].apply(lambda s: s.astype(str).str.strip() == "")
    return blank.all(axis=1)


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #
def load_raw(path: Path) -> pd.DataFrame:
    """Load the raw cohort file as strings (blanks preserved, not parsed to NaN)."""
    df = pd.read_csv(path, sep=SEP, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep=SEP, index=False)


# --------------------------------------------------------------------------- #
# Stage 1: raw -> cleaned (technical cleaning + QC flags)
# --------------------------------------------------------------------------- #
def compute_flags(raw: pd.DataFrame) -> pd.DataFrame:
    """Compute the eight QC flag columns from the raw frame.

    Each flag documents an unresolved data-quality issue rather than silently
    correcting it (see ``data/README_cleaning.md``).
    """
    flags = pd.DataFrame(index=raw.index)

    # Block-wise structural missingness: entire instrument block blank.
    flags["flag_missing_bis_block"] = _all_blank(raw, BIS_ITEMS)
    flags["flag_missing_fatigue_block"] = _all_blank(raw, FSS_ITEMS)
    flags["flag_missing_hads_block"] = _all_blank(raw, HADS_ITEMS)
    flags["flag_missing_cpt_block"] = _all_blank(raw, CPT_COLS)
    flags["flag_missing_rbans_block"] = _all_blank(raw, RBANS_SUBTESTS)

    # Healthy controls that nonetheless carry an IBS severity score.
    flags["flag_hc_with_ibs_sss"] = (
        (raw["Group"].str.strip() == "HC") & (raw["IBS_SSS"].str.strip() != "")
    )

    # Recorded RBANS composite disagrees with the sum of the 5 index scores.
    # (The original notebook hardcoded the two affected subjects, subj_089 and
    # subj_101; this derivation reproduces exactly those two.)
    sum_index = pd.to_numeric(raw["RBANS_Sum_Index"], errors="coerce")
    sum5 = _series_sum(raw, RBANS_INDEX_5)
    flags["flag_rbans_sum_mismatch"] = (
        sum_index.notna() & sum5.notna() & (sum_index != sum5)
    )

    # Recorded Chalder total disagrees with the 13-item FSS sum. (The canonical
    # Chalder scale uses only items 1-11; items 12-13 are extra FSS items, so
    # this flag fires whenever Q12/Q13 are endorsed. It is informational only.)
    # Mirrors the original notebook: the 13-item sum requires *all* 13 items
    # present (min_count=13), otherwise it is NaN and the flag is False.
    tfs = pd.to_numeric(raw["TFS_Chalder"], errors="coerce")
    fss = pd.concat([pd.to_numeric(raw[c], errors="coerce") for c in FSS_ITEMS], axis=1)
    sum13 = fss.sum(axis=1, min_count=len(FSS_ITEMS))
    flags["flag_tfs_vs_13_item_sum_mismatch"] = (
        tfs.notna() & sum13.notna() & (tfs != sum13)
    )

    return flags[FLAG_COLUMNS].astype(bool)


def build_cleaned(raw: pd.DataFrame) -> pd.DataFrame:
    """Stage 1 - technical cleaning. Preserves cohort and recorded values."""
    out = raw.copy()

    # Education: coerce text-like integers to numeric float strings ("12" -> "12.0").
    out["Education"] = out["Education"].map(_fmt_float)

    # HandPref: normalize the atypical "Right+ left" label to "Ambidextrous".
    out["HandPref"] = out["HandPref"].replace({"Right+ left": "Ambidextrous"})

    # Append QC flags as "True"/"False" strings.
    flags = compute_flags(raw)
    for col in FLAG_COLUMNS:
        out[col] = flags[col].map({True: "True", False: "False"})

    return out


# --------------------------------------------------------------------------- #
# Stage 2: cleaned -> analysis-ready (slimmed, RBANS raw total derived)
# --------------------------------------------------------------------------- #
def build_for_analysis(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Stage 2 - drop RBANS index + flag columns, derive RBANS_Sum_Raw."""
    out = cleaned.copy()

    # Broad cohort-relative RBANS raw total = sum of the 12 raw subtests.
    rbans_sum_raw = _series_sum(out, RBANS_SUBTESTS)
    out["RBANS_Sum_Raw"] = rbans_sum_raw.map(
        lambda v: "" if pd.isna(v) else str(float(v))
    )

    missing = [c for c in FOR_ANALYSIS_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError(f"build_for_analysis: missing expected columns {missing}")
    return out[FOR_ANALYSIS_COLUMNS]


# --------------------------------------------------------------------------- #
# Stage 3: analysis-ready -> blinded (drop identifiers, relabel subjects)
# --------------------------------------------------------------------------- #
def build_blinded(for_analysis: pd.DataFrame) -> pd.DataFrame:
    """Stage 3 - drop direct/indirect identifiers and re-label subjects."""
    out = for_analysis.copy()
    out["Subject"] = [f"subj_{i:03d}" for i in range(1, len(out) + 1)]
    return out[BLINDED_COLUMNS]


# --------------------------------------------------------------------------- #
# Verification (value-level, format-agnostic)
# --------------------------------------------------------------------------- #
def _load_committed(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=SEP, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def verify(generated: pd.DataFrame, committed_path: Path, label: str) -> bool:
    """Compare a generated frame against a committed CSV at the value level.

    Cells are compared numerically when both parse as numbers (NaN==NaN),
    otherwise as stripped strings. Returns True on exact value-level match.
    """
    if not committed_path.exists():
        print(f"  [{label}] committed file not found: {committed_path}")
        return False

    com = _load_committed(committed_path)
    gen = generated.copy()
    for c in gen.columns:
        gen[c] = gen[c].astype(str).str.strip()

    ok = True
    if list(gen.columns) != list(com.columns):
        ok = False
        print(f"  [{label}] COLUMN MISMATCH")
        print(f"      only in generated: {set(gen.columns) - set(com.columns)}")
        print(f"      only in committed: {set(com.columns) - set(gen.columns)}")
        common = [c for c in gen.columns if c in com.columns]
    else:
        common = list(gen.columns)

    if len(gen) != len(com):
        ok = False
        print(f"  [{label}] ROW COUNT MISMATCH gen={len(gen)} committed={len(com)}")

    n_rows = min(len(gen), len(com))
    n_diff = 0
    for col in common:
        g = gen[col].iloc[:n_rows]
        c = com[col].iloc[:n_rows]
        gn = pd.to_numeric(g, errors="coerce")
        cn = pd.to_numeric(c, errors="coerce")
        both_num = gn.notna() & cn.notna()
        num_eq = ~both_num | np.isclose(gn.fillna(0), cn.fillna(0))
        str_eq = (g == c) | (both_num)         # string match OR numeric path
        nan_eq = (g == "") & (c == "")
        cell_ok = (both_num & num_eq) | (~both_num & (str_eq | nan_eq))
        bad = ~cell_ok
        if bad.any():
            for idx in g.index[bad][:3]:
                print(f"  [{label}] diff col={col} row={idx} gen={g[idx]!r} committed={c[idx]!r}")
            n_diff += int(bad.sum())

    if n_diff:
        ok = False
        print(f"  [{label}] {n_diff} differing cell(s)")
    if ok:
        print(f"  [{label}] OK - exact value-level match "
              f"({n_rows} rows x {len(common)} cols)")
    return ok


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def run(raw_path: Path, out_dir: Path, do_verify: bool, committed_dir: Path) -> int:
    print(f"Reading raw cohort: {raw_path}")
    raw = load_raw(raw_path)
    print(f"  raw shape: {raw.shape}  "
          f"(Group: {dict(raw['Group'].value_counts())})")

    cleaned = build_cleaned(raw)
    analysis = build_for_analysis(cleaned)
    blinded = build_blinded(analysis)
    print(f"  cleaned:  {cleaned.shape}")
    print(f"  analysis: {analysis.shape}")
    print(f"  blinded:  {blinded.shape}")

    write_csv(cleaned, out_dir / CLEANED_FILE)
    write_csv(analysis, out_dir / ANALYSIS_FILE)
    write_csv(blinded, out_dir / BLINDED_FILE)
    print(f"Wrote 3 files to {out_dir}")

    if not do_verify:
        return 0

    print("\nVerifying value-level equivalence against committed files:")
    all_ok = True
    all_ok &= verify(cleaned, committed_dir / CLEANED_FILE, "cleaned")
    all_ok &= verify(analysis, committed_dir / ANALYSIS_FILE, "for_analysis")
    all_ok &= verify(blinded, committed_dir / BLINDED_FILE, "blinded")
    print("\n" + ("ALL FILES REPRODUCED EXACTLY (value-level)."
                   if all_ok else "VERIFICATION FAILED - see diffs above."))
    return 0 if all_ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw", type=Path, default=_DATA / RAW_FILE,
                   help="raw source CSV (default: data/%s)" % RAW_FILE)
    p.add_argument("--out-dir", type=Path, default=_DATA / "reproduced",
                   help="output directory (default: data/reproduced)")
    p.add_argument("--committed-dir", type=Path, default=_DATA,
                   help="directory of committed files to verify against (default: data/)")
    p.add_argument("--write-inplace", action="store_true",
                   help="write outputs directly into data/ (overwrites committed copies)")
    p.add_argument("--no-verify", action="store_true",
                   help="skip verification against committed files")
    args = p.parse_args(argv)

    out_dir = _DATA if args.write_inplace else args.out_dir
    return run(args.raw, out_dir, not args.no_verify, args.committed_dir)


if __name__ == "__main__":
    raise SystemExit(main())
