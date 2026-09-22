# AI-driven-neuropsych-screening

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Runtime: deterministic · no AI](https://img.shields.io/badge/runtime-deterministic%20%C2%B7%20no%20AI-blue.svg)](docs/prompt_provenance.md)
[![Results: reproducible](https://img.shields.io/badge/results-reproducible-brightgreen.svg)](#reproducibility-across-machines)
[![Cite this repository](https://img.shields.io/badge/cite-CITATION.cff-informational.svg)](CITATION.cff)

_Astri J. Lundervold, Birgitte Berentsen, and Arvid Lundervold:_ <br>**"AI-Assisted Development of a Rule-Based Pipeline for Pre-Examination Screening in Clinical Neuropsychology: An Exploratory Method-Development Study"** (to appear in Journal of the International Neuropsychological Society, JINS)

Paper-and-code repository for the blinded neuropsychological screening pipeline described in the paper above.

## What This Repo Contains

- The blinded analysis dataset: `data/BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv`
- The standalone subject-processing pipeline:
  `scripts/neuropsych_pipeline.py` and `scripts/neuropsych_subj_pipeline.py`
- The two blinded example subject outputs linked to the paper:
  `output_subj/subj_001/` and `output_subj/subj_048/`
- The reproducible Figure 1 source (TikZ) and compiled PDF:
  `figures/figure_1_reasoning_chain.tex`, `figures/figure_1_reasoning_chain.pdf`
- The documented data-cleaning notebook (raw → cleaned → analysis → blinded),
  the narrated companion to `scripts/clean_cohort_data.py`. It reads the
  non-public raw cohort file and is retained for provenance only (outputs
  cleared; not runnable from the public repository):
  `notebooks/01_clean_cohort_data.ipynb`
- The full-cohort Table 1 notebook retained for provenance (requires the
  non-public cleaned cohort file; outputs cleared):
  `notebooks/02_table_1_generation.ipynb`
- A blinded-only notebook for the reproducible subset of Table 1 (the only
  notebook runnable from the public blinded dataset):
  `notebooks/03_table_1_generation_blinded.ipynb`
- A results/robustness notebook (raw-vs-cleaned stability + flag-handling
  policy). It compares the non-public raw and cleaned cohort files and is
  retained for provenance only (outputs cleared; not runnable from the public
  repository):
  `notebooks/04_cleaned_data_results.ipynb`

## Reproducibility Scope

This repository is designed around the public-safe blinded dataset. It fully supports:

- regenerating subject-level reports, JSON summaries, and figures from the blinded CSV
- regenerating the paper-linked outputs for `subj_001` and `subj_048`
- reproducing the blinded-data-supported subset of the paper's Table 1

## Quickstart — Reproduce the Results

End-to-end walkthrough from a clean machine to regenerated numbers, tables,
figures, and reports. Steps 1–5 need only Python; step 6 additionally needs a
LaTeX toolchain (for the typeset `*_report.pdf` files). Each step links to a
detailed section below.

**Prerequisites:** `git` and a conda distribution (Miniforge / Miniconda /
Anaconda).

1. **Clone the repository:**

```bash
git clone https://github.com/arvidl/AI-driven-neuropsych-screening.git
cd AI-driven-neuropsych-screening
```

2. **Create and activate the pinned environment** (see
   [Environment Setup](#environment-setup) for a pip/venv alternative):

```bash
conda env create -f environment.yml
conda activate ai-driven-neuropsych-screening
```

The version pins (notably `seaborn<0.13`) are required to reproduce the
committed figures — see [Reproducibility Across Machines](#reproducibility-across-machines).

3. **(Optional) install a system LaTeX toolchain** if you want the typeset PDF
   reports — see [External LaTeX Requirements](#external-latex-requirements).
   Skip this to reproduce the numbers and figures without the `*_report.pdf`.

4. **Run the smoke tests and regenerate the two manuscript-linked cases** in one
   command:

```bash
./scripts/release_check.sh
```

This runs `pytest tests/test_blinded_pipeline.py` and regenerates
`output_subj/subj_001/` and `output_subj/subj_048/` (figures, `*_report.json`,
`*_report.tex`, and `*_report.pdf` if LaTeX is installed).

5. **Verify your run matches the committed artifacts bit-for-bit** (numbers +
   report text):

```bash
git status --short -- 'output_subj/subj_001/*.json' 'output_subj/subj_001/*.tex' \
                      'output_subj/subj_048/*.json' 'output_subj/subj_048/*.tex'
# empty output => your run reproduced the committed deterministic results
```

6. **Reproduce the blinded subset of the paper's Table 1** — launch Jupyter and
   run the notebook top to bottom (see
   [Reproduce The Blinded Table 1 Subset](#reproduce-the-blinded-table-1-subset)):

```bash
jupyter lab   # open and run notebooks/03_table_1_generation_blinded.ipynb
```

**Optional — full blinded cohort** (all 105 subjects, ~8–14 min):

```bash
python scripts/neuropsych_subj_pipeline.py --all
```

**What reproduces from the public repo:** all numeric values and the Table 1
subset (exactly), the two case figures (manuscript Figures 2–5) and per-subject
reports, and Figure 1 from its TikZ source. **What does not:** the `Education`
and RBANS index-score rows of Table 1, which require non-public data — see
[Table 1 Note](#table-1-note).

## Table 1 Note

The published Table 1 in the paper is kept unchanged.

The new notebook `notebooks/03_table_1_generation_blinded.ipynb` reproduces the subset of Table 1 that is derivable from the blinded dataset only:

- age
- female percentage
- BIS total
- CPT measures
- Chalder total
- HADS anxiety and depression

These rows reproduce **exactly** the values reported in the published Table 1
(the blinded CSV preserves them unchanged).

Two parts of the published Table 1 are **not** reproducible from the blinded CSV
alone and are therefore intentionally not recomputed in the blinded notebook:

- `Education` — this variable is not carried in the released blinded dataset
  (it was dropped during de-identification), so it cannot be recomputed here.
- RBANS **index-score** rows — these require the proprietary RBANS normative
  conversion tables, which cannot be redistributed. The blinded dataset ships
  cohort-standardized RBANS raw subtests instead of the normed indices, so the
  published index-score rows are not derivable from the public data.

Both omissions are limitations of the *public data release*, not of the method:
the full-cohort `notebooks/02_table_1_generation.ipynb` reproduces the complete
Table 1 (all rows, n = 105) but expects the non-public cleaned cohort file, so it
is retained for provenance rather than as the primary public reproduction path.

## Figures

- **Figure 1** (eight-step reasoning-chain schematic) is a conceptual diagram,
  reproducible from LaTeX/TikZ source in `figures/` (`figure_1_reasoning_chain.tex`
  → `figure_1_reasoning_chain.pdf`).
- **Figures 2–5** (the two illustrative cases' multi-panel and radar plots) are
  data-driven and regenerate from the blinded dataset via
  `python scripts/neuropsych_subj_pipeline.py subj_001 subj_048` (written under
  `output_subj/subj_001/` and `output_subj/subj_048/`).

See `figures/README.md` for details.

## Method: AI-Assisted Development & Rule Set

This is an **AI-assisted, rule-based** pipeline, and the two halves of that phrase
are documented separately in `docs/`:

- **`docs/prompt_provenance.md`** — how the pipeline was *produced*: the iterative,
  clinician-led design brief and the verbatim original/updated/system prompts that
  drove the development-time assistants (Claude Opus 4.6, then GPT-5.4 in Cursor) to
  generate `scripts/neuropsych_pipeline.py`, plus the human-in-the-loop review and
  model cards.
- **`docs/rules.md`** — what the pipeline *runs*: the deterministic classification
  thresholds (HADS, BIS, Chalder, CPT, RBANS), the eight QC data-quality flags, the
  eight-step clinical reasoning chain, the cohort-relative percentile/z-score
  context, and the three audience-tailored views — each with code references.

> **AI at development time only, not at runtime.** The prompts and assistants were
> used to *draft* the code, which the authors then verified and corrected line by
> line. The deployed pipeline contains **no model, no AI client library, and no
> network calls**, and **no real or identifiable patient data were ever sent to any
> model**. This is why results are fully deterministic and reproducible.

## Model & Data Card

A compact card for the pipeline; see `docs/` and `data/README.md` for detail.

| | |
|---|---|
| **System** | Deterministic, rule-based decision-*support* pipeline for pre-examination neuropsychological screening; integrates five validated instruments (BIS, Conners CPT-3, Chalder Fatigue Scale, HADS, RBANS) into an eight-step reasoning chain with audience-tailored reports. |
| **Runtime AI** | **None** — no model, AI client library, or network call at runtime; fully deterministic. |
| **Development-time AI** | Claude Opus 4.6 then GPT-5.4 (via Cursor) used to *draft* code, author-verified line by line — see [`docs/prompt_provenance.md`](docs/prompt_provenance.md). |
| **Rules** | Published instrument cutoffs, locked to source values — see [`docs/rules.md`](docs/rules.md). |
| **Public data** | Blinded, de-identified cohort CSV (N = 105); `Education` and RBANS index scores intentionally withheld — see [`data/README.md`](data/README.md). |
| **Non-public data** | Raw/cleaned cohort files with identifiers are **not** distributed, per the study's ethics approval and data-protection constraints. |
| **Intended use** | Research and methods demonstration; screening decision support with a clinician in the loop. |
| **Out of scope** | Not a medical device; not diagnostic; not validated for autonomous clinical use; all outputs require expert review. |
| **License / cite** | MIT (`LICENSE`); citation metadata in `CITATION.cff` — see [Citing This Work](#citing-this-work). |

## Environment Setup

The pipeline is pure Python (NumPy / pandas / SciPy / Matplotlib / Seaborn) and
runs identically on Linux and macOS. It was developed on macOS (Apple Silicon,
MacBook Pro M-series) and is verified on Linux (Ubuntu 24.04); see
[Reproducibility Across Machines](#reproducibility-across-machines).

### Conda (recommended; Linux and macOS)

```bash
conda env create -f environment.yml
conda activate ai-driven-neuropsych-screening
```

### pip + venv (Linux alternative)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "numpy>=1.24,<2" "pandas>=2.0,<3" "scipy>=1.10" "matplotlib>=3.7,<3.9" \
            "seaborn>=0.12,<0.13" "pillow>=10.0" \
            jupyterlab ipykernel pytest
```

### Exact-version lock (fully deterministic install)

For the strongest install determinism, `requirements-lock.txt` pins the **exact**
versions of every package (generated and verified on Ubuntu / CPython 3.11):

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt
```

This guarantees an identical package set on every install and reproduces the
numeric/report outputs **byte-for-byte**. Figures render from the intended
seaborn 0.12 stack; they are visually equivalent but, like all Matplotlib
output, not guaranteed pixel-identical across operating systems / native font
(FreeType) builds. The conda `environment.yml` above remains the primary
cross-platform path; use the lock file when you need a frozen, exact-version
environment.

For notebook work (either setup):

```bash
python -m ipykernel install --user --name ai-driven-neuropsych-screening
jupyter lab
```

## External LaTeX Requirements

LaTeX is not installed through `environment.yml`. The subject pipeline compiles each per-subject PDF report with LaTeX, so to produce the `*_report.pdf` files you should install a system LaTeX distribution plus `biber` and `latexmk`.

Typical Linux (Debian / Ubuntu) setup:

```bash
sudo apt-get update
sudo apt-get install texlive-full biber latexmk
```

or, for a smaller installation:

```bash
sudo apt-get install texlive-latex-extra texlive-bibtex-extra \
                     texlive-fonts-recommended biber latexmk
```

Typical macOS setup:

```bash
brew install --cask mactex
```

or, for a smaller installation:

```bash
brew install --cask basictex
```

## Reproduce Subject Outputs

Run the blinded subject pipeline for the two manuscript-linked cases:

```bash
python scripts/neuropsych_subj_pipeline.py subj_001 subj_048
```

The standalone script in `scripts/neuropsych_pipeline.py` now defaults to the
full cohort CSV when that file is present, and otherwise falls back to the
blinded public CSV shipped in this repository. In the public repository, that
means the default CLI path is safe to run without extra data files.

Run the full blinded cohort (all 105 subjects):

```bash
python scripts/neuropsych_subj_pipeline.py --all
```

Outputs are written under `output_subj/<subject_id>/`. Approximate wall-clock
runtime for the full cohort (single process, Matplotlib `Agg` backend):

| Machine | OS | CPU | Full-cohort runtime |
|---|---|---|---|
| MacBook Pro (M4 Max) | macOS | Apple M4 Max | ~8 min 30 s |
| Dell Precision 7560 | Ubuntu 24.04 | Intel Xeon W-11955M (16 threads, 128 GB) | ~14 min 0 s (839 s) |

The repository tracks figures/reports for `subj_001` and `subj_048` only; the
other 103 per-subject output folders are git-ignored. See
[Reproducibility Across Machines](#reproducibility-across-machines) for the
cross-platform verification.

If you want one command that checks the main release path locally, run:

```bash
./scripts/release_check.sh
```

That script runs the blinded smoke tests and then regenerates the two
manuscript-linked subject outputs.

## Reproducibility Across Machines

The pipeline is **deterministic**: it uses the Matplotlib `Agg` backend and
contains no random-number generation, so identical inputs yield identical
results regardless of platform.

This was verified by regenerating the two manuscript-linked subjects on Linux
and comparing against the committed outputs, which were produced on macOS
(Apple Silicon):

- `subj_001` and `subj_048` `*_report.json` (all computed statistics) and
  `*_report.tex` (the LaTeX report) regenerate **byte-for-byte identically** on
  Ubuntu 24.04 (Dell Precision 7560, Intel Xeon W-11955M) and on the MacBook Pro.
  This match held even when the Linux check ran on an interpreter whose library
  versions differed from those `environment.yml` pins, underscoring that the
  numeric/report results do not depend on the platform or exact library versions
  (the figures do — see the next bullet).
- The figures (`*.png`, `*.pdf`) are **visually identical** across platforms when
  built from the pinned plotting stack (seaborn 0.12.x, Matplotlib 3.8), though
  not byte-identical because font rasterization and embedded PDF metadata differ
  between OS/library builds. Figure *appearance* does depend on the seaborn major
  version: **seaborn 0.13 reworked `violinplot` rendering** (fill colour/alpha and
  panel sizing), so `environment.yml` pins `seaborn>=0.12,<0.13` (and
  `matplotlib<3.9`) to reproduce the committed figures. This affects figures only;
  the numeric/report outputs above are unaffected by library versions. The
  committed figures are the canonical macOS renderings; on the pinned stack the
  Linux re-render matches them to within ~0.02% of pixels (anti-aliasing noise).

To reproduce and check this yourself:

```bash
python scripts/neuropsych_subj_pipeline.py subj_001 subj_048
git status --short -- 'output_subj/subj_001/*.json' 'output_subj/subj_001/*.tex' \
                      'output_subj/subj_048/*.json' 'output_subj/subj_048/*.tex'
# empty output => deterministic results match the committed (macOS) versions
```

## Reproduce The Blinded Table 1 Subset

Start Jupyter and open:

- `notebooks/03_table_1_generation_blinded.ipynb`

That notebook loads `data/BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv`, computes the reproducible subset of Table 1, displays a manuscript-style summary table, and emits LaTeX for the subset only.

## Repository Layout

- `data/`: blinded analysis-ready cohort CSV (see `data/README.md` for the
  data dictionary and ethics scope)
- `scripts/`: blinded neuropsych pipeline code
- `docs/`: method documentation — `prompt_provenance.md` (AI-assisted development
  + verbatim prompts) and `rules.md` (deterministic rule set / thresholds)
- `notebooks/`: manuscript provenance notebook plus blinded public notebook
- `output_subj/`: tracked example outputs for `subj_001` and `subj_048`
- `figures/`: reproducible Figure 1 source (TikZ) + compiled PDF; see
  `figures/README.md`
- `tests/`: blinded pipeline smoke tests
- `CITATION.cff`: machine-readable citation metadata (powers the
  GitHub "Cite this repository" button)

## Release Checklist

Before tagging a release, confirm:

- `./scripts/release_check.sh` passes in a fresh environment
- the working tree contains only intentional tracked artifacts
- the blinded CLI examples in this README still run as written

## Citing This Work

If you use this repository or the accompanying manuscript, please cite **both**:

- **Software** — this repository. GitHub's "Cite this repository" button renders
  APA/BibTeX from [`CITATION.cff`](CITATION.cff).
- **Article** — Lundervold AJ, Berentsen B, Lundervold A. *Journal of the
  International Neuropsychological Society* (accepted, 2026). The exact title and
  author metadata are recorded in [`CITATION.cff`](CITATION.cff).
