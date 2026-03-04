import pdfplumber
import re
from io import BytesIO

def extract_text_from_pdf(pdf_bytes):
    """
    Extracts text from a PDF byte stream using pdfplumber.
    """
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Clean text
        text = clean_text(text)
        
        if not text.strip():
            return None, "No text found in PDF. It might be scanned/image-only."
            
        return text, None
    except Exception as e:
        return None, f"Error extracting PDF: {str(e)}"

def clean_text(text):
    """
    Cleans extracted text by removing extra whitespaces and special characters.
    """
    # Remove excessive newlines and spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text