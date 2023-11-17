#!/usr/bin/env python3
"""Top-level package for metabook."""
# Core Library modules
import logging.config
from importlib.resources import as_file, files

# Third party modules
import yaml  # type: ignore

__title__ = "metabook"
__version__ = "0.1.0"
__author__ = "Stephen R A King"
__description__ = "rename and organize your pdf book collection"
__email__ = "sking.github@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright 2023 Stephen R A King"


LOGGING_CONFIG = """
version: 1
disable_existing_loggers: False
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    stream: ext://sys.stdout
    formatter: basic
  file:
    class: logging.FileHandler
    level: DEBUG
    filename: metabook.log
    encoding: utf-8
    formatter: timestamp

formatters:
  basic:
    style: "{"
    format: "{levelname:s}:{name:s}:{message:s}"
  timestamp:
    style: "{"
    format: "{asctime} - {levelname} - {name} - {message}"

loggers:
  init:
    handlers: [console, file]
    level: DEBUG
    propagate: False
"""

# logging.config.dictConfig(yaml.safe_load(LOGGING_CONFIG))
# logger = logging.getLogger("init")
