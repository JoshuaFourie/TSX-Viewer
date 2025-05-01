"""
File utility functions for TSX Component Manager
"""
import os
import shutil
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

def ensure_directory(directory: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        directory: Directory path to ensure exists
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False

def copy_file(source: str, destination: str) -> bool:
    """
    Copy a file from source to destination
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.error(f"Error copying file from {source} to {destination}: {e}")
        return False

def write_text_file(filepath: str, content: str) -> bool:
    """
    Write text content to a file
    
    Args:
        filepath: Path to write to
        content: Text content to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {filepath}: {e}")
        return False

def read_text_file(filepath: str) -> Optional[str]:
    """
    Read text content from a file
    
    Args:
        filepath: Path to read from
        
    Returns:
        File content or None if error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None