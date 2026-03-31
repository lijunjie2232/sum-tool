"""
Calculator module for computing file checksums.

Supports MD5, SHA1, SHA256, and SHA512 hash algorithms.
"""

import hashlib
import multiprocessing as mp
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


def calculate_file_hash_worker(args: Tuple[str, str]) -> Tuple[str, str, str]:
    """
    Worker function for multiprocessing.Pool to calculate file hash.
    
    Args:
        args: Tuple of (file_path, algorithm)
        
    Returns:
        Tuple of (abs_path, rel_path, hash_value) or (abs_path, rel_path, None) on error
    """
    abs_path, rel_path, algorithm = args
    try:
        hash_value = calculate_file_hash(abs_path, algorithm)
        return (abs_path, rel_path, hash_value)
    except (IOError, OSError) as e:
        print(f"Warning: Could not read file {abs_path}: {e}")
        return (abs_path, rel_path, None)


def calculate_checksums(
    paths: List[str],
    algorithm: str = "sha256",
    exclude_patterns: Optional[List[str]] = None,
    output_file: Optional[str] = None,
    threads: int = 1,
    quiet: bool = False
) -> List[Tuple[str, str]]:
    """
    Calculate checksums for all files in the given paths.
    
    Args:
        paths: List of directory or file paths to process
        algorithm: Hash algorithm to use (default: sha256)
        exclude_patterns: List of glob patterns to exclude
        output_file: Optional path to write the checksums file (if None, print to stdout)
        threads: Number of parallel processes to use (default: 1)
        quiet: If True and no output_file, don't print results (default: False)
        
    Returns:
        List of (hash_value, relative_path) tuples sorted by path
        
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
    
    if not files:
        return []
    
    # Prepare arguments for worker function
    worker_args = [(abs_path, rel_path, algorithm) for abs_path, rel_path in files]
    
    # Calculate checksums using multiprocessing
    checksums = []
    
    if threads > 1:
        # Use multiprocessing Pool
        with mp.Pool(processes=threads) as pool:
            results = pool.map(calculate_file_hash_worker, worker_args)
            
            # Filter out failed calculations
            for abs_path, rel_path, hash_value in results:
                if hash_value is not None:
                    checksums.append((hash_value, rel_path))
    else:
        # Single-threaded calculation
        for abs_path, rel_path in files:
            try:
                hash_value = calculate_file_hash(abs_path, algorithm)
                checksums.append((hash_value, rel_path))
            except (IOError, OSError) as e:
                print(f"Warning: Could not read file {abs_path}: {e}")
                continue
    
    # Sort checksums by relative path for consistent output
    checksums.sort(key=lambda x: x[1])
    
    # Write to output file if specified, otherwise print to stdout
    if output_file:
        # Ensure output file has .sum extension
        if not output_file.endswith('.sum'):
            output_file += '.sum'
        
        # Create parent directories if they don't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        write_sum_file(checksums, output_file, algorithm)
        if not quiet:
            print(f"Checksums written to: {output_file}")
    elif not quiet:
        # Print results to stdout in standard checksum format
        print(f"# {algorithm.upper()} checksums")
        for hash_value, rel_path in checksums:
            print(f"{hash_value}  {rel_path}")
    
    return checksums


def get_algorithm_help() -> str:
    """
    Get help text for supported algorithms.
    
    Returns:
        String describing supported algorithms
    """
    algorithms = ', '.join(sorted(SUPPORTED_ALGORITHMS.keys()))
    return f"Supported algorithms: {algorithms}"
