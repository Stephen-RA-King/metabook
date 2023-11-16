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


def update_filename(book: Path, new_name: str) -> None:
    """Updates the filename of a PDF file.

    Args:
        book (Path): The original path to the PDF file.
        new_name (str): The new name for the PDF file (without extension).

    Raises:
        FileExistsError: If the file with the new name already exists.

    Notes:
        This function updates the filename of the provided PDF file by appending
        '.pdf' to the new name. If the file with the updated name already exists,
        it raises a FileExistsError and prints an error message indicating the
        conflict.
    """
    new_name = "".join([new_name, ".pdf"])
    new_path = book.with_name(new_name)
    try:
        book.rename(new_path)
    except FileExistsError:
        print(f"Cannot rename file. File: {new_name} already exists")


def write_metadata(book: Path, new_name: str) -> None:
    """Writes metadata to a PDF file.

    Args:
        book (Path): The path to the PDF file.
        new_name (str): The new title to set for the PDF.

    Raises:
        ValueError: If an issue occurs with the PDF value.
        AttributeError: If an attribute error happens while updating metadata.
        PermissionError: If permission-related issues occur while writing metadata.

    Notes:
        This function updates the metadata (Title, Subject, Author, Keywords, Creator,
        Producer) of the provided PDF file with the new title. If any errors occur
        during the process, it catches and prints an error message.
    """
    metadata = PdfDict(
        Title=new_name,
        Subject="",
        Author="",
        Keywords="",
        Creator="",
        Producer="",
    )
    try:
        pdf_reader = PdfReader(book)
        pdf_reader.Info.update(metadata)
        PdfWriter().write(book, pdf_reader)
    except (ValueError, AttributeError, PermissionError):
        print("An error occurred writing metadata")
