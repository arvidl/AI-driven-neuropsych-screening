#!/usr/bin/env python3
"""
Standalone neuropsychological profile analysis pipeline.

This file is the canonical, self-contained implementation of the BGA reporting
pipeline. It no longer depends on dated wrapper scripts. The main goals of this
standalone version are:

1. Keep one transparent entrypoint for notebooks, scripts, and batch runs.
2. Make the full analysis traceable in one place for trust and auditability.
3. Reflect the March 16, 2026 update:
   - cleaned analysis-ready CSV
   - revised RBANS handling based on raw subtests plus cohort-standardized
     summary composites
   - revised physician/patient visualizations
   - simplified reasoning and recommendation logic

Outputs per patient (saved to `output/<patient_id>/`):
- JSON clinical report
- LaTeX-compiled PDF clinical report
- Multi-panel domain profiles (clinical/physician/patient) as PDF+PNG
- Radar/spider plots (clinical/physician/patient) as PDF+PNG

The script is intentionally verbose and heavily commented. The comments are not
only for maintainers: they are also meant to help clinicians and researchers
understand which parts of the pipeline are data preparation, normative
comparison, interpretation, visualization, and report generation.
"""

import json
import os
import subprocess
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths are resolved relative to the repository root (one level above scripts/).
# Keeping these explicit makes notebook and CLI behavior easier to reason about.
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent

FULL_DATA_PATH = str(_REPO_ROOT / "data" / "BGA_merged_all_20260208_cleaned_for_analysis.csv")
BLINDED_DATA_PATH = str(_REPO_ROOT / "data" / "BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv")
OUTPUT_BASE = str(_REPO_ROOT / "output")
OUTPUT_SUBJ_BASE = str(_REPO_ROOT / "output_subj")
TEMPLATE_DIR = str(_SCRIPT_DIR)  # LaTeX aux files written alongside script


def _default_data_path() -> str:
    """Prefer the full cohort when available, otherwise fall back to blinded data."""
    full_path = Path(FULL_DATA_PATH)
    if full_path.exists():
        return str(full_path)
    return BLINDED_DATA_PATH


DATA_PATH = _default_data_path()

# Column name mappings
COL_SUBJECT = "Subject"
COL_GROUP = "Group"
COL_GENDER = "Gender"
COL_AGE = "TestAge"
COL_EDUCATION = "Education"
COL_IBS_TYPE = "IBStype"
COL_IBS_SSS = "IBS_SSS"

BIS_ITEMS = [f"BIS_Q{i}_BL" for i in range(1, 7)]
CPT_COLS = [
    "CPT_Detectability", "CPT_Omissions", "CPT_Commissions",
    "CPT_Perseverations", "CPT_HRT", "CPT_HRT_SD",
    "CPT_HRT_Block_Change", "CPT_HRT_ISI_Change", "CPT_Variability",
]
FSS_ITEMS = [f"FSS_Q{i}_BL" for i in range(1, 12)]  # preserved March 16 item set
HADS_SUMMARY = ["HADS_Anxiety", "HADS_Depression"]

# The legacy pipeline relied on normed RBANS index-score columns. The March 16
# revision instead uses raw RBANS subtests, transforms them to cohort-standardized
# z-scores, and aggregates those z-scores into domain-level summaries.
RBANS_SUBTEST_LABELS = {
    "RBANS_Wordlist": "Word List",
    "RBANS_History": "Story Memory",
    "RBANS_Figure": "Figure Copy",
    "RBANS_Line": "Line Orientation",
    "RBANS_Naming": "Picture Naming",
    "RBANS_Fluency": "Semantic Fluency",
    "RBANS_Digitspan": "Digit Span",
    "RBANS_Coding": "Coding",
    "RBANS_WordlistRecall": "Word List Recall",
    "RBANS_HistoryRecall": "Story Recall",
    "RBANS_WordlistRecognition": "Word List Recognition",
    "RBANS_FigureRecognition": "Figure Recall",
}

RBANS_DOMAIN_COLS = {
    "Immediate Memory": ["RBANS_Wordlist", "RBANS_History"],
    "Visuospatial": ["RBANS_Figure", "RBANS_Line"],
    "Language": ["RBANS_Naming", "RBANS_Fluency"],
    "Attention": ["RBANS_Digitspan", "RBANS_Coding"],
    "Delayed Memory": ["RBANS_WordlistRecall", "RBANS_HistoryRecall"],
    "Recognition": ["RBANS_WordlistRecognition", "RBANS_FigureRecognition"],
}

RBANS_SUMMARY_COLS = {
    "Immediate Memory": "RBANS_ImmediateMemory_summary",
    "Visuospatial": "RBANS_Visuospatial_summary",
    "Language": "RBANS_Language_summary",
    "Attention": "RBANS_Attention_summary",
    "Delayed Memory": "RBANS_DelayedMemory_summary",
    "Recognition": "RBANS_Recognition_summary",
    "Total Scale": "RBANS_Sum_Raw",
}

# Expanded CPT view used in the updated clinical panel.
CPT_METRICS_FULL = [
    ("CPT_Detectability", "d'"),
    ("CPT_Omissions", "Omissions"),
    ("CPT_Commissions", "Commissions"),
    ("CPT_Perseverations", "Persev."),
    ("CPT_HRT", "HRT"),
    ("CPT_HRT_SD", "HRT SD"),
    ("CPT_HRT_Block_Change", "Block"),
    ("CPT_HRT_ISI_Change", "ISI"),
    ("CPT_Variability", "Variability"),
]

# These legacy RBANS constants are retained so older notebooks or ad hoc code
# that import them do not break. The active standalone March 16 pipeline uses
# `RBANS_SUBTEST_LABELS`, `RBANS_DOMAIN_COLS`, and `RBANS_SUMMARY_COLS` above.
RBANS_INDICES = [
    "RBANS_Memory_Index", "RBANS_Visuoaspatial_Index",
    "RBANS_Verbalskills_Index", "RBANS_Attention_Index",
    "RBANS_Recall_Index", "RBANS_Fullscale",
]
RBANS_INDEX_LABELS = [
    "Immediate\nMemory", "Visuospatial", "Language",
    "Attention", "Delayed\nMemory", "Total Scale",
]

# Clinical cutoffs
HADS_CUTOFFS = {"normal": 7, "borderline": 10, "clinical": 11}
BIS_CUTOFFS = {"minimal": 6, "mild": 14, "moderate": 24}  # total score
CHALDER_CASENESS = 4  # bimodal total >= 4
CPT_ELEVATED = 60  # T-score >= 60 is elevated
CPT_CLINICAL = 65  # T-score >= 65 is clinically significant
RBANS_CLASSIFICATIONS = {
    "Extremely Low": (0, 69),
    "Borderline": (70, 79),
    "Low Average": (80, 89),
    "Average": (90, 109),
    "High Average": (110, 119),
    "Superior": (120, 129),
    "Very Superior": (130, 200),
}

# Radar spoke definitions
RADAR_COMPACT = {
    "labels": ["Sleep\nquality", "Concentration", "Energy", "Mood", "Memory &\nthinking"],
    "columns": ["BIS_total", "CPT_Detectability", "Chalder_total", "HADS_total", "RBANS_Sum_Raw"],
    "invert": [True, False, True, True, False],
    "patient_labels": ["Sleep\nquality", "Concentration", "Energy", "Mood", "Memory &\nthinking"],
}
RADAR_EXPANDED = {
    "labels": [
        "Sleep\n(BIS)", "Attention\n(CPT d')", "Speed\n(CPT RT)",
        "Energy\n(Chalder)", "Anxiety\n(HADS-A)", "Mood\n(HADS-D)",
        "RBANS\nImmed. Memory", "RBANS\nAttention", "RBANS\nDelayed Memory", "RBANS\nTotal",
    ],
    "columns": [
        "BIS_total", "CPT_Detectability", "CPT_HRT",
        "Chalder_total", "HADS_Anxiety", "HADS_Depression",
        "RBANS_ImmediateMemory_summary", "RBANS_Attention_summary", "RBANS_DelayedMemory_summary", "RBANS_Sum_Raw",
    ],
    "invert": [True, False, True, True, True, True, False, False, False, False],
}

# Color palettes (colorblind-safe)
PAL_IBS = "#E69F00"   # orange
PAL_HC = "#56B4E9"    # sky blue
PAL_PATIENT = "#0077B6"  # dark teal
PAL_CONCERN = "#D55E00"  # vermillion
PAL_GREEN = "#009E73"    # green
PAL_PURPLE = "#CC79A7"   # pink/purple


# ============================================================================
# DATA LOADING & PREPROCESSING
# ============================================================================

def load_cohort(path: str = DATA_PATH) -> pd.DataFrame:
    """Load the cleaned analysis-ready cohort and derive reusable summary fields.

    This is the main schema-adaptation step of the standalone pipeline. By doing
    all derived-score construction here, downstream analysis/plot/report code can
    stay simple and operate on a stable dataframe contract.
    """
    df = pd.read_csv(path, sep=";")
    required = [
        COL_SUBJECT,
        COL_GROUP,
        COL_GENDER,
        COL_AGE,
        *BIS_ITEMS,
        *CPT_COLS,
        *FSS_ITEMS,
        "TFS_Chalder",
        *HADS_SUMMARY,
        *RBANS_SUBTEST_LABELS.keys(),
        "RBANS_Sum_Raw",
    ]
    _require_columns(df, required)

    if COL_EDUCATION not in df.columns:
        df[COL_EDUCATION] = np.nan

    # Derive the scale totals that are referenced repeatedly throughout the
    # pipeline. Centralizing them here avoids duplicated score logic later on.
    df["BIS_total"] = df[BIS_ITEMS].sum(axis=1, min_count=1)
    df["Chalder_total"] = df[FSS_ITEMS].sum(axis=1, min_count=1)
    df["HADS_total"] = df["HADS_Anxiety"] + df["HADS_Depression"]
    df["FSS_mean"] = df[FSS_ITEMS].mean(axis=1)
    df["Chalder_recorded_delta"] = df["Chalder_total"] - df["TFS_Chalder"]

    # Education is one of the few demographic variables used numerically in
    # interpretation, so we coerce it once at load time.
    df[COL_EDUCATION] = pd.to_numeric(df[COL_EDUCATION], errors="coerce")

    # March 16 RBANS model:
    # 1. z-standardize each raw RBANS subtest within the cohort
    # 2. average the relevant z-scores into domain summaries
    # 3. keep RBANS_Sum_Raw as the broad cohort-relative total
    rbans_z = pd.DataFrame({col: _series_z(df[col]) for col in RBANS_SUBTEST_LABELS}, index=df.index)
    for domain, cols in RBANS_DOMAIN_COLS.items():
        df[RBANS_SUMMARY_COLS[domain]] = rbans_z[cols].mean(axis=1, skipna=True)

    return df


def _require_columns(df: pd.DataFrame, columns: List[str]) -> None:
    """Fail early if the expected cleaned-data schema is not present."""
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")


def _series_z(series: pd.Series) -> pd.Series:
    """Return a cohort-standardized z-score version of a numeric series."""
    valid = series.dropna()
    if len(valid) < 2 or valid.std() == 0:
        return pd.Series(np.nan, index=series.index, dtype=float)
    return (series - valid.mean()) / valid.std()


def _rbans_subtest_percentiles(patient: pd.Series, df: pd.DataFrame) -> Dict[str, Optional[float]]:
    """Report raw-subtest percentiles in human-readable label form."""
    out: Dict[str, Optional[float]] = {}
    for col, label in RBANS_SUBTEST_LABELS.items():
        val = patient.get(col, np.nan)
        pct = percentile_rank(val, df[col]) if not pd.isna(val) else np.nan
        out[label] = round(pct, 1) if not np.isnan(pct) else None
    return out


def _relative_profile_label(percentile: float) -> str:
    """Translate a cohort percentile into a plain-language relative profile label."""
    if pd.isna(percentile):
        return "N/A"
    if percentile < 9:
        return "Marked relative weakness"
    if percentile < 25:
        return "Relative weakness"
    if percentile < 40:
        return "Low cohort position"
    if percentile <= 60:
        return "Mid cohort position"
    if percentile <= 75:
        return "Relative strength"
    return "Marked relative strength"


def _missing_note_for_controls(patient: pd.Series) -> str:
    """Clarify that IBS-SSS is not interpreted for healthy controls."""
    if str(patient.get(COL_GROUP, "")) == "HC":
        return " Healthy-control IBS-SSS values are retained in the dataset but are not interpreted as IBS severity."
    return ""


