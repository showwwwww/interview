from pathlib import Path

from .base import BaseReader, Section
from .docx_reader import DocxReader
from .pdf_reader import PdfReader
from .txt_reader import TxtReader

_READER_MAP: dict[str, type[BaseReader]] = {
    ".pdf": PdfReader,
    ".docx": DocxReader,
    ".txt": TxtReader,
}


def get_reader(filepath: str) -> BaseReader:
    ext = Path(filepath).suffix.lower()
    reader_cls = _READER_MAP.get(ext)
    if reader_cls is None:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported types: {', '.join(_READER_MAP)}"
        )
    return reader_cls()
