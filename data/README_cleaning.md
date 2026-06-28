# Data Cleaning Log — BGA Cohort

## Dataset

- **Raw file:** `data/BGA_merged_all_20260208.csv` (105 × 74)
- **Cleaned file:** `data/BGA_merged_all_20260208_cleaned.csv` (105 × 82) — Stage 1
- **Analysis file:** `data/BGA_merged_all_20260208_cleaned_for_analysis.csv` (105 × 68) — Stage 2
- **Blinded analysis file:** `data/BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv` (105 × 64) — Stage 3 (the only public artefact)
- **Date of cleaning decisions:** 2026-03-11 (see decision checklist below)
- **Reproducible source:** `scripts/clean_cohort_data.py` — regenerates all three
  files from the raw file and verifies them cell-for-cell against the committed
  copies. Stage-1 logic originates from `01_data_exploration_20260311.ipynb`.

> **Legacy note.** Earlier drafts also described a
> `data/BGA_merged_all_20260208_analysis_ready.csv` with `use_*` mask columns.
> That variant is **superseded**: the current (March-16) workflow no longer
> constructs it (see `notebooks/04_cleaned_data_results.ipynb`), and the
> deterministic pipeline `scripts/neuropsych_pipeline.py` reads
> `…_cleaned_for_analysis.csv` instead. References to `analysis_ready.csv` below
> are retained for historical context only.

## Purpose

This document describes the transition from the raw cohort file `data/BGA_merged_all_20260208.csv` to the technically cleaned file `data/BGA_merged_all_20260208_cleaned.csv`.

The goal is to make the cleaning process transparent and reproducible while preserving a clear distinction between technical cleaning and later analysis-ready decisions. In particular, the cleaned file is intended to:

- preserve the raw source data unchanged
- retain cohort membership and the core variable structure
- normalize blank-string entries to explicit missing values where appropriate
- standardize selected datatypes and categorical labels needed for reproducible summaries
- document unresolved data-quality issues with explicit flag columns rather than silent corrections

## Raw dataset summary

- Rows: 105
- Columns: 74
- Groups: 65 IBS, 40 HC
- File format: semicolon-delimited CSV

## Cleaning stages

### Stage 1 — Standardization cleaning

These changes improve consistency and auditability without changing the intended scientific meaning of the recorded data. The aim is technical cleaning, not silent conversion to an analysis-ready dataset.

Applied steps:

- Converted blank strings to explicit missing values (`NA`)
- Coerced `Education` from text-like values to numeric for reproducible summaries and modeling
- Standardized metadata labels where needed
- Added subject-level and domain-level issue flags for incomplete or suspicious records
- Preserved recorded scale totals pending source verification when discrepancies could not be resolved conservatively

### Stage 2 — Analysis extract (`…_cleaned_for_analysis.csv`)

Deterministic slimming of the cleaned file into the form the rule-based pipeline
consumes (105 × 68). Implemented in `scripts/clean_cohort_data.py::build_for_analysis`:

- Drop the seven RBANS summary/index columns (`RBANS_Memory_Index`,
  `RBANS_Visuoaspatial_Index`, `RBANS_Verbalskills_Index`,
  `RBANS_Attention_Index`, `RBANS_Recall_Index`, `RBANS_Sum_Index`,
  `RBANS_Fullscale`) — the pipeline derives its own cohort-relative summaries.
- Drop the eight `flag_*` columns (QC metadata, not analysis inputs).
- Add `RBANS_Sum_Raw` = row sum of the 12 RBANS raw subtests (blank when the
  whole RBANS block is missing — 3 subjects).
- Reorder the RBANS recall/recognition subtests (two recalls, then two
  recognitions) and place `RBANS_Sum_Raw` immediately before `TFS_Chalder`.

### Stage 3 — Blinded release (`…_cleaned_for_analysis_blinded.csv`)

De-identification of the analysis extract for public release (105 × 64).
Implemented in `scripts/clean_cohort_data.py::build_blinded`:

- Drop the four free-text / indirect-identifier metadata columns: `Education`,
  `HandPref`, `Mothertounge`, `TestAdmin`.
- Relabel `Subject` to sequential anonymous IDs `subj_001 … subj_105` by row
  order (no link back to the `BGA_xxx` clinical IDs).

This is the **only** file released publicly; see `data/README.md`.

#### Historical Stage 2 (analysis-ready decisions — superseded)

The decisions below were recorded when the plan was to emit an
`analysis_ready.csv` with `use_*` masks. They document the *intent* behind the
conservative flagging and remain useful as rationale, but the masks themselves
were never carried into the current `…_cleaned_for_analysis.csv` pipeline (which
simply excludes flagged values from the affected analyses).

