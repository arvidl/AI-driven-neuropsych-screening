# AI-driven-neuropsych-screening

_Astri J. Lundervold, Birgitte Berentsen, and Arvid Lundervold:_ <br>**"An AI-Assisted, Rule-Based Pipeline for Pre-Examination Screening in Clinical Neuropsychology: An Exploratory Method-Development Study"** (revised manuscript, resubmitted to the Journal of the International Neuropsychological Society, JINS)

Paper-and-code repository for the blinded neuropsychological screening pipeline described in the paper above.

## What This Repo Contains

- The blinded analysis dataset: `data/BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv`
- The standalone subject-processing pipeline:
  `scripts/neuropsych_pipeline.py` and `scripts/neuropsych_subj_pipeline.py`
- The two blinded example subject outputs linked to the paper:
  `output_subj/subj_001/` and `output_subj/subj_048/`
- The documented data-cleaning notebook (raw → cleaned → analysis → blinded),
  the narrated companion to `scripts/clean_cohort_data.py`:
  `notebooks/01_clean_cohort_data.ipynb`
- The full-cohort Table 1 notebook retained for provenance:
  `notebooks/02_table_1_generation.ipynb`
- A blinded-only notebook for the reproducible subset of Table 1:
  `notebooks/03_table_1_generation_blinded.ipynb`
- A results/robustness notebook (raw-vs-cleaned stability + flag-handling policy):
  `notebooks/04_cleaned_data_results.ipynb`

## Reproducibility Scope

This repository is designed around the public-safe blinded dataset. It fully supports:

- regenerating subject-level reports, JSON summaries, and figures from the blinded CSV
- regenerating the paper-linked outputs for `subj_001` and `subj_048`
- reproducing the blinded-data-supported subset of the paper's Table 1

## Table 1 Note

The published Table 1 in the paper is kept unchanged.

The new notebook `notebooks/03_table_1_generation_blinded.ipynb` reproduces the subset of Table 1 that is derivable from the blinded dataset only:

- age
- female percentage
- BIS total
- CPT measures
- Chalder total
- HADS anxiety and depression

Two parts of the published Table 1 are not reproducible from the blinded CSV alone and are therefore intentionally not recomputed in the blinded notebook:

- `Education`
- RBANS index-score rows

The full-cohort `notebooks/02_table_1_generation.ipynb` is included for manuscript provenance, but it expects a non-public cleaned cohort file and is not the primary public reproduction path in this repository.

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
pip install "numpy>=1.24" "pandas>=2.0" "scipy>=1.10" "matplotlib>=3.7" \
            "seaborn>=0.13" "python-docx>=1.1" "pillow>=10.0" \
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
- The figures (`*.png`, `*.pdf`) are **visually identical** but not byte-identical
  across platforms, because Matplotlib font rasterization and embedded PDF
  metadata differ between OS/library builds. The committed figures are the
  canonical macOS renderings.

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
- `tests/`: blinded pipeline smoke tests
- `CITATION.cff`: machine-readable citation metadata (powers the
  GitHub "Cite this repository" button)

## Release Checklist

Before tagging a release, confirm:

- `./scripts/release_check.sh` passes in a fresh environment
- the working tree contains only intentional tracked artifacts
- the blinded CLI examples in this README still run as written
