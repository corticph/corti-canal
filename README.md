<p align="center">
  <img src="https://raw.githubusercontent.com/corticph/corti-canal/refs/heads/main/.github/assets/logo.svg" alt="Corti Canal" width="560">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-%203.10%20|%203.11%20|%203.12%20|%203.13|%203.14-green" alt="Python Versions">
  <img src="https://codecov.io/gh/corticph/corti-canal/graph/badge.svg" alt="Coverage" style="margin-left:5px;">
  <img src="https://img.shields.io/pypi/v/corti-canal.svg" alt="PyPI" style="margin-left:5px;">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License" style="margin-left:5px;">
</p>

<p align="center">
      <a href="#installation">Installation</a> &bull;
      <a href="#usage">Usage</a> &bull;
      <a href="#understanding-the-report">Understanding the Report</a> &bull;
      <a href="#normalization">Normalization</a> &bull;
      <a href="#limitations">Limitations</a>
</p>

---

Canal is a command-line tool that helps you measure how well a speech-recognition model is performing. Give it a CSV with the correct transcripts alongside the model-generated output, and it produces a self-contained HTML report with overall accuracy metrics and a word-by-word comparison so you can see exactly where the model gets things right — and where it doesn't.

<br>

<a href="https://corticph.github.io/corti-canal/">
  <img src="https://raw.githubusercontent.com/corticph/corti-canal/refs/heads/main/.github/assets/report_preview.png" alt="Report Preview" width="100%">
</a>

<br>

## Installation

