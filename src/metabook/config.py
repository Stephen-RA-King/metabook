#!/usr/bin/env python3

# Core Library modules
from pathlib import Path

# Third party modules
from jinja2 import Template


class Config:
    ALLOW_SPACE: bool = True
    API: str = "google"
    DRYRUN: bool = False
    ENGINE: str = "PyPDF2"
    GET_DESCRIPTION: bool = False
    HARDCOPY: bool = True
    HARDCOPY_FILE: Path = Path("hardcopy.txt")
    LINE_LENGTH: int = 80
    LOWERCASE_ONLY: bool = False
    MAX_FILEPATH_LENGTH: int = 255
    RECURSE: bool = False
    SEARCH_PAGES_ISBN: int = 40
    SEARCH_PAGES_PUB: int = 5
    SKIP_EXISTING: bool = True
    TITLE_LEN_MAX: int = 130
    TEMPLATE1: Template = Template(
        r"[{{ PUBLISHER }}] - {{ TITLE }} - {{ SUBTITLE }}  [{{ DATE }}] [{{ ISBN }}]"
    )
    TEMPLATE2: Template = Template(
        r"[{{ PUBLISHER }}] - {{ TITLE }} [{{ DATE }}] [{{ ISBN }}]"
    )


config = Config()
