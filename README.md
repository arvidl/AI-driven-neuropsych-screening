# AI-driven-neuropsych-screening

_Astri J. Lundervold, Birgitte Berentsen, and Arvid Lundervold:_ <br>**"An AI-Initiated, Rule-Based Pipeline for Pre-Examination Screening in Clinical Neuropsychology"** (submitted)

Paper-and-code repository for the blinded neuropsychological screening pipeline and the manuscript artifacts built around it.

## What This Repo Contains

- The blinded analysis dataset: `data/BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv`
- The standalone subject-processing pipeline:
  `scripts/neuropsych_pipeline.py` and `scripts/neuropsych_subj_pipeline.py`
- The two manuscript-linked blinded example outputs:
  `output_subj/subj_001/` and `output_subj/subj_048/`
- The manuscript sources and compiled PDF:
  `JINS/jins_main.tex`, `JINS/jins_references.bib`, `JINS/jins_main.pdf`
- The supplementary sources and compiled PDFs:
  `JINS/supplementary/`, `JINS/supplementary_methods.pdf`
- The anonymized case reports:
  `JINS/case_1_report.pdf`, `JINS/case_2_report.pdf`
- The original Table 1 notebook retained for provenance:
  `notebooks/01_table_1_generation.ipynb`
- A blinded-only notebook for the reproducible subset of Table 1:
  `notebooks/02_table_1_generation_blinded.ipynb`

## Reproducibility Scope

This repository is designed around the public-safe blinded dataset. It fully supports:

- regenerating subject-level reports, JSON summaries, and figures from the blinded CSV
- regenerating the manuscript-linked outputs for `subj_001` and `subj_048`
- reproducing the blinded-data-supported subset of manuscript Table 1

This repository also ships canonical paper artifacts that are preserved as-is:

- `JINS/jins_main.pdf`
- `JINS/supplementary_methods.pdf`
- `JINS/supplementary/supplementary.pdf`
- `JINS/case_1_report.pdf`
- `JINS/case_2_report.pdf`

## Table 1 Note

The published Table 1 in `JINS/jins_main.tex` is kept unchanged.

The new notebook `notebooks/02_table_1_generation_blinded.ipynb` reproduces the subset of Table 1 that is derivable from the blinded dataset only:

- age
- female percentage
- BIS total
- CPT measures
- Chalder total
- HADS anxiety and depression

Two parts of the published Table 1 are not reproducible from the blinded CSV alone and are therefore intentionally not recomputed in the blinded notebook:

- `Education`
- RBANS index-score rows

The original `notebooks/01_table_1_generation.ipynb` is included for manuscript provenance, but it expects a non-public cleaned cohort file and is not the primary public reproduction path in this repository.

## Environment Setup

Create the conda environment:

```bash
conda env create -f environment.yml
conda activate ai-driven-neuropsych-screening
```

For notebook work:

```bash
python -m ipykernel install --user --name ai-driven-neuropsych-screening
jupyter lab
```

## External LaTeX Requirements

LaTeX is not installed through `environment.yml`. To rebuild the manuscript and supplementary PDFs you should install a system LaTeX distribution plus `biber`.

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

Run the full blinded cohort (about 8 min 30 s on a MBP M4 Max):

```bash
python scripts/neuropsych_subj_pipeline.py --all
```

Outputs are written under `output_subj/<subject_id>/`.

If you want one command that checks the main release path locally, run:

```bash
./scripts/release_check.sh
```

That script runs the blinded smoke tests and then regenerates the two
manuscript-linked subject outputs.

## Reproduce The Blinded Table 1 Subset

Start Jupyter and open:

- `notebooks/02_table_1_generation_blinded.ipynb`

That notebook loads `data/BGA_merged_all_20260208_cleaned_for_analysis_blinded.csv`, computes the reproducible subset of Table 1, displays a manuscript-style summary table, and emits LaTeX for the subset only.

## Rebuild Manuscript Artifacts

Main manuscript:

```bash
cd JINS
latexmk -pdf jins_main.tex
```

Supplementary document:

```bash
cd JINS/supplementary
latexmk -pdf supplementary.tex
```

The manuscript source expects the blinded figure files in `output_subj/subj_001/` and `output_subj/subj_048/`.

## Repository Layout

- `data/`: blinded analysis-ready cohort CSV
- `scripts/`: blinded neuropsych pipeline code
- `notebooks/`: manuscript provenance notebook plus blinded public notebook
- `output_subj/`: tracked example outputs for `subj_001` and `subj_048`
- `JINS/`: manuscript, references, supplementary material, and compiled artifacts
- `tests/`: blinded pipeline smoke tests

## Release Checklist

Before tagging a release, confirm:

- `./scripts/release_check.sh` passes in a fresh environment
- the working tree contains only intentional tracked artifacts
- the blinded CLI examples in this README still run as written
- manuscript rebuilds are verified if TeX sources or figures changed
