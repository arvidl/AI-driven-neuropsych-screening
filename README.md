# AI-driven-neuropsych-screening

_Astri J. Lundervold, Birgitte Berentsen, and Arvid Lundervold:_ <br>**"An AI-Assisted, Rule-Based Pipeline for Pre-Examination Screening in Clinical Neuropsychology: An Exploratory Method-Development Study"** (revised manuscript, resubmitted to the Journal of the International Neuropsychological Society, JINS)

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
  The match held even though the Linux run used a different Python/library build
  than `environment.yml` pins (Python 3.9 with NumPy 1.24 / pandas 2.1 /
  SciPy 1.9 / Matplotlib 3.8), which underscores that the numeric results do not
  depend on the platform or exact library versions.
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
