"""Document loader pipeline for EKIP supporting PDF, DOCX, TXT, CSV, XLSX, PPTX, MD, JSON, PNG, JPEG, TIFF, and OCR.

Changes made:
- Integrated Loguru logging for all document loading and parsing steps.
- Added progress callback parameters (parsing_cb, chunking_cb) for granular ingestion updates.
- Added support for TIFF, BMP, JPEG, PNG image OCR loading via pytesseract and PIL.
"""

import os
import json
import re
from typing import List, Callable, Optional
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.logger import get_logger

logger = get_logger("core.loader")


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename to prevent path traversal attacks."""
    cleaned = re.sub(r'[^\w\.\-]', '_', os.path.basename(filename))
    return cleaned or "uploaded_file"


class DocumentLoader:
    """Multi-format document loader with OCR capabilities and progress reporting."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def load_file(
        self,
        file_path: str,
        parsing_cb: Optional[Callable[[float, str], None]] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        **kwargs,
    ) -> List[Document]:
        cb = parsing_cb or progress_cb or kwargs.get("callback")
        file_path = os.path.normpath(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        base = sanitize_filename(file_path)

        logger.info(f"Loading document '{base}' (extension: {ext})")
        if cb:
            cb(0.3, f"Parsing {base}...")

        docs: List[Document] = []
        if ext == ".pdf":
            docs = self._load_pdf(file_path, base)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"]:
            docs = self._load_image(file_path, base)
        elif ext == ".docx":
            try:
                docs = Docx2txtLoader(file_path).load()
            except Exception as e:
                logger.error(f"Error parsing DOCX '{base}': {e}")
                docs = [Document(page_content=f"Error reading docx: {e}", metadata={"source": base})]
        elif ext == ".txt":
            try:
                docs = TextLoader(file_path, encoding="utf-8").load()
            except Exception:
                docs = TextLoader(file_path, encoding="latin-1").load()
        elif ext == ".csv":
            try:
                docs = CSVLoader(file_path, encoding="utf-8").load()
            except Exception:
                docs = CSVLoader(file_path, encoding="latin-1").load()
        elif ext == ".md":
            try:
                docs = TextLoader(file_path, encoding="utf-8").load()
            except Exception:
                docs = TextLoader(file_path, encoding="latin-1").load()
        elif ext == ".json":
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            docs = [Document(page_content=json.dumps(data, indent=2), metadata={"source": base})]
        elif ext in [".xlsx", ".xls"]:
            docs = self._load_excel(file_path, base)
        elif ext == ".pptx":
            docs = self._load_pptx(file_path, base)
        else:
            try:
                docs = TextLoader(file_path, encoding="utf-8").load()
            except Exception:
                docs = [Document(page_content=f"Unsupported format: {ext}", metadata={"source": base})]

        for d in docs:
            d.metadata["source_file"] = base
            d.metadata.setdefault("page_number", d.metadata.get("page", 0) + 1)
            d.metadata.setdefault("ocr", False)

        if cb:
            cb(0.6, f"Parsed {len(docs)} pages/sections from {base}")

        logger.info(f"Parsed {len(docs)} pages from '{base}'")
        return docs

    def _load_pdf(self, file_path: str, base: str) -> List[Document]:
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            total_chars = sum(len(d.page_content) for d in docs)
            if total_chars < 100:
                logger.info(f"PDF '{base}' contains little text; attempting OCR fallback")
                ocr_docs = self._ocr_pdf(file_path, base)
                return ocr_docs if ocr_docs else docs
            for i, d in enumerate(docs):
                d.metadata["source_file"] = base
                d.metadata["page_number"] = d.metadata.get("page", i) + 1
                d.metadata["ocr"] = False
            return docs
        except Exception as e:
            logger.warning(f"PyPDFLoader failed for '{base}': {e}; using OCR fallback")
            return self._ocr_pdf(file_path, base)

    def _ocr_pdf(self, file_path: str, base: str) -> List[Document]:
        try:
            from pdf2image import convert_from_path
            import pytesseract

            images = convert_from_path(file_path)
            docs = []
            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img)
                if text.strip():
                    docs.append(Document(
                        page_content=text,
                        metadata={"source_file": base, "page": i, "page_number": i + 1, "ocr": True}
                    ))
            return docs if docs else [Document(page_content="[PDF content empty or unreadable via OCR]", metadata={"source_file": base})]
        except Exception as e:
            logger.error(f"PDF OCR failed for '{base}': {e}")
            return [Document(page_content=f"[PDF loader fallback error: {e}]", metadata={"source_file": base})]

    def _load_image(self, file_path: str, base: str) -> List[Document]:
        try:
            from PIL import Image
            import pytesseract

            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            return [Document(
                page_content=text if text.strip() else "[Image containing no extractable text]",
                metadata={"source_file": base, "page": 0, "page_number": 1, "ocr": True}
            )]
        except Exception as e:
            logger.error(f"Image OCR failed for '{base}': {e}")
            return [Document(page_content=f"[Image OCR error: {e}]", metadata={"source_file": base})]

    def _load_excel(self, file_path: str, base: str) -> List[Document]:
        try:
            from langchain_community.document_loaders import UnstructuredExcelLoader
            return UnstructuredExcelLoader(file_path).load()
        except Exception:
            try:
                import pandas as pd
                dfs = pd.read_excel(file_path, sheet_name=None)
                docs = []
                for sheet_name, df in dfs.items():
                    text = f"Sheet: {sheet_name}\n" + df.to_csv(index=False)
                    docs.append(Document(page_content=text, metadata={"source_file": base, "sheet": sheet_name}))
                return docs
            except Exception as e:
                return [Document(page_content=f"Error reading Excel: {e}", metadata={"source_file": base})]

    def _load_pptx(self, file_path: str, base: str) -> List[Document]:
        try:
            from langchain_community.document_loaders import UnstructuredPowerPointLoader
            return UnstructuredPowerPointLoader(file_path).load()
        except Exception as e:
            return [Document(page_content=f"Error reading PPTX: {e}", metadata={"source_file": base})]

    def chunk_documents(
        self,
        docs: List[Document],
        file_name: str,
        chunking_cb: Optional[Callable[[float, str], None]] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        **kwargs,
    ) -> List[Document]:
        cb = chunking_cb or progress_cb or kwargs.get("parsing_cb") or kwargs.get("callback")
        if cb:
            cb(0.7, f"Chunking document '{file_name}'...")

        import datetime
        doc_title = file_name.replace("_", " ").rsplit(".", 1)[0].title()
        doc_type = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "file"
        now_iso = datetime.datetime.now().isoformat()

        chunks = self.splitter.split_documents(docs)
        for i, c in enumerate(chunks):
            c.metadata.update({
                "chunk_id": f"{file_name}_{i}",
                "source_file": file_name,
                "filename": file_name,
                "document_id": file_name,
                "document_title": doc_title,
                "page_number": c.metadata.get("page_number", c.metadata.get("page", 1)),
                "upload_timestamp": c.metadata.get("upload_timestamp", now_iso),
                "document_type": doc_type,
            })


        if cb:
            cb(0.85, f"Created {len(chunks)} chunks for {file_name}")

        logger.info(f"Chunked '{file_name}' into {len(chunks)} text chunks.")
        return chunks