def _fmt_number(value: Any, decimals: int = 1) -> Optional[str]:
    """Format a value for titles and report prose while tolerating missing data."""
    if value is None or pd.isna(value):
        return None
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return str(value)
    if float(numeric).is_integer():
        return str(int(numeric))
    return f"{numeric:.{decimals}f}"


def _participant_label(patient_id: str) -> str:
    """Use a neutral label for blinded public IDs."""
    return "Subject" if str(patient_id).startswith("subj_") else "Patient"


def _patient_context_line(
    patient: pd.Series,
    *,
    include_education: bool = True,
    include_ibs_subtype: bool = False,
    include_ibs_severity: bool = False,
) -> str:
    """Build a concise demographic/clinical subtitle for figures."""
    parts: List[str] = []
    age = _fmt_number(patient.get(COL_AGE), decimals=0)
    if age is not None:
        parts.append(f"Age: {age}")

    gender = patient.get(COL_GENDER, None)
    if gender is not None and not pd.isna(gender):
        parts.append(f"Gender: {gender}")

    group = patient.get(COL_GROUP, None)
    if group is not None and not pd.isna(group):
        parts.append(f"Group: {group}")

    if include_education:
        education = _fmt_number(patient.get(COL_EDUCATION), decimals=1)
        if education is not None:
            parts.append(f"Education: {education} yrs")

    if include_ibs_subtype and str(group) == "IBS":
        ibs_type = patient.get(COL_IBS_TYPE, None)
        if ibs_type is not None and not pd.isna(ibs_type) and str(ibs_type).strip():
            parts.append(f"IBS subtype: {ibs_type}")

    if include_ibs_severity and str(group) == "IBS":
        ibs_sss = _fmt_number(patient.get(COL_IBS_SSS), decimals=1)
        if ibs_sss is not None:
            parts.append(f"IBS SSS: {ibs_sss}")

    return " | ".join(parts)


def _report_demographics_rows(demo: Dict[str, Any]) -> str:
    """Render the demographics table rows, omitting unavailable fields."""
    rows = []
    age = _fmt_number(demo.get("age"), decimals=0)
    if age is not None:
        rows.append(r"\textbf{Age:} & " + age + r" years \\")

    gender = demo.get("gender")
    if gender not in (None, "", "N/A"):
        rows.append(r"\textbf{Gender:} & " + _tex_escape(str(gender)) + r" \\")

    education = _fmt_number(demo.get("education"), decimals=1)
    if education is not None:
        rows.append(r"\textbf{Education:} & " + education + r" years \\")

    ibs_status = demo.get("ibs_status")
    if ibs_status not in (None, "", "N/A"):
        rows.append(r"\textbf{Group:} & " + _tex_escape(str(ibs_status)) + r" \\")

    ibs_subtype = demo.get("ibs_subtype")
    if ibs_subtype not in (None, "", "N/A"):
        rows.append(r"\textbf{IBS Subtype:} & " + _tex_escape(str(ibs_subtype)) + r" \\")

    ibs_severity = _fmt_number(demo.get("ibs_severity"), decimals=1)
    if ibs_severity is not None:
        rows.append(r"\textbf{IBS Severity (SSS):} & " + ibs_severity + r" \\")

    return "\n".join(rows) if rows else r"\textbf{Subject ID:} & N/A \\"


def _cohort_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Expose cohort sizes for downstream reporting."""
    group_counts = {str(k): int(v) for k, v in df[COL_GROUP].value_counts().to_dict().items()}
    return {
        "total_n": int(len(df)),
        "group_counts": group_counts,
    }


def get_patient(df: pd.DataFrame, patient_id: str) -> pd.Series:
    """Extract a single patient's row."""
    mask = df[COL_SUBJECT] == patient_id
    if mask.sum() == 0:
        raise ValueError(f"Patient {patient_id} not found in dataset.")
    return df.loc[mask].squeeze()


# ============================================================================
# PERCENTILE & STATISTICAL UTILITIES
# ============================================================================

def percentile_rank(value: float, series: pd.Series) -> float:
    """Compute percentile rank of value within a series (0-100)."""
    if pd.isna(value):
        return np.nan
    valid = series.dropna()
    if len(valid) == 0:
        return np.nan
    return float(stats.percentileofscore(valid, value, kind="rank"))


def percentile_of_wellness(value: float, series: pd.Series, invert: bool = False) -> float:
    """Percentile where higher = better functioning.
    If invert=True, high raw scores mean worse outcomes, so we flip."""
    pct = percentile_rank(value, series)
    if pd.isna(pct):
        return np.nan
    return (100.0 - pct) if invert else pct


def cohort_z_score(value: float, series: pd.Series) -> float:
    """Z-score relative to cohort distribution."""
    if pd.isna(value):
        return np.nan
    valid = series.dropna()
    if len(valid) < 2:
        return np.nan
    return float((value - valid.mean()) / valid.std())


def cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """Cohen's d effect size between two groups."""
    g1 = group1.dropna()
    g2 = group2.dropna()
    if len(g1) < 2 or len(g2) < 2:
        return np.nan
    pooled_std = np.sqrt(((len(g1) - 1) * g1.std()**2 + (len(g2) - 1) * g2.std()**2)
                         / (len(g1) + len(g2) - 2))
    if pooled_std == 0:
        return 0.0
    return float((g1.mean() - g2.mean()) / pooled_std)


def classify_rbans(score: float) -> str:
    """Classify RBANS index score."""
    if pd.isna(score):
        return "N/A"
    for label, (lo, hi) in RBANS_CLASSIFICATIONS.items():
        if lo <= score <= hi:
            return label
    return "N/A"


def classify_hads(score: float) -> str:
    """Classify HADS subscale score."""
    if pd.isna(score):
        return "N/A"
    if score <= HADS_CUTOFFS["normal"]:
        return "Normal"
    elif score <= HADS_CUTOFFS["borderline"]:
        return "Borderline"
    else:
        return "Clinical"


def classify_bis(total: float) -> str:
    """Classify BIS total score."""
    if pd.isna(total):
        return "N/A"
    if total <= BIS_CUTOFFS["minimal"]:
        return "Minimal"
    elif total <= BIS_CUTOFFS["mild"]:
        return "Mild"
    elif total <= BIS_CUTOFFS["moderate"]:
        return "Moderate"
    else:
        return "Severe"


def classify_chalder(total: float) -> str:
    """Classify Chalder bimodal total."""
    if pd.isna(total):
        return "N/A"
    return "Significant fatigue" if total >= CHALDER_CASENESS else "No significant fatigue"


# ============================================================================
# CLINICAL ANALYSIS — JSON GENERATION
# ============================================================================

def analyze_patient(df: pd.DataFrame, patient_id: str,
                    reference_df: pd.DataFrame = None) -> Dict[str, Any]:
    """Generate full clinical analysis JSON for a single patient.

    Parameters
    ----------
    df : pd.DataFrame
        Full dataset (used to look up the patient row).
    patient_id : str
        Subject identifier.
    reference_df : pd.DataFrame, optional
        If provided, all cohort statistics (percentiles, z-scores, group
        comparisons) are computed against this DataFrame instead of *df*.
        This allows a held-out patient to be evaluated against an
        independent reference cohort.  When ``None`` (the default), *df*
        is used — preserving backward compatibility.
    """
    patient = get_patient(df, patient_id)
    ref = reference_df if reference_df is not None else df
    controls = ref[ref[COL_GROUP] == "HC"]
    ibs_group = ref[ref[COL_GROUP] == "IBS"]

    # Demographics
    demographics = {
        "age": _safe_val(patient[COL_AGE]),
        "gender": str(patient[COL_GENDER]),
        "education": _safe_val(patient.get(COL_EDUCATION, np.nan)),
        "ibs_status": str(patient[COL_GROUP]),
        "ibs_subtype": _safe_val(patient.get(COL_IBS_TYPE, None)),
        "ibs_severity": _safe_val(patient.get(COL_IBS_SSS, None)),
    }

    # Domain analyses — use reference cohort for normative statistics
    sleep = _analyze_bis(ref, patient)
    attention = _analyze_cpt(ref, patient)
    fatigue = _analyze_fatigue(ref, patient)
    emotional = _analyze_hads(ref, patient)
    cognition = _analyze_rbans(ref, patient)

    # Cross-domain pattern analysis
    cross_patterns = _cross_domain_analysis(sleep, attention, fatigue, emotional, cognition, demographics)

    # Cohort context — use reference cohort
    cohort_ctx = _cohort_context(ref, patient, demographics)

    # Clinical reasoning chain
    reasoning = _reasoning_chain(sleep, attention, fatigue, emotional, cognition, demographics)

    # Recommendations
    recs = _recommendations(sleep, attention, fatigue, emotional, cognition, demographics)

    return {
        "patient_id": patient_id,
        "demographics": demographics,
        "domain_findings": {
            "sleep_BIS": sleep,
            "attention_CPT": attention,
            "fatigue_Chalder": fatigue,
            "emotional_distress_HADS": emotional,
            "neurocognition_RBANS": cognition,
        },
        "cross_domain_patterns": cross_patterns,
        "cohort_context": cohort_ctx,
        "cohort_summary": _cohort_summary(ref),
        "reasoning_chain": reasoning,
        "recommendations": recs,
        "visualizations_generated": {},  # filled after viz generation
    }


