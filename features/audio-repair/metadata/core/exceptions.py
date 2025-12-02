"""
Custom exceptions for metadata processing.
"""


class MetadataProcessingError(Exception):
    """Base exception for metadata processing errors."""
    
    def __init__(self, message: str, file_path: str = None, original_error: Exception = None):
        self.message = message
        self.file_path = file_path
        self.original_error = original_error
        super().__init__(self.message)


class MusicBrainzError(MetadataProcessingError):
    """Error related to MusicBrainz API operations."""
    
    def __init__(self, message: str, status_code: int = None, response_data: str = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class FileProcessingError(MetadataProcessingError):
    """Error related to file operations."""
    
    def __init__(self, message: str, file_path: str, operation: str = None):
        self.operation = operation
        super().__init__(message, file_path)


class MetadataWriteError(FileProcessingError):
    """Error writing metadata to file."""
    
    def __init__(self, message: str, file_path: str, backup_path: str = None):
        self.backup_path = backup_path
        super().__init__(message, file_path, "write")


class MetadataParsingError(MetadataProcessingError):
    """Error parsing metadata from file or filename."""
    
    def __init__(self, message: str, source: str, file_path: str = None):
        self.source = source  # 'filename', 'embedded', etc.
        super().__init__(message, file_path)


class ConfigurationError(MetadataProcessingError):
    """Error in configuration or setup."""
    pass


class ValidationError(MetadataProcessingError):
    """Error validating metadata."""
    
    def __init__(self, message: str, field_name: str = None, field_value: str = None):
        self.field_name = field_name
        self.field_value = field_value
        super().__init__(message)