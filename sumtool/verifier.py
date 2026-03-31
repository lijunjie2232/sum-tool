"""
Verifier module for verifying file checksums.

Reads .sum files and verifies that files match the recorded checksums.
"""

import os
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .utils import read_sum_file, find_sum_file
from .calculator import calculate_file_hash


@dataclass
class VerificationResult:
    """Result of a single file verification."""
    filepath: str
    expected: str
    actual: Optional[str]
    status: str  # 'OK', 'FAILED', 'MISSING', 'ERROR'
    error_message: Optional[str] = None


def verify_single_file(
    file_path: str,
    expected_hash: str,
    algorithm: str = "sha256"
) -> VerificationResult:
    """
    Verify a single file's checksum.
    
    Args:
        file_path: Path to the file to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm used
        
    Returns:
        VerificationResult object
    """
    if not os.path.exists(file_path):
        return VerificationResult(
            filepath=file_path,
            expected=expected_hash,
            actual=None,
            status='MISSING',
            error_message="File not found"
        )
    
    try:
        actual_hash = calculate_file_hash(file_path, algorithm)
        
        if actual_hash == expected_hash:
            return VerificationResult(
                filepath=file_path,
                expected=expected_hash,
                actual=actual_hash,
                status='OK'
            )
        else:
            return VerificationResult(
                filepath=file_path,
                expected=expected_hash,
                actual=actual_hash,
                status='FAILED',
                error_message="Checksum mismatch"
            )
    
    except Exception as e:
        return VerificationResult(
            filepath=file_path,
            expected=expected_hash,
            actual=None,
            status='ERROR',
            error_message=str(e)
        )


def detect_algorithm(checksums: List[Tuple[str, str]]) -> str:
    """
    Detect the hash algorithm based on hash length.
    
    Args:
        checksums: List of (hash_value, filepath) tuples
        
    Returns:
        Detected algorithm name
    """
    if not checksums:
        return "sha256"  # Default
    
    # Check first non-comment entry
    hash_value = checksums[0][0]
    
    # Map hash length to algorithm
    hash_lengths = {
        32: "md5",
        40: "sha1",
        64: "sha256",
        128: "sha512",
    }
    
    return hash_lengths.get(len(hash_value), "sha256")


def verify_checksums(
    directory: str,
    sum_file: Optional[str] = None
) -> List[VerificationResult]:
    """
    Verify all files listed in a .sum file.
    
    Args:
        directory: Directory containing the files to verify
        sum_file: Path to the .sum file (optional, will search if not provided)
        
    Returns:
        List of VerificationResult objects
        
    Raises:
        FileNotFoundError: If no .sum file is found
        ValueError: If .sum file format is invalid
    """
    # Find .sum file if not specified
    if sum_file is None:
        sum_file = find_sum_file(directory)
        if sum_file is None:
            raise FileNotFoundError(
                f"No .sum file found in directory: {directory}"
            )
    
    # Read checksums from file
    recorded_checksums = read_sum_file(sum_file)
    
    # Detect algorithm from hash length
    algorithm = detect_algorithm(recorded_checksums)
    
    # Get the base directory for relative paths
    # The .sum file location is the reference point
    sum_file_dir = os.path.dirname(os.path.abspath(sum_file))
    
    # Verify each file
    results = []
    for expected_hash, rel_path in recorded_checksums:
        # Construct absolute path from relative path
        abs_path = os.path.join(sum_file_dir, rel_path)
        
        result = verify_single_file(abs_path, expected_hash, algorithm)
        results.append(result)
    
    return results


def print_verification_results(
    results: List[VerificationResult],
    verbose: bool = False
) -> Tuple[int, int, int, int]:
    """
    Print verification results with enhanced formatting and return summary counts.
    
    Args:
        results: List of VerificationResult objects
        verbose: If True, print all results including OK ones
        
    Returns:
        Tuple of (ok_count, failed_count, missing_count, error_count)
    """
    ok_count = 0
    failed_count = 0
    missing_count = 0
    error_count = 0
    
    # First pass: count results
    for result in results:
        if result.status == 'OK':
            ok_count += 1
        elif result.status == 'FAILED':
            failed_count += 1
        elif result.status == 'MISSING':
            missing_count += 1
        elif result.status == 'ERROR':
            error_count += 1
    
    # Print header
    total = len(results)
    print("\n" + "=" * 70)
    print("📋 FILE VERIFICATION REPORT")
    print("=" * 70)
    
    # Print detailed results
    if failed_count > 0:
        print(f"\n❌ FAILED FILES ({failed_count}):")
        print("-" * 70)
        for result in results:
            if result.status == 'FAILED':
                print(f"  ✗ {result.filepath}")
                print(f"    Reason: {result.error_message}")
                print(f"    Expected: {result.expected}")
                print(f"    Got:      {result.actual}")
                print()
    
    if missing_count > 0:
        print(f"\n⚠️  MISSING FILES ({missing_count}):")
        print("-" * 70)
        for result in results:
            if result.status == 'MISSING':
                print(f"  ? {result.filepath}")
                print(f"    Reason: {result.error_message}")
                print()
    
    if error_count > 0:
        print(f"\n💥 ERRORS ({error_count}):")
        print("-" * 70)
        for result in results:
            if result.status == 'ERROR':
                print(f"  ! {result.filepath}")
                print(f"    Error: {result.error_message}")
                print()
    
    if verbose and ok_count > 0:
        print(f"\n✅ VERIFIED FILES ({ok_count}):")
        print("-" * 70)
        for result in results:
            if result.status == 'OK':
                print(f"  ✓ {result.filepath}")
    
    return ok_count, failed_count, missing_count, error_count


def summarize_verification(
    ok_count: int,
    failed_count: int,
    missing_count: int,
    error_count: int
) -> bool:
    """
    Print verification summary with enhanced formatting and return overall success status.
    
    Args:
        ok_count: Number of successful verifications
        failed_count: Number of failed verifications
        missing_count: Number of missing files
        error_count: Number of errors
        
    Returns:
        True if all files verified successfully, False otherwise
    """
    total = ok_count + failed_count + missing_count + error_count
    
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"  Total Files:    {total}")
    print(f"  ✅ Verified:     {ok_count}")
    if failed_count > 0:
        print(f"  ❌ Failed:      {failed_count}")
    if missing_count > 0:
        print(f"  ⚠️  Missing:     {missing_count}")
    if error_count > 0:
        print(f"  💥 Errors:      {error_count}")
    print("=" * 70)
    
    success = (failed_count == 0 and missing_count == 0 and error_count == 0)
    
    if success:
        print("\n🎉 SUCCESS! All files verified successfully!")
        print("✨ File integrity confirmed.\n")
    else:
        print("\n❌ VERIFICATION FAILED!")
        problems = []
        if failed_count > 0:
            problems.append(f"{failed_count} file(s) have mismatched checksums")
        if missing_count > 0:
            problems.append(f"{missing_count} file(s) are missing")
        if error_count > 0:
            problems.append(f"{error_count} error(s) occurred")
        print("⚠️  Issues found:")
        for i, problem in enumerate(problems, 1):
            print(f"   {i}. {problem}")
        print("\n⚠️  File integrity compromised. Please investigate the issues above.\n")
    
    return success