def _safe_val(v):
    """Convert numpy/pandas types to JSON-safe values."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return round(float(v), 2)
    return v


def _analyze_bis(df: pd.DataFrame, patient: pd.Series) -> Dict:
    total = patient["BIS_total"]
    items = {f"Q{i}": _safe_val(patient[f"BIS_Q{i}_BL"]) for i in range(1, 7)}
    pct = percentile_rank(total, df["BIS_total"])
    classification = classify_bis(total)
    z = cohort_z_score(total, df["BIS_total"])

    flags = []
    if classification in ("Moderate", "Severe"):
        flags.append("Clinically elevated insomnia")
    if not pd.isna(total) and total >= 19:
        flags.append("Above clinical threshold (>=19)")

    # Check individual items for >=3 days/week
    high_items = [k for k, v in items.items() if v is not None and v >= 3]
    if len(high_items) >= 3:
        flags.append(f"Multiple items >=3 days/week: {', '.join(high_items)}")

    interp = (
        f"BIS total = {_safe_val(total)} ({classification}). "
        f"Cohort percentile: {pct:.0f}th. z = {z:+.2f}. "
    )
    if classification in ("Moderate", "Severe"):
        interp += "This indicates clinically significant insomnia symptoms that likely impact daytime functioning and cognitive performance."
    elif classification == "Mild":
        interp += "Mild sleep disturbance noted; monitor for worsening or downstream effects on cognition."
    else:
        interp += "Sleep appears within normal limits."

    return {
        "scores": {"total": _safe_val(total), **items},
        "percentile_in_cohort": round(pct, 1) if not np.isnan(pct) else None,
        "z_score": round(z, 2) if not np.isnan(z) else None,
        "classification": classification,
        "interpretation": interp,
        "flags": flags,
    }


def _analyze_cpt(df: pd.DataFrame, patient: pd.Series) -> Dict:
    scores = {}
    pcts = {}
    flags = []

    key_metrics = {
        "Detectability": ("CPT_Detectability", True),    # higher = worse
        "Omissions": ("CPT_Omissions", True),             # higher = worse
        "Commissions": ("CPT_Commissions", True),         # higher = worse
        "HRT": ("CPT_HRT", True),                         # higher = slower = worse
        "HRT_SD": ("CPT_HRT_SD", True),                   # higher = more variable = worse
        "Perseverations": ("CPT_Perseverations", True),
        "Variability": ("CPT_Variability", True),
    }

    for name, (col, worse_if_high) in key_metrics.items():
        val = patient[col]
        scores[name] = _safe_val(val)
        pcts[name] = round(percentile_rank(val, df[col]), 1) if not pd.isna(val) else None

        if not pd.isna(val):
            if worse_if_high and val >= CPT_CLINICAL:
                flags.append(f"{name} clinically elevated (T={val:.0f})")
            elif worse_if_high and val >= CPT_ELEVATED:
                flags.append(f"{name} mildly elevated (T={val:.0f})")

    detect_pct = pcts.get("Detectability")
    z_detect = cohort_z_score(patient["CPT_Detectability"], df["CPT_Detectability"])

    interp = f"CPT Detectability (d') T={scores.get('Detectability', 'N/A')}"
    if detect_pct is not None:
        interp += f" ({detect_pct:.0f}th percentile in cohort, z={z_detect:+.2f}). "
    else:
        interp += ". "

    if len(flags) == 0:
        interp += "All CPT metrics within normal limits. Sustained attention and response control appear intact."
    else:
        interp += f"Elevated metrics: {'; '.join(flags)}. This pattern suggests difficulties with sustained attention and/or response control."

    return {
        "scores": scores,
        "percentiles": pcts,
        "percentile_in_cohort": detect_pct,
        "z_score": round(z_detect, 2) if not np.isnan(z_detect) else None,
        "interpretation": interp,
        "flags": flags,
    }


def _analyze_fatigue(df: pd.DataFrame, patient: pd.Series) -> Dict:
    chalder_total = patient["Chalder_total"]
    tfs = patient.get("TFS_Chalder", np.nan)
    pct = percentile_rank(chalder_total, df["Chalder_total"])
    z = cohort_z_score(chalder_total, df["Chalder_total"])
    classification = classify_chalder(chalder_total)

    items = {f"Q{i}": _safe_val(patient[f"FSS_Q{i}_BL"]) for i in range(1, 12)}
    n_endorsed = sum(1 for v in items.values() if v == 1)

    flags = []
    if not pd.isna(chalder_total) and chalder_total >= CHALDER_CASENESS:
        flags.append(f"Chalder caseness (bimodal total={chalder_total:.0f} >= {CHALDER_CASENESS})")

    interp = (
        f"Chalder Fatigue bimodal total = {_safe_val(chalder_total)} "
        f"({n_endorsed}/11 items endorsed). Classification: {classification}. "
        f"Cohort percentile: {pct:.0f}th. "
    )
    if classification == "Significant fatigue":
        interp += "Clinically significant fatigue present. This may impact attention, processing speed, and overall cognitive efficiency."
    else:
        interp += "No significant fatigue indicated."

    return {
        "scores": {"chalder_bimodal_total": _safe_val(chalder_total), "TFS_Chalder": _safe_val(tfs), "items_endorsed": n_endorsed},
        "percentile_in_cohort": round(pct, 1) if not np.isnan(pct) else None,
        "z_score": round(z, 2) if not np.isnan(z) else None,
        "classification": classification,
        "interpretation": interp,
        "flags": flags,
    }


def _analyze_hads(df: pd.DataFrame, patient: pd.Series) -> Dict:
    anx = patient["HADS_Anxiety"]
    dep = patient["HADS_Depression"]
    total = patient["HADS_total"]

    anx_class = classify_hads(anx)
    dep_class = classify_hads(dep)
    anx_pct = percentile_rank(anx, df["HADS_Anxiety"])
    dep_pct = percentile_rank(dep, df["HADS_Depression"])
    anx_z = cohort_z_score(anx, df["HADS_Anxiety"])
    dep_z = cohort_z_score(dep, df["HADS_Depression"])

    flags = []
    if anx_class == "Clinical":
        flags.append(f"HADS-A clinical ({anx:.0f})")
    elif anx_class == "Borderline":
        flags.append(f"HADS-A borderline ({anx:.0f})")
    if dep_class == "Clinical":
        flags.append(f"HADS-D clinical ({dep:.0f})")
    elif dep_class == "Borderline":
        flags.append(f"HADS-D borderline ({dep:.0f})")

    interp = (
        f"HADS Anxiety = {_safe_val(anx)} ({anx_class}, {anx_pct:.0f}th %ile). "
        f"HADS Depression = {_safe_val(dep)} ({dep_class}, {dep_pct:.0f}th %ile). "
    )
    if "clinical" in (anx_class.lower(), dep_class.lower()):
        interp += "Clinically significant emotional distress present. This is likely to affect cognitive test performance, particularly attention and executive function."
    elif "borderline" in (anx_class.lower(), dep_class.lower()):
        interp += "Subclinical emotional distress noted. May contribute to reduced cognitive efficiency under demanding conditions."
    else:
        interp += "Emotional functioning within normal limits."

    return {
        "scores": {"HADS_A": _safe_val(anx), "HADS_D": _safe_val(dep), "HADS_total": _safe_val(total)},
        "percentile_in_cohort": {"anxiety": round(anx_pct, 1), "depression": round(dep_pct, 1)},
        "z_scores": {"anxiety": round(anx_z, 2) if not np.isnan(anx_z) else None,
                     "depression": round(dep_z, 2) if not np.isnan(dep_z) else None},
        "classification": {"anxiety": anx_class, "depression": dep_class},
        "interpretation": interp,
        "flags": flags,
    }


def _analyze_rbans(df: pd.DataFrame, patient: pd.Series) -> Dict:
    """Summarize RBANS using raw subtests and cohort-standardized composites.

    This is the central conceptual change in the standalone March 16 pipeline.
    Rather than reading the older normed RBANS index-score columns, we compute
    relative within-cohort summaries from the raw subtests available in the
    cleaned analysis file.
    """
    scores: Dict[str, Any] = {}
    percentiles: Dict[str, Optional[float]] = {}
    z_scores: Dict[str, Optional[float]] = {}
    classifications: Dict[str, str] = {}
    flags: List[str] = []

    for label, summary_col in RBANS_SUMMARY_COLS.items():
        val = patient.get(summary_col, np.nan)
        scores[label] = _safe_val(patient["RBANS_Sum_Raw"] if label == "Total Scale" else val)
        pct = percentile_rank(val, df[summary_col]) if not pd.isna(val) else np.nan
        z = cohort_z_score(val, df[summary_col]) if not pd.isna(val) else np.nan
        percentiles[label] = round(pct, 1) if not np.isnan(pct) else None
        z_scores[label] = round(z, 2) if not np.isnan(z) else None
        classifications[label] = _relative_profile_label(pct)
        if label not in ("Recognition", "Total Scale") and not np.isnan(pct) and pct < 16:
            flags.append(f"{label}: marked relative weakness within cohort")

    total_pct = percentiles["Total Scale"]
    if total_pct is not None and total_pct < 16:
        flags.append("RBANS Sum Raw falls in the lowest cohort range")

    domain_order = ["Immediate Memory", "Visuospatial", "Language", "Attention", "Delayed Memory", "Recognition"]
    weak = [label for label in domain_order if (percentiles.get(label) or 0) < 25]
    strong = [label for label in domain_order if (percentiles.get(label) or 0) > 75]
    raw_subtests = {
        label: _safe_val(patient.get(col, np.nan))
        for col, label in RBANS_SUBTEST_LABELS.items()
    }
    raw_subtest_percentiles = _rbans_subtest_percentiles(patient, df)

    interp = (
        f"RBANS Sum Raw = {_safe_val(patient.get('RBANS_Sum_Raw', np.nan))} "
        f"({total_pct if total_pct is not None else 'N/A'}th cohort percentile). "
        "Interpretation is based on the cleaned dataset's raw subtests and cohort-relative summaries "
        "rather than the older RBANS index-score fields. "
    )
    if weak:
        interp += f"Relative weaknesses are most evident in {', '.join(weak)}. "
    if strong:
        interp += f"Relative strengths are most evident in {', '.join(strong)}. "
    if not weak and not strong:
        interp += "The raw RBANS profile is broadly mid-range across domains. "

    return {
        "scores": scores,
        "percentiles": percentiles,
        "z_scores": z_scores,
        "classifications": classifications,
        "percentile_in_cohort": total_pct,
        "z_score": z_scores["Total Scale"],
        "interpretation": interp,
        "flags": flags,
        "raw_subtests": raw_subtests,
        "raw_subtest_percentiles": raw_subtest_percentiles,
    }


def _cross_domain_analysis(sleep, attention, fatigue, emotional, cognition, demographics):
    patterns = []
    sleep_problem = len(sleep["flags"]) > 0
    fatigue_problem = len(fatigue["flags"]) > 0
    attn_problem = len(attention["flags"]) > 0
    mood_problem = len(emotional["flags"]) > 0
    cog_problem = len(cognition["flags"]) > 0
    is_ibs = demographics.get("ibs_status") == "IBS"

    # --- Insomnia-Fatigue-Attention cascade ---
    if sleep_problem and fatigue_problem and attn_problem:
        patterns.append(
            "A full insomnia-fatigue-attention cascade is present: elevated BIS scores indicate disrupted "
            "sleep architecture, which is the most parsimonious explanation for the co-occurring Chalder "
            "fatigue caseness and the CPT attention deficits. Chronic sleep loss impairs prefrontal "
            "cortical function, reducing sustained attention capacity and increasing commission errors "
            "(Lim & Dinges, 2010). This triad should be treated as an integrated problem with sleep "
            "as the upstream driver.")
    elif sleep_problem and fatigue_problem:
        patterns.append(
            "Insomnia-fatigue co-occurrence: Elevated BIS and Chalder scores together suggest that "
            "poor sleep is driving daytime fatigue. Although CPT performance is currently preserved, "
            "this combination places the patient at risk for developing attentional difficulties if "
            "sleep disturbance persists (Fortier-Brochu et al., 2012).")
    elif sleep_problem and attn_problem:
        patterns.append(
            "Sleep-attention link: Insomnia co-occurs with CPT attention deficits. Sleep disruption "
            "degrades vigilance and sustained attention via reduced thalamo-cortical arousal regulation "
            "(Krause et al., 2017). Treating the sleep disturbance may improve attentional performance.")
    elif (sleep_problem or fatigue_problem) and attn_problem:
        patterns.append(
            "Fatigue/sleep and attention co-occur: Either sleep disruption or fatigue appears to be "
            "contributing to attentional difficulties on CPT.")

    # --- Mood-Cognition interaction ---
    if mood_problem and (attn_problem or cog_problem):
        patterns.append(
            "Mood-cognition interaction: Emotional distress (HADS) co-occurs with cognitive difficulties. "
            "Anxiety consumes working memory resources through worry-related rumination, while depression "
            "slows processing speed and impairs encoding (Castaneda et al., 2008). Both mechanisms can "
            "degrade performance on RBANS and CPT independently of any organic pathology.")
    elif mood_problem:
        patterns.append(
            "Elevated emotional distress (HADS) is present without frank cognitive impairment. However, "
            "subclinical anxiety/depression can still reduce cognitive efficiency under demanding conditions "
            "and should be monitored as a risk factor for future cognitive decline.")

    # --- Mood-Sleep bidirectional ---
    if mood_problem and sleep_problem:
        patterns.append(
            "Mood-sleep bidirectional relationship: Both insomnia and emotional distress are elevated, "
            "consistent with their well-documented bidirectional association (Baglioni et al., 2011). "
            "Insomnia is both a symptom and a maintaining factor for anxiety and depression; treating "
            "sleep may yield secondary mood benefits and vice versa.")

    # --- Gut-brain axis ---
    if is_ibs:
        if fatigue_problem or mood_problem or sleep_problem:
            patterns.append(
                "Gut-brain axis involvement: As an IBS patient with elevated scores in "
                f"{'sleep, ' if sleep_problem else ''}{'fatigue, ' if fatigue_problem else ''}"
                f"{'mood, ' if mood_problem else ''}"
                "this profile is consistent with gut-brain axis mediated effects. IBS-associated "
                "visceral hypersensitivity activates the hypothalamic-pituitary-adrenal (HPA) axis and "
                "alters serotonergic signaling, which can drive insomnia, fatigue, and affective "
                "dysregulation (Mayer et al., 2015). An integrated treatment approach addressing both "
                "gastrointestinal and neuropsychological symptoms is warranted.")
        else:
            patterns.append(
                "Despite IBS diagnosis, the neuropsychological profile is largely intact. This may "
                "reflect effective coping, lower disease severity, or resilience factors. Nevertheless, "
                "the gut-brain axis remains a relevant context: IBS patients are at elevated risk for "
                "developing sleep, fatigue, and mood difficulties over time.")

    # --- Memory-specific patterns ---
    if cog_problem and not attn_problem and not mood_problem:
        patterns.append(
            "Isolated cognitive weakness is present (RBANS) without attentional or mood-related "
            "contributors. This pattern warrants monitoring and possible follow-up neuropsychological "
            "evaluation to track trajectory and rule out neurodegenerative processes, especially "
            "if the patient is older or reports subjective cognitive decline.")

    # --- Protective / intact pattern ---
    if not any([sleep_problem, fatigue_problem, attn_problem, mood_problem, cog_problem]):
        patterns.append(
            "No cross-domain pathological patterns identified. The profile is intact across all "
            "assessed domains. This is a reassuring finding, though routine monitoring remains "
            "appropriate given the clinical context.")
    elif sleep_problem and not any([fatigue_problem, attn_problem, mood_problem, cog_problem]):
        patterns.append(
            "Sleep disturbance is the sole area of concern. Notably, fatigue, attention, mood, and "
            "cognition remain intact, suggesting either adequate compensatory mechanisms or that the "
            "insomnia has not yet cascaded into downstream functional impairment. Early intervention "
            "is recommended to prevent such progression.")

    return " ".join(patterns)


def _cohort_context(df, patient, demographics):
    group = demographics["ibs_status"]
    subgroup = df[df[COL_GROUP] == group]
    n_sub = len(subgroup)
    total = len(df)
    ctx = f"Patient belongs to the {group} group (n={n_sub} of {total} total). "
    if group == "IBS":
        subtype = demographics.get("ibs_subtype")
        if subtype:
            n_type = len(df[df[COL_IBS_TYPE] == subtype])
            ctx += f"IBS subtype: {subtype} (n={n_type} in cohort). "
    age = demographics.get("age")
    if age:
        age_mean = df[COL_AGE].mean()
        age_sd = df[COL_AGE].std()
        ctx += f"Age {age:.0f} (cohort M={age_mean:.1f}, SD={age_sd:.1f}). "
    return ctx


def _reasoning_chain(sleep, attention, fatigue, emotional, cognition, demographics):
    """Create a concise, readable reasoning chain for clinicians and users."""
    steps = []
    age = _fmt_number(demographics.get("age"), decimals=0)
    edu = _fmt_number(demographics.get("education"), decimals=1)
    is_ibs = demographics.get("ibs_status") == "IBS"
    context_parts = []
    gender = demographics.get("gender")
    if gender not in (None, "", "N/A"):
        context_parts.append(str(gender))
    if age is not None:
        context_parts.append(f"age {age}")
    if edu is not None:
        context_parts.append(f"education {edu} years")
    if demographics.get("ibs_status") not in (None, "", "N/A"):
        context_parts.append(f"{demographics.get('ibs_status')} group")
    if is_ibs and demographics.get("ibs_subtype") not in (None, "", "N/A"):
        context_parts.append(f"IBS subtype {demographics.get('ibs_subtype')}")

    sev = _fmt_number(demographics.get("ibs_severity"), decimals=1)
    sev_txt = f" IBS-SSS={sev}." if is_ibs and sev is not None else _missing_note_for_controls({"Group": demographics.get("ibs_status")})
    steps.append(
        "Step 1: Demographic and clinical context — "
        + (", ".join(context_parts) if context_parts else "demographic metadata available")
        + "."
        + sev_txt
    )

    steps.append(
        f"Step 2: Sleep (BIS) — Total score {sleep['scores'].get('total')}, classified as "
        f"{sleep.get('classification')} (cohort {sleep.get('percentile_in_cohort')}th percentile)."
    )
    steps.append(
        f"Step 3: Fatigue (Chalder) — Bimodal total {fatigue['scores'].get('chalder_bimodal_total')}, "
        f"{fatigue.get('classification')} (cohort {fatigue.get('percentile_in_cohort')}th percentile)."
    )
    steps.append(
        f"Step 4: Emotional distress (HADS) — Anxiety {emotional['scores'].get('HADS_A')} "
        f"({emotional['classification']['anxiety']}), Depression {emotional['scores'].get('HADS_D')} "
        f"({emotional['classification']['depression']})."
    )
    steps.append(
        f"Step 5: Sustained attention (CPT) — Detectability T={attention['scores'].get('Detectability')}, "
        f"Omissions T={attention['scores'].get('Omissions')}, Commissions T={attention['scores'].get('Commissions')}, "
        f"HRT T={attention['scores'].get('HRT')}."
    )

    weak_domains = [k for k, v in cognition["classifications"].items() if "weakness" in v.lower()]
    strong_domains = [k for k, v in cognition["classifications"].items() if "strength" in v.lower() and k != "Total Scale"]
    cog_sentence = (
        f"Step 6: Neurocognition (RBANS) — Sum Raw {_safe_val(cognition['scores'].get('Total Scale'))} "
        f"at the {cognition.get('percentile_in_cohort')}th cohort percentile. "
        "The interpretation uses raw subtests plus cohort-standardized summary composites."
    )
    if weak_domains:
        cog_sentence += f" Relative weaknesses are present in {', '.join(weak_domains)}."
    elif strong_domains:
        cog_sentence += f" Relative strengths are present in {', '.join(strong_domains)}."
    else:
        cog_sentence += " No marked cohort-relative cognitive extremes are evident."
    steps.append(cog_sentence)

    flagged_domains = []
    if sleep["flags"]:
        flagged_domains.append("sleep")
    if attention["flags"]:
        flagged_domains.append("attention")
    if fatigue["flags"]:
        flagged_domains.append("fatigue")
    if emotional["flags"]:
        flagged_domains.append("mood")
    if cognition["flags"]:
        flagged_domains.append("cognition")
    steps.append(
        "Step 7: Cross-domain integration — "
        + (
            f"Flags span {', '.join(flagged_domains)}, supporting an interacting symptom pattern."
            if flagged_domains
            else "No domain crosses major flag thresholds; the profile is comparatively even."
        )
    )

    if sleep["flags"] and fatigue["flags"] and attention["flags"]:
        prognosis = (
            "Sleep-fatigue-attention coupling is prominent, suggesting that addressing insomnia and daytime fatigue "
            "is likely to produce the largest downstream gains."
        )
    elif emotional["flags"] and (attention["flags"] or cognition["flags"]):
        prognosis = (
            "Mood and cognitive inefficiency co-occur, so emotional stabilization may improve concentration "
            "and reduce apparent cognitive burden."
        )
    else:
        prognosis = "The prognosis depends mainly on whether the flagged domains respond to targeted follow-up."

    steps.append(f"Step 8: Prognostic formulation — {prognosis}")
    return steps


def _recommendations(sleep, attention, fatigue, emotional, cognition, demographics):
    """Generate short, traceable recommendations tied to flagged domains."""
    therapeutic: List[str] = []
    further: List[str] = []
    is_ibs = demographics.get("ibs_status") == "IBS"
    sev = demographics.get("ibs_severity")

    if sleep["classification"] in ("Moderate", "Severe"):
        therapeutic.append(
            "SLEEP: Prioritize CBT-I and structured sleep-hygiene measures, as insomnia is a likely upstream driver "
            "of daytime fatigue and reduced cognitive efficiency."
        )
    elif sleep["classification"] == "Mild":
        therapeutic.append("SLEEP: Use a sleep diary and brief behavioral sleep interventions, with re-check if symptoms escalate.")

    if fatigue["classification"] == "Significant fatigue":
        therapeutic.append(
            "FATIGUE: Use paced activity scheduling and screen for reversible medical contributors such as anemia, thyroid disease, and vitamin deficiency."
        )
        if sleep["flags"]:
            therapeutic.append("FATIGUE-SLEEP LINK: Reassess fatigue after sleep-focused treatment before escalating to more extensive fatigue workup.")

    if attention["flags"]:
        therapeutic.append(
            "ATTENTION: Add compensatory supports for sustained attention, such as task chunking, fewer distractions, and written reminders."
        )
        further.append("ATTENTION: Repeat CPT or broader attentional testing if problems persist after sleep, mood, or fatigue interventions.")

    anx_class = emotional["classification"]["anxiety"]
    dep_class = emotional["classification"]["depression"]
    if anx_class in ("Clinical", "Borderline"):
        therapeutic.append("ANXIETY: Consider CBT-based anxiety treatment; anxious arousal can worsen sleep and concentration.")
    if dep_class in ("Clinical", "Borderline"):
        therapeutic.append("DEPRESSION: Consider behavioral activation or psychotherapy if low mood is affecting energy, motivation, or cognition.")

    weak_cog = [k for k, v in cognition["classifications"].items() if "weakness" in v.lower()]
    if weak_cog:
        further.append(
            f"COGNITION: Follow up the cohort-relative RBANS weaknesses in {', '.join(weak_cog)} if the patient reports matching day-to-day difficulties."
        )
        further.append(
            "COGNITION: If cognitive complaints persist despite treating sleep, fatigue, and mood contributors, consider expanded neuropsychological assessment."
        )

    if is_ibs:
        therapeutic.append(
            "IBS INTEGRATION: Coordinate neuropsychological follow-up with gastrointestinal care, since gut-brain symptoms may reinforce sleep, fatigue, and mood burden."
        )
        if sev is not None and sev > 300:
            further.append("IBS: High symptom burden supports close gastroenterology follow-up alongside symptom-targeted psychological care.")

    if not therapeutic:
        therapeutic.append("No immediate domain-specific treatment is required; routine monitoring and healthy lifestyle maintenance are appropriate.")
    if not further:
        further.append("No urgent further examinations are indicated unless symptoms worsen or new subjective cognitive complaints emerge.")

    return {"therapeutic": therapeutic, "further_examinations": further}


# ============================================================================
# VISUALIZATION A: MULTI-PANEL DOMAIN PROFILES
# ============================================================================

def generate_multipanel(df: pd.DataFrame, patient_id: str, output_dir: str,
                        audience: str = "clinical",
                        reference_df: pd.DataFrame = None) -> Tuple[str, str]:
    """Generate multi-panel domain-profile figure.

    When *reference_df* is given, cohort distributions in violin/swarm
    plots are drawn from the reference cohort rather than *df*.
    """
    patient = get_patient(df, patient_id)
    ref = reference_df if reference_df is not None else df

    if audience == "patient":
        return _multipanel_patient(ref, patient, patient_id, output_dir)
    elif audience == "physician":
        return _multipanel_physician(ref, patient, patient_id, output_dir)
    else:
        return _multipanel_clinical(ref, patient, patient_id, output_dir)


def _multipanel_clinical(df, patient, pid, out_dir):
    """Clinical audience: full statistical detail."""
    sns.set_theme(style="whitegrid", palette="colorblind", font_scale=0.9)
    fig = plt.figure(figsize=(28, 16))

    # Layout: 2 rows. Row1: BIS, CPT(4), Chalder. Row2: HADS(2), RBANS(6)
    gs = fig.add_gridspec(2, 12, hspace=0.35, wspace=0.4)

    # Panel 1: BIS Total
    ax_bis = fig.add_subplot(gs[0, 0:3])
    _violin_panel(ax_bis, df, patient, "BIS_total", "BIS Total Score",
                  cutoffs=[(19, "Clinical threshold", "r"), (7, "Minimal", "gray")],
                  higher_worse=True, show_stats=True)

    # Panel 2: CPT key metrics
    ax_cpt = fig.add_subplot(gs[0, 3:8])
    _grouped_bar_cpt(ax_cpt, df, patient, show_stats=True)

    # Panel 3: Chalder
    ax_fss = fig.add_subplot(gs[0, 8:12])
    _violin_panel(ax_fss, df, patient, "Chalder_total", "Chalder Fatigue (bimodal)",
                  cutoffs=[(CHALDER_CASENESS, "Caseness", "r")],
                  higher_worse=True, show_stats=True)

    # Panel 4: HADS
    ax_hads = fig.add_subplot(gs[1, 0:5])
    _hads_panel(ax_hads, df, patient, show_stats=True)

    # Panel 5: RBANS
    ax_rbans = fig.add_subplot(gs[1, 5:12])
    _rbans_panel(ax_rbans, df, patient, show_stats=True)

    context_line = _patient_context_line(patient, include_education=True)
    title = f"Neuropsychological Domain Profile — {pid}"
    if context_line:
        title += f"\n{context_line}"
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.98)

    pdf_path = os.path.join(out_dir, f"{pid}_multipanel_clinical.pdf")
    png_path = os.path.join(out_dir, f"{pid}_multipanel_clinical.png")
    plt.savefig(pdf_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.savefig(png_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return pdf_path, png_path


def _multipanel_physician(df, patient, pid, out_dir):
    """Physician audience: traffic-light summary using March 16 domain choices."""
    sns.set_theme(style="whitegrid", font_scale=1.0)
    fig = plt.figure(figsize=(24, 10))
    gs = fig.add_gridspec(1, 5, wspace=0.35)

    domains = [
        ("BIS_total", "Sleep (BIS)", True, [(19, "Clinical", "r")]),
        ("CPT_Detectability", "Attention (CPT d')", True, []),
        ("Chalder_total", "Fatigue (Chalder)", True, [(4, "Caseness", "r")]),
        ("HADS_total", "Distress (HADS)", True, [(15, "Moderate", "r"), (8, "Mild", "#E69F00")]),
        ("RBANS_Sum_Raw", "Cognition (RBANS)", False, []),
    ]

    for i, (col, title, higher_worse, cuts) in enumerate(domains):
        ax = fig.add_subplot(gs[0, i])
        val = patient.get(col, np.nan)
        pct = percentile_of_wellness(val, df[col], invert=higher_worse) if not pd.isna(val) else 50

        # Traffic light color
        if pct < 16:
            marker_color = "#D55E00"  # red
            status = "ACTION"
        elif pct < 50:
            marker_color = "#E69F00"  # amber
            status = "MONITOR"
        else:
            marker_color = "#009E73"  # green
            status = "OK"

        _violin_panel_simple(ax, df, patient, col, title, cuts, higher_worse, marker_color)
        ax.set_title(f"{title}\n[{status}]", fontsize=12, fontweight="bold",
                     color=marker_color)

    context_line = _patient_context_line(patient, include_education=False)
    title = f"Clinical Summary — {pid}"
    if context_line:
        title += f"\n{context_line}"
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)
    pdf_path = os.path.join(out_dir, f"{pid}_multipanel_physician.pdf")
    png_path = os.path.join(out_dir, f"{pid}_multipanel_physician.png")
    plt.savefig(pdf_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.savefig(png_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return pdf_path, png_path


def _multipanel_patient(df, patient, pid, out_dir):
    """Patient audience: accessible infographic using broader March 16 composites."""
    sns.set_theme(style="white", font_scale=1.1)
    fig, axes = plt.subplots(1, 5, figsize=(24, 8))

    domains = [
        ("BIS_total", "Sleep Quality", True),
        ("CPT_Detectability", "Concentration", True),
        ("Chalder_total", "Energy Level", True),
        ("HADS_total", "Emotional\nWellbeing", True),
        ("RBANS_Sum_Raw", "Memory &\nThinking", False),
    ]

    for ax, (col, title, invert) in zip(axes, domains):
        val = patient.get(col, np.nan)
        pct = percentile_of_wellness(val, df[col], invert=invert) if not pd.isna(val) else 50

        # Horizontal gauge
        _gauge_panel(ax, pct, title)

    fig.suptitle(
        f"Your Neuropsychological Profile",
        fontsize=16, fontweight="bold", y=1.02
    )
    fig.text(0.5, -0.02,
             "Each bar shows where your score falls compared to others in the study.\n"
             "Longer bars = better functioning in that area.",
             ha="center", fontsize=11, style="italic", color="gray")

    pdf_path = os.path.join(out_dir, f"{pid}_multipanel_patient.pdf")
    png_path = os.path.join(out_dir, f"{pid}_multipanel_patient.png")
    plt.savefig(pdf_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.savefig(png_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return pdf_path, png_path


# --- Helper panels ---

def _violin_panel(ax, df, patient, col, title, cutoffs=None, higher_worse=False, show_stats=False):
    """Standard violin + swarm + patient marker panel."""
    plot_df = df[[COL_GROUP, col]].dropna()
    if len(plot_df) == 0:
        ax.set_title(title + "\n(no data)")
        return

    sns.violinplot(data=plot_df, x=COL_GROUP, y=col, ax=ax, inner="quart",
                   palette={("IBS"): PAL_IBS, "HC": PAL_HC}, alpha=0.4, order=["HC", "IBS"])
    sns.stripplot(data=plot_df, x=COL_GROUP, y=col, ax=ax,
                  palette={"IBS": PAL_IBS, "HC": PAL_HC}, alpha=0.3, size=3, order=["HC", "IBS"])

    # Patient marker
    val = patient[col]
    grp = patient[COL_GROUP]
    x_pos = 0 if grp == "HC" else 1
    if not pd.isna(val):
        ax.plot(x_pos, val, marker="D", color=PAL_PATIENT, markersize=14, zorder=10,
                markeredgecolor="white", markeredgewidth=2)
        pct = percentile_rank(val, df[col])
        ax.annotate(f"{val:.0f}\n({pct:.0f}th %ile)", (x_pos, val),
                    textcoords="offset points", xytext=(15, 5),
                    fontsize=8, fontweight="bold", color=PAL_PATIENT,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

    # Cutoff lines
    if cutoffs:
        for cutval, label, color in cutoffs:
            ax.axhline(y=cutval, ls="--", color=color, alpha=0.6, linewidth=1)
            ax.text(ax.get_xlim()[1], cutval, f" {label}", fontsize=7, color=color,
                    va="center", ha="left")

    if show_stats:
        z = cohort_z_score(val, df[col])
        if not np.isnan(z):
            ax.text(0.02, 0.98, f"z = {z:+.2f}", transform=ax.transAxes,
                    fontsize=8, va="top", color="gray")

    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel("")


def _violin_panel_simple(ax, df, patient, col, title, cutoffs, higher_worse, marker_color):
    """Simplified violin for physician view."""
    plot_df = df[[COL_GROUP, col]].dropna()
    if len(plot_df) == 0:
        ax.set_title(title)
        return

    sns.violinplot(data=plot_df, x=COL_GROUP, y=col, ax=ax, inner="quart",
                   color="lightgray", alpha=0.5, order=["HC", "IBS"])

    val = patient[col]
    grp = patient[COL_GROUP]
    x_pos = 0 if grp == "HC" else 1
    if not pd.isna(val):
        ax.plot(x_pos, val, marker="*", color=marker_color, markersize=20, zorder=10,
                markeredgecolor="white", markeredgewidth=1.5)

    if cutoffs:
        for cutval, label, color in cutoffs:
            ax.axhline(y=cutval, ls="--", color=color, alpha=0.5)

    ax.set_xlabel("")


def _gauge_panel(ax, percentile, title):
    """Horizontal gauge bar for patient view."""
    ax.clear()
    # Background gradient zones
    ax.barh(0, 100, height=0.6, color="#f0f0f0", edgecolor="none")
    ax.barh(0, 33, height=0.6, color="#ffcccc", alpha=0.4, edgecolor="none")
    ax.barh(0, 66, height=0.6, color="#fff3cc", alpha=0.3, edgecolor="none")
    ax.barh(0, 100, height=0.6, color="#ccffcc", alpha=0.2, edgecolor="none")

    # Patient score
    color = "#D55E00" if percentile < 25 else ("#E69F00" if percentile < 50 else "#009E73")
    ax.barh(0, percentile, height=0.6, color=color, alpha=0.7, edgecolor="none")
    ax.plot(percentile, 0, marker="|", color="black", markersize=30, markeredgewidth=3)

    # Labels
    if percentile < 25:
        label = "Some difficulty"
    elif percentile < 50:
        label = "Below average"
    elif percentile < 75:
        label = "Good"
    else:
        label = "Excellent"

    ax.text(percentile + 2, 0, label, fontsize=11, fontweight="bold", va="center", color=color)
    ax.set_xlim(0, 110)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["", "Some\ndifficulty", "Average", "Good", "Excellent"], fontsize=8)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)


def _grouped_bar_cpt(ax, df, patient, show_stats=False):
    """Expanded 9-variable CPT profile for the clinical panel."""
    x = np.arange(len(CPT_METRICS_FULL))
    width = 0.25

    hc = df[df[COL_GROUP] == "HC"]
    ibs = df[df[COL_GROUP] == "IBS"]

    hc_means = [hc[col].mean() for col, _ in CPT_METRICS_FULL]
    ibs_means = [ibs[col].mean() for col, _ in CPT_METRICS_FULL]
    pat_vals = [patient.get(col, np.nan) for col, _ in CPT_METRICS_FULL]

    ax.bar(x - width, hc_means, width, label="HC mean", color=PAL_HC, alpha=0.6)
    ax.bar(x, ibs_means, width, label="IBS mean", color=PAL_IBS, alpha=0.6)
    ax.bar(x + width, pat_vals, width, label="Patient", color=PAL_PATIENT, alpha=0.85)

    higher_worse = {
        "CPT_Detectability": True,
        "CPT_Omissions": True,
        "CPT_Commissions": True,
        "CPT_Perseverations": True,
        "CPT_HRT": True,
        "CPT_HRT_SD": True,
        "CPT_HRT_Block_Change": True,
        "CPT_HRT_ISI_Change": True,
        "CPT_Variability": True,
    }
    for idx, (col, _) in enumerate(CPT_METRICS_FULL):
        val = pat_vals[idx]
        if pd.isna(val):
            continue
        if higher_worse[col] and val >= CPT_CLINICAL:
            ax.plot(idx + width, val + 1, "v", color=PAL_CONCERN, markersize=7)
        elif higher_worse[col] and val >= CPT_ELEVATED:
            ax.plot(idx + width, val + 1, "v", color=PAL_IBS, markersize=7)

    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in CPT_METRICS_FULL], fontsize=8)
    ax.set_ylabel("T-score", fontsize=9)
    ax.set_title("CPT Performance Metrics", fontsize=11, fontweight="bold")
    ax.axhline(50, ls=":", color="gray", alpha=0.5, label="T=50")
    ax.axhline(CPT_ELEVATED, ls="--", color="orange", alpha=0.4)
    ax.axhline(CPT_CLINICAL, ls="--", color="red", alpha=0.4)
    ax.legend(fontsize=7, loc="upper right", ncol=2)


def _hads_panel(ax, df, patient, show_stats=False):
    """HADS anxiety and depression panel."""
    # Prepare data for grouped display
    plot_data = []
    for _, row in df.iterrows():
        plot_data.append({"Group": row[COL_GROUP], "Subscale": "Anxiety", "Score": row["HADS_Anxiety"]})
        plot_data.append({"Group": row[COL_GROUP], "Subscale": "Depression", "Score": row["HADS_Depression"]})
    plot_df = pd.DataFrame(plot_data).dropna()

    sns.violinplot(data=plot_df, x="Subscale", y="Score", hue="Group", ax=ax,
                   inner="quart", palette={"IBS": PAL_IBS, "HC": PAL_HC}, alpha=0.4,
                   split=True)

    # Patient markers
    for i, (sub, col) in enumerate([(0, "HADS_Anxiety"), (1, "HADS_Depression")]):
        val = patient[col]
        if not pd.isna(val):
            ax.plot(sub, val, marker="D", color=PAL_PATIENT, markersize=14, zorder=10,
                    markeredgecolor="white", markeredgewidth=2)
            pct = percentile_rank(val, df[col])
            ax.annotate(f"{val:.0f} ({pct:.0f}th)", (sub, val),
                        textcoords="offset points", xytext=(15, 5),
                        fontsize=9, fontweight="bold", color=PAL_PATIENT)

    # Cutoff zones
    ax.axhspan(0, 7, alpha=0.05, color="green", label="Normal")
    ax.axhspan(8, 10, alpha=0.05, color="orange", label="Borderline")
    ax.axhspan(11, 21, alpha=0.05, color="red", label="Clinical")
    ax.axhline(y=8, ls="--", color="orange", alpha=0.5)
    ax.axhline(y=11, ls="--", color="red", alpha=0.5)

    ax.set_title("HADS — Anxiety & Depression", fontsize=11, fontweight="bold")
    ax.set_ylabel("Score (0-21)")
    ax.legend(fontsize=8, loc="upper right")


def _rbans_panel(ax, df, patient, show_stats=False):
    """Clinical RBANS panel showing all raw subtests on a z-standardized scale."""
    cols = list(RBANS_SUBTEST_LABELS)
    x = np.arange(len(cols))
    width = 0.25

    # We z-standardize within the observed cohort so that very different raw
    # RBANS subtests can be plotted on one interpretable common axis.
    z_df = pd.DataFrame({col: _series_z(df[col]) for col in cols}, index=df.index)
    hc = df[df[COL_GROUP] == "HC"]
    ibs = df[df[COL_GROUP] == "IBS"]
    hc_means = [z_df.loc[hc.index, col].mean() for col in cols]
    ibs_means = [z_df.loc[ibs.index, col].mean() for col in cols]
    patient_z = [z_df.loc[patient.name, col] if patient.name in z_df.index else np.nan for col in cols]

    ax.bar(x - width, hc_means, width, label="HC mean", color=PAL_HC, alpha=0.6)
    ax.bar(x, ibs_means, width, label="IBS mean", color=PAL_IBS, alpha=0.6)
    ax.bar(x + width, patient_z, width, label="Patient", color=PAL_PATIENT, alpha=0.85)

    for idx, col in enumerate(cols):
        raw_val = patient.get(col, np.nan)
        if not pd.isna(raw_val):
            ax.text(idx + width, patient_z[idx] + 0.08, f"{raw_val:.0f}", fontsize=7, ha="center", color=PAL_PATIENT)

    ax.axhline(0, ls=":", color="gray", alpha=0.6)
    ax.axhline(-1, ls="--", color="orange", alpha=0.25)
    ax.axhline(-1.5, ls="--", color="red", alpha=0.25)
    ax.set_xticks(x)
    ax.set_xticklabels(
        ["Word\nList", "Story\nMem", "Figure\nCopy", "Line\nOrient", "Naming", "Fluency", "Digit\nSpan", "Coding", "Word\nRecall", "Story\nRecall", "Word\nRecog", "Figure\nRecall"],
        fontsize=8,
    )
    ax.set_ylabel("Cohort-standardized score", fontsize=9)
    ax.set_title(
        f"RBANS Raw Subtests (Sum Raw={_safe_val(patient.get('RBANS_Sum_Raw', np.nan))})",
        fontsize=11,
        fontweight="bold",
    )
    ax.legend(fontsize=7, loc="upper right")


# ============================================================================
# VISUALIZATION B: RADAR / SPIDER PLOTS
# ============================================================================

def generate_radar(df: pd.DataFrame, patient_id: str, output_dir: str,
                   audience: str = "clinical",
                   reference_df: pd.DataFrame = None) -> Tuple[str, str]:
    """Generate audience-tailored radar/spider plot.

    When *reference_df* is given, group statistics (means, percentiles,
    Cohen's d) are computed from the reference cohort.
    """
    patient = get_patient(df, patient_id)
    ref = reference_df if reference_df is not None else df
    controls = ref[ref[COL_GROUP] == "HC"]
    ibs_group = ref[ref[COL_GROUP] == "IBS"]

    expanded = (audience == "clinical")
    config = RADAR_EXPANDED if expanded else RADAR_COMPACT

    # Compute percentile-of-wellness for each domain
    patient_pcts = []
    ctrl_medians = []
    ctrl_uppers = []
    ctrl_lowers = []
    ibs_medians = []

    for col, inv in zip(config["columns"], config["invert"]):
        series = ref[col]
        val = patient[col]
        patient_pcts.append(percentile_of_wellness(val, series, invert=inv))

        # Control group stats (in percentile-of-wellness space)
        ctrl_vals = controls[col].dropna()
        ctrl_pows = [percentile_of_wellness(v, series, invert=inv) for v in ctrl_vals]
        ctrl_pows = [p for p in ctrl_pows if not np.isnan(p)]
        if ctrl_pows:
            ctrl_medians.append(np.median(ctrl_pows))
            ctrl_uppers.append(np.percentile(ctrl_pows, 84))
            ctrl_lowers.append(np.percentile(ctrl_pows, 16))
        else:
            ctrl_medians.append(50)
            ctrl_uppers.append(84)
            ctrl_lowers.append(16)

        ibs_vals = ibs_group[col].dropna()
        ibs_pows = [percentile_of_wellness(v, series, invert=inv) for v in ibs_vals]
        ibs_pows = [p for p in ibs_pows if not np.isnan(p)]
        ibs_medians.append(np.median(ibs_pows) if ibs_pows else 50)

    N = len(config["labels"])
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    # Close polygons
    pat_vals = patient_pcts + patient_pcts[:1]
    ctrl_med = ctrl_medians + ctrl_medians[:1]
    ctrl_up = ctrl_uppers + ctrl_uppers[:1]
    ctrl_lo = ctrl_lowers + ctrl_lowers[:1]
    ibs_med = ibs_medians + ibs_medians[:1]

    sns.set_theme(style="whitegrid", palette="colorblind")
    # The clinical version includes a right-side inset and a larger legend, so
    # it benefits from a slightly wider canvas than the compact radar views.
    fig_size = (11.5, 9.5) if expanded else (9, 9)
    fig, ax = plt.subplots(figsize=fig_size, subplot_kw=dict(polar=True))

    # Layer 1: Clinical concern zone
    concern = [16] * N + [16]
    ax.fill(angles, concern, color="red", alpha=0.06, label="Clinical concern zone (<16th %ile)")

    # Layer 2: Healthy control range
    ax.fill(angles, ctrl_up, color="green", alpha=0.10)
    ax.fill(angles, ctrl_lo, color="white", alpha=1.0)
    ax.fill(angles, ctrl_lo, color="green", alpha=0.04)
    # Draw band properly
    for i in range(N):
        a1, a2 = angles[i], angles[i + 1]
        ax.fill([a1, a1, a2, a2], [ctrl_lo[i], ctrl_up[i], ctrl_up[i + 1], ctrl_lo[i + 1]],
                color="green", alpha=0.10)
    ax.plot(angles, ctrl_med, "s-", color="green", alpha=0.4, linewidth=1, markersize=3,
            label="Healthy control median")

    # Layer 3: IBS median
    ax.plot(angles, ibs_med, "o--", color=PAL_IBS, alpha=0.6, linewidth=1.5,
            markersize=5, label="IBS group median")

    # Layer 4: Patient profile
    ax.plot(angles, pat_vals, "D-", color=PAL_PATIENT, linewidth=2.5, markersize=10,
            zorder=5, label=f"{_participant_label(patient_id)} {patient_id}")
    ax.fill(angles, pat_vals, color=PAL_PATIENT, alpha=0.06)

    # Annotate vertices
    for i, (angle, val) in enumerate(zip(angles[:-1], patient_pcts)):
        if np.isnan(val):
            continue
        if audience == "clinical":
            z_val = cohort_z_score(patient[config["columns"][i]], ref[config["columns"][i]])
            # Central labels can stack on top of each other when several scores
            # fall in the concern zone. Keep the full percentile + z-score detail
            # for less crowded points, but collapse the most central callouts to a
            # shorter percentile label and push them outward from the origin.
            txt = f"{val:.0f}th"
            if val >= 25 and not np.isnan(z_val):
                txt = f"{txt}\nz={z_val:+.1f}"
        elif audience == "physician":
            txt = f"{val:.0f}th"
        else:
            txt = ""  # patient view uses qualitative labels

        color = PAL_CONCERN if val < 16 else (PAL_IBS if val < 50 else PAL_GREEN)
        marker_color = PAL_CONCERN if val < 16 else PAL_PATIENT

        # Spread annotation boxes around the circle instead of placing every box
        # at the same northeast offset, which creates avoidable clutter near the
        # center of the clinical detail plot.
        x_sign = 1 if np.cos(angle) >= 0 else -1
        y_sign = 1 if np.sin(angle) >= 0 else -1
        x_mag = 14 if abs(np.cos(angle)) > 0.25 else 7
        y_mag = 14 if abs(np.sin(angle)) > 0.25 else 7
        if audience == "clinical" and val < 25:
            x_mag += 4
            y_mag += 4
        xytext = (x_sign * x_mag, y_sign * y_mag)
        ha = "left" if x_sign > 0 else "right"
        va = "bottom" if y_sign > 0 else "top"
        is_central_clinical_label = audience == "clinical" and val < 25
        label_fontsize = 6 if is_central_clinical_label else (7 if audience == "clinical" else 9)
        label_alpha = 0.45 if is_central_clinical_label else 0.65
        label_color = PAL_CONCERN if val < 16 else ("dimgray" if is_central_clinical_label else marker_color)

        # Re-plot vertex with traffic-light color for physician
        if audience == "physician":
            ax.plot(angle, val, "D", color=color, markersize=12, zorder=6,
                    markeredgecolor="white", markeredgewidth=1.5)

        if txt:
            bbox = None if is_central_clinical_label else dict(
                boxstyle="round,pad=0.10",
                facecolor="white",
                alpha=label_alpha,
                edgecolor="none",
            )
            ax.annotate(txt, (angle, val), textcoords="offset points",
                        xytext=xytext, fontsize=label_fontsize,
                        fontweight="bold", color=label_color,
                        ha=ha, va=va,
                        bbox=bbox)

    # Axis labels
    ax.set_xticks(angles[:-1])
    if audience == "patient":
        ax.set_xticklabels(config["labels"], fontsize=13, fontweight="bold")
        ax.set_yticks([25, 50, 75])
        ax.set_yticklabels(["Some\ndifficulty", "Good", "Excellent"],
                           fontsize=9, color="gray")
    elif audience == "physician":
        ax.set_xticklabels(config["labels"], fontsize=11, fontweight="bold")
        ax.set_yticks([16, 50, 84])
        ax.set_yticklabels(["16th", "50th", "84th"], fontsize=8, color="gray")
    else:
        ax.set_xticklabels(config["labels"], fontsize=9)
        ax.set_yticks([16, 50, 84])
        ax.set_yticklabels(["16th %ile", "50th %ile", "84th %ile"],
                           fontsize=8, color="gray")

    ax.set_ylim(0, 100)
    legend_anchor = (1.28, 1.10) if audience == "clinical" else (1.35, 1.1)
    ax.legend(loc="upper right", bbox_to_anchor=legend_anchor, fontsize=9)

    # Title
    aud_label = {"clinical": "Clinical Detail", "physician": "Physician Summary",
                 "patient": "Your Profile"}[audience]
    context_line = _patient_context_line(
        patient,
        include_education=False,
        include_ibs_subtype=False,
        include_ibs_severity=(audience == "clinical"),
    )
    title = f"Neuropsychological Profile — {patient_id} ({aud_label})"
    if context_line:
        title += f"\n{context_line}"
    ax.set_title(title, fontsize=12, fontweight="bold", pad=30)

    # Patient interpretation sentence
    if audience == "patient":
        interpretation = _plain_language_summary(patient_pcts, config["labels"])
        fig.text(0.5, 0.02, interpretation, ha="center", fontsize=11,
                 style="italic", wrap=True,
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow",
                           edgecolor="gray", alpha=0.8))

    # Cohen's d inset for clinical
    if audience == "clinical":
        _add_cohens_d_inset(fig, ref, config)
        # `tight_layout` does not cooperate with manual inset axes. Use explicit
        # margins instead so the radar, title, legend, and inset all have stable
        # breathing room and figure generation stays warning-free.
        fig.subplots_adjust(left=0.05, right=0.68, top=0.86, bottom=0.08)
    else:
        plt.tight_layout(rect=[0, 0.05, 0.85, 0.95])

    pdf_path = os.path.join(output_dir, f"{patient_id}_radar_{audience}.pdf")
    png_path = os.path.join(output_dir, f"{patient_id}_radar_{audience}.png")
    plt.savefig(pdf_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.savefig(png_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return pdf_path, png_path


def _plain_language_summary(pcts: list, labels: list) -> str:
    """Generate patient-friendly interpretation."""
    clean_labels = [l.replace("\n", " ") for l in labels]
    strengths = [clean_labels[i] for i, p in enumerate(pcts) if not np.isnan(p) and p >= 60]
    concerns = [clean_labels[i] for i, p in enumerate(pcts) if not np.isnan(p) and p < 30]
    moderate = [clean_labels[i] for i, p in enumerate(pcts) if not np.isnan(p) and 30 <= p < 50]

    parts = []
    if strengths:
        parts.append(f"Your profile shows relative strengths in {', '.join(strengths)}")
    if concerns:
        parts.append(f"areas of concern in {', '.join(concerns)} that may benefit from attention")
    elif moderate:
        parts.append(f"some areas to monitor: {', '.join(moderate)}")

    if parts:
        return ". ".join(parts) + "."
    return "Your profile is within typical ranges across all assessed domains."


def _add_cohens_d_inset(fig, df, config):
    """Add Cohen's d effect size inset for clinical audience."""
    controls = df[df[COL_GROUP] == "HC"]
    ibs_group = df[df[COL_GROUP] == "IBS"]

    ax_inset = fig.add_axes([0.81, 0.14, 0.17, 0.42])
    inset_label_wrap = {
        "RBANS Total": "RBANS\nTotal",
        "RBANS Delayed Memory": "RBANS Delayed\nMem.",
        "RBANS Immed. Memory": "RBANS Immed.\nMem.",
    }
    ds = []
    labels = []
    for col, inv, label in zip(config["columns"], config["invert"], config["labels"]):
        d = cohens_d(controls[col], ibs_group[col])
        if inv:
            d = -d  # flip so positive d = IBS worse
        ds.append(d)
        flat_label = label.replace("\n", " ")
        labels.append(inset_label_wrap.get(flat_label, flat_label))

    colors = [PAL_CONCERN if abs(d) > 0.5 else (PAL_IBS if abs(d) > 0.2 else "gray") for d in ds]
    y_pos = np.arange(len(labels))
    ax_inset.barh(y_pos, ds, color=colors, alpha=0.7)
    ax_inset.set_yticks(y_pos)
    ax_inset.set_yticklabels(labels, fontsize=6)
    ax_inset.tick_params(axis="y", pad=1)
    ax_inset.set_xlabel("Cohen's d\n(IBS vs HC)", fontsize=8)
    ax_inset.set_title("Effect Sizes", fontsize=9, fontweight="bold")
    ax_inset.axvline(x=0, color="gray", linewidth=0.5)
    ax_inset.axvline(x=0.2, color="gray", linewidth=0.5, ls=":")
    ax_inset.axvline(x=-0.2, color="gray", linewidth=0.5, ls=":")


# ============================================================================
# LATEX REPORT GENERATION
# ============================================================================

def generate_latex_report(analysis: Dict, output_dir: str) -> str:
    """Generate LaTeX PDF report for a patient."""
    pid = analysis["patient_id"]
    demo = analysis["demographics"]
    domains = analysis["domain_findings"]

    tex_content = _build_latex(pid, demo, domains, analysis)

    tex_path = os.path.join(output_dir, f"{pid}_report.tex")
    pdf_path = os.path.join(output_dir, f"{pid}_report.pdf")

    with open(tex_path, "w") as f:
        f.write(tex_content)

    # Compile twice for references
    for _ in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
            capture_output=True, text=True, timeout=60
        )

    # Clean auxiliary files (silently skip if permission denied)
    for ext in [".aux", ".log", ".out"]:
        aux = os.path.join(output_dir, f"{pid}_report{ext}")
        try:
            if os.path.exists(aux):
                os.remove(aux)
        except OSError:
            pass

    return pdf_path


