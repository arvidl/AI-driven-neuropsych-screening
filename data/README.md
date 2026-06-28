# `data/` — blinded analysis-ready cohort

This folder contains the single de-identified CSV that supports the public
reproducibility scope of the manuscript "An AI-Initiated, Rule-Based Pipeline
for Pre-Examination Screening in Clinical Neuropsychology".

| File | Rows | Format | Encoding |
| ---- | ---- | ------ | -------- |
| `BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv` | 105 participants + 1 header | semicolon-separated, UTF-8 | LF line endings |

## Provenance and ethics

The data originate from the Bergen Brain–Gut–Microbiota (B-BGM) study
(Berentsen et al., 2020) at the National Centre for Functional
Gastrointestinal Disorders, Haukeland University Hospital, Bergen, Norway.

- The study was approved by the Regional Committee for Medical and Health
  Research Ethics, South East Norway (**REK 2015-01621**).
- All participants provided written informed consent prior to data
  collection, in accordance with the Declaration of Helsinki (2008).
- The version of the dataset shipped here is a **blinded subset**: it
  contains no direct identifiers (no name, national identity number, date
  of birth, contact information, hospital ID, free-text notes, exact
  examination dates, or postal codes) and only the variables required to
  reproduce the manuscript's blinded analyses. Anonymous subject IDs were
  assigned at preparation time and bear no relation to clinical IDs.
- Re-identification is considered very unlikely under the present REK
  approval given the small set of retained variables and the absence of
  rare-event combinations. Any attempt at re-identification, linkage with
  external datasets, or derivation of indirect identifiers is prohibited.

The non-blinded source dataset is **not** publicly distributable. Requests
for derived analyses that exceed this blinded scope should be addressed to
the corresponding author and are subject to institutional data-sharing
agreements and a renewed REK assessment.

## Variable dictionary

All scores are baseline (`_BL` suffix where applicable). Item-level
question fields (`*_Q*_BL`) are included to allow exact reconstruction of
the published sum scores.

| Group | Columns | Description |
| ----- | ------- | ----------- |
| Identifiers | `Subject` | Anonymous serial ID (string, e.g. `subj_001`) |
| Demographics | `Gender`, `TestAge` | Categorical sex; age in years at testing |
| Clinical group | `Group`, `IBStype`, `IBS_SSS` | IBS / HC; IBS subtype (D / C / M); IBS Severity Scoring System total (0–500) |
| Sleep — Bergen Insomnia Scale | `BIS_Q1_BL`–`BIS_Q6_BL` | Six items, days/week (0–7); manuscript total = sum |
| Sustained attention — Conners CPT-3 | `CPT_Detectability`, `CPT_Omissions`, `CPT_Commissions`, `CPT_Perseverations`, `CPT_HRT`, `CPT_HRT_SD`, `CPT_HRT_Block_Change`, `CPT_HRT_ISI_Change`, `CPT_Variability` | Software-generated T-scores (M = 50, SD = 10) |
| Fatigue — Chalder Fatigue Scale (FSS form) | `FSS_Q1_BL`–`FSS_Q13_BL`, `TFS_Chalder` | Per-item Likert + the bimodal Chalder total (0–11) |
| Emotional distress — HADS | `HADS_Q1_BL`–`HADS_Q14_BL`, `HADS_Anxiety`, `HADS_Depression` | Per-item raw + subscale totals (each 0–21) |
| Neurocognition — RBANS | `RBANS_Wordlist`, `RBANS_History`, `RBANS_Figure`, `RBANS_Line`, `RBANS_Naming`, `RBANS_Fluency`, `RBANS_Digitspan`, `RBANS_Coding`, `RBANS_WordlistRecall`, `RBANS_HistoryRecall`, `RBANS_WordlistRecognition`, `RBANS_FigureRecognition`, `RBANS_Sum_Raw` | Subtest raw scores plus the broad raw total used in cohort-relative analyses |

Two manuscript Table 1 rows are deliberately **not** in this CSV because
they could not be released in blinded form:

- `Education` (years)
- The five RBANS index scores (Immediate Memory, Visuospatial /
  Constructional, Language, Attention, Delayed Memory) and the RBANS Total
  Scale index

These rows are kept in the published Table 1 for record but are not
recomputed by `notebooks/03_table_1_generation_blinded.ipynb`.

## Reproducibility scope

The pipeline scripts and the public Table 1 notebook fall back to this CSV
when the non-public source file is absent, so a fresh checkout reproduces
the blinded analyses without any additional data steps. See the top-level
`README.md` ("Reproducibility Scope") for details.

## Citation

If you use this dataset, please cite the article (see `CITATION.cff`) and
the original cohort publication:

Berentsen B, Nagaraja BH, Teige ES, et al. *Study protocol of the Bergen
brain–gut–microbiota study: a prospective case-report characterization and
dietary intervention study to evaluate the effects of microbiota
alterations on cognition and anatomical and functional brain connectivity
in patients with irritable bowel syndrome.* Medicine. 2020;99(37):e21950.
