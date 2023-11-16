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


def render_template(meta: dict[str, str]) -> str:
    """Renders a template based on metadata information.

    Args:
        meta (Dict[str, str]): A dictionary containing metadata information,
            with keys such as 'SUBTITLE' and 'TITLE'.

    Returns:
        str: The rendered template as a string.

    Notes:
        This function checks the provided metadata for 'SUBTITLE' and 'TITLE'.
        If 'SUBTITLE' is not 'None' and the combined length of 'TITLE' and 'SUBTITLE'
        along with the extra characters (' + 3') does not exceed the maximum
        title length specified in 'config.TITLE_LEN_MAX', it uses 'TEMPLATE1'
        to render the template based on the metadata. If the conditions are not met,
        it falls back to using 'TEMPLATE2' to render the template with the provided
         metadata.
    """
    if meta["SUBTITLE"] != "None":
        title_length = len(meta["TITLE"]) + len(meta["SUBTITLE"]) + 3
        if title_length <= config.TITLE_LEN_MAX:
            return config.TEMPLATE1.render(meta)
    return config.TEMPLATE2.render(meta)