def _tex_escape(s):
    """Escape special LaTeX characters."""
    if s is None:
        return "N/A"
    s = str(s)
    # Replace >= and <= before escaping other chars
    s = s.replace(">=", "$\\geq$")
    s = s.replace("<=", "$\\leq$")
    for char in ["&", "%", "$", "#", "_", "{", "}"]:
        # Don't double-escape $ signs we just introduced
        if char == "$":
            continue
        s = s.replace(char, f"\\{char}")
    s = s.replace("~", "\\textasciitilde{}")
    s = s.replace("^", "\\textasciicircum{}")
    return s


def _build_latex(pid, demo, domains, analysis):
    """Build the full LaTeX document string with embedded figures and detailed captions."""
    sleep = domains["sleep_BIS"]
    cpt = domains["attention_CPT"]
    fatigue = domains["fatigue_Chalder"]
    hads = domains["emotional_distress_HADS"]
    rbans = domains["neurocognition_RBANS"]
    recs = analysis["recommendations"]

    # RBANS table rows. In the standalone March 16 pipeline these are cohort-
    # relative summaries plus Sum Raw, not the older normed index-score fields.
    rbans_rows = ""
    for idx_name in ["Immediate Memory", "Visuospatial", "Language", "Attention", "Delayed Memory", "Recognition", "Total Scale"]:
        score = rbans["scores"].get(idx_name, "N/A")
        pct = rbans["percentiles"].get(idx_name, "N/A")
        cls = rbans["classifications"].get(idx_name, "N/A")
        rbans_rows += f"    {_tex_escape(idx_name)} & {score} & {pct} & {_tex_escape(cls)} \\\\\n"

    # CPT table rows
    cpt_rows = ""
    cpt_metric_info = {
        "Detectability": ("Signal detection sensitivity (d')", True),
        "Omissions": ("Missed targets (inattention)", True),
        "Commissions": ("False alarms (impulsivity)", True),
        "HRT": ("Mean reaction time", True),
        "HRT_SD": ("Reaction time variability", True),
        "Perseverations": ("Anticipatory responses", True),
        "Variability": ("Response speed consistency", True),
    }
    for metric, (desc, worse_high) in cpt_metric_info.items():
        t_val = cpt["scores"].get(metric, "N/A")
        pct_val = cpt.get("percentiles", {}).get(metric, "N/A")
        flag = ""
        if isinstance(t_val, (int, float)) and not pd.isna(t_val):
            if worse_high and t_val >= CPT_CLINICAL:
                flag = "\\textcolor{clinred}{Clinical}"
            elif worse_high and t_val >= CPT_ELEVATED:
                flag = "\\textcolor{clinamber}{Elevated}"
            else:
                flag = "\\textcolor{clingreen}{Normal}"
        cpt_rows += f"    {_tex_escape(desc)} & T={t_val} & {pct_val} & {flag} \\\\\n"

    # Reasoning steps — formatted as subsections for readability
    reasoning_sections = ""
    for step_text in analysis["reasoning_chain"]:
        # Split step label from content
        if ": " in step_text and step_text.startswith("Step"):
            parts = step_text.split(": ", 1)
            label = parts[0]
            # Extract sublabel (e.g., "Step 2: Sleep (BIS)")
            if " — " in parts[1]:
                sublabel, content = parts[1].split(" — ", 1)
                reasoning_sections += (
                    f"\\paragraph{{{_tex_escape(label)}: {_tex_escape(sublabel)}}}\n"
                    f"{_tex_escape(content)}\n\n"
                )
            else:
                reasoning_sections += (
                    f"\\paragraph{{{_tex_escape(label)}}}\n"
                    f"{_tex_escape(parts[1])}\n\n"
                )
        else:
            reasoning_sections += f"{_tex_escape(step_text)}\n\n"

    # Recommendations — formatted with bold domain labels
    ther_items = "\n".join([f"  \\item {_tex_escape(r)}" for r in recs["therapeutic"]])
    exam_items = "\n".join([f"  \\item {_tex_escape(r)}" for r in recs["further_examinations"]])

    # Make domain labels bold in recommendations
    for domain_tag in ["SLEEP:", "ANXIETY:", "DEPRESSION:", "FATIGUE:", "ATTENTION:",
                        "COGNITION:", "IBS INTEGRATION:", "IBS:",
                        "SLEEP-COGNITION LINK:", "FATIGUE-SLEEP LINK:",
                        "ATTENTION-SLEEP/FATIGUE LINK:"]:
        ther_items = ther_items.replace(_tex_escape(domain_tag),
                                        "\\textbf{" + _tex_escape(domain_tag) + "}")
        exam_items = exam_items.replace(_tex_escape(domain_tag),
                                        "\\textbf{" + _tex_escape(domain_tag) + "}")

    # Flags by domain
    flags_sections = ""
    domain_labels_map = {
        "sleep_BIS": "Sleep (BIS)",
        "attention_CPT": "Attention (CPT)",
        "fatigue_Chalder": "Fatigue (Chalder)",
        "emotional_distress_HADS": "Emotional Distress (HADS)",
        "neurocognition_RBANS": "Neurocognition (RBANS)",
    }
    any_flags = False
    for dname, ddata in domains.items():
        flags = ddata.get("flags", [])
        if flags:
            any_flags = True
            flags_sections += f"\\textbf{{{_tex_escape(domain_labels_map.get(dname, dname))}:}}\n"
            flags_sections += "\\begin{itemize}[leftmargin=2em, topsep=0pt]\n"
            for f in flags:
                flags_sections += f"  \\item {_tex_escape(f)}\n"
            flags_sections += "\\end{itemize}\n"
    if not any_flags:
        flags_sections = "No clinical flags were identified across any domain.\n"

    # Figure file names
    mp_clin = f"{pid}_multipanel_clinical.png"
    mp_phys = f"{pid}_multipanel_physician.png"
    mp_pat = f"{pid}_multipanel_patient.png"
    rd_clin = f"{pid}_radar_clinical.png"
    rd_phys = f"{pid}_radar_physician.png"
    rd_pat = f"{pid}_radar_patient.png"
    demographics_rows = _report_demographics_rows(demo)
    cohort_summary = analysis.get("cohort_summary", {})
    total_n = cohort_summary.get("total_n")
    group_counts = cohort_summary.get("group_counts", {})
    if total_n is not None:
        visualization_context = (
            f"All scores are shown in the context of the full cohort (N={total_n}), "
            f"split by IBS status (n={group_counts.get('IBS', 0)}) vs. "
            f"healthy controls (n={group_counts.get('HC', 0)})."
        )
    else:
        visualization_context = "All scores are shown in the context of the full available cohort."
    participant_label = _participant_label(pid)

    tex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.2cm]{geometry}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage[colorlinks=true,linkcolor=clinteal,urlcolor=clinteal]{hyperref}
