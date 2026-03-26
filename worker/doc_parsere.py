import os
from io import BytesIO
from typing import List
from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract


def parse_document(file_obj, file_type: str) -> List[str]:
    """
    Universal parser:
    Handles BytesIO + file path + multiple file types
    """

    file_type = file_type.lower().replace(".", "")

    # -------------------
    # PDF
    # -------------------
    if file_type == "pdf":
        if isinstance(file_obj, BytesIO):
            file_obj.seek(0)
        reader = PdfReader(file_obj)

        text = []
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text.append(content)

        text = "\n".join(text)

    # -------------------
    # DOCX
    # -------------------
    elif file_type == "docx":
        if isinstance(file_obj, BytesIO):
            file_obj.seek(0)

        doc = Document(file_obj)
        text = "\n".join([p.text for p in doc.paragraphs])

    # -------------------
    # TXT
    # -------------------
    elif file_type == "txt":
        if isinstance(file_obj, BytesIO):
            file_obj.seek(0)
            text = file_obj.read().decode("utf-8", errors="ignore")
        else:
            with open(file_obj, "r", encoding="utf-8") as f:
                text = f.read()

    # -------------------
    # IMAGE (OCR)
    # -------------------
    elif file_type in ["png", "jpg", "jpeg"]:
        if isinstance(file_obj, BytesIO):
            file_obj.seek(0)
            image = Image.open(file_obj)
        else:
            image = Image.open(file_obj)

        text = pytesseract.image_to_string(image)

    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    # -------------------
    # CLEAN + CHUNK
    # -------------------
    text = " ".join(text.split())

    return chunk_text(text)

def chunk_text(text: str, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks