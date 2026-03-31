"""
Calculator module for computing file checksums.

Supports MD5, SHA1, SHA256, and SHA512 hash algorithms.
"""

import hashlib
from pathlib import Path
from typing import List, Tuple, Optional

from .utils import collect_files, write_sum_file


# Supported hash algorithms
SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a single file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        ValueError: If the algorithm is not supported
        FileNotFoundError: If the file doesn't exist
    """
    algorithm = algorithm.lower()
    
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. "
            f"Supported: {', '.join(SUPPORTED_ALGORITHMS.keys())}"
        )
    
    hash_func = SUPPORTED_ALGORITHMS[algorithm]()
    
    # Read file in chunks to handle large files efficiently
    chunk_size = 8192
    
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def calculate_checksums(
    paths: List[str],
    algorithm: str = "sha256",
    exclude_patterns: Optional[List[str]] = None,
    output_file: Optional[str] = None
) -> List[Tuple[str, str]]:
    """
    Calculate checksums for all files in the given paths.
    
    Args:
        paths: List of directory or file paths to process
        algorithm: Hash algorithm to use (default: sha256)
        exclude_patterns: List of glob patterns to exclude
        output_file: Optional path to write the checksums file
        
    Returns:
        List of (hash_value, relative_path) tuples
        
    Raises:
        ValueError: If the algorithm is not supported
    """
    algorithm = algorithm.lower()
    
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. "
            f"Supported: {', '.join(SUPPORTED_ALGORITHMS.keys())}"
        )
    
    # Collect all files to process
    files = collect_files(paths, exclude_patterns)
    
    # Calculate checksums
    checksums = []
    for abs_path, rel_path in files:
        try:
            hash_value = calculate_file_hash(abs_path, algorithm)
            checksums.append((hash_value, rel_path))
        except (IOError, OSError) as e:
            print(f"Warning: Could not read file {abs_path}: {e}")
            continue
    
    # Write to output file if specified
    if output_file:
        # Ensure output file has .sum extension
        if not output_file.endswith('.sum'):
            output_file += '.sum'
        
        # Create parent directories if they don't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        write_sum_file(checksums, output_file, algorithm)
        print(f"Checksums written to: {output_file}")
    
    return checksums


def get_algorithm_help() -> str:
    """
    Get help text for supported algorithms.
    
    Returns:
        String describing supported algorithms
    """
    algorithms = ', '.join(sorted(SUPPORTED_ALGORITHMS.keys()))
    return f"Supported algorithms: {algorithms}"