\usepackage{longtable}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{float}
\usepackage{parskip}

\definecolor{clinred}{RGB}{213,94,0}
\definecolor{clinamber}{RGB}{230,159,0}
\definecolor{clingreen}{RGB}{0,158,115}
\definecolor{clinteal}{RGB}{0,119,182}

\captionsetup{font=small, labelfont=bf, textfont=it}

\pagestyle{fancy}
\fancyhf{}
\rhead{\small Neuropsychological Report}
\lhead{\small """ + _tex_escape(pid) + r"""}
\rfoot{\thepage}

\titleformat{\section}{\Large\bfseries\color{clinteal}}{\thesection}{1em}{}
\titleformat{\subsection}{\large\bfseries\color{clinteal!70!black}}{\thesubsection}{1em}{}
\titleformat{\paragraph}[runin]{\normalsize\bfseries\color{clinteal!60!black}}{}{0em}{}[.]

\begin{document}

\begin{center}
{\LARGE\bfseries Neuropsychological Assessment Report}\\[0.5em]
{\large """ + _tex_escape(participant_label) + r""": """ + _tex_escape(pid) + r"""}\\[0.3em]
{\normalsize Date of Report: \today}
\end{center}

\vspace{0.5em}
\noindent\rule{\textwidth}{0.4pt}

