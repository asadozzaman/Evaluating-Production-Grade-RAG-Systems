from dataclasses import dataclass
from pathlib import Path
import csv
import io
import re

from app.config import BACKEND_ROOT, get_settings
from app.models import SourceDocument


@dataclass(frozen=True)
class DocumentChunk:
    source_document_id: int
    source_title: str
    text: str
    section_reference: str


TEXT_EXTENSIONS = {".txt", ".md"}


def extract_document_text(document: SourceDocument) -> str:
    if document.source_kind == "uri":
        return ""
    if not document.storage_path:
        return ""

    upload_root = Path(get_settings().upload_dir)
    if not upload_root.is_absolute():
        upload_root = BACKEND_ROOT / upload_root
    path = upload_root / document.storage_path
    if not path.is_file():
        return ""

    extension = path.suffix.lower()
    if extension in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="ignore")
    if extension == ".csv":
        return extract_csv_text(path)
    if extension == ".docx":
        return extract_docx_text(path)
    if extension == ".pdf":
        return extract_pdf_text(path)
    return ""


def extract_csv_text(path: Path) -> str:
    content = path.read_text(encoding="utf-8", errors="ignore")
    output = io.StringIO()
    for row in csv.reader(io.StringIO(content)):
        output.write(" | ".join(cell.strip() for cell in row if cell.strip()))
        output.write("\n")
    return output.getvalue()


def extract_docx_text(path: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        return ""

    document = Document(path)
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(page.strip() for page in pages if page.strip())


def chunk_document(document: SourceDocument, text: str, chunk_size: int = 900, overlap: int = 140) -> list[DocumentChunk]:
    normalized = normalize_whitespace(text)
    if not normalized:
        return []

    chunks: list[DocumentChunk] = []
    start = 0
    index = 1
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            sentence_end = normalized.rfind(".", start, end)
            if sentence_end > start + chunk_size // 2:
                end = sentence_end + 1

        chunk_text = normalized[start:end].strip()
        if chunk_text:
            chunks.append(
                DocumentChunk(
                    source_document_id=document.id,
                    source_title=document.title,
                    text=chunk_text,
                    section_reference=f"{document.title} - chunk {index}",
                )
            )
            index += 1

        if end >= len(normalized):
            break
        start = max(0, end - overlap)

    return chunks


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
