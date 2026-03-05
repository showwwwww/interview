"""Integration test: end-to-end process_file with mocked LLM."""

from pathlib import Path
from unittest.mock import MagicMock

from main import process_file, discover_files


class TestProcessFile:
    def test_txt_to_docx(self, sample_txt_file, tmp_output, mock_llm_client):
        tmp_output.mkdir(parents=True, exist_ok=True)
        process_file(sample_txt_file, tmp_output, "docx", mock_llm_client)
        outputs = list(tmp_output.iterdir())
        assert len(outputs) >= 2
        names = [f.name for f in outputs]
        assert any("plainEnglish" in n for n in names)
        assert any("summary" in n for n in names)
        assert all(n.endswith(".docx") for n in names)

    def test_txt_to_txt(self, sample_txt_file, tmp_output, mock_llm_client):
        tmp_output.mkdir(parents=True, exist_ok=True)
        process_file(sample_txt_file, tmp_output, "txt", mock_llm_client)
        outputs = list(tmp_output.iterdir())
        assert any(f.name.endswith(".txt") for f in outputs)

    def test_txt_to_pdf(self, sample_txt_file, tmp_output, mock_llm_client):
        tmp_output.mkdir(parents=True, exist_ok=True)
        process_file(sample_txt_file, tmp_output, "pdf", mock_llm_client)
        outputs = list(tmp_output.iterdir())
        assert any(f.name.endswith(".pdf") for f in outputs)

    def test_txt_to_all(self, sample_txt_file, tmp_output, mock_llm_client):
        tmp_output.mkdir(parents=True, exist_ok=True)
        process_file(sample_txt_file, tmp_output, "all", mock_llm_client)
        outputs = list(tmp_output.iterdir())
        extensions = {f.suffix for f in outputs}
        assert ".docx" in extensions
        assert ".txt" in extensions
        assert ".pdf" in extensions

    def test_docx_to_docx(self, sample_docx_file, tmp_output, mock_llm_client):
        tmp_output.mkdir(parents=True, exist_ok=True)
        process_file(sample_docx_file, tmp_output, "docx", mock_llm_client)
        outputs = list(tmp_output.iterdir())
        assert len(outputs) >= 2


class TestDiscoverFiles:
    def test_single_file(self, sample_txt_file):
        files = discover_files(str(sample_txt_file))
        assert len(files) == 1

    def test_directory(self, tmp_path, sample_txt_file):
        import shutil
        target = tmp_path / "docs"
        target.mkdir()
        shutil.copy(sample_txt_file, target / "doc1.txt")
        shutil.copy(sample_txt_file, target / "doc2.txt")
        files = discover_files(str(target))
        assert len(files) == 2

    def test_unsupported_file_raises(self, tmp_path):
        p = tmp_path / "data.csv"
        p.touch()
        import pytest
        with pytest.raises(ValueError):
            discover_files(str(p))

    def test_missing_path_raises(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            discover_files(str(tmp_path / "nonexistent"))
