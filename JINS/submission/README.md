# JINS submission package — 2026-04-24

Submission to the **Special Issue 1: Artificial Intelligence in Neuropsychology**
of the *Journal of the International Neuropsychological Society* (deadline
15 May 2026; co-organizers Thomas, Langer, Lundervold).

This folder bundles everything needed for the ScholarOne submission. Each file
is uploaded as a separate item in ScholarOne; no further bundling is required.

## `manuscript/`

| File | Purpose |
| ---- | ------- |
| `AI_driven_neuropsych_screening_20260424.docx` | **Main manuscript file** for upload (Microsoft Word, JINS-compliant; *upload as the manuscript file in ScholarOne*) |
| `cover_letter.md` | Cover letter — confirms submission to the Special Issue on *Artificial Intelligence in Neuropsychology* and the AI-use declaration. Export to `.docx` or `.pdf` before uploading. Fill in the suggested-reviewer block first. |
| `jins_main.tex` | LaTeX source of the manuscript (working copy used to generate the .docx; not uploaded) |
| `jins_references.bib` | BibLaTeX bibliography (working copy; not uploaded) |
| `jins_main.pdf` | Compiled PDF of the LaTeX source (review reference; not uploaded) |
| `manuscript_word_export.pdf` | Earlier draft (`AI_driven_neuropsych_screening_20260422_docx.pdf`); kept for reference, not uploaded |

The new `AI_driven_neuropsych_screening_20260424.docx` is built directly from
the aligned LaTeX source by `JINS/build_jins_docx.py` and conforms to the
JINS *Preparing your materials* checklist:

- Times New Roman 12 pt throughout, double-spaced
- Continuous line numbering on the manuscript-body section
- Title page (page 1) with running head ("Lundervold-AI Pre-Examination
  Screening", 39 chars), full title, author block with superscript
  affiliations, country names, corresponding-author block (capitalised
  email, no hyphen), ORCID iDs, and word counts
- Structured Abstract (Objective / Method / Results / Conclusions) with six
  semicolon-separated MeSH-style keywords (page 2)
- Statement of Research Significance with three underlined headings (page 3,
  133 words; under the 150-word cap)
- Manuscript body (Introduction → Method → Results → Discussion →
  Conclusions, page 4 onward) with Helsinki-Declaration ethics statement and
  named IRB approval (REK2015-01621)
- `[INSERT TABLE 1 HERE]`, `[INSERT TABLE 2 HERE]`, `[INSERT TABLE 3 HERE]`,
  and `[INSERT FIGURE 1–5 HERE]` callouts in the body
- Acknowledgements section followed by **Competing Interests** and
  **Sources of Support** sub-headings, plus a **Data Availability Statement**
  and a **Supplementary Material** pointer
- References in APA 7 style with all authors listed for 3–20 author works
- Tables 1–3 and Figures 1–5 each on a separate page after the references;
  Figure Legends on a dedicated page that precedes the figures
- Word counts: abstract 224 (≤ 250) and manuscript body 4 961 (≤ 5 000)

> **Action items before upload:**
> 1. Convert `cover_letter.md` to `.docx` or `.pdf` and fill in the
>    Suggested Reviewers block.
> 2. Open `AI_driven_neuropsych_screening_20260424.docx` in Microsoft Word,
>    confirm the page numbering, line numbers, and any country/state
>    abbreviations look correct, and adjust the running head if needed.
> 3. In ScholarOne, select **"Artificial Intelligence in Neuropsychology"**
>    when prompted for the special issue.

## `figures/`

Each figure is a single, self-contained PDF. Captions live on the dedicated
**Figure Legends** page in the manuscript file (per JINS guidance), and each
figure is also embedded inside the docx after the legends so reviewers can
see the figure inline if they wish.

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

> **Cambridge artwork guide:** PDFs as supplied are vector graphics and meet
> JINS' "twice intended size, ≥ 300 dpi photo reduction" requirement. If
> ScholarOne requests rasterised images, export each to TIFF/PNG at 300 dpi
> (halftone) / 600 dpi (line art) using e.g.
> `magick -density 600 Figure_X.pdf Figure_X.tif`. Provide alt-text for
> each figure via Cambridge's Accessibility Descriptions Submission Form.

## `supplementary/`

Three independent PDF files, uploaded as separate Supplementary File items
in ScholarOne. JINS does not typeset supplementary content; the files ship
exactly as they appear here.

| File | Description |
| ---- | ----------- |
| `S1_supplementary_methods.pdf` | Prompt-development brief and complete decision-rule specification (system prompt, five assessment domains, visualization design, audience-tailored variants, structured JSON schema, and the full deterministic rule set used at runtime) |
| `S2_case_1_report.pdf` | Full audience-tailored pipeline report for Case 1 (subj_001) |
| `S3_case_2_report.pdf` | Full audience-tailored pipeline report for Case 2 (subj_048) |

## Submission checklist

- [ ] Cover letter exported to `.docx` (or PDF) and reviewer block populated
- [ ] **Special Issue selected** ("Artificial Intelligence in Neuropsychology")
      in ScholarOne
- [ ] Manuscript Word file (`AI_driven_neuropsych_screening_20260424.docx`)
      uploaded as the main manuscript
- [ ] Figures 1–5 uploaded as separate items, captions kept on the Figure
      Legends page in the manuscript
- [ ] Supplementary materials S1, S2, S3 uploaded as separate items with
      one-sentence captions in the ScholarOne metadata
- [ ] AI-use declaration in Acknowledgements matches the cover-letter wording
- [ ] Competing-interests, funding, ORCID, ethics-approval, and
      data-availability statements present in the main file
- [ ] Accessibility alt-text provided (or noted as "to follow at proofs")
