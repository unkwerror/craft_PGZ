# models/tender.py
from dataclasses import dataclass
from typing import List
from .document import Document

@dataclass
class Tender:
    reg_number: str
    title: str
    price: str
    end_date: str
    documents: List[Document]
