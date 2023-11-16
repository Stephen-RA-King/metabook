#!/usr/bin/env python3
# Core Library modules
import os
import re
import sys
from pathlib import Path
from typing import Optional

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


def sanitize_isbn(isbn_list: list[str]) -> list[str]:
    """Cleans and sanitizes a list of ISBN (International Standard Book Number) strings.

    Args:
        isbn_list (List[str]): A list of ISBN strings that may contain non-numeric
        characters.

    Returns:
        List[str]: A list of sanitized ISBN strings with non-numeric characters removed.
                   Only ISBN strings with exactly 13 numeric characters are included.
    """
    sanitized_list = []
    for isbn in isbn_list:
        sanitized_isbn = re.sub(r"\D", "", isbn)
        if len(sanitized_isbn) == 13:
            sanitized_list.append(sanitized_isbn)
    return sanitized_list


def normalize_filename(name: str) -> str:
    """Normalizes a given filename by removing invalid characters, replacing certain
    characters, and applying additional formatting options based on configuration
    settings.

    Args:
        name (str): The input filename to be normalized.

    Returns:
        str: The normalized filename.

    Configuration Options:
        - ALLOW_SPACE (bool): If False, replaces spaces with underscores.
        - LOWERCASE_ONLY (bool): If True, converts the filename to lowercase.
    """
    name = "".join(c for c in name if c not in r'\/*?"<>|')
    # name = name.title()
    name = name.replace(":", "-")
    if config.ALLOW_SPACE is False:
        name = name.replace(" ", "_")
    if config.LOWERCASE_ONLY is True:
        name = name.lower()
    return name


def hardcopy(book: str, isbn_list: list, new_name: str) -> None:
    """Writes information about a book to a 'hardcopy.txt' file.

    Args:
        book (str): The name or identifier of the original book.
        isbn_list (list): A list of ISBNs associated with the book.
        new_name (str): The new name or identifier for the book.

    Returns:
        None

    Notes:
        This function appends information about a book, such as ISBNs, the original
        book name, and the new book name to a 'hardcopy.txt' file. It opens the file
        in append mode, writes the information in a formatted manner, and closes the
        file.
    """
    with open("hardcopy.txt", mode="a", encoding="utf-8") as f:
        lines_to_write = f"{'*' * 90}\n{isbn_list}\nOld: {book}\nNew: {new_name}\n"
        f.write(lines_to_write)


def output(
    old_name: Optional[str] = None,
    skip: bool = False,
    isbn_list: Optional[list[str]] = None,
    new_name: Optional[str] = None,
    no_meta: bool = False,
    no_isbn: bool = False,
) -> None:
    """Generates output based on specified parameters."""

    def the_end():  # type: ignore
        print(f"{'*' * 90}")

    if old_name:
        print(f"processing: {old_name}")
    if skip:
        print("...skipping previously processed file")
        the_end()
    if isbn_list:
        print(f"using isbns: {isbn_list}")
    if new_name:
        print(f"new name: {new_name}")
        the_end()
    if no_meta:
        print("meta information cannot be found")
        the_end()
    if no_isbn:
        print("isbn ids cannot be found")
        the_end()
