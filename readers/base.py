from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Section:
    title: str
    number: str
    content: str


class BaseReader(ABC):
    @abstractmethod
    def read(self, filepath: str) -> list[Section]:
        """Read a document and return a list of Section objects."""
        ...
