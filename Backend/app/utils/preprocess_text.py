import io
import logging
import re
from PyPDF2 import PdfReader
from docx import Document
from pdf2image import convert_from_bytes
import pytesseract

logger = logging.getLogger(__name__)

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
        doc = Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"

    elif extension.endswith(".txt"):
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT files must use UTF-8 encoding") from exc

    else:
        raise ValueError("Unsupported file type")

    return text


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
