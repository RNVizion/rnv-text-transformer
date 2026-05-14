"""
RNV Text Transformer - Batch Processor Module
Handles batch processing of multiple files

Python 3.13 Optimized:
- Modern type hints
- Generator-based processing for memory efficiency
- Proper error handling per file

"""

from __future__ import annotations

from pathlib import Path
from typing import Generator, NamedTuple
from dataclasses import dataclass

from core.text_transformer import TextTransformer
from utils.file_handler import FileHandler, FileReadError, FileWriteError
from utils.config import SUPPORTED_EXTENSIONS
from utils.logger import get_module_logger

_logger = get_module_logger("BatchProcessor")


@dataclass
class BatchResult:
    """Result of processing a single file."""
    file_path: Path
    success: bool
    message: str
    original_size: int = 0
    processed_size: int = 0


class BatchProgress(NamedTuple):
    """Progress information for batch processing."""
    current: int
    total: int
    current_file: str
    percent: float


class BatchProcessor:
    """
    Handles batch processing of multiple files.
    
    Supports:
    - Processing all supported files in a folder
    - Recursive folder processing
    - Output to same location or new folder
    - Progress reporting via generator
    """
    
    __slots__ = ('transform_mode', 'recursive', 'output_folder', '_cancelled')
    
    def __init__(
        self,
        transform_mode: str,
        recursive: bool = False,
        output_folder: Path | None = None
    ) -> None:
        """
        Initialize batch processor.
        
        Args:
            transform_mode: Transformation mode to apply
            recursive: If True, process subfolders recursively
            output_folder: Output folder (None = same as source)
        """
        self.transform_mode = transform_mode
        self.recursive = recursive
        self.output_folder = output_folder
        self._cancelled = False
    
    def cancel(self) -> None:
        """Request cancellation of batch processing."""
        self._cancelled = True
    
    def get_supported_files(self, folder: Path) -> list[Path]:
        """
        Get list of supported files in folder.
        
        Args:
            folder: Folder to scan
            
        Returns:
            List of supported file paths
        """
        files: list[Path] = []
        
        if self.recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in folder.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(file_path)
        
        return sorted(files)
    
    def process_folder(
        self, 
        folder: Path
    ) -> Generator[tuple[BatchProgress, BatchResult | None], None, list[BatchResult]]:
        """
        Process all supported files in a folder.
        
        This is a generator that yields progress updates and results.
        The final return value is the complete list of results.
        
        Args:
            folder: Folder containing files to process
            
        Yields:
            Tuple of (BatchProgress, BatchResult or None)
            
        Returns:
            List of all BatchResult objects
        """
        files = self.get_supported_files(folder)
        total = len(files)
        results: list[BatchResult] = []
        
        if total == 0:
            return results
        
        for i, file_path in enumerate(files):
            if self._cancelled:
                # Add cancelled result for remaining files
                result = BatchResult(
                    file_path=file_path,
                    success=False,
                    message="Cancelled"
                )
                results.append(result)
                continue
            
            # Yield progress before processing
            progress = BatchProgress(
                current=i + 1,
                total=total,
                current_file=file_path.name,
                percent=(i / total) * 100
            )
            yield (progress, None)
            
            # Process the file
            result = self._process_file(file_path, folder)
            results.append(result)
            
            # Yield result after processing
            yield (progress, result)
        
        return results
    
    def _process_file(self, file_path: Path, source_folder: Path) -> BatchResult:
        """
        Process a single file.
        
        Args:
            file_path: Path to file to process
            source_folder: Source folder (for relative path calculation)
            
        Returns:
            BatchResult with processing outcome
        """
        try:
            # Read file content
            content = FileHandler.read_file_content(file_path)
            if content is None:
                return BatchResult(
                    file_path=file_path,
                    success=False,
                    message="Could not read file content"
                )
            
            original_size = len(content)
            
            # Transform content
            transformed = TextTransformer.transform_text(content, self.transform_mode)
            processed_size = len(transformed)
            
            # Determine output path
            output_path = self._get_output_path(file_path, source_folder)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write transformed content
            # For non-text files, we write as .txt
            if file_path.suffix.lower() not in ('.txt', '.md', '.py', '.js', '.html', '.log'):
                output_path = output_path.with_suffix('.txt')
            
            FileHandler.write_text_file(output_path, transformed)
            
            return BatchResult(
                file_path=file_path,
                success=True,
                message=f"Saved to {output_path.name}",
                original_size=original_size,
                processed_size=processed_size
            )
            
        except FileReadError as e:
            if _logger:
                _logger.warning(f"Batch read error: {file_path.name}", details=str(e))
            return BatchResult(
                file_path=file_path,
                success=False,
                message=f"Read error: {e}"
            )
        except FileWriteError as e:
            if _logger:
                _logger.warning(f"Batch write error: {file_path.name}", details=str(e))
            return BatchResult(
                file_path=file_path,
                success=False,
                message=f"Write error: {e}"
            )
        except Exception as e:
            if _logger:
                _logger.error(f"Unexpected batch error: {file_path.name}", error=e)
            return BatchResult(
                file_path=file_path,
                success=False,
                message=f"Error: {e}"
            )
    
    def _get_output_path(self, file_path: Path, source_folder: Path) -> Path:
        """
        Get output path for a processed file.
        
        Args:
            file_path: Original file path
            source_folder: Source folder root
            
        Returns:
            Output file path
        """
        if self.output_folder is None:
            # Same location - add suffix to filename
            stem = file_path.stem
            suffix = file_path.suffix
            return file_path.with_name(f"{stem}_transformed{suffix}")
        else:
            # Preserve relative path structure in output folder
            try:
                relative = file_path.relative_to(source_folder)
            except ValueError:
                relative = Path(file_path.name)
            
            return self.output_folder / relative
    
    @staticmethod
    def get_summary(results: list[BatchResult]) -> dict:
        """
        Get summary statistics from batch results.
        
        Args:
            results: List of BatchResult objects
            
        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        total_original = sum(r.original_size for r in results if r.success)
        total_processed = sum(r.processed_size for r in results if r.success)
        
        return {
            'total_files': total,
            'successful': successful,
            'failed': failed,
            'total_original_bytes': total_original,
            'total_processed_bytes': total_processed,
        }
