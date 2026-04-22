# JINS submission package — 2026-04-22

This folder bundles everything needed for the ScholarOne submission to the
*Journal of the International Neuropsychological Society*. Each file is
ready to be uploaded as a separate item in ScholarOne; no further bundling
is required.

## `manuscript/`

| File | Purpose |
| ---- | ------- |
| `cover_letter.md` | Editor cover letter (fill in suggested-reviewer block, then export to .docx or PDF before upload) |
| `jins_main.tex` | LaTeX source of the manuscript (working copy, version 2026-04-22) |
| `jins_references.bib` | BibLaTeX bibliography (includes new `Akbari2025Attention` entry) |
| `jins_main.pdf` | Compiled PDF of the LaTeX source (review reference, 23 pages) |
| `manuscript_word_export.pdf` | Word export PDF you provided (`AI_driven_neuropsych_screening_20260422_docx.pdf`); replace with the matching `.docx` before submitting |

> **Action item before upload:** Re-import `jins_main.pdf` into Word, accept
> the four small edits (version stamp, Akbari citation, removal of orphan
> paragraph, "genetics" added to Limitations), save as `.docx`, and place
> next to or in lieu of `manuscript_word_export.pdf`.

## `figures/`

Each figure is a single, self-contained PDF. Captions live in the manuscript
file (per JINS guidance).

| File | Source |
| ---- | ------ |
| `Figure_1_reasoning_chain.pdf` | Built from `_build/Figure_1_reasoning_chain.tex` (TikZ extracted from manuscript) |
| `Figure_2_case1_multipanel.pdf` | `output_subj/subj_001/subj_001_multipanel_clinical.pdf` |
| `Figure_3_case1_radar.pdf` | Composite of three subj_001 radar variants, built from `_build/Figure_3_case1_radar.tex` |
| `Figure_4_case2_multipanel.pdf` | `output_subj/subj_048/subj_048_multipanel_clinical.pdf` |
| `Figure_5_case2_radar.pdf` | Composite of three subj_048 radar variants, built from `_build/Figure_5_case2_radar.tex` |

The `_build/` subfolder contains the standalone LaTeX wrappers and intermediate
files used to generate Figures 1, 3, and 5. It is not part of the submission
itself but is kept for reproducibility; delete it before zipping if desired.

> **Cambridge artwork guide:** PDFs as supplied are vector graphics. If
> ScholarOne requests rasterised images, export each to TIFF/PNG at
> 300 dpi (halftone) / 600 dpi (line art) using e.g.
> `magick -density 600 Figure_X.pdf Figure_X.tif`. Provide alt-text for each
> figure via Cambridge's Accessibility Descriptions Submission Form.

## `supplementary/`

Three independent PDF files, uploaded as separate Supplementary File items
in ScholarOne. JINS does not typeset supplementary content; the files ship
exactly as they appear here.

| File | Description |
| ---- | ----------- |
| `S1_supplementary_methods.pdf` | Prompt-development brief and complete decision-rule specification |
| `S2_case_1_report.pdf` | Full audience-tailored pipeline report for Case 1 (subj_001) |
| `S3_case_2_report.pdf` | Full audience-tailored pipeline report for Case 2 (subj_048) |

## Submission checklist

- [ ] Cover letter exported to `.docx` (or PDF) and reviewer block populated
- [ ] Manuscript Word file (`.docx`) regenerated from updated `jins_main.pdf`
- [ ] Figures 1–5 uploaded as separate items, captions kept in manuscript
- [ ] Supplementary materials S1, S2, S3 uploaded as separate items with
      one-sentence captions in the ScholarOne metadata
- [ ] AI-use declaration in Acknowledgments matches the cover-letter wording
- [ ] Competing-interests, funding, ORCID, ethics-approval, and
      data-availability statements present in the main file
- [ ] Accessibility alt-text provided (or noted as "to follow at proofs")
