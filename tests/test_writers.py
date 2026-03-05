"""Tests for TXT, DOCX, and PDF writers."""

from pathlib import Path

from readers.base import Section
from writers.txt_writer import write_txt
from writers.docx_writer import write_docx
from writers.pdf_writer import write_pdf


def _sample_sections():
    return [
        Section(title="Overview", number="1", content="This is the overview section."),
        Section(title="Details", number="2", content="- Point one\n- Point two\n- Point three"),
    ]


class TestTxtWriter:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "out.txt"
        write_txt(_sample_sections(), str(out))
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "Overview" in text
        assert "Point one" in text

    def test_utf8_content(self, tmp_path):
        sections = [Section(title="Légal", number="1", content="Contrat général — résumé")]
        out = tmp_path / "utf8.txt"
        write_txt(sections, str(out))
        text = out.read_text(encoding="utf-8")
        assert "résumé" in text


class TestDocxWriter:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "out.docx"
        write_docx(_sample_sections(), str(out))
        assert out.exists()
        assert out.stat().st_size > 0

    def test_bullet_detection(self, tmp_path):
        sections = [Section(title="Bullets", number="1", content="- A\n- B\n- C")]
        out = tmp_path / "bullets.docx"
        write_docx(sections, str(out))
        assert out.exists()


class TestPdfWriter:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "out.pdf"
        write_pdf(_sample_sections(), str(out))
        assert out.exists()
        assert out.stat().st_size > 0

    def test_bullet_content(self, tmp_path):
        sections = [Section(title="Summary", number="1", content="- Fact A\n- Fact B")]
        out = tmp_path / "summary.pdf"
        write_pdf(sections, str(out))
        assert out.exists()