## Decision checklist

Record each manual cleaning decision here before updating the analysis-ready dataset.

| Decision | Chosen option | Rationale | Date decided |
|---|---|---|---|
| Interpretation of `IBS_SSS` in healthy controls | **Provisional:** retain HC values in `..._cleaned.csv`, but do not interpret them as IBS severity in formal analyses until construct validity is clarified | This preserves observed data while preventing premature clinical interpretation of HC scores. | 2026-03-11 |
| Authoritative fatigue score for `TFS_Chalder` | **Provisional:** retain recorded `TFS_Chalder` in cleaned and analysis-ready data; do not recalculate until the intended scoring rule is verified | The audit suggests a documentation/scoring-definition mismatch rather than a simple arithmetic error, so silent recalculation would be risky. | 2026-03-11 |
| Resolution of `RBANS_Sum_Index` mismatch for `subj_089` | **Provisional:** retain as recorded, keep flagged, and exclude only from analyses that use `RBANS_Sum_Index` unless source verification is available | This avoids unverified correction while limiting downstream bias in RBANS summary-score analyses. | 2026-03-11 |
| Resolution of `RBANS_Sum_Index` mismatch for `subj_101` | **Provisional:** retain as recorded, keep flagged, and exclude only from analyses that use `RBANS_Sum_Index` unless source verification is available | This case is especially suspicious, but source verification should precede any direct overwrite. | 2026-03-11 |
| Inclusion rule for highly incomplete subjects | **Provisional:** use domain-specific inclusion rather than a single common cohort | Missingness is blockwise and uneven across instruments, so a universal exclusion rule would discard usable information unnecessarily. | 2026-03-11 |
| Handling of blockwise missingness | **Provisional:** treat full missing test blocks as structural missingness and preserve explicit flag columns | The pattern suggests non-administered or unavailable assessments rather than isolated item-level omission. | 2026-03-11 |
| Normalization of `HandPref` categories | **Provisional:** recode `Right+ left` to `Ambidextrous` in the cleaned dataset and note the normalization in documentation | This improves category consistency while preserving the meaning of the original entry. | 2026-03-11 |
| Treatment of decimal values in `Education` | **Provisional:** retain decimal values as recorded and treat them as valid years of education unless source records indicate otherwise | The decimal pattern appears systematic rather than erroneous, so rounding would remove information without clear justification. | 2026-03-11 |
| Policy for correcting suspicious but unverifiable values | **Provisional:** correct only when source-verified; otherwise retain flagged values and exclude them only from affected analyses if necessary | This is the most conservative and reproducible rule for auditability and downstream reporting. | 2026-03-11 |

## Data-quality issues identified in the raw file

### 1. Missingness

Key missingness patterns:

- `FSS_Q1_BL` to `FSS_Q13_BL` and `TFS_Chalder`: 21 missing each
- HADS summary and item variables: 12 missing each
- BIS item variables: 8 missing each
- CPT variables: 3 to 4 missing
- RBANS variables: 3 missing in most columns
- `Education`: additional blank-string missing values detected after normalization

Blockwise missingness:

- Entire fatigue block missing for 21 subjects
- Entire HADS block missing for 12 subjects
- Entire BIS block missing for 8 subjects
- Entire CPT block missing for 3 subjects
- Entire RBANS block missing for 3 subjects

### 2. Datatype issues

- `Education` stored as text-like values in the raw CSV
- Blank strings used instead of explicit missing values in several metadata fields

### 3. Category inconsistencies

- `HandPref` contains atypical label: `Right+ left`
- Blank values present in `Mothertounge`, `HandPref`, and `TestAdmin`

### 4. Clinical/derived-score inconsistencies

- `IBS_SSS` appears in many healthy controls and requires interpretation
- `TFS_Chalder` does not match the 13-item item sum described in the current data dictionary
- `RBANS_Sum_Index` discrepancy identified for:
  - `subj_089`
  - `subj_101`

## Cleaning actions performed

| Variable(s) | Issue | Action taken | Rationale |
|---|---|---|---|
| Metadata fields | Blank strings | Converted to explicit `NA` values | Improves reproducibility of missing-data handling without altering cohort membership |
| `Education` | Text-like numeric values | Coerced to numeric | Supports reproducible numeric summaries while preserving recorded years of education |
| `HandPref` | `Right+ left` | Normalized to `Ambidextrous` | Improves category consistency while preserving the apparent meaning of the original entry |
| Fatigue variables | Total does not match documented 13-item sum | Retained recorded total and added a discrepancy flag | Avoids undocumented score rewriting while keeping the issue auditable |
| `RBANS_Sum_Index` | Subject-level mismatch | Flagged for source verification | Preserves the recorded value while making the unresolved discrepancy explicit |

