# Legal Document Converter

A Python CLI tool that converts legal documents into two reader-friendly formats using an LLM:

- **Plain English** — word-for-word conversion preserving all context, understandable by non-legal readers.
- **Bullet-point Summary** — concise bullet-point summary of each section, preserving legal meaning.

## Supported Formats

| Direction | Formats |
|-----------|---------|
| **Input** | PDF, DOCX, TXT |
| **Output** | DOCX, TXT, PDF |

## Setup

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and set your OpenAI API key
```

## Usage

```bash
# Convert a single file (output as DOCX by default)
python main.py --input path/to/document.pdf

# Convert all files in a folder
python main.py --input ./input --output ./output

# Choose output format
python main.py -i ./input -f txt       # TXT only
python main.py -i ./input -f pdf       # PDF only
python main.py -i ./input -f both      # TXT + DOCX
python main.py -i ./input -f all       # TXT + DOCX + PDF

# Parallel processing (multiple files at once)
python main.py -i ./input --parallel          # 4 workers (default)
python main.py -i ./input --workers 8         # custom worker count

# Launch the GUI
python gui.py
```

### CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--input`, `-i` | Input file or folder (required) | — |
| `--output`, `-o` | Output folder | `./output` |
| `--format`, `-f` | Output format: `txt`, `docx`, `pdf`, `both`, `all` | `docx` |
| `--parallel` | Enable parallel file processing | off |
| `--workers`, `-w` | Number of parallel workers (implies `--parallel`) | `4` |

### Output Files

For each input document, two output files are generated:

```
DocumentName_plainEnglish.docx
DocumentName_summary.docx
```

A `quality_report.txt` is written to the output folder if any quality issues are detected (empty responses, suspiciously short output, missing section titles, truncated text).

## Configuration

Environment variables (set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `MODEL_NAME` | `gpt-4o-mini` | LLM model to use |
| `MAX_TOKENS` | `3000` | Max tokens per section chunk |
| `MAX_RETRIES` | `3` | API retry attempts on failure |

## Project Structure

```
legal-doc-converter/
├── main.py                      # CLI entry point
├── config.py                    # Environment and configuration
├── requirements.txt             # Python dependencies
├── readers/
│   ├── base.py                  # Section dataclass, BaseReader ABC
│   ├── pdf_reader.py            # PDF input (pdfplumber + PyPDF2 fallback)
│   ├── docx_reader.py           # DOCX input (python-docx)
│   └── txt_reader.py            # Plain text input
├── gui.py                       # Tkinter GUI
├── processing/
│   ├── section_splitter.py      # Heading detection and token-bounded splitting
│   ├── prompt_builder.py        # LLM prompt templates
│   ├── llm_client.py            # OpenAI API client with retry logic
│   ├── post_processor.py        # Clean markdown artifacts from LLM output
│   └── quality_checker.py       # Quality checks and quality_report.txt
├── writers/
│   ├── docx_writer.py           # DOCX output
│   ├── txt_writer.py            # TXT output
│   └── pdf_writer.py            # PDF output
├── utils/
│   └── logger.py                # Console + file logging
└── tests/                       # pytest test suite
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Logging

All processing steps and errors are logged to both the console (INFO level) and `converter.log` (DEBUG level).
