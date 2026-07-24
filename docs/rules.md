# Rule Set Implemented in the Pipeline

This document catalogues the **deterministic** rules encoded in
`scripts/neuropsych_pipeline.py` (per-subject analysis/report) and
`scripts/clean_cohort_data.py` (data-quality flags). Every rule below is
hard-coded and human-verified against the cited source instruments; the pipeline
performs **no learning and calls no model or network at runtime**, so identical
inputs always yield identical outputs. For how these rules were drafted with AI
assistance, see [`docs/prompt_provenance.md`](prompt_provenance.md).

Line references point at the current `scripts/` sources and may drift as the code
evolves; the function/constant **names** are the stable anchors.

---

## 1. Domain classification thresholds

Cutoffs are locked to published instrument values and defined as module constants
near the top of `scripts/neuropsych_pipeline.py`.

| Domain / instrument | Constant | Rule (as coded) | Classifier |
|---|---|---|---|
| **Emotional distress — HADS** (per subscale, 0–21) | `HADS_CUTOFFS = {normal: 7, borderline: 10, clinical: 11}` | `≤7` → Normal; `8–10` → Borderline; `≥11` → Clinical | `classify_hads()` |
| **Sleep — BIS** (total score) | `BIS_CUTOFFS = {minimal: 6, mild: 14, moderate: 24}` | `≤6` → Minimal; `7–14` → Mild; `15–24` → Moderate; `≥25` → Severe | `classify_bis()` |
| **Fatigue — Chalder** (bimodal total, 0–11) | `CHALDER_CASENESS = 4` | `≥4` → Significant fatigue; else No significant fatigue | `classify_chalder()` |
| **Sustained attention — CPT** (T-scores) | `CPT_ELEVATED = 60`, `CPT_CLINICAL = 65` | `T ≥ 60` → elevated; `T ≥ 65` → clinically significant | applied in the CPT panel/flag logic |
| **Neurocognition — RBANS** (index score) | `RBANS_CLASSIFICATIONS` | Extremely Low `0–69`; Borderline `70–79`; Low Average `80–89`; Average `90–109`; High Average `110–119`; Superior `120–129`; Very Superior `130–200` | `classify_rbans()` |

**RBANS note (public data).** `classify_rbans()` applies to normed RBANS **index**
scores, which require proprietary conversion tables and are therefore *not* shipped
in the public blinded dataset. In the public/blinded path the pipeline instead uses
the **raw subtests plus cohort-standardized summary composites** (percentiles and
z-scores within the cohort). See the README "Table 1 Note".

Missing values are handled uniformly: every classifier returns `"N/A"` when the
input is `NaN`, rather than imputing.

## 2. Cohort-relative context

For each domain the pipeline computes the subject's standing **within the cohort**
(N = 105), not only against fixed cutoffs:

- **Percentile rank** in the cohort distribution (`percentile_rank()`).
- **z-score** relative to the cohort mean/SD (`cohort_z_score()`).
- Group-aware handling, e.g. IBS-SSS is retained but **not interpreted as severity
  for healthy controls** (`_missing_note_for_controls()`).

These feed the per-domain `percentile_in_cohort` / interpretation fields in the
report JSON and the "cohort context" layers of the figures.

## 3. Data-quality (QC) flags

Computed during cleaning in `scripts/clean_cohort_data.py` (`compute_flags()`,
`FLAG_COLUMNS`) and documented with full rationale in
[`data/README_cleaning.md`](../data/README_cleaning.md). Each flag **documents** an
unresolved issue rather than silently correcting it.

| Flag | Meaning |
|---|---|
| `flag_missing_bis_block` | Entire BIS item block is blank |
| `flag_missing_fatigue_block` | Entire Chalder/FSS item block is blank |
| `flag_missing_hads_block` | Entire HADS item block is blank |
| `flag_missing_cpt_block` | Entire CPT block is blank |
| `flag_missing_rbans_block` | Entire RBANS subtest block is blank |
| `flag_hc_with_ibs_sss` | A healthy control carries an IBS-SSS value |
| `flag_rbans_sum_mismatch` | Recorded `RBANS_Sum_Index` ≠ sum of the five domain indices |
| `flag_tfs_vs_13_item_sum_mismatch` | Chalder total fatigue score inconsistent with the 13-item sum |

## 4. Clinical reasoning chain (8 steps)

Built deterministically in `_reasoning_chain()` from the per-domain results; the
steps are stored under `reasoning_chain` in the report JSON and typeset in the
"Clinical Reasoning Chain" section of each `*_report.pdf`.

1. **Demographic and clinical context** — gender, age, education, group, IBS
   subtype/severity (IBS-SSS only interpreted for the IBS group).
2. **Sleep (BIS)** — total score, classification, cohort percentile.
3. **Fatigue (Chalder)** — bimodal total, caseness classification, cohort percentile.
4. **Emotional distress (HADS)** — anxiety and depression subscale scores and
   classifications.
5. **Sustained attention (CPT)** — key T-scores (Detectability, Omissions,
   Commissions, HRT).
6. **Neurocognition (RBANS)** — cohort-percentile standing plus relative
   strengths/weaknesses across subtests (raw + cohort-standardized composites).
7. **Cross-domain integration** — which domains are flagged, and whether they
   suggest an interacting symptom pattern or a comparatively even profile.
8. **Prognostic/recommendation synthesis** — e.g. a prominent
   sleep–fatigue–attention coupling points to prioritising insomnia/fatigue; mood
   co-occurring with cognitive inefficiency points to emotional stabilization
   first. Feeds the `recommendations` (`therapeutic`, `further_examinations`) block.

All wording is template-driven and fully determined by the numeric inputs and the
rules above — there is no free-text generation at runtime.

## 5. Audience tailoring

Every figure is rendered in three deterministic variants (report JSON
`visualizations_generated`; files under `output_subj/<id>/`):

- **Clinical peers** — full statistical detail (z-scores, percentiles, effect
  sizes), technical labels, expanded (up to 10-spoke) radar.
- **Referring physicians** — simplified traffic-light (green/amber/red) summary,
  brief action points, compact 5-spoke radar.
- **Patients / close persons** — plain-language labels, qualitative anchors,
  warm/non-alarming color-blind-safe palette, compact radar.

Radar plots normalize all domains to a **common 0–100 percentile-of-wellness
scale with consistent polarity (higher = better)**, inverting instruments where a
high raw score means a worse outcome (BIS, Chalder, HADS, CPT).

## 6. Where each rule lives

| Concern | Location |
|---|---|
| Threshold constants | `scripts/neuropsych_pipeline.py` (`HADS_CUTOFFS`, `BIS_CUTOFFS`, `CHALDER_CASENESS`, `CPT_ELEVATED`, `CPT_CLINICAL`, `RBANS_CLASSIFICATIONS`) |
| Classifiers | `classify_hads()`, `classify_bis()`, `classify_chalder()`, `classify_rbans()` |
| Cohort context | `percentile_rank()`, `cohort_z_score()`, `analyze_patient()` |
| Reasoning chain | `_reasoning_chain()` |
| Report assembly (LaTeX) | report-generation section of `scripts/neuropsych_pipeline.py` |
| QC flags | `scripts/clean_cohort_data.py` (`compute_flags()`, `FLAG_COLUMNS`) + `data/README_cleaning.md` |

You can inspect the realized output of all of the above for the two tracked cases
in `output_subj/subj_001/subj_001_report.json` and
`output_subj/subj_048/subj_048_report.json`.