% ================================================================
\section{Demographics and Clinical Context}
% ================================================================

\begin{tabular}{ll}
""" + demographics_rows + r"""
\end{tabular}

\medskip\noindent """ + _tex_escape(analysis["cohort_context"]) + r"""

% ================================================================
\section{Domain Findings}
% ================================================================

\subsection{Sleep --- Bergen Insomnia Scale (BIS)}
""" + _tex_escape(sleep["interpretation"]) + r"""

\noindent\begin{tabular}{llll}
\textbf{BIS Total:} & """ + str(sleep["scores"].get("total", "N/A")) + r""" &
\textbf{Classification:} & \textbf{""" + _tex_escape(sleep["classification"]) + r"""} \\
\textbf{Cohort percentile:} & """ + str(sleep.get("percentile_in_cohort", "N/A")) + r"""th &
\textbf{Cohort z-score:} & $""" + str(sleep.get("z_score", "N/A")) + r"""$ \\
\end{tabular}

\subsection{Sustained Attention --- Continuous Performance Test (CPT)}
""" + _tex_escape(cpt["interpretation"]) + r"""

\begin{table}[H]
\centering\small
\begin{tabular}{lccc}
\toprule
\textbf{CPT Metric} & \textbf{T-score} & \textbf{Cohort \%ile} & \textbf{Status} \\
\midrule
""" + cpt_rows + r"""\bottomrule
\end{tabular}
\caption{CPT-3 performance metrics. T-scores are normed (M=50, SD=10). Higher T-scores indicate less favorable performance across the displayed CPT metrics. Scores $\geq$60 are mildly elevated; $\geq$65 are clinically significant.}
\end{table}

