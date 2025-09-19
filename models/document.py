# models/document.py
from dataclasses import dataclass

@dataclass
class Document:
    name: str
    url: str
    original_filename: str
