#!/usr/bin/env python3
"""
Blinded neuropsychological profile analysis pipeline.

This is a thin public-safe wrapper around `neuropsych_pipeline.py` that:
- reads only the blinded cohort CSV
- uses `subj_###` identifiers directly
- writes outputs under `output_subj/<subject_id>/`

All statistics, figures, and reports are computed from the blinded dataset only.
"""

import argparse

from neuropsych_pipeline import (
    BLINDED_DATA_PATH,
    COL_GROUP,
    OUTPUT_SUBJ_BASE,
    get_all_patient_ids,
    load_cohort,
    process_batch,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for blinded subject processing."""
    parser = argparse.ArgumentParser(
        description="Blinded neuropsychological profile pipeline for subj_### IDs",
        epilog="Examples:\n"
               "  python neuropsych_subj_pipeline.py subj_001\n"
               "  python neuropsych_subj_pipeline.py subj_001 subj_002\n"
               "  python neuropsych_subj_pipeline.py --all --batch-size 10\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "subjects",
        nargs="*",
        help="Subject ID(s) to process (e.g., subj_001 subj_002). If omitted, processes the first subject only.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all blinded subjects in the cohort.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of subjects per batch for progress reporting (default: 10).",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=BLINDED_DATA_PATH,
        help=f"Path to blinded cohort CSV (default: {BLINDED_DATA_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_SUBJ_BASE,
        help=f"Output directory (default: {OUTPUT_SUBJ_BASE})",
    )
    return parser.parse_args()


def main() -> None:
    """Run the blinded subject pipeline."""
    args = parse_args()
    df = load_cohort(args.data)
    all_ids = get_all_patient_ids(df)

    if args.all:
        subject_ids = all_ids
    elif args.subjects:
        subject_ids = args.subjects
    else:
        subject_ids = [all_ids[0]]

    print(f"Cohort loaded: {len(df)} subjects ({df[COL_GROUP].value_counts().to_dict()})")
    print(f"Processing {len(subject_ids)} subject(s) in batches of {args.batch_size}")

    for i in range(0, len(subject_ids), args.batch_size):
        batch = subject_ids[i : i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (len(subject_ids) + args.batch_size - 1) // args.batch_size
        print(f"\n{'='*60}")
        print(f"Batch {batch_num}/{total_batches}: {batch}")
        print(f"{'='*60}")
        results = process_batch(df, batch, args.output_dir)
        print(f"Batch {batch_num} complete: {len(results)} subject(s) processed.")

    print(f"\nAll done. {len(subject_ids)} subject(s) processed.")


if __name__ == "__main__":
    main()
