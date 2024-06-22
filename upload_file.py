import fitz  # PyMuPDF
from docx import Document

def allowed_file(filename):
    """
    Check if the file has an allowed extension.
    
    Args:
    - filename (str): The name of the file to check.
    
    Returns:
    - bool: True if the file extension is allowed, False otherwise.
    """
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    """
    Extract text from a file based on its extension.
    
    Args:
    - file_path (str): The path to the file.
    
    Returns:
    - str: The extracted text from the file.
    """
    file_extension = file_path.rsplit('.', 1)[1].lower()
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_path)
    elif file_extension == 'txt':
        return extract_text_from_txt(file_path)
    return ''

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file.
    
    Args:
    - file_path (str): The path to the PDF file.
    
    Returns:
    - str: The extracted text from the PDF file.
    """
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_path):
    """
    Extract text from a DOCX file.
    
    Args:
    - file_path (str): The path to the DOCX file.
    
    Returns:
    - str: The extracted text from the DOCX file.
    """
    doc = Document(file_path)
    full_text = [para.text for para in doc.paragraphs]
    return '\n'.join(full_text)

def extract_text_from_txt(file_path):
    """
    Extract text from a TXT file.
    
    Args:
    - file_path (str): The path to the TXT file.
    
    Returns:
    - str: The extracted text from the TXT file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# Example usage
if __name__ == "__main__":
    file_path = "example.pdf"
    if allowed_file(file_path):
        text = extract_text_from_file(file_path)
        print("Extracted Text:", text)
