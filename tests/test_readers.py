"""Tests for document readers."""

from readers.txt_reader import TxtReader
from readers.docx_reader import DocxReader
from readers import get_reader

import pytest


class TestTxtReader:
    def test_reads_sections_by_heading(self, sample_txt_file):
        reader = TxtReader()
        sections = reader.read(str(sample_txt_file))
        assert len(sections) >= 3
        assert sections[0].title.startswith("ARTICLE I")
        assert "terms and conditions" in sections[0].content

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.txt"
        p.write_text("", encoding="utf-8")
        reader = TxtReader()
        sections = reader.read(str(p))
        assert len(sections) == 1
        assert sections[0].content == ""

    def test_no_headings_falls_back_to_single_section(self, tmp_path):
        p = tmp_path / "plain.txt"
        p.write_text("Just some plain text without any headings.", encoding="utf-8")
        reader = TxtReader()
        sections = reader.read(str(p))
        assert len(sections) == 1
        assert "plain text" in sections[0].content


class TestDocxReader:
    def test_reads_headings_as_sections(self, sample_docx_file):
        reader = DocxReader()
        sections = reader.read(str(sample_docx_file))
        assert len(sections) >= 2
        titles = [s.title for s in sections]
        assert "Agreement Overview" in titles
        assert "Obligations" in titles

    def test_empty_docx(self, tmp_path):
        from docx import Document

        doc = Document()
        p = tmp_path / "empty.docx"
        doc.save(str(p))
        reader = DocxReader()
        sections = reader.read(str(p))
        assert len(sections) == 1


class TestGetReader:
    def test_txt_extension(self, tmp_path):
        p = tmp_path / "test.txt"
        p.touch()
        reader = get_reader(str(p))
        assert isinstance(reader, TxtReader)

    def test_docx_extension(self, tmp_path):
        p = tmp_path / "test.docx"
        p.touch()
        reader = get_reader(str(p))
        assert isinstance(reader, DocxReader)

    def test_unsupported_extension(self, tmp_path):
        p = tmp_path / "test.csv"
        p.touch()
        with pytest.raises(ValueError, match="Unsupported"):
            get_reader(str(p))
