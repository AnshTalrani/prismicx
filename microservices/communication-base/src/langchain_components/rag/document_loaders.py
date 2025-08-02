"""Document loading utilities for the RAG system."""

from typing import List, Dict
from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    JSONLoader,
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

class DocumentLoader:
    """Loads and manages raw documents"""
    
    Stores:
    - Raw documents
    - Source files
    - Training data
    - Knowledge base content
    
    LOADER_MAP = {
        '.pdf': PyPDFLoader,
        '.json': JSONLoader,
        '.csv': CSVLoader,
        '.txt': TextLoader,
        '.md': UnstructuredMarkdownLoader
    }
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def load_directory(self, path: str) -> List:
        """Load all supported documents from a directory."""
        documents = []
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            ext = os.path.splitext(file)[1].lower()
            
            if ext in self.LOADER_MAP:
                loader = self.LOADER_MAP[ext](file_path)
                documents.extend(loader.load())
        
        return self.text_splitter.split_documents(documents) 