# Legal Document Converter — Remaining Tasks

Based on the compliance review against **Python Test 2.pdf** requirements.

---

## Required

### 1. Add PDF Output Writer
- [x] Create `writers/pdf_writer.py` using `fpdf2`
- [x] Support section headings and body text with readable formatting
- [x] Handle bullet-point content (summary documents)
- [x] Add `"pdf"` as a `--format` choice in `main.py` CLI args
- [x] Wire `write_pdf()` into the `_write()` helper in `process_file()`
- [x] Add the PDF library to `requirements.txt`

### 2. Add LLM Output Post-Processing
- [x] Create `processing/post_processor.py`
- [x] Strip markdown artifacts from LLM responses (e.g. `**bold**`, `### headings`, code fences)
- [x] Normalize whitespace and blank lines
- [x] Verify section numbering in output matches the original section numbers
- [x] Integrate post-processing into `process_file()` between LLM response and write step

---

## Recommended

### 3. Improve PDF Reader Section Detection
- [x] Detect headings in PDF text (all-caps lines, numbered headings) inside `PdfReader` rather than returning a single section
- [x] Align PDF heading detection with the patterns already used by `TxtReader` and `section_splitter.py`

### 4. Add Tests
- [x] Create `tests/` directory with `conftest.py`
- [x] Unit tests for each reader (PDF, DOCX, TXT) with sample fixtures
- [x] Unit tests for `section_splitter.py` (heading detection, token splitting)
- [x] Unit tests for `prompt_builder.py`
- [x] Unit tests for `post_processor.py`
- [x] Unit tests for each writer (TXT, DOCX, PDF)
- [x] Integration test for end-to-end `process_file()` with a mocked LLM client
- [x] Add `pytest` to `requirements.txt`

### 5. Add README
- [x] Project overview and purpose
- [x] Setup instructions (venv, dependencies, `.env`)
- [x] Usage examples (CLI flags, input/output)
- [x] Supported file formats (input and output)
- [x] Project structure overview

### 6. Fix `.env.example`
- [x] Replace the real API key with a placeholder (`your-openai-api-key-here`)

---

## Optional Enhancements (from spec)

### 7. Parallel Processing
- [x] Process multiple files concurrently using `concurrent.futures.ThreadPoolExecutor`
- [x] Add `--workers` CLI flag to control concurrency (default: 1 for sequential)
- [x] Ensure logging remains coherent under parallelism

### 8. Quality Checks
- [x] Flag sections where the LLM response is suspiciously short relative to the input
- [x] Flag sections where the LLM response is empty or appears truncated
- [x] Log warnings for any flagged sections

### 9. GUI
- [x] Tkinter GUI for selecting input/output folders, format, and workers (`gui.py`)
