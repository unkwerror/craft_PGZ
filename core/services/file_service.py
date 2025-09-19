#core/services/file_service.py
import os
from pathlib import Path
from typing import Union


class FileService:
    """
    Сервис для работы с файловой системой.
    Все результаты работы приложения хранятся в одной базовой папке.
    """

    def __init__(self, base_dir: Union[str, Path] = "results"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_tender_dir(self, reg_number: str) -> Path:
        """
        Возвращает папку для тендера. Если нет — создаёт.
        """
        tender_dir = self.base_dir / reg_number
        tender_dir.mkdir(parents=True, exist_ok=True)
        return tender_dir

    def get_documents_dir(self, reg_number: str) -> Path:
        """
        Возвращает папку для документов тендера.
        """
        docs_dir = self.get_tender_dir(reg_number) / "documents"
        docs_dir.mkdir(parents=True, exist_ok=True)
        return docs_dir

    def save_text(self, reg_number: str, filename: str, text: str, encoding="utf-8") -> Path:
        """
        Сохраняет текстовый файл (например, HTML).
        """
        tender_dir = self.get_tender_dir(reg_number)
        filepath = tender_dir / filename
        with open(filepath, "w", encoding=encoding) as f:
            f.write(text)
        return filepath

    def save_binary(self, reg_number: str, filename: str, content: bytes) -> Path:
        """
        Сохраняет бинарный файл (например, документ).
        """
        docs_dir = self.get_documents_dir(reg_number)
        filepath = docs_dir / filename
        with open(filepath, "wb") as f:
            f.write(content)
        return filepath

    def list_tenders(self):
        """
        Возвращает список всех сохранённых тендеров.
        """
        return [p.name for p in self.base_dir.iterdir() if p.is_dir()]
