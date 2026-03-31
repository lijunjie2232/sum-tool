"""
Utility functions for sumtool.

Provides file path handling, .sum file reading/writing, and pattern matching.
"""

import os
import fnmatch
from pathlib import Path
from typing import List, Tuple, Optional


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Get the relative path of a file relative to the base path.
    
    Args:
        file_path: Absolute or relative path to the file
        base_path: Base directory path to calculate relative path from
        
    Returns:
        Relative path string
    """
    abs_file = os.path.abspath(file_path)
    abs_base = os.path.abspath(base_path)
    rel_path = os.path.relpath(abs_file, abs_base)
    return rel_path


def find_sum_file(directory: str) -> Optional[str]:
    """
    Find a .sum file in the given directory.
    
    Args:
        directory: Directory to search in
        
    Returns:
        Path to the first .sum file found, or None if not found
    """
    dir_path = Path(directory)
    sum_files = list(dir_path.glob("*.sum"))
    
    if sum_files:
        return str(sum_files[0])
    return None


def read_sum_file(sum_file_path: str) -> List[Tuple[str, str]]:
    """
    Read a .sum file and return list of (hash, filepath) tuples.
    
    Args:
        sum_file_path: Path to the .sum file
        
    Returns:
        List of (hash_value, relative_path) tuples
        
    Raises:
        ValueError: If the file format is invalid
    """
    checksums = []
    
    with open(sum_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Standard checksum format: "hash  filename" (two spaces)
            parts = line.split('  ', 1)
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid format at line {line_num}: expected 'hash  filepath'"
                )
            
            hash_value, filepath = parts
            checksums.append((hash_value.strip(), filepath.strip()))
    
    return checksums


def write_sum_file(
    checksums: List[Tuple[str, str]],
    output_path: str,
    algorithm: str = "sha256"
) -> None:
    """
    Write checksums to a .sum file.
    
    Args:
        checksums: List of (hash_value, relative_path) tuples
        output_path: Path to the output .sum file
        algorithm: Hash algorithm name (for comment header)
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {algorithm.upper()} checksums\n")
        for hash_value, filepath in checksums:
            f.write(f"{hash_value}  {filepath}\n")


def should_exclude(file_path: str, exclude_patterns: List[str]) -> bool:
    """
    Check if a file path matches any of the exclude patterns.
    
    Args:
        file_path: Path to check (relative path)
        exclude_patterns: List of glob patterns to exclude
        
    Returns:
        True if the file should be excluded
    """
    if not exclude_patterns:
        return False
    
    for pattern in exclude_patterns:
        # Match against the full relative path
        if fnmatch.fnmatch(file_path, pattern):
            return True
        
        # Also match against just the filename
        filename = os.path.basename(file_path)
        if fnmatch.fnmatch(filename, pattern):
            return True
        
        # Check if any part of the path matches (for directory exclusion)
        path_parts = Path(file_path).parts
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True
    
    return False


def collect_files(
    paths: List[str],
    exclude_patterns: Optional[List[str]] = None
) -> List[Tuple[str, str]]:
    """
    Collect all files from the given paths, respecting exclude patterns.
    
    Args:
        paths: List of directory or file paths to process
        exclude_patterns: List of glob patterns to exclude
        
    Returns:
        List of (absolute_file_path, relative_file_path) tuples
    """
    if exclude_patterns is None:
        exclude_patterns = []
    
    collected = []
    
    for path in paths:
        path = os.path.abspath(path)
        
        if os.path.isfile(path):
            # Single file - use parent directory as base for relative path
            base_dir = os.path.dirname(path)
            rel_path = os.path.basename(path)
            
            if not should_exclude(rel_path, exclude_patterns):
                collected.append((path, rel_path))
        
        elif os.path.isdir(path):
            # Directory - recursively walk
            for root, dirs, files in os.walk(path):
                # Filter out excluded directories
                dirs[:] = [
                    d for d in dirs
                    if not should_exclude(d, exclude_patterns)
                ]
                
                for filename in files:
                    abs_file = os.path.join(root, filename)
                    rel_path = get_relative_path(abs_file, path)
                    
                    if not should_exclude(rel_path, exclude_patterns):
                        collected.append((abs_file, rel_path))
    
    return collected
