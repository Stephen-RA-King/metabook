from pathlib import Path
import pdfplumber
from PyPDF2 import PdfReader


book = Path(r"D:\DEVOPS PROJECT\BOOKS\Graphite, Grafana & Prometheus\learn-grafana-7-interactive-dashboards.pdf")

"""
with pdfplumber.open(book) as pdf:
    for count, page in enumerate(pdf.pages):
        print(f"page: {count}", end='')
        text = page.extract_text()
"""

with open(book, "rb") as pdf_file:
    pdf_reader = PdfReader(pdf_file)
    num_pages = len(pdf_reader.pages)
    for page_number in range(num_pages):
        page = pdf_reader.pages[page_number]
        page_text = page.extract_text()
        print(f"Page {page_number + 1}:\n{page_text}\n")
