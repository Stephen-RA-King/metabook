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


def text_block(string: str) -> str:
    """Formats a string into text blocks based on a specified line length.

    Args:
        string (str): The input string to be formatted into text blocks.

    Returns:
        str: The formatted string with line breaks based on the configured line length.

    Notes:
        This function formats the input string into text blocks, ensuring that each line
        does not exceed the configured line length (as specified in
        'config.LINE_LENGTH'). It breaks the string into lines, adding line breaks
        ('\n') to ensure that each line respects the maximum line length. The resulting
        formatted string is returned.
    """
    result = []
    final_result = ""
    current_line = ""
    words = string.split()
    for word in words:
        if len(current_line) + len(word) + 1 <= config.LINE_LENGTH:
            current_line = "".join([current_line, " ", word])
        else:
            result.append(current_line)
            current_line = word
    if current_line:
        result.append(current_line)
    for line in result:
        final_result = "".join([final_result, "\n", line])
    return final_result.lstrip()


def find_isbn_in_pdf(pdf_file: Path) -> list[str]:
    """Extracts ISBNs from a PDF file using multiple regex patterns.

    Args:
        pdf_file (Path): The Path object representing the PDF file.

    Returns:
        List[str]: A list of ISBNs found in the PDF.

    Note:
        This function uses two regex patterns to search for ISBNs in the PDF.
        It stops searching after a specified number of pages
        (config.SEARCH_PAGES_ISBN).
    """
    isbn_list = []
    pattern1 = re.compile(r"(?i)ISBN(?:-13)?\D*(\d(?:\W*\d){12})", re.M)
    pattern2 = re.compile(
        r"(?:ISBN(?:-13)?:? )?(?=[0-9]{13}$|(?=(?:[0-9]+[- ]){4})[- 0-9]"
        r"{17}$)97[89][- ]?[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[0-9]",
        re.M,
    )

    patterns = (pattern1, pattern2)
    """
    def get_isbn(pat):
        isbns = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for count, page in enumerate(pdf.pages):
                    print(f"page: {count}", end='')
                    text = page.extract_text()
                    matches = pat.findall(text)
                    if matches:
                        isbns.extend(matches)
                        break
                    if count > config.SEARCH_PAGES:
                        break
        except (ValueError, TypeError, KeyError):
            print("An error has occurred whilst trying to find the ISBN")
        return isbns
    """

    def get_isbn(pat) -> list[str]:  # type: ignore
        isbns = []
        try:
            with open(pdf_file, "rb") as pdf:
                pdf_reader = Reader(pdf)
                num_pages = len(pdf_reader.pages)
                for page_number in range(num_pages):
                    page = pdf_reader.pages[page_number]
                    text = page.extract_text()
                    matches = pat.findall(text)
                    if matches:
                        isbns.extend(matches)
                        break
                    if page_number > config.SEARCH_PAGES_ISBN:
                        break
        except (ValueError, TypeError, KeyError, IndexError, PdfReadError):
            print("An error has occurred whilst trying to find the ISBN")
        return isbns

    for index, pattern in enumerate(patterns):
        print(f"using pattern {index + 1}")
        isbn_list = get_isbn(pattern)
        if isbn_list:
            break

    return isbn_list


def publisher_find(book: Path) -> Optional[str]:
    """Finds the publisher of a PDF book.

    Args:
        book (Path): The path to the PDF book.

    Returns:
        str: The found publisher's name, if identified.

    Notes:
        This function attempts to find the publisher of the provided PDF book.
        It first checks if any known publishers' names are in the book's filename.
        If not found, it searches through the text content of the book's pages
        using pdfplumber, returning the first identified publisher.

        If an error occurs during the search process, such as ValueError,
        TypeError, or KeyError, it prints an error message indicating the issue.
    """
    for publisher in publishers:
        if publisher in book.name:
            return publisher
    try:
        with pdfplumber.open(book) as pdf:
            for count, page in enumerate(pdf.pages):
                text = page.extract_text()
                for publisher in publishers:
                    if publisher in text:
                        return publisher
                if count > config.SEARCH_PAGES_PUB:
                    break
    except (ValueError, TypeError, KeyError):
        print("An error has occurred whilst trying to find the publisher")
    return None