The recommended way to install Canal is with [pipx](https://pipx.pypa.io/), which installs CLI tools in isolated environments:

```bash
pipx install corti-canal
```

<details>
<summary>Don't have pipx installed?</summary>
<br/>
Install pipx first, then install Canal:

```bash
# macOS
brew install pipx
pipx ensurepath

# Linux (Debian/Ubuntu)
sudo apt install pipx
pipx ensurepath

# With pip (any platform)
pip install --user pipx
pipx ensurepath
```

After installing pipx, restart your terminal and then run:

```bash
pipx install corti-canal
```

</details>

To upgrade to the latest version:

```bash
pipx upgrade corti-canal
```

## Usage

```
canal report [OPTIONS] INPUT_PATH
```

Generate an ASR evaluation report from a CSV file. The CSV must contain at least two columns: one with reference transcripts (ground truth) and one with hypothesis transcripts (model output).

Use `canal report --help` to view the full command description and available options.

### Arguments

<table>
<colgroup>
  <col width="150">
  <col>
</colgroup>
<tr><th>Argument</th><th>Description</th></tr>
<tr><td><code>INPUT_PATH</code></td><td>Path to the CSV file containing the evaluation data.</td></tr>
</table>

### Options

<table>
<tr><th>Option</th><th>Default</th></tr>
<tr><td><code>--output-path</code></td><td><code>canal-report-{time}.html</code></td></tr>
<tr><td colspan="2">Path for the generated report. Defaults to a timestamped file in the current directory (e.g., <code>canal-report-20251224-173020.html</code>).</td></tr>
<tr><td><code>--ref-col</code></td><td><code>ref</code></td></tr>
<tr><td colspan="2">Name of the CSV column containing the ground-truth <strong>reference</strong> transcripts.</td></tr>
<tr><td><code>--gen-col</code></td><td><code>gen</code></td></tr>
<tr><td colspan="2">Name of the CSV column containing the model-<strong>generated</strong> transcripts.</td></tr>
<tr><td><code>--medical-terms</code></td><td><code>None</code></td></tr>
<tr><td colspan="2">Path to a file containing medical terms (one per line) used to compute the Medical Term Recall metric. If not provided, Medical Term Recall will not be computed.</td></tr>
<tr><td><code>--disable-normalization</code></td><td><code>False</code></td></tr>
<tr><td colspan="2">Disable text normalization before computing metrics. Basic normalization includes lowercasing and removing punctuation and diacritics.</td></tr>
<tr><td><code>--alignment-type</code></td><td><code>lv</code></td></tr>
<tr><td colspan="2">Algorithm used to align reference and hypothesis words. <code>lv</code> (Levenshtein) is a conventional word-level alignment used for metrics like WER and CER. <code>ea</code> (ErrorAlign) is a more advanced algorithm that aligns words closer to the way a human reader would.</td></tr>
<tr><td><code>--overwrite</code></td><td><code>False</code></td></tr>
<tr><td colspan="2">Allow overwriting an existing report file. Without this flag, Canal will refuse to write over an existing file.</td></tr>
</table>

### Example

```bash
# Columns are named "ref" and "gen" (the defaults)
canal report data.csv

# Custom column names and output path
canal report --ref-col text --gen-col transcript --output-path report.html data.csv

# With medical term recall
canal report --medical-terms medical_terms.txt data.csv
```

### Input CSV format

The CSV file should contain at minimum a reference column and a hypothesis column. Any additional columns are ignored.

```
ref,gen
"The patient was prescribed amoxicillin.","The patient was prescribed amoxicilin."
"The colonoscopy revealed no significant abnormalities.","The colonoscopy revealed significant abnormalities."
```

### Medical terms format

The medical terms file is a plain text file (e.g., a `.txt` file) with one term per line. Do not include a column header, as this will be interpreted as a medical term. It is used with the `--medical-terms` option to compute the Medical Term Recall (MTR) metric, which measures how many of the listed terms were correctly transcribed.

```
amoxicillin
atrial fibrillation
colonoscopy
deep vein thrombosis
hypertension
...
```


## Understanding the Report

> **See it in action:** The [`example/`](example/) folder contains sample input files and a [pre-generated report](https://corticph.github.io/corti-canal/) you can open in your browser.

The generated HTML report is fully self-contained (no external dependencies) and can be opened in any browser. It has two main sections:

### Summary

The summary section contains two tables side by side:

#### Dataset Metrics

<table>
<colgroup>
  <col width="240">
  <col>
</colgroup>
<tr><th>Metric</th><th>What it measures</th></tr>
<tr><td><strong>Word Error Rate (WER)</strong></td><td>The proportion of words the model got wrong — whether by misspelling them, adding extra words, or leaving words out. A WER of 0% means every word was correct; 6% means roughly 6 in 100 words had an error. <strong>Lower is better.</strong></td></tr>
<tr><td><strong>Character Error Rate (CER)</strong></td><td>Like WER, but counted per character instead of per word. This gives a more fine-grained view: a single-letter typo (e.g. "amoxicillin" → "amoxicilin") counts as one full word error in WER but only a small character error in CER. <strong>Lower is better.</strong></td></tr>
<tr><td><strong>Medical Term Recall (MTR)</strong></td><td>The proportion of medical terms from your keyword list that the model transcribed correctly. 100% means every term was captured. Only shown when the <code>--medical-terms</code> option is used. <strong>Higher is better.</strong></td></tr>
</table>

#### Dataset Summary

<table>
<colgroup>
  <col width="340">
  <col>
</colgroup>
<tr><th>Field</th><th>What it shows</th></tr>
<tr><td><strong>Number of examples</strong></td><td>How many transcript pairs were evaluated.</td></tr>
<tr><td><strong>Number of reference words / characters</strong></td><td>Total words and characters in the ground truth.</td></tr>
<tr><td><strong>Number of generated words / characters</strong></td><td>Total words and characters in the model output.</td></tr>
</table>


### Examples (Word Alignments)

Below the summary, the report lists every transcript pair with a word-level alignment visualization. Each example shows two rows:

- **Ref.** -- the ground-truth **reference** transcript
- **Gen.** -- the model-**generated** transcript

Words are color-coded to show the alignment result:

<table>
<colgroup>
  <col width="90">
  <col width="130">
  <col>
</colgroup>
<tr><th>Color</th><th>Label</th><th>Meaning</th></tr>
<tr><td>Black</td><td><strong>Correct</strong></td><td>The word was transcribed correctly.</td></tr>
<tr><td>Orange</td><td><strong>Misspelling</strong></td><td>The model produced a different word than the reference.</td></tr>
<tr><td>Teal</td><td><strong>Extra Word</strong></td><td>The model inserted a word that is not in the reference.</td></tr>
<tr><td>Red</td><td><strong>Missing Word</strong></td><td>A reference word was missing from the model output.</td></tr>
<tr><td>Grey</td><td><strong>Padding</strong></td><td>Visual padding to keep the reference and hypothesis rows aligned.</td></tr>
<tr><td>Blue box</td><td><strong>Medical Term</strong></td><td>Indicates a designated medical term for tracking recall. Only shown when the <code>--medical-terms</code> option is used.</td></tr>
</table>

This visualization makes it easy to spot patterns -- for example, if the model consistently misspells certain medical terms or drops words at the end of sentences.

## Normalization

By default, Canal normalizes both reference and generated text before computing metrics and alignments. This ensures that superficial differences in casing, punctuation, or accented characters don't inflate error rates. You can disable this with `--disable-normalization`.

The normalization pipeline applies the following steps in order:

1. **Unicode NFC composition** -- Decomposes and recomposes Unicode characters into their canonical composed form (e.g. `e` + combining acute accent becomes `é`).
2. **Tokenization** -- Splits text into words. Punctuation at the boundaries of words is stripped, while internal punctuation is preserved (e.g. "don't" stays as one token). Hyphens and forward slashes act as word boundaries.
3. **Lowercasing** -- Converts all characters to lowercase.
4. **Latin transliteration** -- Converts accented Latin letters to their ASCII equivalents (e.g. `é` → `e`, `ñ` → `n`, `ü` → `u`). Non-Latin scripts (Greek, Cyrillic, etc.) are left unchanged. See [anyascii.com](https://anyascii.com/) for an interactive demo of how this kind of transliteration works.

## Limitations

- **Latin script only.** The normalization pipeline is designed for Latin script languages. Evaluating non-Latin script language data may lead to unexpected results.
- **Overlapping medical terms are counted multiple times.** If terms in the medical terms list overlap (e.g. "blood" and "blood sugar"), each match is counted independently for Medical Term Recall metric.
