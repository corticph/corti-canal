from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from click.testing import CliRunner

from corti_canal.cli.main import MEDICAL_TERM_RECALL, REPORT_METRICS, cli


@patch("corti_canal.cli.main.generate_report")
@patch("corti_canal.cli.main.Dataset")
def test_report_default_options(mock_dataset_cls, mock_generate_report, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.touch()

    runner = CliRunner()
    result = runner.invoke(cli, ["report", str(csv_path)])

    assert result.exit_code == 0

    instance = mock_dataset_cls.return_value
    instance.load_csv.assert_called_once_with(csv_path, ref_col="ref", hyp_col="gen")

    call_kwargs = mock_generate_report.call_args[1]
    assert call_kwargs["alignment_type"] == "levenshtein"
    assert str(call_kwargs["path"]).startswith("canal-report-")
    assert str(call_kwargs["path"]).endswith(".html")


@patch("corti_canal.cli.main.generate_report")
@patch("corti_canal.cli.main.Dataset")
def test_report_custom_columns(mock_dataset_cls, mock_generate_report, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.touch()

    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--ref-col", "text", "--gen-col", "transcript", str(csv_path)])

    assert result.exit_code == 0
    instance = mock_dataset_cls.return_value
    instance.load_csv.assert_called_once_with(csv_path, ref_col="text", hyp_col="transcript")


@patch("corti_canal.cli.main.generate_report")
@patch("corti_canal.cli.main.Dataset")
def test_report_with_medical_terms(mock_dataset_cls, mock_generate_report, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.touch()
    terms_path = tmp_path / "terms.txt"
    terms_path.write_text("hypertension\ndiabetes\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--medical-terms", str(terms_path), str(csv_path)])

    assert result.exit_code == 0

    instance = mock_dataset_cls.return_value
    instance.add_keyword_list.assert_called_once_with("medical_terms", ["hypertension", "diabetes"])

    call_kwargs = mock_generate_report.call_args[1]
    assert MEDICAL_TERM_RECALL in call_kwargs["report_metrics"]


@patch("corti_canal.cli.main.generate_report")
@patch("corti_canal.cli.main.Dataset")
def test_report_without_medical_terms(mock_dataset_cls, mock_generate_report, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.touch()

    runner = CliRunner()
    result = runner.invoke(cli, ["report", str(csv_path)])

    assert result.exit_code == 0

    instance = mock_dataset_cls.return_value
    instance.add_keyword_list.assert_not_called()

    call_kwargs = mock_generate_report.call_args[1]
    assert call_kwargs["report_metrics"] == REPORT_METRICS
    assert MEDICAL_TERM_RECALL not in call_kwargs["report_metrics"]


@patch("corti_canal.cli.main.generate_report")
@patch("corti_canal.cli.main.Dataset")
def test_report_alignment_type_ea(mock_dataset_cls, mock_generate_report, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.touch()

    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--alignment-type", "ea", str(csv_path)])

    assert result.exit_code == 0

    call_kwargs = mock_generate_report.call_args[1]
    assert call_kwargs["alignment_type"] == "error_align"


@patch("corti_canal.cli.main.generate_report")
@patch("corti_canal.cli.main.Dataset")
def test_report_custom_output_path(mock_dataset_cls, mock_generate_report, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.touch()
    output = tmp_path / "custom.html"

    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--output-path", str(output), str(csv_path)])

    assert result.exit_code == 0

    call_kwargs = mock_generate_report.call_args[1]
    assert call_kwargs["path"] == output


@patch("corti_canal.cli.main.generate_report")
@patch("corti_canal.cli.main.Dataset")
def test_report_overwrite_flag(mock_dataset_cls, mock_generate_report, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.touch()

    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--overwrite", str(csv_path)])

    assert result.exit_code == 0

    call_kwargs = mock_generate_report.call_args[1]
    assert call_kwargs["allow_overwrite"] is True


def test_report_missing_input():
    runner = CliRunner()
    result = runner.invoke(cli, ["report"])

    assert result.exit_code != 0