def fetch_book_metadata(isbn: str) -> dict:
    """Fetches book metadata from the Google Books API based on the provided ISBN.

    Args:
        isbn (str): The ISBN (International Standard Book Number) of the book.

    Returns:
        dict: A dictionary containing the fetched book metadata. The keys include:
              - "TITLE": Title of the book.
              - "SUBTITLE": Subtitle of the book (if available, otherwise "None").
              - "AUTHORS": List of authors of the book.
              - "DATE": Publication year of the book (first 4 characters of the full
                date, or "None" if not available).
              - "PUBLISHER": Publisher of the book, with possible mapping applied.
              - "ISBN": The provided ISBN.

    Note:
        This function queries the Google Books API using the provided ISBN to
        retrieve book metadata. The "PUBLISHER" field may undergo mapping based on
        the `publisher_mapping` dictionary.
    """
    meta = {}
    # url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    url = book_apis[config.API].format(isbn=isbn)
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                metadata = data["items"][0]["volumeInfo"]
                if metadata:
                    meta["TITLE"] = metadata.get("title", "None")
                    meta["SUBTITLE"] = metadata.get("subtitle", "None")
                    if config.GET_DESCRIPTION:
                        meta["DESCRIPTION"] = text_block(
                            metadata.get("description", "None")
                        )
                    meta["AUTHORS"] = metadata.get("authors", [])
                    meta["DATE"] = metadata.get("publishedDate", "None")[:4]
                    publisher = metadata.get("publisher", "None")
                    if publisher in publisher_mapping:
                        meta["PUBLISHER"] = publisher_mapping[publisher]
                    else:
                        meta["PUBLISHER"] = publisher
                    meta["ISBN"] = isbn

    except RequestException:
        print("An error occurred whilst getting book metadata")
    return meta


def main():  # type: ignore
    args, parser = _parse_args(sys.argv[1:])

    if args.folder[0] == ".":
        folder = Path(os.getcwd())
    else:
        folder = Path(args.folder[0])
    if args.recurse:
        config.RECURSE = True
    if args.all:
        config.SKIP_EXISTING = False
    if args.dryrun:
        config.DRYRUN = True
    if args.log:
        config.HARDCOPY = True

    print(folder)

    if config.HARDCOPY_FILE.exists():
        config.HARDCOPY_FILE.unlink()
    try:
        books: list[Path] = find_books(folder)
        if books:
            for book in books:
                output(old_name=book.name)
                if config.SKIP_EXISTING and book.name.startswith("["):
                    output(skip=True)
                    continue
                else:
                    isbn_numbers: list[str] = find_isbn_in_pdf(book)
                    isbn_numbers = sanitize_isbn(isbn_numbers)
                    if isbn_numbers:
                        output(isbn_list=isbn_numbers)
                        isbn_number: str = isbn_numbers[0]
                        meta: dict[str, str] = fetch_book_metadata(isbn_number)
                        if meta:
                            if meta["PUBLISHER"] == "None":
                                found_publisher = publisher_find(book)
                                meta["PUBLISHER"] = (
                                    found_publisher
                                    if found_publisher is not None
                                    else "None"
                                )
                            new_name: str = render_template(meta)
                            new_name = normalize_filename(new_name)
                            output(new_name=new_name)
                            if config.HARDCOPY:
                                hardcopy(book.name, isbn_numbers, new_name)
                            if config.DRYRUN and meta:
                                continue
                            else:
                                write_metadata(book, new_name)
                                update_filename(book, new_name)
                        else:
                            output(no_meta=True)
                    else:
                        output(no_isbn=True)
        else:
            print("No books found")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    SystemExit(main())
