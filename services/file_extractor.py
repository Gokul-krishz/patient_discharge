"""
File text extraction service
Handles extraction of text from various file formats
"""
import PyPDF2
import docx
from PIL import Image
import pytesseract
from typing import Optional

class FileExtractor:
    """Service for extracting text from files"""
    
    @staticmethod
    def extract_from_pdf(filepath: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
        return text.strip()
    
    @staticmethod
    def extract_from_docx(filepath: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(filepath)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise Exception(f"Error extracting DOCX: {str(e)}")
        return text.strip()
    
    @staticmethod
    def extract_from_image(filepath: str) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image)
        except Exception as e:
            raise Exception(f"Error extracting text from image: {str(e)}")
        return text.strip()
    
    @staticmethod
    def extract_from_txt(filepath: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            raise Exception(f"Error reading text file: {str(e)}")
        return text.strip()
    
    @staticmethod
    def extract_text(filepath: str, filename: str) -> str:
        """
        Extract text from file based on extension
        
        Args:
            filepath: Full path to the file
            filename: Name of the file (to determine extension)
            
        Returns:
            Extracted text content
        """
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        extractors = {
            'pdf': FileExtractor.extract_from_pdf,
            'docx': FileExtractor.extract_from_docx,
            'txt': FileExtractor.extract_from_txt,
            'png': FileExtractor.extract_from_image,
            'jpg': FileExtractor.extract_from_image,
            'jpeg': FileExtractor.extract_from_image,
            'gif': FileExtractor.extract_from_image,
            'bmp': FileExtractor.extract_from_image,
        }
        
        extractor = extractors.get(extension)
        if not extractor:
            raise Exception(f"Unsupported file format: {extension}")
        
        return extractor(filepath)
