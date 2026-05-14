"""
RNV Text Transformer - File Handler Module
Handles reading and writing various file formats

Python 3.13 Optimized:
- Match statement for cleaner file type dispatch
- Exception chaining with 'from' clause
- Modern type hints
- Pathlib integration
- Robust error handling for edge cases
- Lazy imports for heavy modules (docx, pypdf, striprtf)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import BadZipFile

from utils.config import MAX_FILE_SIZE, SUPPORTED_EXTENSIONS
from utils.logger import get_module_logger

_logger = get_module_logger("FileHandler")

if TYPE_CHECKING:
    from os import PathLike


class FileReadError(Exception):
    """Custom exception for file reading errors."""
    __slots__ = ()


class FileWriteError(Exception):
    """Custom exception for file writing errors."""
    __slots__ = ()


class FileHandler:
    """
    Handles file operations for multiple formats.
    
    Supports: TXT, MD, DOCX, PDF, RTF, PY, JS, HTML, LOG
    """
    
    __slots__ = ()  # No instance attributes needed
    
    @staticmethod
    def read_file_content(file_path: str | PathLike[str]) -> str | None:
        """
        Read content from various file formats.
        
        Uses Python 3.10+ match statement for cleaner dispatch.
        
        Args:
            file_path: Path to the file to read
        
        Returns:
            File content as string, or None if error
        
        Raises:
            FileReadError: With detailed error message
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        # Validate file exists and is a regular file (single check)
        if not path.is_file():
            if path.exists():
                raise FileReadError(f"Not a regular file (may be directory): {path.name}")
            raise FileReadError(f"File not found: {path.name}")
        
        # Check file size limit
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE // (1024 * 1024)
            raise FileReadError(f"File too large (max {max_mb}MB): {path.name}")
        
        try:
            # Use match statement for cleaner dispatch (Python 3.10+)
            match ext:
                case '.txt' | '.md' | '.py' | '.js' | '.html' | '.log':
                    return FileHandler._read_text_file(path)
                case '.docx':
                    return FileHandler._read_docx_file(path)
                case '.pdf':
                    return FileHandler._read_pdf_file(path)
                case '.rtf':
                    return FileHandler._read_rtf_file(path)
                case _:
                    # Default to text for unknown extensions
                    return FileHandler._read_text_file(path)
                    
        except UnicodeDecodeError as e:
            # Try with different encoding
            if _logger:
                _logger.warning(f"UTF-8 decode failed for {path.name}", details="trying latin-1 fallback")
            try:
                with open(path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as fallback_error:
                if _logger:
                    _logger.error(f"Encoding fallback failed for {path.name}", error=fallback_error)
                raise FileReadError(f"Encoding error: {fallback_error}") from e
        
        except FileReadError:
            raise  # Re-raise our custom exceptions
        
        except Exception as e:
            if _logger:
                _logger.error(f"Failed to read {ext} file: {path.name}", error=e)
            raise FileReadError(f"Failed to read {ext} file: {e}") from e
    
    @staticmethod
    def _read_text_file(file_path: Path) -> str:
        """
        Read plain text file with UTF-8 encoding.
        
        Args:
            file_path: Path object to the file
            
        Returns:
            File contents as string
        """
        return file_path.read_text(encoding='utf-8')
    
    @staticmethod
    def _read_docx_file(file_path: Path) -> str:
        """
        Read Microsoft Word document.
        
        Args:
            file_path: Path object to the .docx file
            
        Returns:
            Extracted text from document
            
        Raises:
            FileReadError: If document is corrupted or invalid
        """
        # Lazy import - only load when needed
        import docx
        
        try:
            doc = docx.Document(str(file_path))
            return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
        except BadZipFile as e:
            if _logger:
                _logger.error(f"Invalid .docx file: {file_path.name}", error=e)
            raise FileReadError("Invalid or corrupted Word document (not a valid .docx file)") from e
        except Exception as e:
            # Catch other docx-related errors
            error_msg = str(e).lower()
            if 'package' in error_msg or 'corrupt' in error_msg:
                if _logger:
                    _logger.error(f"Corrupted .docx file: {file_path.name}", error=e)
                raise FileReadError("Corrupted Word document - file may be damaged") from e
            if _logger:
                _logger.error(f"Error reading .docx: {file_path.name}", error=e)
            raise FileReadError(f"Error reading Word document: {e}") from e
    
    @staticmethod
    def _read_pdf_file(file_path: Path) -> str:
        """
        Read PDF document.
        
        Args:
            file_path: Path object to the .pdf file
            
        Returns:
            Extracted text from all pages
            
        Raises:
            FileReadError: If PDF is encrypted or contains no extractable text
        """
        # Lazy import - only load when needed
        from pypdf import PdfReader
        
        try:
            reader = PdfReader(str(file_path))
            
            # Check for password protection
            if reader.is_encrypted:
                raise FileReadError("Cannot read password-protected PDF files")
            
            # Extract text from all pages
            text = '\n'.join(
                page.extract_text() or ''
                for page in reader.pages
            )
            
            # Check if any text was extracted
            if not text.strip():
                raise FileReadError(
                    "PDF contains no extractable text (may be scanned/image-only)"
                )
            
            return text
            
        except FileReadError:
            raise  # Re-raise our custom errors
        except Exception as e:
            if _logger:
                _logger.error(f"Error reading PDF: {file_path.name}", error=e)
            raise FileReadError(f"Error reading PDF: {e}") from e
    
    @staticmethod
    def _read_rtf_file(file_path: Path) -> str:
        """
        Read Rich Text Format file.
        
        Args:
            file_path: Path object to the .rtf file
            
        Returns:
            Plain text extracted from RTF
            
        Raises:
            FileReadError: If RTF cannot be parsed
        """
        # Lazy import - only load when needed
        from striprtf.striprtf import rtf_to_text
        
        # Try UTF-8 first, fall back to Windows-1252 (common for RTF files)
        rtf_content: str | None = None
        
        try:
            rtf_content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                rtf_content = file_path.read_text(encoding='windows-1252')
            except UnicodeDecodeError:
                # Last resort: latin-1 accepts any byte sequence
                rtf_content = file_path.read_text(encoding='latin-1')
        
        try:
            return rtf_to_text(rtf_content)
        except Exception as e:
            if _logger:
                _logger.error(f"Error parsing RTF: {file_path.name}", error=e)
            raise FileReadError(f"Error parsing RTF content: {e}") from e
    
    @staticmethod
    def write_text_file(file_path: str | PathLike[str], content: str) -> None:
        """
        Write content to a text file.
        
        Args:
            file_path: Path to save the file
            content: Text content to write
        
        Raises:
            FileWriteError: If write fails
        """
        try:
            path = Path(file_path)
            path.write_text(content, encoding='utf-8')
        except Exception as e:
            if _logger:
                _logger.error(f"Error saving file: {Path(file_path).name}", error=e)
            raise FileWriteError(f"Error saving file: {e}") from e
    
    @staticmethod
    def get_file_name(file_path: str | PathLike[str]) -> str:
        """
        Get filename from path.
        
        Args:
            file_path: Full file path
        
        Returns:
            Filename only (without directory)
        """
        return Path(file_path).name
    
    @staticmethod
    def get_file_extension(file_path: str | PathLike[str]) -> str:
        """
        Get file extension from path.
        
        Args:
            file_path: Full file path
        
        Returns:
            File extension (including dot)
        """
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def is_supported_format(file_path: str | PathLike[str]) -> bool:
        """
        Check if file format is supported using O(1) frozenset lookup.
        
        Args:
            file_path: Full file path
        
        Returns:
            True if format is supported
        """
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_EXTENSIONS