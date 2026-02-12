from datetime import datetime
from pathlib import Path
from typing import Optional

import rich_click as click
from bewer import Dataset
from bewer.reporting.html.labels import HTMLAlignmentLabels
from bewer.reporting.html.report import ReportMetric, ReportSummaryItem, generate_report

REPORT_METRICS = [
    ReportMetric("wer"),
    ReportMetric("cer"),
]

MEDICAL_TERM_RECALL = ReportMetric("legacy_medical_word_accuracy", label="Medical Term Recall")

REPORT_SUMMARY_ITEMS = [
    ReportSummaryItem("num_examples", label="Number of examples"),
    ReportSummaryItem("num_ref_words", label="Number of reference words"),
    ReportSummaryItem("num_ref_chars", label="Number of reference characters"),
    ReportSummaryItem("num_hyp_words", label="Number of generated words"),
    ReportSummaryItem("num_hyp_chars", label="Number of generated characters"),
]

LABELS = HTMLAlignmentLabels()

LABELS.REF = "Ref."
LABELS.HYP = "Gen."

LABELS.KEYWORD = "Medical Term"
LABELS.KEYWORD_TOOLTIP = "Indicates a medical term from the provided keyword list."

LABELS.MATCH = "Correct"
LABELS.MATCH_TOOLTIP = "A word that is correctly generated and matches the reference."

LABELS.SUBSTITUTION = "Misspelling"
LABELS.SUBSTITUTION_TOOLTIP = "A word that is misspelled in the generated text."

LABELS.INSERTION = "Extra Word"
LABELS.INSERTION_TOOLTIP = "An extra word that appears in the generated text but not in the reference."

LABELS.DELETION = "Missing Word"
LABELS.DELETION_TOOLTIP = "A word that is missing from the generated text but appears in the reference."

LABELS.PADDING = "Padding"
LABELS.PADDING_TOOLTIP = (
    "Padding tokens added to align the reference and generated text for visualization purposes. "
    "These do not correspond to actual words in the reference or generated text."
)

ALIGNMENT_TYPE_MAP = {
    "lv": "levenshtein",
    "ea": "error_align",
}


@click.group()
def cli():
    """Command-line interface for Corti Canal ASR evaluation."""
    pass


@cli.command(
    help=(
        "Generate an ASR evaluation report from a CSV file. The CSV must contain at least two columns: one with "
        "reference transcripts (ground truth) and one with hypothesis transcripts (model output)."
    ),
)
@click.option(
    "--output-path",
    type=Path,
    default=None,
    help="Path for the generated report. When omitted, a timestamped filename is created in the current directory.",
)
@click.option(
    "--ref-col",
    type=str,
    default="ref",
    help="Name of the CSV column containing the ground-truth reference transcripts.",
)
@click.option(
    "--gen-col",
    type=str,
    default="gen",
    help="Name of the CSV column containing the model-generated transcripts.",
)
@click.option(
    "--medical-terms",
    type=Path,
    default=None,
    help=(
        "Path to a file containing medical terms used to compute the Medical Term Recall metric. The file should "
        "have one term per line. If not provided, the Medical Term Recall metric will not be computed."
    ),
)
@click.option(
    "--alignment-type",
    type=click.Choice(["lv", "ea"]),
    default="lv",
    help=(
        "Algorithm used to align reference and hypothesis words. "
        '"lv" uses Levenshtein edit-distance; "ea" uses ErrorAlign. '
    ),
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help=(
        "Allow overwriting an existing report file. Without this flag, Canal will refuse to write over an existing "
        "file."
    ),
)
@click.argument(
    "input-path",
    type=Path,
    help="Path to the CSV file containing the evaluation data.",
)
def report(
    input_path: Path,
    ref_col: str,
    gen_col: str,
    medical_terms: Path | None,
    alignment_type: str,
    overwrite: bool,
    output_path: Optional[Path],
) -> None:
    """Generate an ASR evaluation report from a CSV file."""

    if output_path is None:
        output_path = Path(f"canal-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html")

    dataset = Dataset()
    dataset.load_csv(
        input_path,
        ref_col=ref_col,
        hyp_col=gen_col,
    )
    if medical_terms is not None:
        with open(medical_terms, "r") as f:
            keyword_list = [kw.strip() for kw in f.read().strip().splitlines()]
        dataset.add_keyword_list("medical_terms", keyword_list)
        report_metrics = REPORT_METRICS + [MEDICAL_TERM_RECALL]
    else:
        report_metrics = REPORT_METRICS

    generate_report(
        dataset=dataset,
        path=output_path,
        allow_overwrite=overwrite,
        alignment_type=ALIGNMENT_TYPE_MAP[alignment_type],
        alignment_labels=LABELS,
        report_metrics=report_metrics,
        report_summary=REPORT_SUMMARY_ITEMS,
    )
