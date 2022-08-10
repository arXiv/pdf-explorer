import PyPDF2
from PyPDF2 import PdfFileReader
import os

def get_reader (fname):
    try:
        return PdfFileReader(fname)
    except PyPDF2.errors.PdfReadError:
        return None

def get_num_words (reader):
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return len(text.split())

def check_bitmapped_pages (fname):
    reader = get_reader(fname)
    if not reader:
        raise Exception ("Not a PDF")
    fsize = os.path.getsize(fname)
    num_words = get_num_words (reader)
    if num_words == 0 or num_words < 200 or fsize / num_words > 2000:
        return True
    return False