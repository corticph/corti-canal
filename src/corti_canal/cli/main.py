from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import rich_click as click
from bewer import Dataset
from bewer.reporting.html.labels import HTMLAlignmentLabels
from bewer.reporting.html.report import ReportAlignment, ReportMetric, ReportSummaryItem, generate_report

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
        "Path to a file containing medical terms used to compute the medical term recall metric. The file should "
        "have one term per line. If not provided, the medical term recall metric will not be computed."
    ),
)
@click.option(
    "--disable-normalization",
    is_flag=True,
    default=False,
    help=(
        "Disable text normalization before computing metrics. Basic normalization includes lowercasing and removing "
        "punctuation and diacritics."
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
    disable_normalization: bool,
    alignment_type: str,
    overwrite: bool,
    output_path: Optional[Path],
) -> None:
    """Generate an ASR evaluation report from a CSV file."""

    click.echo()

    if output_path is None:
        output_path = Path(f"canal-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html")

    if not input_path.is_file():
        click.echo(f"Error: Input CSV file '{input_path.absolute()}' does not exist.", err=True)
        raise click.Abort()

    if medical_terms is not None and not medical_terms.is_file():
        click.echo(f"Error: Medical terms file '{medical_terms.absolute()}' does not exist.", err=True)
        raise click.Abort()

    if ref_col == gen_col:
        click.echo("Error: --ref-col and --gen-col cannot be the same column.", err=True)
        raise click.Abort()

    try:
        df = pd.read_csv(input_path, nrows=0)  # Read only the header row
    except Exception as e:
        click.echo(f"Error: Failed to read input CSV file '{input_path.absolute()}'. {str(e)}", err=True)
        raise click.Abort()

    if ref_col not in df.columns:
        col_names = ", ".join(df.columns)
        click.echo(
            f"Error: --ref-col '{ref_col}' is not a valid column in the input CSV. Available columns: {col_names}",
            err=True,
        )
        raise click.Abort()

    if gen_col not in df.columns:
        col_names = ", ".join(df.columns)
        click.echo(
            f"Error: --gen-col '{gen_col}' is not a valid column in the input CSV. Available columns: {col_names}",
            err=True,
        )
        raise click.Abort()

    metadata = {
        "Normalization": "Enabled" if not disable_normalization else "Disabled",
        "Alignment method": "Levenshtein" if alignment_type == "lv" else "ErrorAlign",
    }

    dataset = Dataset()
    dataset.load_csv(
        input_path,
        ref_col=ref_col,
        hyp_col=gen_col,
    )

    click.echo(click.style("✓", fg="green") + f" Successfully loaded {len(dataset)} examples.")

    use_normalization = not disable_normalization

    report_metrics = [
        ReportMetric("wer", label="Word Error Rate", normalized=use_normalization),
        ReportMetric("cer", label="Character Error Rate", normalized=use_normalization),
    ]
    report_alignment = ReportAlignment(ALIGNMENT_TYPE_MAP[alignment_type], normalized=use_normalization)

    if medical_terms is not None:
        with open(medical_terms, "r") as f:
            keyword_list = [kw.strip() for kw in f.read().strip().splitlines()]
        dataset.add_keyword_list("medical_terms", keyword_list)
        report_metrics.append(
            ReportMetric(
                "mtr",
                label="Medical Term Recall",
                normalized=use_normalization,
            )
        )
        click.echo(click.style("✓", fg="green") + f" Successfully loaded {len(keyword_list)} medical terms.")

    generate_report(
        dataset=dataset,
        path=output_path,
        allow_overwrite=overwrite,
        alignment_labels=LABELS,
        report_alignment=report_alignment,
        report_metrics=report_metrics,
        report_summary=REPORT_SUMMARY_ITEMS,
        metadata=metadata,
    )
    click.echo(click.style("✓", fg="green") + f" Report generated at '{output_path.absolute()}'.\n")
