import io
import logging
import re
from PyPDF2 import PdfReader
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pdf2image import convert_from_bytes
import pytesseract

logger = logging.getLogger(__name__)


def _extract_docx_sections(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    sections = []
    current_title = None
    current_lines = []

    def flush_section():
        section_text = "\n".join(current_lines).strip()
        if section_text:
            sections.append((current_title, section_text))

    for element in doc.element.body.iterchildren():
        if element.tag.endswith("}p"):
            paragraph = Paragraph(element, doc)
            paragraph_text = paragraph.text.strip()
            if not paragraph_text:
                continue
            style_name = paragraph.style.name if paragraph.style else ""
            if style_name == "Title" or style_name.startswith("Heading"):
                flush_section()
                current_title = paragraph_text
                current_lines = []
            else:
                current_lines.append(paragraph_text)
        elif element.tag.endswith("}tbl"):
            table = Table(element, doc)
            for row in table.rows:
                cells = []
                for cell in row.cells:
                    cell_text = clean_text(cell.text)
                    if cell_text and (not cells or cell_text != cells[-1]):
                        cells.append(cell_text)
                if cells:
                    current_lines.append(" | ".join(cells))

    flush_section()
    return sections


def extract_text(file_bytes, filename, max_pages=200):
    text = ""
    extension = filename.lower()
    if extension.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        if len(reader.pages) > max_pages:
            raise ValueError(f"PDF exceeds the {max_pages}-page limit")
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            else:
                logger.info("Using OCR for PDF page %s", page_num + 1)
                # Convert this page to image and extract text with OCR
                images = convert_from_bytes(file_bytes, first_page=page_num+1, last_page=page_num+1)
                for image in images:
                    text += pytesseract.image_to_string(image, lang="eng") + "\n"

    elif extension.endswith(".docx"):
        sections = _extract_docx_sections(file_bytes)
        text = "\n".join(
            "\n".join(part for part in (title, section_text) if part)
            for title, section_text in sections
        )

    elif extension.endswith(".txt"):
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT files must use UTF-8 encoding") from exc

    else:
        raise ValueError("Unsupported file type")

    return text


def extract_sections(file_bytes, filename, max_pages=200):
    if filename.lower().endswith(".docx"):
        return _extract_docx_sections(file_bytes)
    return [(None, extract_text(file_bytes, filename, max_pages=max_pages))]


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # normalize spaces/newlines
    return text.strip()

def chunk_text(text, chunk_size=300, overlap=40):
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk size or overlap")
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i+chunk_size])
        if chunk:
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks


def chunk_sections(sections, chunk_size=300, overlap=40):
    section_chunks = []
    for title, text in sections:
        cleaned_text = clean_text(text)
        if not cleaned_text:
            continue
        chunks = chunk_text(cleaned_text, chunk_size=chunk_size, overlap=overlap)
        for chunk in chunks:
            if title:
                chunk = f"{title}: {chunk}"
            section_chunks.append((chunk, title))
    return section_chunks