## Subject-level flags

| Subject | Issue | Resolution | Included in cleaned file | Included in analysis-ready file |
|---|---|---|---|---|
| `subj_089` | RBANS sum mismatch | Pending source verification | Yes | [Yes/No] |
| `subj_101` | RBANS sum mismatch | Pending source verification | Yes | [Yes/No] |
| `subj_065` | Extensive missingness | Flagged | Yes | [Yes/No] |
| `subj_067` | Extensive missingness | Flagged | Yes | [Yes/No] |
| `subj_103` | Missing RBANS block and metadata gaps | Flagged | Yes | [Yes/No] |

## Output files

### Cleaned file

The cleaned CSV should include:

- explicit missing values in place of blank-string placeholders where appropriate
- corrected dtypes needed for reproducible summaries
- normalized categorical labels where the intended meaning is clear
- subject-level or domain-level issue flags for unresolved missingness or score concerns
- no row exclusions unless explicitly documented
- no silent conversion of unresolved issues into final analysis decisions

### Analysis-ready file

The analysis-ready CSV should only be saved after decisions have been finalized regarding:

- handling of healthy-control `IBS_SSS`
- subject exclusion due to incompleteness
- RBANS discrepancy resolution
- fatigue-score handling

In other words, the cleaned file should document issues conservatively, whereas the analysis-ready file may implement justified interpretation or exclusion rules once those decisions have been finalized.

**Superseded design (historical).** An earlier plan proposed a
`data/BGA_merged_all_20260208_analysis_ready.csv` that preserved the cleaned
source data and added explicit `use_*` mask columns (domain-level
`use_bis`/`use_fatigue`/`use_hads`/`use_cpt`/`use_rbans` and variable-specific
`use_ibs_sss`/`use_rbans_sum_index`/`use_tfs_chalder_recorded`, plus
`*_analysis` companion columns). This file is **no longer produced**. The
current analysis input is `…_cleaned_for_analysis.csv` (Stage 2 above), and the
conservative-masking intent is realised by excluding flagged values only from
the affected analyses within `scripts/neuropsych_pipeline.py`.

These flag-handling decisions also determine how the manuscript should eventually be revised. If the `flag_` columns continue to function as domain-specific or variable-specific routing metadata, then the main consequence for `JINS/jins_main.tex` will be clearer Methods wording about conservative masking and interpretation, with little expected change to the primary IBS-versus-HC comparisons. By contrast, if the flags are later used to redefine the analytic cohort more aggressively, then Table 1, the `Group differences across domains` subsection, pipeline summary counts, and possibly abstract-level percentages should all be recomputed before the manuscript is updated.

## Reproduction

All three derived files are regenerated deterministically from the raw file by:

```bash
python scripts/clean_cohort_data.py            # write to data/reproduced/ + verify
python scripts/clean_cohort_data.py --write-inplace   # overwrite data/*.csv
```

For a narrated, reviewer-facing walk-through of the same procedure (rationale +
the exact stage code printed inline + live flag summaries + verification), see
the companion notebook `notebooks/01_clean_cohort_data.ipynb`, which imports and
runs this script.

The script implements Stages 1–3 above and verifies each output cell-for-cell
against the committed copy. Expected result:

```
[cleaned]      OK - exact value-level match (105 rows x 82 cols)
[for_analysis] OK - exact value-level match (105 rows x 68 cols)
[blinded]      OK - exact value-level match (105 rows x 64 cols)
ALL FILES REPRODUCED EXACTLY (value-level).
```

Note: the committed `…_cleaned.csv` is stored in a cosmetically space-padded
`"; "` layout (a later re-save); the script emits canonical plain `";"` CSVs, so
verification compares values, not raw bytes. Upstream, the raw file itself is
reproducible via `data/_sources/build_raw_cohort.py` (git-ignored provenance
bundle).

## Version history

| Version | Date | Description |
|---|---|---|
| v1 | 2026-03-11 | Initial cleaning log + Stage-1 cleaning in `01_data_exploration_20260311.ipynb` |
| v2 | 2026-03-16 | Switched from `analysis_ready.csv` to `…_cleaned_for_analysis.csv` pipeline input |
| v3 | 2026-06-28 | Consolidated, documented, and verified Stages 1–3 in `scripts/clean_cohort_data.py` |

## Notes

- The raw source file must remain unchanged.
- Any future corrections should be recorded here and in the cleaning code.
- If source documents are used to resolve discrepancies, document exactly which variables changed and why.