\subsection{Fatigue --- Chalder Fatigue Scale}
""" + _tex_escape(fatigue["interpretation"]) + r"""

\noindent\begin{tabular}{llll}
\textbf{Bimodal total:} & """ + str(fatigue["scores"].get("chalder_bimodal_total", "N/A")) + r"""/11 &
\textbf{Classification:} & \textbf{""" + _tex_escape(fatigue["classification"]) + r"""} \\
\textbf{Cohort percentile:} & """ + str(fatigue.get("percentile_in_cohort", "N/A")) + r"""th &
\textbf{Caseness threshold:} & $\geq$4 \\
\end{tabular}

\subsection{Emotional Distress --- Hospital Anxiety and Depression Scale (HADS)}
""" + _tex_escape(hads["interpretation"]) + r"""

\noindent\begin{tabular}{lllll}
 & \textbf{Score} & \textbf{Classification} & \textbf{Cohort \%ile} & \textbf{z-score} \\
\textbf{HADS-A:} & """ + str(hads["scores"].get("HADS_A", "N/A")) + r""" & """ + _tex_escape(hads["classification"]["anxiety"]) + r""" & """ + str(hads.get("percentile_in_cohort", {}).get("anxiety", "N/A")) + r"""th & $""" + str(hads.get("z_scores", {}).get("anxiety", "N/A")) + r"""$ \\
\textbf{HADS-D:} & """ + str(hads["scores"].get("HADS_D", "N/A")) + r""" & """ + _tex_escape(hads["classification"]["depression"]) + r""" & """ + str(hads.get("percentile_in_cohort", {}).get("depression", "N/A")) + r"""th & $""" + str(hads.get("z_scores", {}).get("depression", "N/A")) + r"""$ \\
\end{tabular}

\smallskip\noindent\small Cutoffs: 0--7 Normal; 8--10 Borderline; 11--21 Clinical caseness.

\subsection{Neurocognition --- RBANS}
""" + _tex_escape(rbans["interpretation"]) + r"""

