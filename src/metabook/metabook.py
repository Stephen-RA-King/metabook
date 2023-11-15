# Core Library modules
import os
import re
import sys
from pathlib import Path

# Third party modules
import pdfplumber
import requests
from pdfrw import PdfDict, PdfReader, PdfWriter
from PyPDF2 import PdfReader as Reader
from PyPDF2.errors import PdfReadError
from requests import RequestException

# Local modules
from .cli import _parse_args
from .config import config
from .publishers import publisher_mapping, publishers

book_apis = {
    "google": "https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}",
}


def find_books(directory: Path) -> list[Path]:
    """Finds all PDF files in the specified directory.

    Args:
        directory (Path): The Path object representing the directory to search for
        PDF files.

    Returns:
        List[Path]: A list of Path objects representing the matching PDF files.
    """
    directory_path = Path(directory)
    matching_files = []
    if config.RECURSE:
        for file_path in directory_path.rglob("*" + ".pdf"):
            matching_files.append(file_path)
    else:
        for file_path in directory_path.glob("*" + ".pdf"):
            matching_files.append(file_path)
    return matching_files