\begin{table}[H]
\centering\small
\begin{tabular}{lccc}
\toprule
\textbf{Index} & \textbf{Score} & \textbf{Cohort \%ile} & \textbf{Classification} \\
\midrule
""" + rbans_rows + r"""\bottomrule
\end{tabular}
\caption{RBANS summary values in the standalone March 16 pipeline. Domain scores reflect cohort-standardized raw-subtest composites, and ``Total Scale'' reflects RBANS Sum Raw. Classifications describe relative position within the observed cohort rather than external age-corrected norms.}
\end{table}

% ================================================================
\section{Clinical Flags}
% ================================================================
""" + flags_sections + r"""

% ================================================================
\section{Cross-Domain Pattern Analysis}
% ================================================================
""" + _tex_escape(analysis["cross_domain_patterns"]) + r"""

% ================================================================
\section{Clinical Reasoning Chain}
% ================================================================

The following reasoning chain traces the step-by-step clinical logic used to integrate findings across domains, identify mechanistic links, and arrive at the recommendations below.

""" + reasoning_sections + r"""

% ================================================================
\section{Recommendations Based on Pre-Screening Results}
% ================================================================

Each recommendation below is explicitly linked to the pre-screening domain finding(s) that justify it. Domain labels in \textbf{bold} indicate the driving finding. Recommendations follow a two-stage structure: (1)~determine whether further examination is necessary, then (2)~outline treatment planning and interventions.

\subsection{Further Examinations or Referrals Recommended}
\begin{itemize}[leftmargin=*]
""" + exam_items + r"""
\end{itemize}

\subsection{Suggested Therapeutic Interventions}
\begin{itemize}[leftmargin=*]
""" + ther_items + r"""
\end{itemize}

% ================================================================
\newpage
\section{Visualizations}
% ================================================================

Three pairs of complementary figures are provided, each tailored to a specific audience.
""" + _tex_escape(visualization_context) + r"""

% --- A. CLINICAL AUDIENCE ---
\subsection{For Clinical Peers}

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{""" + mp_clin + r"""}
\caption{\textbf{Multi-panel domain profile (clinical detail).}
Each panel shows the cohort distribution (violin plots split by IBS/HC group) with the patient's score marked as a blue diamond.
\textbf{Panel 1 (BIS):} Insomnia total score with clinical threshold (dashed red, $\geq$19) and minimal cutoff (dashed gray).
\textbf{Panel 2 (CPT):} Grouped bars comparing HC mean, IBS mean, and patient T-scores; red/orange triangles flag elevated metrics.
\textbf{Panel 3 (Chalder):} Fatigue bimodal total with caseness threshold (dashed red, $\geq$4).
\textbf{Panel 4 (HADS):} Split violin for Anxiety and Depression; shaded zones mark Normal (green), Borderline (amber), and Clinical (red) ranges.
\textbf{Panel 5 (RBANS):} Raw RBANS subtests displayed on a common cohort-standardized scale, with the patient's raw score annotated above each bar and the broader RBANS Sum Raw shown in the title.
Percentile ranks and z-scores annotate each patient marker. All distributions are within-cohort.}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth]{""" + rd_clin + r"""}
\caption{\textbf{Radar plot (clinical detail, expanded 10-spoke version).}
Each radial axis represents one domain or subscale, transformed to a common 0--100 percentile-of-wellness scale (higher = better functioning; scales where high raw scores indicate worse outcomes are inverted).
\textbf{Green band:} Healthy control range (16th--84th percentile, i.e.\ $\pm$1~SD).
\textbf{Orange dashed line:} IBS group median profile.
\textbf{Red center zone:} Clinical concern ($<$16th percentile).
\textbf{Blue polygon:} Patient profile, with percentile and z-score annotations at each vertex.
\textbf{Inset (right):} Cohen's $d$ effect sizes for IBS vs.\ HC on each domain. Positive values indicate the IBS group performs worse. $|d| > 0.2$ (small effect) shown in amber; $|d| > 0.5$ (medium effect) in red. This inset contextualizes whether any patient deviations from the healthy range are consistent with the broader IBS group pattern or represent individual-specific findings.}
\end{figure}

% --- B. PHYSICIAN AUDIENCE ---
\subsection{For Referring Physicians}

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{""" + mp_phys + r"""}
\caption{\textbf{Clinical summary (physician view).}
Five-domain overview using simplified violin plots with traffic-light status labels:
\textcolor{clingreen}{\textbf{OK}} ($\geq$50th percentile of wellness),
\textcolor{clinamber}{\textbf{MONITOR}} (16th--49th percentile),
\textcolor{clinred}{\textbf{ACTION}} ($<$16th percentile).
The patient's score is shown as a large star marker. This view is designed for rapid clinical triage: domains marked ACTION warrant immediate intervention or referral; MONITOR domains should be tracked at follow-up.}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.75\textwidth]{""" + rd_phys + r"""}
\caption{\textbf{Radar plot (physician view, compact 5-spoke).}
Same percentile-of-wellness normalization as the clinical version, but using five composite domain spokes for rapid pattern recognition.
Vertex colors follow the traffic-light system: green ($\geq$50th), amber (16th--49th), red ($<$16th).
The overall polygon shape reveals whether difficulties are focal (one spoke depressed) or diffuse (multiple spokes depressed).
The green shaded band shows the typical healthy control range for reference.}
\end{figure}

% --- C. PATIENT AUDIENCE ---
\subsection{For the Patient and Close Persons}

\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{""" + mp_pat + r"""}
\caption{\textbf{Your results at a glance.}
Each horizontal bar shows how your score compares to others in the study. Longer bars (reaching further right) mean better functioning in that area.
The labels ``Some difficulty'', ``Average'', ``Good'', and ``Excellent'' describe where your score falls.
Areas shown in green are going well; areas in amber or red may benefit from support or follow-up.
This chart covers five areas of health: sleep quality, concentration ability, energy levels, emotional wellbeing, and memory and thinking skills.}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.75\textwidth]{""" + rd_pat + r"""}
\caption{\textbf{Your overall profile.}
This spider chart shows all five areas together so you can see the overall shape of your strengths and any areas of difficulty.
Points further from the center are better. The green shaded area shows the ``typical healthy range.''
The orange dashed line shows the average for people with IBS.
The blue shape is your personal profile.
The sentence at the bottom provides a plain-language summary of what the chart shows.}
\end{figure}

% ================================================================
\vfill
\noindent\rule{\textwidth}{0.4pt}\\
\small\textit{This report was generated by an AI-based neuropsychological analysis pipeline.
All interpretations should be reviewed and validated by a qualified clinical neuropsychologist.
Findings are based on cross-sectional cohort data (N=105). CPT values remain norm-referenced T-scores, whereas the RBANS section in this standalone March 16 pipeline uses raw subtests and cohort-standardized summaries rather than external age-corrected RBANS index norms.
Clinical cutoffs follow established guidelines: HADS (Zigmond \& Snaith, 1983; Bjelland et al., 2002),
BIS (Pallesen et al., 2008), Chalder Fatigue Scale (Chalder et al., 1993),
RBANS (Randolph, 1998), CPT-3 (Conners, 2014).}

\end{document}
"""
    return tex


# ============================================================================
# BATCH PROCESSING ORCHESTRATOR
# ============================================================================

def process_patient(df: pd.DataFrame, patient_id: str,
                    output_base: str = OUTPUT_BASE,
                    reference_df: pd.DataFrame = None) -> Dict:
    """Process a single patient: analysis + all visualizations + report.

    Parameters
    ----------
    reference_df : pd.DataFrame, optional
        Independent reference cohort for normative statistics.
        Passed through to ``analyze_patient``, ``generate_multipanel``,
        and ``generate_radar``.  ``None`` keeps original behaviour.
    """
    out_dir = os.path.join(output_base, patient_id)
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Processing patient: {patient_id}")
    print(f"{'='*60}")

    # 1. Clinical analysis
    print("  [1/4] Running clinical analysis...")
    analysis = analyze_patient(df, patient_id, reference_df=reference_df)

    # 2. Multi-panel figures
    print("  [2/4] Generating multi-panel figures...")
    viz_files = {"multi_panel": {}, "radar_plot": {}}
    for aud in ["clinical", "physician", "patient"]:
        pdf, png = generate_multipanel(df, patient_id, out_dir, audience=aud,
                                       reference_df=reference_df)
        viz_files["multi_panel"][aud] = {"pdf": os.path.basename(pdf), "png": os.path.basename(png)}

    # 3. Radar plots
    print("  [3/4] Generating radar plots...")
    for aud in ["clinical", "physician", "patient"]:
        pdf, png = generate_radar(df, patient_id, out_dir, audience=aud,
                                  reference_df=reference_df)
        viz_files["radar_plot"][aud] = {"pdf": os.path.basename(pdf), "png": os.path.basename(png)}

    analysis["visualizations_generated"] = viz_files

    # 4. Save JSON
    json_path = os.path.join(out_dir, f"{patient_id}_report.json")
    with open(json_path, "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    # 5. LaTeX report
    print("  [4/4] Generating LaTeX report...")
    try:
        pdf_path = generate_latex_report(analysis, out_dir)
        if os.path.exists(pdf_path):
            print(f"  LaTeX PDF generated: {pdf_path}")
        else:
            print("  WARNING: LaTeX compilation may have failed.")
    except Exception as e:
        print(f"  WARNING: LaTeX report generation failed: {e}")

    print(f"  DONE. Output in: {out_dir}")
    return analysis


def process_batch(df: pd.DataFrame, patient_ids: List[str],
                  output_base: str = OUTPUT_BASE,
                  reference_df: pd.DataFrame = None) -> List[Dict]:
    """Process a batch of patients.

    Parameters
    ----------
    reference_df : pd.DataFrame, optional
        Independent reference cohort.  Threaded through to
        ``process_patient`` and all downstream functions.
    """
    results = []
    for i, pid in enumerate(patient_ids):
        print(f"\n[Batch {i+1}/{len(patient_ids)}]")
        try:
            result = process_patient(df, pid, output_base,
                                     reference_df=reference_df)
            results.append(result)
        except Exception as e:
            print(f"  ERROR processing {pid}: {e}")
            results.append({"patient_id": pid, "error": str(e)})
    return results


def get_all_patient_ids(df: pd.DataFrame) -> List[str]:
    """Get sorted list of all patient IDs."""
    return sorted(df[COL_SUBJECT].unique().tolist())


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Standalone neuropsychological profile analysis pipeline (March 16 model)",
        epilog="Examples:\n"
               "  python neuropsych_pipeline.py subj_001\n"
               "  python neuropsych_pipeline.py subj_001 subj_048\n"
               "  python neuropsych_pipeline.py --all --batch-size 5\n"
               "  python neuropsych_pipeline.py --data /path/to/full_cohort.csv BGA_XXX\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "patients", nargs="*",
        help="Record ID(s) to process (for example subj_001 or BGA_XXX, depending on the selected cohort file). "
             "If omitted, processes the first record only.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Process all records in the selected cohort.",
    )
    parser.add_argument(
        "--batch-size", type=int, default=5,
        help="Number of records per batch (default: 5). "
             "Only affects progress logging, not parallelism.",
    )
    parser.add_argument(
        "--data", type=str, default=DATA_PATH,
        help=(
            "Path to cohort CSV "
            f"(default: {DATA_PATH}; full cohort if available, otherwise the blinded public CSV)"
        ),
    )
    parser.add_argument(
        "--output-dir", type=str, default=OUTPUT_BASE,
        help=f"Output directory (default: {OUTPUT_BASE})",
    )
    args = parser.parse_args()

    df = load_cohort(args.data)
    all_ids = get_all_patient_ids(df)

    if args.all:
        patient_ids = all_ids
    elif args.patients:
        patient_ids = args.patients
    else:
        patient_ids = [all_ids[0]]

    print(f"Cohort loaded: {len(df)} subjects ({df[COL_GROUP].value_counts().to_dict()})")
    print(f"Processing {len(patient_ids)} patient(s) in batches of {args.batch_size}")

    # Process in batches for clearer progress reporting
    for i in range(0, len(patient_ids), args.batch_size):
        batch = patient_ids[i : i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (len(patient_ids) + args.batch_size - 1) // args.batch_size
        print(f"\n{'='*60}")
        print(f"Batch {batch_num}/{total_batches}: {batch}")
        print(f"{'='*60}")
        results = process_batch(df, batch, args.output_dir)
        print(f"Batch {batch_num} complete: {len(results)} patient(s) processed.")

    print(f"\nAll done. {len(patient_ids)} patient(s) processed.")
